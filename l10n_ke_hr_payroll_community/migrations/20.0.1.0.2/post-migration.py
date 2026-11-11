"""20.0.1.0.2: converge existing installs to the Tier I/II NSSF split.

Fresh installs get the new state from the XML data files directly. Records
under <data noupdate="1"> are skipped by upgrades, so this migration applies
the same state to databases that already have the 20.0.1.0.x rules:

1. Deactivate the old single-line ``ke_rule_nssf`` (replaced by
   ``ke_rule_nssf_t1`` / ``ke_rule_nssf_t2``). Old slips keep their stored
   lines; only future computes are affected.
2. Point ``ke_structure_regular`` at the new 11-rule set.
3. Refresh ``amount_python_compute`` on the rules whose bodies changed since
   20.0.1.0.0 (30% pension leg, nonresident post-med add-back, fringe info
   fix). Bodies below are frozen snapshots of
   ``data/hr_salary_rule_data.xml`` at 20.0.1.0.2.
"""


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    ref = lambda xmlid: env.ref(xmlid, raise_if_not_found=False)

    old_nssf = ref('l10n_ke_hr_payroll_community.ke_rule_nssf')
    if old_nssf and old_nssf.active:
        old_nssf.write({'active': False})

    wanted = [
        'l10n_ke_hr_payroll_community.ke_rule_basic',
        'l10n_ke_hr_payroll_community.ke_rule_gross',
        'l10n_ke_hr_payroll_community.ke_rule_nssf_t1',
        'l10n_ke_hr_payroll_community.ke_rule_nssf_t2',
        'l10n_ke_hr_payroll_community.ke_rule_shif',
        'l10n_ke_hr_payroll_community.ke_rule_ahl',
        'l10n_ke_hr_payroll_community.ke_rule_taxable',
        'l10n_ke_hr_payroll_community.ke_rule_paye',
        'l10n_ke_hr_payroll_community.ke_rule_net',
        'l10n_ke_hr_payroll_community.ke_rule_helb',
        'l10n_ke_hr_payroll_community.ke_rule_fringe_info',
    ]
    struct = ref('l10n_ke_hr_payroll_community.ke_structure_regular')
    if struct:
        ids = [r.id for xmlid in wanted if (r := ref(xmlid))]
        if ids:
            struct.write({'rule_ids': [(6, 0, ids)]})

    bodies = {
        'l10n_ke_hr_payroll_community.ke_rule_taxable': """pension_cap = payslip.ke_get_param('ke_pension_cap')
mortgage_cap = payslip.ke_get_param('ke_mortgage_cap')
post_med_cap = payslip.ke_get_param('ke_post_med_cap')
# Pension deduction = min(voluntary + NSSF, monthly cap, 30% of pensionable).
# v1: pensionable == contract.wage (no allowance rules yet); revisit with allowance rules.
# ke_pension holds voluntary pension EXCLUDING NSSF (NSSF added automatically); entering total pension double-counts NSSF.
pensionable = contract.wage
pension_ded = min(contract.ke_pension - categories.KE_NSSF, pension_cap['monthly'], 0.3 * pensionable)
result = categories.GROSS + categories.KE_SHIF + categories.KE_AHL - pension_ded - min(contract.ke_mortgage, mortgage_cap) - min(contract.ke_post_med, post_med_cap)""",
        'l10n_ke_hr_payroll_community.ke_rule_paye': """bands = payslip.ke_get_param('ke_paye_bands')
disability = payslip.ke_get_param('ke_disability')
ins = payslip.ke_get_param('ke_insurance')
taxable = KE_TAXABLE
# Disability exemption needs a valid certificate: first ke_disability of taxable pay is exempt.
if contract.ke_disabled and contract.ke_disability_cert:
    taxable = max(KE_TAXABLE - disability, 0.0)
# Non-resident employees get no reliefs and no pension/mortgage/post-med deduction.
# KE_TAXABLE already deducted all three, so add those three deductions back here.
nonresident = bool(contract.ke_nonresident)
if nonresident:
    pension_cap = payslip.ke_get_param('ke_pension_cap')
    mortgage_cap = payslip.ke_get_param('ke_mortgage_cap')
    post_med_cap = payslip.ke_get_param('ke_post_med_cap')
    pension_ded = min(contract.ke_pension - categories.KE_NSSF, pension_cap['monthly'], 0.3 * contract.wage)
    taxable = taxable + pension_ded + min(contract.ke_mortgage, mortgage_cap) + min(contract.ke_post_med, post_med_cap)
tax = 0.0
base = 0.0
for width, rate in bands:
    w = width if width > 0 else float('inf')
    chunk = min(max(taxable - base, 0.0), w)
    tax += chunk * rate
    base += w
    if taxable <= base:
        break
relief = 0.0
ins_relief = 0.0
if not contract.ke_secondary and not nonresident:
    relief = payslip.ke_get_param('ke_personal_relief')
if not contract.ke_secondary and not nonresident:
    ins_relief = min(ins['rate'] * (contract.ke_insurance_life + contract.ke_insurance_health + contract.ke_insurance_edu), ins['monthly_max'])
result = -max(tax - relief - ins_relief, 0.0)""",
        'l10n_ke_hr_payroll_community.ke_rule_fringe_info': """# Informational only: employer fringe benefit tax is computed off-slip at
# 30% x (mkt - contract.ke_loan_rate) x contract.ke_loan_balance / 12.
# No ke_get_param lookup here on purpose: fringe rates are seeded from
# 2026 only, and this info rule must stay 0.0 on every slip, including
# pre-2026 periods (a lookup would raise UserError there).
result = 0.0""",
    }
    for xmlid, body in bodies.items():
        rule = ref(xmlid)
        if rule and rule.amount_python_compute.strip() != body.strip():
            rule.write({'amount_python_compute': body})
