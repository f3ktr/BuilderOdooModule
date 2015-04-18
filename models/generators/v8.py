from collections import defaultdict
from jinja2 import Environment, FileSystemLoader
import posixpath
import zipfile
from StringIO import StringIO
import base64
import os
from openerp import models, api, fields, _


class GeneratorBase(models.TransientModel):
    """
    Their job is to generate code.
    """
    _name = 'builder.generator.v8'
    _description = '8.0'

    @api.model
    def get_template_paths(self):
        return [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'templates', '8.0'))]

    @api.model
    def get_zipped_module(self, module):

        def groups_attribute(groups):
            return 'groups="{list}"'.format(list=','.join([i.xml_id for i in groups])) if len(groups) else ''

        def field_options(options):
            opts = []
            for op in options:
                opts.append((op.value, op.name))
            return repr(opts)

        def write_template(template_obj, zf, fname, template, d):
            i = zipfile.ZipInfo(fname)
            i.compress_type = zipfile.ZIP_DEFLATED
            i.external_attr = 2175008768
            zf.writestr(i, template_obj.get_template(template).render(d))

        templates = Environment(
            loader=FileSystemLoader(
                self.get_template_paths()
            )
        )

        templates.filters.update({
            'dot2dashed': lambda x: x.replace('.', '_'),
            'dot2name': lambda x: ''.join([s.capitalize() for s in x.split('.')]),
            'cleargroup': lambda x: x.replace('.', '_'),
            'groups': groups_attribute,
            'field_options': field_options,
        })

        zfileIO = StringIO()

        zfile = zipfile.ZipFile(zfileIO, 'w')

        has_models = len(module.model_ids)
        has_data = len(module.data_file_ids)
        has_website = len(module.website_theme_ids) \
                      or len(module.website_asset_ids) \
                      or len(module.website_menu_ids) \
                      or len(module.website_page_ids)

        module_data = []

        if has_models:
            module_data.append('views/views.xml')
            module_data.append('views/actions.xml')
            module_data.append('views/menu.xml')

            write_template(templates, zfile, module.name + '/__init__.py'       , '__init__.py.jinja2' , {'packages': ['models']})
            write_template(templates, zfile, module.name + '/models/__init__.py', '__init__.py.jinja2' , {'packages': ['models']})
            write_template(templates, zfile, module.name + '/views/menu.xml'    , 'views/menus.xml.jinja2'           , {'module': module, 'menus': module.menu_ids})
            write_template(templates, zfile, module.name + '/views/actions.xml' , 'views/actions.xml.jinja2'        , {'module': module})
            write_template(templates, zfile, module.name + '/views/views.xml'   , 'views/views.xml.jinja2'           , {'models': module.view_ids})
            write_template(templates, zfile, module.name + '/models/models.py'  , 'models/models.py.jinja2'          , {'models': module.model_ids})

        if len(module.rule_ids) or len(module.group_ids):
            module_data.append('security/security.xml')
            write_template(templates, zfile, module.name + '/security/security.xml'       , 'security/security.xml.jinja2' , {
                'module': module,
                'rules': module.rule_ids,
                'groups': module.group_ids,
            })

        if len(module.model_access_ids):
            module_data.append('security/ir.model.access.csv')
            write_template(templates, zfile, module.name + '/security/ir.model.access.csv'       , 'security/ir.model.access.csv.jinja2' , {
                'module': module,
                'model_access': module.model_access_ids,
            })

        if len(module.cron_job_ids):
            module_data.append('data/cron.xml')
            write_template(templates, zfile, module.name + '/data/cron.xml'       , 'data/cron.xml.jinja2' , {
                'module': module,
                'cron_jobs': module.cron_job_ids,
            })

        if module.icon_image:
            info = zipfile.ZipInfo(module.name + '/static/description/icon.png')
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zfile.writestr(info, base64.decodestring(module.icon_image))

        if module.description_html:
            info = zipfile.ZipInfo(module.name + '/static/description/index.html')
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zfile.writestr(info, module.description_html)


        #website stuff
        for data in module.data_file_ids:
            info = zipfile.ZipInfo(posixpath.join(module.name, data.path.strip('/')))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zfile.writestr(info, base64.decodestring(data.content))

        for theme in module.website_theme_ids:
            if theme.image:
                info = zipfile.ZipInfo(module.name + '/static/themes/' + theme.asset_id.attr_id +'.png')
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 2175008768
                zfile.writestr(info, base64.decodestring(theme.image))

        if module.website_asset_ids:
            module_data.append('views/website_assets.xml')
            write_template(templates, zfile, module.name + '/views/website_assets.xml', 'views/website_assets.xml.jinja2',
                                {'module': module, 'assets': module.website_asset_ids},
                                )
        if module.website_page_ids:
            module_data.append('views/website_pages.xml')
            write_template(templates, zfile, module.name + '/views/website_pages.xml', 'views/website_pages.xml.jinja2',
                                {'module': module, 'pages': module.website_page_ids, 'menus': module.website_menu_ids},
                                )
        if module.website_theme_ids:
            module_data.append('views/website_themes.xml')
            write_template(templates, zfile, module.name + '/views/website_themes.xml', 'views/website_themes.xml.jinja2',
                                {'module': module, 'themes': module.website_theme_ids},
                                )

        if module.website_snippet_ids:
            snippet_type = defaultdict(list)
            for snippet in module.website_snippet_ids:
                snippet_type[snippet.is_custom_category].append(snippet)

            module_data.append('views/website_snippets.xml')
            write_template(templates, zfile, module.name + '/views/website_snippets.xml', 'views/website_snippets.xml.jinja2',
                                {'module': module, 'snippet_type': snippet_type},
                                )

        #end website stuff


        #this must be last to include all resources
        write_template(templates, zfile, module.name + '/__openerp__.py', '__openerp__.py.jinja2',
                            {'module': module, 'data': module_data})

        zfile.close()
        zfileIO.flush()
        return zfileIO


