import random

__author__ = 'one'

from openerp import models, api, fields, _


class SelectionRandomGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.selection'
    _description = 'Selection Random Generator'
    _inherits = {
        'builder.ir.model.demo.generator': 'base_id'
    }
    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.ir.model.demo.generator.base']
    _target_type = 'selection'

    base_id = fields.Many2one(
        comodel_name='builder.ir.model.demo.generator',
        string='Base',
        ondelete='cascade',
        required=True
    )

    custom_selection = fields.Boolean("Custom Selection", default=False)
    selection_options = fields.Char("Selection Options", help="Options separated by '|'. ")

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.multi
    def get_generator(self, field):
        while True:
            yield self.get_random_value_from_field(field)

    @api.multi
    def get_random_value_from_field(self, field):
        options = []
        if field.ttype == 'selection':
            options = [op.value for op in field.option_ids]
        if self.custom_selection:
            return random.choice([op for op in self.selection_options.split('|')])
        else:
            return random.choice(options)