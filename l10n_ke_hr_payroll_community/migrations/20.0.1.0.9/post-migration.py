"""20.0.1.0.9: pin the module to the canonical Localization category.

The "Choose a Payroll Localization" Apps action exact-matches
``base.module_category_accounting_localizations``. Manifest category
strings resolve by name walk, and long-lived databases grow duplicate
category nodes (translated names, repeated installs), so the manifest
alone parked this module on a twin node and hid it from that list.
Point it at the canonical xmlid on every upgrade; harmless no-op on
clean databases. Drop the twin node if nothing references it.
"""


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    canonical = env.ref('base.module_category_accounting_localizations',
                        raise_if_not_found=False)
    if not canonical:
        return
    mod = env['ir.module.module'].search(
        [('name', '=', 'l10n_ke_hr_payroll_community')], limit=1)
    if not mod:
        return
    old = mod.category_id
    if old != canonical:
        mod.write({'category_id': canonical.id})
    if old and old != canonical and not env['ir.module.module'].search(
            [('category_id', '=', old.id)], limit=1):
        old.unlink()
