from base64 import decodestring
import re
from string import Template
from types import MethodType
import os
import mimetypes
import string

from openerp import models, fields, api, _, tools
from .utils import simple_selection
from .utils.formats import json


MODULE_EXPORTER_RE = re.compile('_export_\w[\w_]+')


def get_module_exporters(model):
    return [
        (attr.replace('_export_', ''), attr.replace('_export_', '').capitalize()) for attr in dir(model)
        if MODULE_EXPORTER_RE.match(attr) and isinstance(getattr(model, attr), MethodType)
    ]

MODULE_IMPORTER_RE = re.compile('_import_\w[\w_]+')


def get_module_importers(model):
    return [
        (attr.replace('_import_', ''), attr.replace('_import_', '').capitalize()) for attr in dir(model)
        if MODULE_IMPORTER_RE.match(attr) and isinstance(getattr(model, attr), MethodType)
    ]


class Module(models.Model):
    _name = 'builder.ir.module.module'

    @api.model
    def _get_categories(self):
        return [(c.name, c.name) for c in self.env['ir.module.category'].search([])]

    name = fields.Char("Technical Name", required=True, select=True)
    category_id = fields.Selection(simple_selection('ir.module.category', 'name') , 'Category')
    shortdesc = fields.Char('Module Name', translate=True, required=True)
    summary = fields.Char('Summary', translate=True)
    description = fields.Text("Description", translate=True)
    description_html = fields.Html(string='Description HTML', sanitize=False)
    author = fields.Char("Author", required=True)
    maintainer = fields.Char('Maintainer')
    contributors = fields.Text('Contributors')
    website = fields.Char("Website")

    version = fields.Char('Version', default='0.1')
    mirror = fields.Text('CodeMirror')

    url = fields.Char('URL')
    sequence = fields.Integer('Sequence')
    # dependencies_id = fields.One2many('programming.module.dependency', 'module_id', 'Dependencies')
    auto_install = fields.Boolean('Automatic Installation',
                                   help='An auto-installable module is automatically installed by the '
                                        'system when all its dependencies are satisfied. '
                                        'If the module has no dependency, it is always installed.')
    license = fields.Selection([
        ('GPL-2', 'GPL Version 2'),
        ('GPL-2 or any later version', 'GPL-2 or later version'),
        ('GPL-3', 'GPL Version 3'),
        ('GPL-3 or any later version', 'GPL-3 or later version'),
        ('AGPL-3', 'Affero GPL-3'),
        ('Other OSI approved licence', 'Other OSI Approved Licence'),
        ('Other proprietary', 'Other Proprietary')
    ], string='License', default='AGPL-3')

    application = fields.Boolean('Application')

    icon_image = fields.Binary(string='Icon')
    icon_image_name = fields.Char('Icon Filename')

    menus_by_module = fields.Text(string='Menus')
    reports_by_module = fields.Text(string='Reports')
    views_by_module = fields.Text(string='Views')

    post_install_action = fields.Reference([
                                    ('builder.ir.actions.act_window', 'Window'),
                                    # ('builder.ir.actions.act_url', 'URL'),
    ], 'After Install Action')

    models_count = fields.Integer("Models Count", compute='_compute_models_count', store=False, search=True)

    dependency_ids = fields.One2many(
        comodel_name='builder.ir.module.dependency',
        inverse_name='module_id',
        string='Dependencies',
        copy=True
    )

    model_ids = fields.One2many('builder.ir.model', 'module_id', 'Models', copy=True)
    view_ids = fields.One2many('builder.ir.ui.view', 'module_id', 'Views', copy=True)
    menu_ids = fields.One2many('builder.ir.ui.menu', 'module_id', 'Menus', copy=True)
    group_ids = fields.One2many('builder.res.groups', 'module_id', 'Groups', copy=True)
    model_access_ids = fields.One2many('builder.ir.model.access', 'module_id', 'ACLs', copy=True)
    rule_ids = fields.One2many('builder.ir.rule', 'module_id', 'Rules', copy=True)
    cron_job_ids = fields.One2many('builder.ir.cron', 'module_id', 'Cron Jobs', copy=True)
    action_ids = fields.One2many('builder.ir.actions.actions', 'module_id', 'Actions', copy=True)
    action_window_ids = fields.One2many('builder.ir.actions.act_window', 'module_id', 'Window Actions', copy=True)
    action_url_ids = fields.One2many('builder.ir.actions.act_url', 'module_id', 'URL Actions', copy=True)
    workflow_ids = fields.One2many('builder.workflow', 'module_id', 'Workflows', copy=True)
    backend_asset_ids = fields.One2many('builder.web.asset', 'module_id', 'Assets', copy=True)

    data_file_ids = fields.One2many('builder.data.file', 'module_id', 'Data Files', copy=True)
    snippet_bookmarklet_url = fields.Char('Link', compute='_compute_snippet_bookmarklet_url')

    @api.model
    def _get_default_author(self):
        return self.env.user.name if self.env.user else None

    _defaults = {
        'author': _get_default_author
    }

    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        default['shortdesc'] = _('%s (copy)') % self.shortdesc
        return super(Module, self).copy(default)

    @api.onchange('shortdesc')
    def _compute_name(self):
        if not self.name and self.shortdesc:
            self.name = self.shortdesc.lower().replace(' ', '_').replace('.', '_')

    @api.one
    @api.depends('name')
    def _compute_snippet_bookmarklet_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        link = """
javascript:(function(){
    function script(url, callback){
        var new_script = document.createElement('script');
        new_script.src = url + '?__stamp=' + Math.random();
        new_script.onload = new_script.onreadystatechange = callback;
        document.getElementsByTagName('head')[0].appendChild(new_script);
        new_script.type='text/javascript';
    };
    window.odooUrl = '$base_url';
    window.newSnippetUrl = '$base_url/builder/$module/snippet/add';
    script('$base_url/builder/static/src/js/snippet_loader.js');
})();
        """
        self.snippet_bookmarklet_url = Template(link).substitute(base_url=base_url, module=self.name)

    @api.multi
    def dependencies_as_list(self):
        return [str(dep.name) for dep in self.dependency_ids]

    @api.one
    def add_dependency(self, names):
        if not names:
            return

        dependency_obj = self.env['builder.ir.module.dependency']
        if not isinstance(names, list):
            names = [names]

        for name in names:
            if not dependency_obj.search([('module_id', '=', self.id), ('dependency_module_name', '=', name)]).id:
                dependency_obj.create({
                    'module_id': self.id,
                    'type': 'manual',
                    'dependency_module_name': name
                })

    @api.one
    @api.depends('model_ids')
    def _compute_models_count(self):
        self.models_count = len(self.model_ids)

    @api.multi
    def action_base_files(self):
        search = self.env.ref('builder.view_builder_data_file_filter', False)
        return {
            'name': _('Files'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'kanban,tree,form',
            'res_model': 'builder.data.file',
            'views': [(False, 'kanban'),(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            'search_view_id': search.id if search else False,
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_models(self):

        tree_view = self.env.ref('builder.builder_ir_model_tree_view', False)
        form_view = self.env.ref('builder.builder_ir_model_form_view', False)

        return {
            'name': _('Models'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form,diagram',
            'res_model': 'builder.ir.model',
            'views': [(tree_view and tree_view.id or False, 'tree'), (form_view and form_view.id or False, 'form')],
            'view_id': tree_view and tree_view.id,
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_views(self):

        tree_view = self.env.ref('builder.builder_ir_ui_view_tree', False)
        form_view = self.env.ref('builder.builder_ir_ui_view_form', False)

        return {
            'name': _('Views'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.ir.ui.view',
            'views': [(tree_view.id if tree_view else False, 'tree'), (form_view.id if form_view else False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_actions(self):

        return {
            'name': _('Actions'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.ir.actions.act_window',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_menus(self):

        return {
            'name': _('Menus'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.ir.ui.menu',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_groups(self):

        return {
            'name': _('Groups'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.res.groups',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_model_access(self):

        return {
            'name': _('Access Control Rules'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.ir.model.access',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_rules(self):

        return {
            'name': _('Model Rules'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.ir.rule',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_workflows(self):
        return {
            'name': _('Workflows'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.workflow',
            'views': [(False, 'tree'), (False, 'form'), (False, 'diagram')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_config_models(self):

        return {
            'name': _('Configuration Models'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.res.config.settings',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_cron_jobs(self):

        return {
            'name': _('Cron Jobs'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.ir.cron',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_backend_assets(self):

        return {
            'name': _('Backend Assets'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.web.asset',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_website_pages(self):

        return {
            'name': _('Pages'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.website.page',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_website_assets(self):

        return {
            'name': _('Assets'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.website.asset',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_website_themes(self):

        return {
            'name': _('Themes'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.website.theme',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_website_media_item(self):

        return {
            'name': _('Media Manager'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.website.media.item',
            'views': [(False, 'kanban'), (False, 'tree')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_website_menus(self):

        return {
            'name': _('Website Menus'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.website.menu',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }


    @api.multi
    def action_website_snippets(self):

        return {
            'name': _('Snippets'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'builder.website.snippet',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_diagram(self):

        diagram_view = self.env.ref('builder.view_builder_model_diagram', False)

        return {
            'name': _('UML Diagram'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'diagram',
            'res_model': 'builder.ir.module.module',
            'views': [(diagram_view and diagram_view.id or False, 'diagram'), ],
            'view_id': diagram_view and diagram_view.id,
            'res_id': self.id,
            'target': 'new',
            # 'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
            'context': {
                'default_module_id': self.id,
                'diagram_view': True
            },
        }

    def action_edit_description_html(self, cr, uid, ids, context=None):
        if not len(ids) == 1:
            raise ValueError('One and only one ID allowed for this action')
        url = '/builder/page/designer?model={model}&res_id={id}&enable_editor=1'.format(id=ids[0], model=self._name)
        return {
            'name': _('Edit Template'),
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

    def import_models(self, model):
        pass

    @api.multi
    def _export_zip(self):
        return self.get_zipped_module()

    @api.multi
    def _export_odoo(self):
        return json.JsonExport(self.env).export(self)

    @api.model
    def _import_odoo(self, importer):
        return json.JsonImport(self.env).build(self, decodestring(importer.file))


class DataFile(models.Model):
    _name = 'builder.data.file'

    _rec_name = 'path'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    path = fields.Char(string='Path', required=True)
    filename = fields.Char('Filename', compute='_compute_stats', store=True)
    file_type_icon = fields.Char('Icon File', store=True)
    content_type = fields.Char('Content Type', compute='_compute_stats', store=True)
    is_image = fields.Boolean('Is Image', compute='_compute_stats', store=True)
    image_small = fields.Binary('Image Thumb', compute='_compute_stats', store=True)
    in_media = fields.Boolean('In Media', compute='_compute_is_in_media', store=False, search=True)
    extension = fields.Char('Extension', compute='_compute_stats', store=True)
    size = fields.Integer('Size', compute='_compute_stats', store=True)
    content = fields.Binary('Content')
    media_item_ids = fields.One2many('builder.website.media.item', 'file_id', 'Media Files', copy=True)

    @api.one
    @api.depends('media_item_ids.file_id')
    def _compute_is_in_media(self):
        self.in_media = len(self.media_item_ids) > 0

    @api.multi
    def action_add_as_media_item(self):
        self.env['builder.website.media.item'].create({
            'module_id': self.module_id.id,
            'file_id': self.id,
        })

    @api.one
    @api.depends('content', 'path')
    def _compute_stats(self):
        if self.content:
            self.size = len(decodestring(self.content))
            self.filename = os.path.basename(self.path)
            self.extension = os.path.splitext(self.path)[1]
            self.content_type = mimetypes.guess_type(self.filename)[0] if mimetypes.guess_type(self.filename) else False
            self.is_image = self.content_type in ['image/png', 'image/jpeg', 'image/gif', 'image/bmp']

            self.image_small = tools.image_resize_image_small(self.content, size=(100, 100)) if self.is_image else False
        else:
            self.size = False
            self.filename = False
            self.extension = False
            self.content_type = False
            self.image_small = False
            self.is_image = False
