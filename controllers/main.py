from openerp.addons.web import http
from openerp.addons.web.controllers.main import content_disposition
from openerp.addons.web.http import request


class MainController(http.Controller):

    @http.route('/builder/generate/<string:generator>/<string:modules>', type='http', auth="user")
    def download(self, generator, modules, **kwargs):

        generator = request.env[generator]
        modules = request.env['builder.ir.module.module'].search([
            ('id', 'in', modules.split(','))
        ])
        filename = "{name}.{ext}".format(name=modules[0].name if len(modules) == 1 else 'modules', ext="zip")
        zip_io = generator.get_zipped_modules(modules)

        return request.make_response(
            zip_io.getvalue(),
            headers=[
                ('Content-Type', 'plain/text' or 'application/octet-stream'),
                ('Content-Disposition', content_disposition(filename))
            ]
        )

    @http.route('/builder/export/<string:exchanger>/<string:modules>', type='http', auth="user")
    def export(self, exchanger, modules, **kwargs):
        exchanger = request.env[exchanger]
        modules = request.env['builder.ir.module.module'].search([
            ('id', 'in', modules.split(','))
        ])

        filename = "{name}.{ext}".format(name=modules[0].name if len(modules) == 1 else 'modules', ext=exchanger.get_extension())

        file_io = exchanger.get_exported_modules(modules)

        return request.make_response(
                    file_io.getvalue(),
                    headers=[('Content-Type', 'application/octet-stream'),
                             ('Content-Disposition', content_disposition(filename))])