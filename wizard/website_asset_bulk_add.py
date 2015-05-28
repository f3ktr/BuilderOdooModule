__author__ = 'one'

from openerp import models, api, fields, _


class ModelImport(models.TransientModel):
    _name = 'builder.website.asset.data.wizard'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='CASCADE')
    data_ids = fields.Many2many('builder.data.file', 'builder_website_asset_data_file_rel', 'wizard_id', 'data_id', 'Files')

    @api.one
    def action_import(self):
        asset_model_name = self.env.context.get('asset_model', 'builder.website.asset.item')
        model = self.env[self.env.context.get('active_model')].search([('id', '=', self.env.context.get('active_id'))])
        asset_item_model = self.env[asset_model_name]
        model_field = self.env.context.get('model_link_field', 'asset_id')
        asset_field = self.env.context.get('asset_field', 'file_id')

        for data_file in self.data_ids:
            current_file = self.env[asset_model_name].search([(model_field, '=', model.id), (asset_field, '=', data_file.id)])

            if not current_file.id:
                new_item = asset_item_model.create(dict(((model_field, model.id), (asset_field, data_file.id))))

        return {'type': 'ir.actions.act_window_close'}