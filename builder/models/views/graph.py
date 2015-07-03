from ..fields import snake_case
from openerp import models, fields, api

__author__ = 'one'


class GraphView(models.Model):
    _name = 'builder.views.graph'

    _inherit = ['ir.mixin.polymorphism.subclass']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    attr_type = fields.Selection([('bar', 'Bar'), ('pie', 'Pie'), ('line', 'Line'), ('pivot', 'Pivot')], 'Type')
    attr_stacked = fields.Boolean('Stacked')
    attr_orientation = fields.Selection([('horizontal', 'Horizontal'), ('vertical', 'Vertical')], 'Orientation')
    field_ids = fields.One2many('builder.views.graph.field', 'view_id', 'Items', copy=True)

    _defaults = {
        'type': 'graph',
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
        self.xml_id = "view_{snake}_graph".format(snake=snake_case(self.model_id.model))
        self.model_inherit_type = self.model_id.inherit_type  # shouldn`t be doing that
        self.model_name = self.model_id.model  # shouldn`t be doing that


class GraphField(models.Model):
    _name = 'builder.views.graph.field'
    _inherit = 'builder.views.abstract.field'

    view_id = fields.Many2one('builder.views.graph', string='View', ondelete='cascade')
    operator = fields.Selection([('+', '+')], 'Operator')
    type = fields.Selection([('row', 'row'), ('col', 'col'), ('measure', 'measure')], 'Type')
    interval = fields.Selection([('month', 'month'), ('year', 'year'), ('day', 'day')], 'Interval')
