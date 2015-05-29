from jinja2 import Environment, FileSystemLoader
import os

from ..utils.jinja2.utils import groups_attribute, field_options, field_attrs
from ..utils.zip import ZipFile, ModuleZipFile
from openerp import models, api


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
    def get_template_paths(self):
        return [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'templates', '8.0'))]

    @api.model
    def create_jinja_env(self):
        return Environment(
            loader=FileSystemLoader(
                self.get_template_paths()
            )
        )

    @api.model
    def get_jinja_filters(self):
        return {
            'dot2dashed': lambda x: x.replace('.', '_'),
            'dot2name': lambda x: ''.join([s.capitalize() for s in x.split('.')]),
            'cleargroup': lambda x: x.replace('.', '_'),
            'groups': groups_attribute,
            'field_options': field_options,
            'fieldattrs': field_attrs,
        }

    @api.model
    def get_jinja_globals(self):
        return {
            'getattr': getattr,
        }

    @api.model
    def get_zipped_modules(self, modules):
        jinja_env = self.create_jinja_env()

        jinja_env.globals.update(self.get_jinja_globals())
        jinja_env.filters.update(self.get_jinja_filters())

        zip_file = ZipFile(jinja_env)
        [self.generate_module(ModuleZipFile(zip_file, module), module) for module in modules]

        return zip_file.get_zip()

    @api.model
    def generate_module(self, zip_file, module):
        raise NotImplementedError
