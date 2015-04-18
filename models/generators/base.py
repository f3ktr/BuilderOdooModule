from openerp import models, api, fields, _


class GeneratorBase(models.TransientModel):
    """
    Their job is to generate code.
    """
    _name = 'builder.generator.base'

    @api.model
    def get_generators(self):
        ms = self.env['ir.model'].search([
            ('model', 'ilike', 'builder.generator.%'),
            ('model', '!=', 'builder.generator.base')
        ])

        return [
            (model.model, model.name)
            for model in ms
        ]

    @api.model
    def get_zipped_module(self, module):
        raise NotImplementedError