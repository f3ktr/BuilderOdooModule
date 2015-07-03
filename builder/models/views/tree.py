from ..fields import snake_case
from openerp import models, fields, api
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class TreeView(models.Model):
    _name = 'builder.views.tree'

    _inherit = ['ir.mixin.polymorphism.subclass']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    field_parent_id = fields.Many2one('builder.ir.model.fields', string='Field Parent', ondelete='set null')
    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    field_ids = fields.One2many('builder.views.tree.field', 'view_id', 'Fields', copy=True)
    attr_toolbar = fields.Boolean('Show Toolbar', default=False)
    attr_fonts = fields.Char('Fonts', help='Font definition. Ex: bold:message_unread==True')
    attr_colors = fields.Char('Colors',
                              help='Color definition. Ex: "gray:probability == 100;'
                                   'red:date_deadline and (date_deadline &lt; current_date)"')

    _defaults = {
        'type': 'tree',
        'subclass_model': lambda s, c, u, cxt=None: s._name,
    }

    @api.model
    def create_instance(self, id):
        self.create({
            'view_id': id,
        })

    @api.multi
    def action_save(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('model_id')
    def _onchange_model_id(self):
        model_id = self.model_id
        self.name = model_id.name
        self.xml_id = "view_{snake}_tree".format(snake=snake_case(model_id.model))
        self.model_inherit_type = model_id.inherit_type  # shouldn`t be doing that
        self.model_name = model_id.model  # shouldn`t be doing that

        if not len(self.field_ids):
            field_list = []
            for field in model_id.field_ids:
                if field.ttype in ['binary', 'one2many', 'many2many']:
                    continue
                if field.is_inherited and not self.env.context.get('add_inherited_fields', True):
                    continue
                field_list.append({'field_id': field.id, 'field_ttype': field.ttype, 'model_id': model_id.id,
                                   'special_states_field_id': model_id.special_states_field_id.id})

            self.field_ids = field_list


class TreeField(models.Model):
    _name = 'builder.views.tree.field'
    _inherit = 'builder.views.abstract.field'

    view_id = fields.Many2one('builder.views.tree', string='View', ondelete='cascade')
    widget = fields.Selection(FIELD_WIDGETS_ALL, 'Widget')
    widget_options = fields.Char('Widget Options')

    nolabel = fields.Boolean('Hide Label')

    invisible = fields.Boolean('Invisible')
    readonly = fields.Boolean('Readonly')
    domain = fields.Char('Domain')

    @api.one
    @api.depends('field_id.ttype', 'view_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype


