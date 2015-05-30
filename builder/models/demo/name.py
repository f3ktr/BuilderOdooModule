import random
import string

__author__ = 'one'

from openerp import models, api, fields, _
import re


class NameGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.name'
    _description = 'Name Generator'
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

    name_type = fields.Selection([
                                     ('Name', 'Alex (any gender)'),
                                     ('MaleName', 'John (male name)'),
                                     ('FemaleName', 'Jane (female name)'),
                                     ('MaleName Surname', 'John Smith'),
                                     ('FemaleName Surname', 'Jane Smith'),
                                     ('Title Name Surname', 'Mr. Alex Smith'),
                                     ('Name Initial. Surname', 'Alex J. Smith'),
                                     ('Surname', 'Smith (surname)'),
                                 ], required=True)

    name_type_schema = fields.Char(required=True, help=_("Valid placeholders are : Title, Name, MaleName, FemaleName, Surname, Initial"))

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.onchange('name_type')
    def onchange_name_type(self):
        self.name_type_schema = self.name_type

    @api.multi
    def get_generator(self, field):
        while True:
            placeholder = self.name_type_schema

            # noinspection PyTypeChecker
            placeholder = re.sub('MaleName', self.get_random_name_part, placeholder)
            placeholder = re.sub('FemaleName', self.get_random_name_part, placeholder)
            placeholder = re.sub('Surname', self.get_random_name_part, placeholder)
            placeholder = re.sub('Initial', self.get_random_name_part, placeholder)
            placeholder = re.sub('Title', self.get_random_name_part, placeholder)

            yield placeholder

    def get_random_name_part(self, m):
        parts = self.get_demo_data()
        return random.choice(parts.get(m.group(0), []))