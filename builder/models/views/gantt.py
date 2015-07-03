from ..fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


# TODO: add support for levels?
class GanttView(models.Model):
    _name = 'builder.views.gantt'

    _inherit = ['ir.mixin.polymorphism.subclass']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    attr_date_start_field_id = fields.Many2one('builder.ir.model.fields', 'Date Start Field', ondelete='set null',
                                               required=True)
    attr_date_stop_field_id = fields.Many2one('builder.ir.model.fields', 'Date Stop Field', ondelete='set null')
    attr_date_delay_field_id = fields.Many2one('builder.ir.model.fields', 'Date Delay Field', ondelete='set null')
    attr_progress_field_id = fields.Many2one('builder.ir.model.fields', 'Progress Field', ondelete='set null')
    attr_default_group_by_field_id = fields.Many2one('builder.ir.model.fields', 'Default Group By Field',
                                                     ondelete='set null')
    attr_color_field_id = fields.Many2one('builder.ir.model.fields', 'Color Field', ondelete='set null')
    attr_mode = fields.Selection(
        [
            ('day', 'Day'),
            ('3days', '3 Days'),
            ('week', 'Week'),
            ('3weeks', '3 Weeks'),
            ('month', 'Month'),
            ('3months', '3 Months'),
            ('year', 'Year'),
            ('3years', '3 Years'),
            ('5years', '5 Years'),
        ],
        'Mode',
        default='month'
    )

    field_ids = fields.One2many('builder.views.gantt.field', 'view_id', 'Items', copy=True)

    _defaults = {
        'type': 'gantt',
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
        self.xml_id = "view_{snake}_gantt".format(snake=snake_case(self.model_id.model))
        self.model_inherit_type = self.model_id.inherit_type  #shouldn`t be doing that
        self.model_name = self.model_id.model  #shouldn`t be doing that


class GanttField(models.Model):
    _name = 'builder.views.gantt.field'
    _inherit = 'builder.views.abstract.field'

    view_id = fields.Many2one('builder.views.gantt', string='View', ondelete='cascade')