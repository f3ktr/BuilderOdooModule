__author__ = 'one'

from openerp import models, api, fields, _


class MediaItemBulkAddWizard(models.TransientModel):
    _name = 'builder.website.media.item.bulk.add.wizard'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='CASCADE')
    data_ids = fields.Many2many('builder.data.file', 'builder_website_media_item_bulk_data_file_rel', 'wizard_id', 'data_id', 'Files')

    @api.one
    def action_import(self):
        media_item_model = self.env['builder.website.media.item']

        for data_file in self.data_ids:
            new_item = media_item_model.create({
                'file_id': data_file.id,
                'module_id': self.module_id.id,
            })

        return {'type': 'ir.actions.act_window_close'}