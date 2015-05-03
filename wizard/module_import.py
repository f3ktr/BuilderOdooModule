import base64
import io

__author__ = 'one'

import zipfile
from openerp import models, api, fields


class ModuleImport(models.TransientModel):
    _name = 'builder.ir.module.module.import.wizard'

    @api.model
    def _get_import_types(self):
        return self.env['builder.exchanger.base'].get_exchangers()

    file = fields.Binary('File', required=True)
    file_version = fields.Char('Version', compute='_compute_version')
    version = fields.Char('Version', compute='_compute_version')
    import_type = fields.Selection(_get_import_types, 'Format', required=True)
    ignore_version = fields.Boolean('Ignore Version')

    @api.multi
    def action_import(self):
        """
        :type self: ModuleImport
        """
        file_like_object = io.BytesIO(base64.decodestring(self.file))
        zf = zipfile.ZipFile(file_like_object)
        self.env[self.import_type].import_modules(zf)

        return {'type': 'ir.actions.act_window_close'}
