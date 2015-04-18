from StringIO import StringIO
import base64
import json
import zipfile
import os
from openerp.addons.web import http
from openerp.addons.web.controllers.main import content_disposition
import posixpath
from openerp.addons.web.http import request
from ..tools.formats.json import JsonExport


class MainController(http.Controller):

    @http.route('/builder/generate/<model("builder.ir.module.module"):module>/<string:generator>', type='http', auth="user")
    def download(self, module, generator, **kwargs):

        generator = module.env[generator]
        filename = "{name}.{ext}".format(name=module.name, ext="zip")

        zfileIO = generator.get_zipped_module(module)

        return request.make_response(
            zfileIO.getvalue(),
            headers=[('Content-Type', 'plain/text' or 'application/octet-stream'),
                     ('Content-Disposition', content_disposition(filename))])


    @http.route('/builder/export/<string:format>/<model("builder.ir.module.module"):module>', type='http', auth="user")
    def export(self, module, format, **kwargs):

        filename = "{name}.{ext}".format(name=module.name, ext=format)

        fileIO = getattr(module, '_export_{format}'.format(format=format))()

        return request.make_response(
                    fileIO.getvalue(),
                    headers=[('Content-Type', 'application/octet-stream'),
                             ('Content-Disposition', content_disposition(filename))])