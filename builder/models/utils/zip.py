import posixpath
import zipfile
from StringIO import StringIO


class ZipFile(object):

    def __init__(self, jinja_env=None, compress_type=zipfile.ZIP_DEFLATED, external_attr=2175008768):
        self.jinja_env = jinja_env
        self.fileIO = StringIO()
        self.zip = zipfile.ZipFile(self.fileIO, 'w')
        self.default_compress_type = compress_type
        self.default_external_attr = external_attr

    def write_template(self, filename, template, d, **kwargs):
        if not self.jinja_env:
            raise ValueError('Jinja2 Environment is not set')
        self.write(filename, self.jinja_env.get_template(template).render(d).encode('UTF-8'), **kwargs)

    def write(self, filename, content, external_attr=2175008768, compress_type=None):
        info = zipfile.ZipInfo(filename)
        info.compress_type = compress_type or self.default_compress_type
        info.external_attr = external_attr or self.default_external_attr
        self.zip.writestr(info, content)

    def get_zip(self):
        self.zip.close()
        self.fileIO.flush()
        return self.fileIO


class ModuleZipFile(object):
    def __init__(self, zip_file, module):
        self.zip_file = zip_file
        self.module = module

    def write_template(self, filename, template, d, **kwargs):
        self.zip_file.write_template(posixpath.join(self.module.name, filename), template, d, **kwargs)

    def write(self, filename, content, **kwargs):
        self.zip_file.write(posixpath.join(self.module.name, filename), content, **kwargs)
