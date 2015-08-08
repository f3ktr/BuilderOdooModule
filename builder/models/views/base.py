from openerp.exceptions import ValidationError
from openerp import models, api, fields, _

FIELD_WIDGETS_ALL = [
    ('barchart', "FieldBarChart"),
    ('binary', "FieldBinaryFile"),
    ('boolean', "FieldBoolean"),
    ('char', "FieldChar"),
    ('char_domain', "FieldCharDomain"),
    ('date', "FieldDate"),
    ('datetime', "FieldDatetime"),
    ('email', "FieldEmail"),
    ('float', "FieldFloat"),
    ('float_time', "FieldFloat"),
    ('html', "FieldTextHtml"),
    ('image', "FieldBinaryImage"),
    ('integer', "FieldFloat"),
    ('kanban_state_selection', "KanbanSelection"),
    ('many2many', "FieldMany2Many"),
    ('many2many_binary', "FieldMany2ManyBinaryMultiFiles"),
    ('many2many_checkboxes', "FieldMany2ManyCheckBoxes"),
    ('many2many_kanban', "FieldMany2ManyKanban"),
    ('many2many_tags', "FieldMany2ManyTags"),
    ('many2one', "FieldMany2One"),
    ('many2onebutton', "Many2OneButton"),
    ('monetary', "FieldMonetary"),
    ('one2many', "FieldOne2Many"),
    ('one2many_list', "FieldOne2Many"),
    ('percentpie', "FieldPercentPie"),
    ('priority', "Priority"),
    ('progressbar', "FieldProgressBar"),
    ('radio', "FieldRadio"),
    ('reference', "FieldReference"),
    ('selection', "FieldSelection"),
    ('statinfo', "StatInfo"),
    ('statusbar', "FieldStatus"),
    ('text', "FieldText"),
    ('url', "FieldUrl"),
    ('x2many_counter', "X2ManyCounter"),
]


class ViewSelector(models.TransientModel):
    _name = 'builder.views.selector'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    model_id = fields.Many2one('builder.ir.model', 'Model', ondelete='cascade', required=True)
    model_name = fields.Char('Model Name', related='model_id.name', store=False)
    add_inherited_fields = fields.Boolean('Add Inherited Fields', default=True)
    model_inherit_type = fields.Selection([('mixed', 'Mixed'), ('class', 'Class'), ('prototype', 'Prototype'), ('delegation', 'Delegation')], 'Inherit Type', related='model_id.inherit_type')
    special_states_field_id = fields.Many2one('builder.ir.model.fields', 'States Field',
                                              related='model_id.special_states_field_id')
    model_groups_date_field_ids = fields.One2many('builder.ir.model.fields', string='Has Date Fields',
                                                  related='model_id.groups_date_field_ids')
    type = fields.Selection(
        [
            ('form', 'Form'),
            ('tree', 'Tree'),
            ('calendar', 'Calendar'),
            ('gantt', 'Gantt'),
            ('kanban', 'Kanban'),
            ('graph', 'Graph'),
            ('search', 'Search'),
            ('diagram', 'Diagram'),
        ], 'Type', required=True, default='form')

    inherit_view = fields.Boolean('Inherit')
    inherit_view_id = fields.Many2one('ir.ui.view', 'Inherit View')
    inherit_view_ref = fields.Char('Inherit View Ref')

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
        if self.inherit_view and self.model_id and self.type:
            views = self.env['ir.ui.view'].search([('type', '=', self.type), ('model', '=', self.model_id.model)])
            if views:
                self.inherit_view_id = views[0].id

    @api.one
    @api.constrains('inherit_view_ref')
    def _check_view_ref(self):
        if self.inherit_view_ref:
            exists = self.env['ir.model.data'].xmlid_lookup(self.inherit_view_ref)
            if exists:
                view = self.env['ir.model.data'].get_object(*self.inherit_view_ref.split('.'))
                if not view.model == self.model_id.model:
                    raise ValidationError("View Ref is not a valid view reference")

    @api.multi
    def action_show_view(self):
        view_type_names = {
            'form': _('Form View View'),
            'tree': _('Tree View View'),
            'search': _('Search View View'),
            'graph': _('Graph View View'),
            'gantt': _('Gantt View View'),
            'kanban': _('Kanban View View'),
            'calendar': _('Calendar View View'),
        }

        return {
            'name': view_type_names[self.type],
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'builder.views.' + self.type,
            'views': [(False, 'form')],
            'res_id': False,
            'target': 'new',
            'context': {
                'default_model_id': self.model_id.id,
                'default_special_states_field_id': self.special_states_field_id.id,
                'default_module_id': self.model_id.module_id.id,
                'add_inherited_fields': self.add_inherited_fields,
                'default_inherit_view': self.inherit_view,
                'default_inherit_view_id': self.inherit_view_id.id,
                'default_inherit_view_ref': self.inherit_view_ref,
            },
        }


