"""20.0.1.0.3: wire statutory creditor partners to their payable accounts.

Registers and partners are noupdate records, so data files only take
effect on fresh installs (ke_authority_partners_data.xml,
ke_register_partners_data.xml). This migration converges upgrades:

1. For each authority: adopt the same-named existing partner if there is
   one (set its payable property + vendor rank, link the register if it
   has none), else keep the shipped partner and link the register to it.
   Shipped duplicates with no moves behind them are removed.
"""


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    pairs = [
        ('ke_partner_kra', 'Kenya Revenue Authority',
         'ke_account_paye_payable', 'KRA - PAYE'),
        ('ke_partner_nssf', 'NSSF',
         'ke_account_nssf_payable', 'NSSF Kenya'),
        ('ke_partner_sha', 'Social Health Authority',
         'ke_account_shif_payable', 'SHA - SHIF'),
        ('ke_partner_ahl', 'Affordable Housing Board',
         'ke_account_ahl_payable', 'Housing Levy'),
    ]
    MoveLine = env['account.move.line']
    for partner_xmlid, name, account_xmlid, register_name in pairs:
        account = env.ref(
            'l10n_ke_hr_payroll_account_community.' + account_xmlid,
            raise_if_not_found=False)
        register = env['hr.contribution.register'].search(
            [('name', '=', register_name)], limit=1)
        if not account or not register:
            continue
        shipped = env.ref(
            'l10n_ke_hr_payroll_account_community.' + partner_xmlid,
            raise_if_not_found=False)
        existing = env['res.partner'].search([('name', '=', name)])
        if shipped:
            existing = existing.filtered(lambda p: p.id != shipped.id)
        target = existing[:1] if existing else shipped
        if not target:
            continue
        vals = {}
        if target.property_account_payable_id != account:
            vals['property_account_payable_id'] = account.id
        if not target.supplier_rank:
            vals['supplier_rank'] = 1
        if vals:
            target.write(vals)
        if not register.partner_id:
            register.write({'partner_id': target.id})
        if shipped and existing and not MoveLine.search(
                [('partner_id', '=', shipped.id)], limit=1):
            shipped.unlink()
