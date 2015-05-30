import random
from openerp import models, api, fields

__author__ = 'one'


class NormalDistributionGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.normal_distribution'
    _description = 'Normal Distribution Generator'
    _inherits = {
        'builder.ir.model.demo.generator': 'base_id'
    }
    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.ir.model.demo.generator.base']
    _target_type = 'integer'

    base_id = fields.Many2one(
        comodel_name='builder.ir.model.demo.generator',
        string='Base',
        ondelete='cascade',
        required=True
    )

    mean = fields.Float('Mean')
    stdev = fields.Float('Std Deviation')

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.multi
    def get_generator(self, field):
        while True:
            yield self.format_value(field, random.gauss(self.mean, self.stdev))


    @api.model
    def format_value(self, field, value):
        if field.ttype == 'integer':
            return int(value)
        else:
            return value