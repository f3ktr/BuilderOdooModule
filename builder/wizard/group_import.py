__author__ = 'one'

from openerp import models, api, fields, _


class GroupImport(models.TransientModel):
    _name = 'builder.res.groups.import.wizard'

    group_ids = fields.Many2many('res.groups', 'builder_res_groups_import_wizard_group_rel', 'wizard_id', 'group_id', 'Groups')
    set_inherited = fields.Boolean('Set as Inherit', default=True)

    @api.one
    def action_import(self):
        group_obj = self.env['builder.res.groups']
        module = self.env[self.env.context.get('active_model')].search([('id', '=', self.env.context.get('active_id'))])

        for group in self.group_ids:
            data = self.env['ir.model.data'].search([('model', '=', group._name), ('res_id', '=', group.id)])
            xml_id = "{module}.{id}".format(module=data.module, id=data.name)

            module_group = self.env['builder.res.groups'].search([('module_id', '=', module.id), ('xml_id', '=', xml_id)])

            if not module_group.id:
                new_group = group_obj.create({
                    'module_id': self.env.context.get('active_id'),
                    'name': group.name,
                    'inherited': self.set_inherited,
                    'xml_id': xml_id,
                })

        return {'type': 'ir.actions.act_window_close'}