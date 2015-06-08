import base64
import io
import json

__author__ = 'one'

import zipfile
from openerp import models, api, fields


class ModuleImport(models.TransientModel):
    _name = 'builder.ir.module.module.import.wizard'

    @api.model
    def _get_import_types(self):
        return self.env['builder.exchanger.base'].get_exchangers()

    file = fields.Binary('File', required=True)
    import_type = fields.Selection(_get_import_types, 'Format', required=True)
    ignore_version = fields.Boolean('Ignore Version')

    @property
    def versions_mismatch(self):
        return self.file and not (self.builder_version == self.file_version)

    @property
    def file_version(self):
        if self.file:
            try:
                file_like_object = io.BytesIO(base64.decodestring(self.file))
            except:
                raise ValueError(self.file)
            zf = zipfile.ZipFile(file_like_object)
            metadata = zf.open('metadata')
            data = json.loads(metadata.read())
            metadata.close()
            return data.get('version')
        else:
            return False

    @property
    def builder_version(self):
        builders = self.env['ir.module.module'].search([
            ('name', '=', 'builder'),
        ])

        return builders.installed_version if builders else False

    @api.multi
    def action_import(self):
        """
        :type self: ModuleImport
        """
        if self.builder_version != self.file_version and not self.ignore_version:
            raise ValueError('File version ({fv}) do not match builder version ({bv})'.format(fv=self.file_version, bv=self.builder_version))

        file_like_object = io.BytesIO(base64.decodestring(self.file))
        zf = zipfile.ZipFile(file_like_object)
        self.env[self.import_type].import_modules(zf)

        # return {'type': 'ir.actions.act_window_close'}
        return self.env.ref('builder.open_module_tree').read()
