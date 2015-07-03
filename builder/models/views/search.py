from collections import defaultdict
from ..fields import snake_case
from openerp import models, fields, api

__author__ = 'one'


class SearchView(models.Model):
    _name = 'builder.views.search'

    _inherit = ['ir.mixin.polymorphism.subclass']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    field_ids = fields.One2many('builder.views.search.field', 'view_id', 'Search Items', copy=True)

    _defaults = {
        'type': 'search',
        'subclass_model': lambda s, c, u, cxt=None: s._name,
    }

    @api.model
    def create_instance(self, id):
        self.create({
            'view_id': id,
        })

    @api.multi
    def action_save(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.onchange('model_id')
    def _onchange_model_id(self):
        model_id = self.model_id
        self.name = model_id.name
        self.xml_id = "view_{snake}_search".format(snake=snake_case(model_id.model))
        self.model_inherit_type = model_id.inherit_type  # shouldn`t be doing that
        self.model_name = model_id.model  # shouldn`t be doing that

    @api.multi
    def find_field_by_name(self, name):
        field_obj = self.env['builder.ir.model.fields']
        return field_obj.search([('model_id', '=', self.id), ('name', '=', name)])

    @property
    def ungrouped_fields(self):
        flat = []
        for field in self.field_ids:
            if not field.group:
                flat.append(field)
        return flat

    @property
    def groups(self):
        groups = defaultdict(list)
        for field in self.field_ids:
            if field.group:
                groups[field.group].append(field)
        return groups


class SearchField(models.Model):
    _name = 'builder.views.search.field'
    _inherit = 'builder.views.abstract.field'

    _order = 'view_id, sequence, id'

    view_id = fields.Many2one('builder.views.search', string='View', ondelete='cascade')
    type = fields.Selection([('field', 'Field'), ('filter', 'Filter'), ('separator', 'Separator')], string='Type',
                            required=False, default='field')
    field_id = fields.Many2one('builder.ir.model.fields', string='Field', required=False, ondelete='cascade')
    group_field_id = fields.Many2one('builder.ir.model.fields', string='Group By', ondelete='set null')
    group = fields.Char('Group')
    attr_name = fields.Char('Name')
    attr_string = fields.Char('String')
    attr_filter_domain = fields.Char('Filter Domain')
    attr_domain = fields.Char('Domain')
    attr_operator = fields.Char('Operator')
    attr_help = fields.Char('Help')

    @api.one
    @api.depends('field_id.ttype', 'view_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype
