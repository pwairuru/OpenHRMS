"""20.0.1.0.2: point KE rule legs at the per-authority payable accounts.

Data-file writes cannot do this on upgrade: the KE salary rules were
created under <data noupdate="1">, so ir.model.data marks them noupdate
and the loader skips them on every upgrade (mapping XML only takes
effect on fresh installs). This migration applies the same mapping
unconditionally.
"""


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    company = env.ref('base.main_company', raise_if_not_found=False)
    if not company:
        return

    mapping = [
        ('l10n_ke_hr_payroll_community.ke_rule_nssf_t1', 'account_credit_id', '230110'),
        ('l10n_ke_hr_payroll_community.ke_rule_nssf_t2', 'account_credit_id', '230110'),
        ('l10n_ke_hr_payroll_community.ke_rule_shif', 'account_credit_id', '230120'),
        ('l10n_ke_hr_payroll_community.ke_rule_ahl', 'account_credit_id', '230130'),
        ('l10n_ke_hr_payroll_community.ke_rule_paye', 'account_credit_id', '230140'),
        ('l10n_ke_hr_payroll_community.ke_rule_helb', 'account_credit_id', '230150'),
    ]
    for xmlid, leg, code in mapping:
        rule = env.ref(xmlid, raise_if_not_found=False)
        account = env['account.account'].search(
            [('code', '=', code), ('company_ids', '=', company.id)],
            limit=1)
        if rule and account and rule[leg] != account:
            rule.write({leg: account.id})
