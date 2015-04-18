__author__ = 'one'

from openerp import models, api, fields, _


class ExchangerBase(models.TransientModel):
    """
    Their job is to exchange data.
    """

    _name = 'builder.exchanger.base'
    _description = 'Base Exchanger'

    @api.model
    def get_exchangers(self):
        ms = self.env['ir.model'].search([
            ('model', 'ilike', 'builder.exchanger.%'),
            ('model', '!=', 'builder.exchanger.base')
        ])

        return [
            (model.model, model.name)
            for model in ms
        ]
