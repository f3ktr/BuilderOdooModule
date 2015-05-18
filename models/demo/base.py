from openerp import models, api, fields, _


class GeneratorInterface(models.AbstractModel):
    _name = 'builder.ir.model.demo.generator.base'
    _description = 'Generator Interface'

    @api.one
    def get_generator(self):
        raise NotImplementedError

    @api.multi
    def action_save(self):
        return {'type': 'ir.actions.act_window_close'}


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

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

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
    def get_generator(self):
        return self.get_instance().generate()

    @api.multi
    def action_open_view(self):
        model = self._model
        action = model.get_formview_action(self.env.cr, self.env.uid, self.ids, self.env.context)
        action.update({'target': 'new'})
        return action


class IrModel(models.Model):
    _name = 'builder.ir.model'
    _inherit = ['builder.ir.model']

    demo_data_ids = fields.One2many(
        comodel_name='builder.ir.model.demo.generator',
        inverse_name='model_id',
        string='Demo Data',
    )


class IrModule(models.Model):
    _name = 'builder.ir.module.module'
    _inherit = ['builder.ir.module.module']

    demo_data_ids = fields.One2many(
        comodel_name='builder.ir.model.demo.generator',
        inverse_name='module_id',
        string='Demo Data',
    )
