from random import randint, sample
import openerp

__author__ = 'deimos'

from openerp import models, api, fields, _


class AutoincrementGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.autoincrement'
    _description = 'AutoIncremental Number'
    _inherits = {
        'builder.ir.model.demo.generator': 'base_id'
    }
    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.ir.model.demo.generator.base']
    _target_type = 'int'

    base_id = fields.Many2one(
        comodel_name='builder.ir.model.demo.generator',
        string='Base',
        ondelete='cascade',
        required=True
    )

    start_number = fields.Float('Start at', required=True, default=1)
    increment = fields.Float('Increment', required=True, default=1)

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.model
    def format_value(self, field, value):
        if field.ttype == 'integer':
            return int(value)
        else:
            return value

    @api.multi
    def get_generator(self, field):
        n = self.start_number
        yield self.format_value(field, n)

        while True:
            n = n + self.increment
            yield self.format_value(field, n)
