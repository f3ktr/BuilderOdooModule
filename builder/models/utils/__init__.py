import types
from openerp import api
from openerp.osv import fields as fields_old


def simple_selection(model, value_field, label_field=None, domain=None):
    domain = domain or []
    label_field = label_field or value_field

    @api.model
    def _selection_function(self):
        return [(getattr(c, value_field), getattr(c, label_field)) for c in self.env[model].search(domain)]
    return _selection_function


def get_field_types(model):
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
        not issubclass(v, fields_old.function) and \
        (not context.get('from_diagram', False) or (
            context.get('from_diagram', False) and (k in ['one2many', 'many2one', 'many2many'])))

    ])
