from collections import defaultdict
import re
import types
from openerp.osv import fields  as fields_old
from openerp import models, fields, api, _


class IrModel(models.Model):
    _name = 'builder.res.config.settings'
    _description = "Configuration Model"
    _order = 'sequence asc, model asc'

    _rec_name = 'model'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', required=True, select=1, ondelete='cascade')
    sequence = fields.Integer('Sequence')
    model = fields.Char('Model', required=True, select=1)
    name = fields.Char('Description', required=True)

    field_ids = fields.One2many('builder.res.config.settings.field', 'model_id', 'Fields', required=True, copy=True)

    @api.multi
    def action_fields(self):
        return {
            'name': _('Fields'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': self.field_ids._name,
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('model_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.module_id.id,
                'default_model_id': self.id,
            },
        }


class InheritsModel(models.Model):
    _name = 'builder.res.config.settings.field'
    _order = 'position asc'

    @api.model
    def _get_fields_type_selection(self):
        context = {}
        # Avoid too many nested `if`s below, as RedHat's Python 2.6
        # break on it. See bug 939653.
        return sorted([
            (k, k) for k, v in fields_old.__dict__.iteritems()
            if type(v) == types.TypeType and \
            issubclass(v, fields_old._column) and \
            v != fields_old._column and \
            not v._deprecated and \
            # not issubclass(v, fields_old.function)])
            not issubclass(v, fields_old.function)
        ])

    model_id = fields.Many2one('builder.ir.model', 'Model', ondelete='cascade')
    module_id = fields.Many2one('builder.ir.module.module', string='Module', related='model_id.module_id',
                                ondelete='cascade')

    position = fields.Integer('Position')

    setting_field_type = fields.Selection([
                                              ('module', 'Module Toggle Field'),
                                              ('default', 'Default Value Field'),
                                              ('group', 'Group Field'),
                                              ('other', 'Normal Field'),
                                          ], 'Setting Type', default='other', required=True)

    toggle_module_id = fields.Many2one('ir.module.module', 'Module', store=False)
    toggle_module_name = fields.Char('Module Name')

    default_type = fields.Selection([('module', 'Module'), ('system', 'System')], 'Default Type')
    default_system_model_id = fields.Many2one('ir.model', 'System Model', store=False)
    default_model_id = fields.Many2one('builder.ir.model', 'Builder Model')
    default_model = fields.Char('Model')
    default_field_name = fields.Char('Field Name')
    default_system_model_field_id = fields.Many2one('ir.model.fields', 'System Field', store=False, domain="[('model_id', '=', default_system_model_id)]", change_default=True)
    default_model_field_id = fields.Many2one('builder.ir.model.fields', 'Builder Field', domain="[('model_id', '=', default_model_id)]", change_default=True)

    group_type = fields.Selection([('module', 'Module'), ('system', 'System')], 'Group Type')
    group_system_group_id = fields.Many2one('res.groups', 'System Group', store=False)
    group_group_id = fields.Many2one('builder.res.groups', 'Builder Group')
    group_name = fields.Char('Implied Group')

    name = fields.Char('Field', compute='_compute_field_name', store=True, readonly=False)

    relation = fields.Char('Object Relation',
                           help="For relationship fields, the technical name of the target model")

    relation_model_id = fields.Many2one('builder.ir.model', 'Model', ondelete='set null')

    relation_many2many_comodel_name = fields.Char('Comodel Name')
    relation_many2many_relation = fields.Char('Relation Name')
    relation_many2many_column1 = fields.Char('Column1')
    relation_many2many_column2 = fields.Char('Column2')

    relation_create_inverse_relation = fields.Boolean('Create Inverse Relation',
                                                      help="Generates an inverse relation in the target model.")
    reverse_relation_name = fields.Char('Reverse Relation Name')
    reverse_relation_field_description = fields.Char('Reverse Relation Description')

    relation_field = fields.Char('Relation Field',
                                 help="For one2many fields, the field on the target model that implement the opposite many2one relationship")

    field_description = fields.Char('Field Label')
    related = fields.Char('Related')
    ttype = fields.Selection(_get_fields_type_selection, 'Field Type')
    required = fields.Boolean('Required')
    readonly = fields.Boolean('Readonly')
    select_level = fields.Selection(
        [('0', 'Not Searchable'), ('1', 'Always Searchable'), ('2', 'Advanced Search (deprecated)')], 'Searchable',
        required=True, default='0')
    translate = fields.Boolean('Translatable',
                               help="Whether values for this field can be translated (enables the translation mechanism for that field)")
    size = fields.Char('Size')
    index = fields.Boolean('Index')
    help = fields.Text('Help')
    delegate = fields.Boolean('Delegate', default=True, help=''' set it to ``True`` to make fields of the target model
        accessible from the current model (corresponds to ``_inherits``)''')
    auto_join = fields.Boolean('Auto Join', help='Whether JOINs are generated upon search through that field (boolean, by default ``False``')
    groups = fields.Char('Groups', help='''comma-separated list of group xml ids (string); this
                                         restricts the field access to the users of the given groups only''')
    decimal_digits = fields.Char('Decimal Digits', )
    decimal_precision = fields.Char('Decimal Precision')

    on_delete = fields.Selection([('cascade', 'Cascade'), ('set null', 'Set NULL'), ('restrict', 'Restrict')],
                                 'On Delete', default='set null', help='On delete property for many2one fields')
    domain = fields.Char('Domain', default='[]',
                         help="The optional domain to restrict possible values for relationship fields, "
                              "specified as a Python expression defining a list of triplets. "
                              "For example: [('color','=','red')]")
    default_value = fields.Char('Default Value')

    @api.onchange('default_type', 'default_model_id', 'default_system_model_id')
    def onchange_default_model_id(self):
        self.default_model = False
        if self.default_type == 'module' and self.default_model_id:
            self.default_model = self.default_model_id.model
        elif self.default_type == 'system' and self.default_system_model_id:
            self.default_model = self.default_system_model_id.model

    @api.onchange('default_type', 'default_model_field_id', 'default_system_model_field_id')
    def onchange_default_model_field_id(self):
        self.default_field_name = False
        if self.default_type == 'module' and self.default_model_field_id:
            self.default_field_name = self.default_model_field_id.name
            self.ttype = self.default_model_field_id.ttype
        elif self.default_type == 'system' and self.default_system_model_field_id:
            self.default_field_name = self.default_system_model_field_id.name
            self.ttype = self.default_system_model_field_id.ttype


    @api.onchange('relation_model_id')
    def onchange_relation_model_id(self):
        if self.relation_model_id:
            self.relation = self.relation_model_id.model
        else:
            self.relation = False

    @api.one
    @api.onchange('setting_field_type', 'toggle_module_name', 'default_field_name', 'group_name')
    @api.depends('setting_field_type', 'toggle_module_name', 'default_field_name', 'group_name')
    def _compute_field_name(self):
        if self.setting_field_type == 'module' and self.toggle_module_name:
            self.name = "module_{}".format(self.toggle_module_name)
            self.ttype = 'boolean'
        elif self.setting_field_type == 'default' and self.default_field_name:
            self.name = "default_{}".format(self.default_field_name)
        elif self.setting_field_type == 'group' and self.group_name:
            self.name = "group_{}".format(re.sub('\.', '_', self.group_name))
            self.ttype = 'boolean'

    @api.onchange('toggle_module_id')
    def onchange_toggle_module_id(self):
        if self.setting_field_type == 'module' and self.toggle_module_id:
            self.toggle_module_name = self.toggle_module_id.name

    @api.onchange('default_type', 'default_system_model_id', 'default_model_id')
    def onchange_default_system(self):
        if self.default_type == 'module' and self.default_model_id:
            self.default_model = self.default_model_id.model
        elif self.default_type == 'system' and self.default_system_model_id:
            self.default_model = self.default_system_model_id.model

    @api.onchange('group_type', 'group_system_group_id', 'group_group_id')
    def onchange_default_system(self):
        if self.group_type == 'module' and self.group_group_id:
            self.group_name = "{module}.{id}".format(module=self.module_id.name, id=self.group_group_id.name)
        elif self.group_type == 'system' and self.group_system_group_id:
            data = self.env['ir.model.data'].search([('model', '=', 'res.groups'), ('res_id', '=', self.group_system_group_id.id)])
            if data:
                self.group_name = "{module}.{id}".format(module=data.module, id=data.name)

    # @api.onchange('default_system_model_id', 'default_type')
    # def onchange_default_model(self):
    #     if self.default_type == 'system':
    #         self.default_model =

