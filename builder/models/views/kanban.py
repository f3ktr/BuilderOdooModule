from ..fields import snake_case
from openerp import models, fields, api

__author__ = 'one'


class KanbanView(models.Model):
    _name = 'builder.views.kanban'

    _inherit = ['ir.mixin.polymorphism.subclass']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    attr_default_group_by_field_id = fields.Many2one('builder.ir.model.fields', 'Default Group By Field',
                                                     ondelete='set null')
    attr_template = fields.Text('Template')
    attr_quick_create = fields.Boolean('Quick Create', default=True)
    # attr_quick_create = fields.Selection([(1, 'Quick Create'), (2, 'No Quick Create')], 'Quick Create')
    field_ids = fields.Many2many('builder.ir.model.fields', 'builder_view_views_kanban_field_rel', 'view_id',
                                 'field_id', 'Items')
    # field_ids = fields.One2many('builder.views.kanban.field', 'view_id', 'Items')

    _defaults = {
        'type': 'kanban',
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
        self.name = self.model_id.name
        self.xml_id = "view_{snake}_kanban".format(snake=snake_case(self.model_id.model))
        self.model_inherit_type = self.model_id.inherit_type  # shouldn`t be doing that
        self.model_name = self.model_id.model  # shouldn`t be doing that


class KanbanField(models.Model):
    _name = 'builder.views.kanban.field'
    _inherit = 'builder.views.abstract.field'

    view_id = fields.Many2one('builder.views.kanban', string='View', ondelete='cascade')
    invisible = fields.Boolean('Invisible')
