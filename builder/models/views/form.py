from ..fields import snake_case
from openerp.exceptions import ValidationError
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL
from collections import defaultdict


class FormView(models.Model):
    _name = 'builder.views.form'

    _inherit = ['ir.mixin.polymorphism.subclass']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    states_clickable = fields.Boolean('States Clickable', default=False)
    show_status_bar = fields.Boolean('Show Status Bar', default=False)
    visible_states = fields.Char('Visible States')

    statusbar_button_ids = fields.One2many('builder.views.form.statusbar.button', 'view_id', 'Status Bar Buttons', copy=True)
    button_ids = fields.One2many('builder.views.form.button', 'view_id', 'Buttons', copy=True)
    field_ids = fields.One2many('builder.views.form.field', 'view_id', 'Items', copy=True)

    @api.onchange('inherit_view_id')
    def onchange_inherit_view_id(self):
        self.inherit_view_ref = False
        if self.inherit_view_id:
            data = self.env['ir.model.data'].search([('model', '=', 'ir.ui.view'), ('res_id', '=', self.inherit_view_id.id)])
            self.inherit_view_ref = "{module}.{id}".format(module=data.module, id=data.name) if data else False

    @api.onchange('type')
    def onchange_type(self):
        self.inherit_view_ref = False
        self.inherit_view_id = False

    @api.onchange('inherit_view')
    def onchange_inherit_view(self):
        if self.inherit_view and self.model_id:
            views = self.env['ir.ui.view'].search([('type', '=', 'form'), ('model', '=', self.model_id.model)])
            if views:
                self.inherit_view_id = views[0].id

    @api.one
    @api.constrains('inherit_view_ref')
    def _check_view_ref(self):
        exists = self.env['ir.model.data'].xmlid_lookup(self.inherit_view_ref)
        if exists:
            view = self.env['ir.model.data'].get_object(*self.inherit_view_ref.split('.'))
            if not view.model == self.model_id.model:
                raise ValidationError("View Ref is not a valid view reference")

    _defaults = {
        'type': 'form',
        'subclass_model': lambda s, c, u, cxt=None: s._name,
    }

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.name = self.model_id.name
        self.xml_id = "view_{snake}_form".format(snake=snake_case(self.model_id.model))
        self.show_status_bar = True if self.model_id.special_states_field_id.id else False
        self.model_inherit_type = self.model_id.inherit_type #shouldn`t be doing that
        self.model_name = self.model_id.model #shouldn`t be doing that

        if not len(self.field_ids):
            field_list = []
            for field in self.model_id.field_ids:
                if field.name in ['state']:
                    continue
                if field.is_inherited and not self.env.context.get('add_inherited_fields', True):
                    continue
                field_list.append({'field_id': field.id, 'widget': DEFAULT_WIDGETS_BY_TYPE.get(field.ttype), 'field_ttype': field.ttype, 'model_id': self.model_id.id, 'special_states_field_id': self.model_id.special_states_field_id.id})

            self.field_ids = field_list

    @api.model
    def create_instance(self, id):
        self.create({
            'view_id': id,
        })

    @api.multi
    def action_save(self):
        return {'type': 'ir.actions.act_window_close'}

    @property
    def flat_fields(self):
        return [
            field for field in self.field_ids if not field.page
        ]

    @property
    def pages(self):
        pages = defaultdict(list)
        [
            pages[field.page].append(field)
            for field in self.field_ids
            if field.page
        ]
        return pages


DEFAULT_WIDGETS_BY_TYPE = {
    'binary': 'image'
}


class StatusBarActionButton(models.Model):
    _name = 'builder.views.form.statusbar.button'

    _order = 'sequence, name'

    view_id = fields.Many2one('builder.views.form', string='View', ondelete='cascade')
    model_id = fields.Many2one('builder.ir.model', string='Model', related='view_id.view_id.model_id', store=True)
    special_states_field_id = fields.Many2one('builder.ir.model.fields', related='model_id.special_states_field_id', string='States Field')
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    highlighted = fields.Boolean('Highlighted')
    type = fields.Selection(
        [
            ('action', 'Defined Action'),
            ('object', 'Model Action'),
        ],
        'Type',
        required=True
    )
    states = fields.Char('States')
    method_name = fields.Char('Method Name')
    action_ref = fields.Char('Action Reference')
    domain = fields.Char('Domain')
    context = fields.Char('Context')

    @api.onchange('type', 'name')
    def _onchange_type(self):
        if (self.type == 'object') and self.name:
            self.method_name = "action_{name}".format(name=snake_case(self.name.replace(' ', '.')).lower())


class FormField(models.Model):
    _name = 'builder.views.form.field'
    _inherit = 'builder.views.abstract.field'

    view_id = fields.Many2one('builder.views.form', string='View', ondelete='cascade')
    page = fields.Char('Page')

    related_field_view_type = fields.Selection([('default', 'Default'), ('defined', 'Defined'), ('custom', 'Custom')], 'View Type', default='default')
    related_field_form_ref = fields.Char('Form View ID')
    related_field_tree_ref = fields.Char('Tree View ID')
    domain = fields.Char('Domain')
    context = fields.Char('Context')
    related_field_mode = fields.Selection([('tree', 'Tree'), ('form', 'Form')], 'Mode', default='tree')
    related_field_tree_editable = fields.Selection([('False', 'No Editable'), ('top', 'Top'), ('bottom', 'Bottom')], 'Tree Editable', default='bottom')

    widget = fields.Selection(FIELD_WIDGETS_ALL, 'Widget')
    widget_options = fields.Char('Widget Options')

    nolabel = fields.Boolean('Hide Label')

    required = fields.Boolean('Required')
    required_condition = fields.Char('Required Condition')

    invisible = fields.Boolean('Invisible')
    invisible_condition = fields.Char('Invisible Condition')

    readonly = fields.Boolean('Readonly')
    readonly_condition = fields.Char('Readonly Condition')

    states = fields.Char('States')

    @api.one
    @api.depends('field_id.ttype')
    def _compute_field_type(self):
        self.field_ttype = self.field_id.ttype

    @property
    def has_attrs(self):
        return self.readonly or self.required or self.invisible


class FormButton(models.Model):
    _name = 'builder.views.form.button'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    view_id = fields.Many2one('builder.views.form', string='View', ondelete='cascade')
    model_id = fields.Many2one('builder.ir.model', string='Model', related='view_id.view_id.model_id', store=True)

    type = fields.Selection(
        [
            ('action', 'Defined Action'),
            ('object', 'Model Action'),
        ],
        'Type',
        required=True
    )

    states = fields.Char('States')

    method_name = fields.Char('Method Name')
    action_ref = fields.Char('Action Reference')
    domain = fields.Char('Domain')
    context = fields.Char('Context')

    icon = fields.Char('Icon')
    field_id = fields.Many2one(
        comodel_name='builder.ir.model.fields',
        string='Count Field',
        ondelete='set null',
    )
    widget = fields.Selection(
        [
            ('info', 'Info'),
            ('percent', 'Percent Pie'),
            ('monetary', 'Monetary'),
            ('barchart', 'Bar Chart'),
            ('progressbar', 'Progress Bar'),
            ('counter', 'Counter'),
        ],
        'Widget'
    )

    @api.onchange('name', 'type')
    def onchange_name(self):
        if self.name:
            self.method_name = 'do_{name}'.format(name=self.name.lower().replace(' ', '_'))









