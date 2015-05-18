from random import randint
import openerp

__author__ = 'deimos'

from openerp import models, api, fields, _


class RandomStringGenerator(models.Model):
    _name = 'builder.ir.model.demo.generator.randomstr'
    _description = 'Random String'
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

    min_word_length = fields.Integer('Minimum Word Length', required=True)
    max_word_length = fields.Integer('Maximum Word Length', required=True)
    min_word_count = fields.Integer('Minimum Word Count', required=True)
    max_word_count = fields.Integer('Maximum Word Count', required=True)
    allowed_chars = fields.Char('Allowed Chars', required=True, default='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')

    @api.constrains('max_word_length')
    def _check_max_word_length(self):
        if self.min_word_length > self.max_word_length:
            raise openerp.exceptions.Warning('Minimum Word Length can\'t be greater than Maximum Word Length')

    @api.constrains('max_word_count')
    def _check_max_word_count(self):
        if self.min_word_count > self.max_word_count:
            raise openerp.exceptions.Warning('Minimum Word Count can\'t be greater than Maximum Word Count')

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.one
    def get_generator(self):
        while True:
            words = []
            for i in range(randint(self.min_word_count, self.max_word_count)):
                word = ''
                for l in range(randint(self.min_word_length, self.max_word_length)):
                    word += self.allowed_chars[randint(0, len(self.allowed_chars)-1)]
                words.append(word)
            yield ' '.join(words)