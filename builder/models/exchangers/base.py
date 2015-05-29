import json
from ..utils.zip import ZipFile, ModuleZipFile
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

    @api.model
    def get_version(self):
        builders = self.env['ir.module.module'].search([
            ('name', '=', 'builder'),

        ])

        return builders.installed_version if builders else None

    @api.model
    def get_extension(self, module):
        raise NotImplementedError

    @api.model
    def export_module(self, module):
        raise NotImplementedError

    @api.model
    def get_export_module_filename(self, module):
        raise NotImplementedError

    @api.model
    def get_metadata(self):
        return json.dumps({
            'version': self.get_version()
        })

    @api.model
    def get_exported_modules(self, modules):
        zip_file = ZipFile()
        zip_file.write('metadata', self.get_metadata())
        [zip_file.write(self.get_export_module_filename(module), self.export_module(module)) for module in modules]
        return zip_file.get_zip()

    @api.model
    def import_modules(self, zip_file):
        [
            self.load_module(zip_file.read(module)) for module in zip_file.namelist()
            if module != 'metadata'
        ]

    @api.model
    def load_module(self, module):
        raise NotImplementedError