from collections import defaultdict
import base64

from openerp import models, api


class GeneratorV8(models.TransientModel):
    """
    Their job is to generate code.
    """
    _name = 'builder.generator.v8'
    _inherit = ['builder.generator.base']
    _description = '8.0'

    @api.model
    def generate_module(self, zip_file, module):

        has_models = any(model.define for model in module.model_ids)
        module_data = []
        py_packages = []
        demo_data = []
        model_packages = []

        if len(module.rule_ids) or len(module.group_ids):
            module_data.append('security/security.xml')
            zip_file.write_template(
                'security/security.xml',
                'security/security.xml.jinja2', {
                    'module': module,
                    'rules': module.rule_ids,
                    'groups': module.group_ids,
                })

        if len(module.model_access_ids):
            module_data.append('security/ir.model.access.csv')
            zip_file.write_template(
                'security/ir.model.access.csv',
                'security/ir.model.access.csv.jinja2', {
                    'module': module,
                    'model_access': module.model_access_ids,
                })

        if module.view_ids:
            module_data.append('views/views.xml')
            zip_file.write_template(
                'views/views.xml',
                'views/views.xml.jinja2',
                {'views': module.view_ids}
            )

        if module.action_window_ids:
            module_data.append('views/actions.xml')
            zip_file.write_template(
                'views/actions.xml',
                'views/actions.xml.jinja2',
                {'module': module}
            )

        if module.menu_ids:
            module_data.append('views/menu.xml')
            zip_file.write_template(
                'views/menu.xml',
                'views/menus.xml.jinja2',
                {'module': module, 'menus': module.menu_ids}
            )

        if has_models:
            py_packages.append('models')
            model_packages.append('models')

            zip_file.write_template(
                'models/models.py',
                'models/models.py.jinja2',
                {'models': [model for model in module.model_ids if model.define]}
            )

        for model in module.model_ids:
            if not model.demo_records:
                continue

            filename = 'demo/{model}_demo.xml'.format(model=model.model.lower().replace('.', '_'))
            demo_data.append(filename)
            zip_file.write_template(
                filename,
                'demo/model_demo.xml.jinja2',
                {
                    'model': model,
                    'records': model.demo_records
                }
            )

        if len(module.cron_job_ids):
            module_data.append('data/cron.xml')
            zip_file.write_template(
                'data/cron.xml',
                'data/cron.xml.jinja2', {
                    'module': module,
                    'cron_jobs': module.cron_job_ids,
                })

        if len(module.workflow_ids):
            module_data.append('data/workflow.xml')
            zip_file.write_template(
                'data/workflow.xml',
                'data/workflow.xml.jinja2', {
                    'module': module,
                    'workflows': module.workflow_ids,
                })

        if len(module.backend_asset_ids):
            module_data.append('views/assets.xml')
            zip_file.write_template(
                'views/assets.xml',
                'views/web_assets.xml.jinja2', {
                    'module': module,
                    'assets': module.backend_asset_ids,
                })

        if len(module.setting_ids):
            module_data.append('views/settings.xml')
            zip_file.write_template(
                'views/settings.xml',
                'views/settings.xml.jinja2', {
                    'module': module,
                    'settings': module.setting_ids,
                })

            model_packages.append('settings')
            zip_file.write_template(
                'models/settings.py',
                'models/settings.py.jinja2', {
                    'module': module,
                    'settings': module.setting_ids,
                })

        if module.icon_image:
            zip_file.write(
                'static/description/icon.png',
                base64.decodestring(module.icon_image)
            )

        if module.description_html:
            zip_file.write(
                'static/description/index.html',
                module.description_html
            )

        # website stuff
        for data in module.data_file_ids:
            zip_file.write(
                data.path.strip('/'),
                base64.decodestring(data.content)
            )

        for theme in module.website_theme_ids:
            if theme.image:
                zip_file.write(
                    'static/themes/' + theme.asset_id.attr_id + '.png',
                    base64.decodestring(theme.image)
                )

        if module.website_asset_ids:
            module_data.append('views/website_assets.xml')
            zip_file.write_template(
                'views/website_assets.xml',
                'views/website_assets.xml.jinja2',
                {'module': module, 'assets': module.website_asset_ids},
            )

        if module.website_page_ids:
            module_data.append('views/website_pages.xml')
            zip_file.write_template(
                'views/website_pages.xml',
                'views/website_pages.xml.jinja2',
                {'module': module, 'pages': module.website_page_ids, 'menus': module.website_menu_ids},
            )

            controller_pages = [p for p in module.website_page_ids if not p.attr_page and p.gen_controller]

            if controller_pages:
                py_packages.append('controllers')

                zip_file.write_template(
                    'controllers/__init__.py',
                    '__init__.py.jinja2',
                    {'packages': ['main']}
                )

                zip_file.write_template(
                    'controllers/main.py',
                    'controllers/main.py.jinja2',
                    {'module': module, 'pages': controller_pages},
                )

        if module.website_theme_ids:
            module_data.append('views/website_themes.xml')
            zip_file.write_template(
                'views/website_themes.xml',
                'views/website_themes.xml.jinja2',
                {'module': module, 'themes': module.website_theme_ids},
            )
        if module.website_media_item_ids:
            module_data.append('views/website_images.xml')
            zip_file.write_template(
                'views/website_images.xml',
                'views/website_images.xml.jinja2',
                {'module': module, 'images': module.website_media_item_ids},
            )

        if module.website_snippet_ids:
            snippet_type = defaultdict(list)
            for snippet in module.website_snippet_ids:
                snippet_type[snippet.is_custom_category].append(snippet)

            module_data.append('views/website_snippets.xml')
            zip_file.write_template(
                'views/website_snippets.xml',
                'views/website_snippets.xml.jinja2',
                {'module': module, 'snippet_type': snippet_type},
            )

        if model_packages:
            zip_file.write_template(
                'models/__init__.py',
                '__init__.py.jinja2',
                {'packages': model_packages}
            )

        zip_file.write_template(
            '__init__.py',
            '__init__.py.jinja2',
            {'packages': py_packages}
        )

        # end website stuff

        # this must be last to include all resources
        zip_file.write_template(
            '__openerp__.py',
            '__openerp__.py.jinja2',
            {
                'module': module,
                'data': module_data,
                'demo': demo_data
            }
        )
