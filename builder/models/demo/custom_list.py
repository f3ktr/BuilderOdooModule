import random
import openerp

__author__ = 'deimos'

from openerp import models, api, fields, _


class RandomStringGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.custom_list'
    _description = 'Custom List'
    _inherits = {
        'builder.ir.model.demo.generator': 'base_id'
    }
    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.ir.model.demo.generator.base']
    _target_type = 'char'

    base_id = fields.Many2one(
        comodel_name='builder.ir.model.demo.generator',
        string='Base',
        ondelete='cascade',
        required=True
    )

    list_type = fields.Selection([
                                     ('colors', 'Colors'),
                                     ('marital_status', 'Marital Status'),
                                     ('department_names', 'Department Names'),
                                     ('company_names', 'Company Names'),
                                     ('drug_names', 'Drug Names'),
                                     ('country_names', 'Country Names'),
                                     ('custom', 'Custom List'),
    ], required=True, default=3)
    custom_list = fields.Char("Custom List", size=1024)

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.multi
    def get_generator(self, field):
        while True:
            if self.list_type == 'custom':
                yield random.choice(self.custom_list.split('|'))
            else:
                yield self.get_value_from_list(field, self.list_type)

    @api.multi
    def get_value_from_list(self, field, list_type):
        data = self.get_demo_data()
        return random.choice(data.get(list_type, []))