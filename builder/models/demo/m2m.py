import random
import string

__author__ = 'one'

from openerp import models, api, fields, _
import re


class M2mGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.m2m'
    _description = 'Many2Many Generator'
    _inherits = {
        'builder.ir.model.demo.generator': 'base_id'
    }
    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.ir.model.demo.generator.base']
    _target_type = 'many2many'

    base_id = fields.Many2one(
        comodel_name='builder.ir.model.demo.generator',
        string='Base',
        ondelete='cascade',
        required=True
    )

    specify_references = fields.Boolean('Specify References')
    reference_list = fields.Char('References')
    min_reference_count = fields.Integer('Min Reference Count', default=1)
    max_reference_count = fields.Integer('Max Reference Count', default=1)

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.multi
    def get_generator(self, field):
        while True:
            if self.base_id.generate_null_values(field):
                yield False
            else:
                yield self.get_reference_values(field)

    @staticmethod
    def format_ref_values(values):
        return "[(6,0, [" + (", ".join(["ref('{ref}')".format(ref=ref) for ref in values])) + "])]"

    def get_reference_values(self, field):
        if self.specify_references:
            return self.format_ref_values(random.sample(self.reference_list.split('|'), random.randint(self.min_reference_count, self.max_reference_count)))
        else:
            if field.relation_model_id:
                sample = random.sample(range(0, field.relation_model_id.demo_records), random.randint(self.min_reference_count, self.max_reference_count))
                return self.format_ref_values([field.relation_model_id.demo_xml_id(index) for index in sample])
            else:
                return False
