from openerp import models, api, fields, _


class ModuleImport(models.TransientModel):
    _name = 'builder.ir.module.export.wizard'

    @api.model
    def _get_export_types(self):
        return self.env['builder.exchanger.base'].get_exchangers()

    export_type = fields.Selection(_get_export_types, 'Format', required=True)

    @api.model
    def _get_default_exporter(self):
        exporters = self.env['builder.exchanger.base'].get_exchangers()
        if exporters:
            return exporters[0][0]

    _defaults = {
        'export_type': _get_default_exporter
    }

    @api.multi
    def action_export(self):
        ids = self.env.context.get('active_ids') or [self.env.context.get('active_ids')]
        return {
            'type': 'ir.actions.act_url',
            'url': '/builder/export/{format}/{ids}'.format(ids=','.join([str(i) for i in ids if i]), format=self.export_type),
            'target': 'self'
        }
