from openerp import models, api, fields, _


class ModuleGenerate(models.TransientModel):
    _name = 'builder.ir.module.module.generate.wizard'

    @api.model
    def _get_generators(self):
        return self.env['builder.generator.base'].get_generators()

    generator = fields.Selection(_get_generators, 'Version', required=True)

    @api.multi
    def action_generate(self):
        module = self.env[self.env.context.get('active_model')].search([('id', '=', self.env.context.get('active_id'))])

        return {
            'type': 'ir.actions.act_url',
            'url': '/builder/generate/{id}/{generator}'.format(id=module.id, generator=self.generator),
            'target': 'self'
        }
