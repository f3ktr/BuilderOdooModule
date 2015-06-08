import random
import string

__author__ = 'one'

from openerp import models, api, fields, _


class DateGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.date'
    _description = 'Date Generator'
    _inherits = {
        'builder.ir.model.demo.generator': 'base_id'
    }
    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.ir.model.demo.generator.base']
    _target_type = 'date'

    base_id = fields.Many2one(
        comodel_name='builder.ir.model.demo.generator',
        string='Base',
        ondelete='cascade',
        required=True
    )

    dynamic_datetime = fields.Boolean('Dynamic Datetime')
    min_days_diff = fields.Integer('Min Days')
    max_days_diff = fields.Integer('Max Days')

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.multi
    def get_generator(self, field):
        while True:
            yield 'date'
