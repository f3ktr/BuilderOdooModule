from openerp import models, api, fields, _


class DemoDataCreator(models.TransientModel):
    _name = 'builder.ir.model.demo.creator.wizard'

    model_id = fields.Many2one(
        comodel_name='builder.ir.model',
        string='Model',
        ondelete='cascade',
    )
    type = fields.Selection(selection='_get_type_selection', string='Type', required=True)
    target_fields_type = fields.Char('Target Fields Type', compute='_compute_target_fields_type')

    @api.one
    @api.depends('type')
    def _compute_target_fields_type(self):
        self.target_fields_type = self.env[self.type]._model._target_type if self.type else False

    @api.model
    def _get_type_selection(self):
        return self.env['builder.ir.model.demo.generator'].get_generators()

    @api.multi
    def action_create(self):
        model = self.env[self.type]._model
        return {
            'name': model._description,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': self.type,
            'views': [(False, 'form')],
            'res_id': False,
            'target': 'new',
            'context': {
                'default_model_id': self.model_id.id,
                'default_module_id': self.model_id.module_id.id,
                'default_target_fields_type': self.target_fields_type,
            },
        }

DemoDataCreator()