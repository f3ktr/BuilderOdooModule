import random
import string

__author__ = 'one'

from openerp import models, api, fields, _

class EmailGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.email'
    _description = 'Email Generator'
    _inherits = {
        'builder.ir.model.demo.generator': 'base_id'
    }
    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.ir.model.demo.generator.base']
    _target_type = 'char'

    _domain_suffixes = ["edu", "com", "us", "org", "cu", "net", "co.uk"]

    base_id = fields.Many2one(
        comodel_name='builder.ir.model.demo.generator',
        string='Base',
        ondelete='cascade',
        required=True
    )

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.multi
    def get_generator(self, field):
        while True:
            name = "".join(random.sample(string.lowercase, random.randint(3, 10)))
            domain = "".join(random.sample(string.lowercase, random.randint(5, 15)))
            domainsuffix = random.choice(self._domain_suffixes)
            yield "{name}@{domain}.{domainsuffix}".format(name=name, domain=domain, domainsuffix=domainsuffix)
