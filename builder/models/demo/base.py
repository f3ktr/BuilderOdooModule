import json
import pickle
import os
import random

from openerp import models, api, fields, _


class GeneratorInterface(models.AbstractModel):
    _name = 'builder.ir.model.demo.generator.base'
    _description = 'Generator Interface'

    @api.multi
    def get_generator(self, field):
        raise NotImplementedError

    @api.multi
    def action_save(self):
        return {'type': 'ir.actions.act_window_close'}

    _demo_data = {}
    @api.model
    def get_demo_data(self, filename=None, dataFormat='json'):
        if filename is None:
            filename = "{name}.json".format(name=self.subclass_model)
        if filename not in self._demo_data:
            fullname = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data', filename))
            if os.path.exists(fullname):
                try:
                    if dataFormat == 'json':
                        self._demo_data[filename] = json.loads(open(fullname).read())
                    else:
                        self._demo_data[filename] = open(fullname).read()
                except Exception, e:
                    return {}
        return self._demo_data.get(filename, {})


class Generator(models.Model):
    _name = 'builder.ir.model.demo.generator'
    _description = 'Generic Generator'
    _inherit = ['ir.mixin.polymorphism.superclass', 'builder.ir.model.demo.generator.base']
    _order = 'module_id asc, model_id asc'
    _target_type = 'char'

    model_id = fields.Many2one('builder.ir.model', ondelete='cascade')
    module_id = fields.Many2one('builder.ir.module.module', 'Module', related='model_id.module_id', ondelete='cascade',
                                store=True)
    type = fields.Char('Type', compute='_compute_type')
    target_fields_type = fields.Char('Target Fields Type', compute='_compute_target_fields_type')
    field_ids = fields.Many2many(
        comodel_name='builder.ir.model.fields',
        relation='builder_model_demo_fields_rel',
        column1='generator_id',
        column2='field_id',
        string='Fields',
    )
    field_names = fields.Char('Field Names', compute='_compute_field_names', store=True)
    allow_nulls = fields.Boolean('Allow Null Values', help='If the field is not required allow to generate null values for them.')

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.multi
    def generate_null_values(self, field):
        if self.allow_nulls and not field.required:
            return random.random() <= (1.0 / (self.model_id.demo_records + 1))
        return False

    @api.one
    @api.depends('subclass_model')
    def _compute_type(self):
        data = dict(self.get_generators())
        self.type = data.get(self.subclass_model, _('Unknown'))

    @api.one
    @api.depends('field_ids.name')
    def _compute_field_names(self):
        self.field_names = ', '.join([field.name for field in self.field_ids])

    @api.one
    @api.depends('subclass_model')
    def _compute_target_fields_type(self):
        self.target_fields_type = self.env[self.subclass_model]._model._target_type



    @api.model
    def get_generators(self):
        ms = self.env['ir.model'].search([
            ('model', 'ilike', 'builder.ir.model.demo.generator.%'),
            ('model', 'not in', ['builder.ir.model.demo.generator.base', 'builder.ir.model.demo.generator'])
        ])

        return [
            (model.model, model.name)
            for model in ms
        ]

    @api.one
    def get_generator(self, field):
        return self.get_instance().get_generator(field)

    @api.multi
    def action_open_view(self):
        model = self._model
        action = model.get_formview_action(self.env.cr, self.env.uid, self.ids, self.env.context)
        action.update({'target': 'new'})
        return action


class IrModel(models.Model):
    _name = 'builder.ir.model'
    _inherit = ['builder.ir.model']

    demo_records = fields.Integer('Demo Records')
    demo_data_ids = fields.One2many(
        comodel_name='builder.ir.model.demo.generator',
        inverse_name='model_id',
        string='Demo Data',
        copy=True,
    )
    demo_xml_id_sample = fields.Text(compute='_compute_demo_xml_id_sample', store=True)

    @api.one
    @api.depends('demo_records', 'model')
    def _compute_demo_xml_id_sample(self):
        tmpl = '{model}_'.format(model=self.model.lower().replace('.', '_')) + '{id}' if self.model else 'model_'
        self.demo_xml_id_sample = pickle.dumps([tmpl.format(id=i) for i in xrange(self.demo_records)])

    @api.multi
    def demo_xml_id(self, index):
        return pickle.loads(self.demo_xml_id_sample)[index]

    _field_generators = None
    @property
    def field_generators(self, reload=False):
        if not self._field_generators or reload:
            result = {}

            for generator in self.demo_data_ids:
                for field in generator.field_ids:
                    if field.name not in result:
                        result[field.name] = generator.instance.get_generator(field)

            self._field_generators = result
        return self._field_generators


class IrModule(models.Model):
    _name = 'builder.ir.module.module'
    _inherit = ['builder.ir.module.module']

    demo_data_ids = fields.One2many(
        comodel_name='builder.ir.model.demo.generator',
        inverse_name='module_id',
        string='Demo Data',
        copy=True,
    )
