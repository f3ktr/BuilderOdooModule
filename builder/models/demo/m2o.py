import random
import string

__author__ = 'one'

from openerp import models, api, fields, _
import re


class M2oGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.m2o'
    _description = 'Many2One Generator'
    _inherits = {
        'builder.ir.model.demo.generator': 'base_id'
    }
    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.ir.model.demo.generator.base']
    _target_type = 'many2one'

    base_id = fields.Many2one(
        comodel_name='builder.ir.model.demo.generator',
        string='Base',
        ondelete='cascade',
        required=True
    )

    specify_references = fields.Boolean('Specify References')
    reference_list = fields.Char('References')

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.multi
    def get_generator(self, field):
        while True:
            yield self.get_reference_value(field)

    def get_reference_value(self, field):
        if self.specify_references:
            return random.choice(self.reference_list.split('|'))
        else:
            if field.relation_model_id:
                related_demo_count = field.relation_model_id.demo_records
                return field.relation_model_id.demo_xml_id(random.randint(0, related_demo_count-1))
            else:
                return False