VIEW_TYPES = {
    'calendar': 'builder.views.calendar',
    'form': 'builder.views.form',
    'gantt': 'builder.views.gantt',
    'graph': 'builder.views.graph',
    'kanban': 'builder.views.kanban',
    'search': 'builder.views.search',
    'tree': 'builder.views.tree',
    'qweb': 'builder.ir.ui.view',
    'diagram': 'builder.ir.ui.view',
}


class View(models.Model):
    _name = 'builder.ir.ui.view'
    _rec_name = 'xml_id'

    _inherit = ['ir.mixin.polymorphism.superclass']

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='CASCADE')
    model_id = fields.Many2one('builder.ir.model', ondelete='cascade')
    model_inherit_type = fields.Selection([('mixed', 'Mixed'), ('class', 'Class'), ('prototype', 'Prototype'), ('delegation', 'Delegation')], 'Inherit Type', related='model_id.inherit_type', store=False, search=True)
    model_name = fields.Char('Model Name', related='model_id.name', store=False)
    special_states_field_id = fields.Many2one('builder.ir.model.fields', 'States Field',
                                              related='model_id.special_states_field_id')
    model_groups_date_field_ids = fields.One2many('builder.ir.model.fields', string='Has Date Fields',
                                                  related='model_id.groups_date_field_ids')
    group_ids = fields.Many2many('builder.res.groups', 'builder_ir_ui_view_group_rel', 'view_id', 'group_id', string='Groups', help="If this field is empty, the view applies to all users. Otherwise, the view applies to the users of those groups only.")

    # type = fields.Char('View Type')
    type = fields.Selection(
        [
            ('form', 'Form'),
            ('tree', 'Tree'),
            ('calendar', 'Calendar'),
            ('gantt', 'Gantt'),
            ('kanban', 'Kanban'),
            ('graph', 'Graph'),
            ('search', 'Search'),
            ('diagram', 'Diagram'),
            ('qweb', 'QWeb'),
        ], 'Type', required=True, default='form')

    name = fields.Char('View Name', required=True)
    xml_id = fields.Char('View ID', required=True)
    priority = fields.Integer('Sequence')

    inherit_id = fields.Many2one('builder.ir.ui.view', 'Inherited View', ondelete='cascade', select=True)
    inherit_children_ids = fields.One2many('builder.ir.ui.view', 'inherit_id', 'Inherit Views')
    field_parent = fields.Char('Child Field')

    inherit_view = fields.Boolean('Inherit')
    inherit_view_id = fields.Many2one('ir.ui.view', 'Inherit View')
    inherit_view_ref = fields.Char('Inherit View Ref')
    inherit_change_ids = fields.One2many(
        comodel_name='builder.ir.ui.view.inherit.change',
        inverse_name='view_id',
        string='Changes',
    )

    @api.onchange('type')
    def _onchange_type(self):
        self.subclass_model = 'builder.views.' + self.type

    @api.multi
    def action_open_view(self):
        model = self._model
        action = model.get_formview_action(self.env.cr, self.env.uid, self.ids, self.env.context)
        action.update({'target': 'new'})
        return action

    @api.multi
    def action_save(self):
        return {'type': 'ir.actions.act_window_close'}

    @property
    def real_xml_id(self):
        return self.xml_id if '.' in self.xml_id else '{module}.{xml_id}'.format(module=self.module_id.name, xml_id=self.xml_id)


class InheritViewChange(models.Model):
    _name = 'builder.ir.ui.view.inherit.change'

    view_id = fields.Many2one(
        comodel_name='builder.ir.ui.view',
        string='View',
        ondelete='cascade',
    )
    inherit_view_type = fields.Selection([('field', 'Field'), ('xpath', 'XPath')], 'Selection Type', default='field',
                                         required=True)
    inherit_view_target = fields.Char('Inherit Target', required=True)
    inherit_view_position = fields.Selection([('after', 'After'), ('before', 'Before'), ('inside', 'Inside'), ('replace', 'Replace'), ('attribute', 'Attribute')], 'Inherit Position', default='after',
                                             required=True)
    inherit_view_attribute = fields.Char('Change Attribute')
    inherit_view_attribute_value = fields.Char('Change Attribute Value')
    inherit_view_field = fields.Char('Field')


class AbstractViewField(models.AbstractModel):
    _name = 'builder.views.abstract.field'

    _rec_name = 'field_id'
    _order = 'view_id, sequence'

    view_id = fields.Many2one('builder.ir.ui.view', string='Name', ondelete='cascade')
    sequence = fields.Integer('Sequence')
    field_id = fields.Many2one('builder.ir.model.fields', string='Field', required=True, ondelete='cascade')
    field_ttype = fields.Char(string='Field Type', compute='_compute_field_ttype')
    model_id = fields.Many2one('builder.ir.model', related='view_id.model_id', string='Model')
    special_states_field_id = fields.Many2one('builder.ir.model.fields',
                                              related='view_id.model_id.special_states_field_id', string='States Field')
    module_id = fields.Many2one('builder.ir.model', related='view_id.model_id.module_id', string='Module')
    string = fields.Char('String')

    @api.one
    @api.depends('field_id.ttype')
    def _compute_field_ttype(self):
        self.field_ttype = self.field_id.ttype