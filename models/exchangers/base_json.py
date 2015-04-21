import json

from openerp import models, api


class OdooBuilderTranslator(object):
    def __init__(self):
        self.seen_models = set()

    def translate(self, obj):
        if isinstance(obj, models.Model):
            instance = {'@model': obj._model._name, '@id': obj.id}
            obj_id = obj._model._name, obj.id
            if obj.id and obj_id not in self.seen_models and obj._model._name.startswith('builder.'):
                self.seen_models.add(obj_id)
                for name, column in obj._model._columns.items():
                    if name in ['id', 'write_uid', 'write_date', 'create_date', 'create_uid']:
                        continue
                    if getattr(column, '_fnct', False) or not getattr(column, 'store', True):
                        continue
                    if column._type in ['char', 'boolean', 'integer', 'reference', 'text', 'html', 'float', 'date', 'datetime', 'selection', 'binary']:
                        instance[name] = getattr(obj, name)
                    else:
                        instance[name] = getattr(self, 'handle_model_{type}'.format(type=column._type))(obj, name)
            return instance if obj.id else False
        return obj

    def handle_model_one2many(self, obj, name):
        return [
            self.translate(item)
            for item in getattr(obj, name)
        ]

    def handle_model_many2many(self, obj, name):
        return [
            self.translate(item)
            for item in getattr(obj, name)
        ]

    def handle_model_many2one(self, obj, name):
        return self.translate(getattr(obj, name))


class JSONExchanger(models.Model):
    _name = 'builder.exchanger.json'
    _inherit = ['builder.exchanger.base']
    _description = 'Odoo Builder JSON'

    @api.model
    def get_extension(self):
        return 'obj1'

    @api.model
    def get_export_module_filename(self, module):
        return '{name}.json'.format(name=module.name)

    @api.model
    def export_module(self, module):
        translator = OdooBuilderTranslator()
        return json.dumps(translator.translate(module), sort_keys=True, indent=4)
