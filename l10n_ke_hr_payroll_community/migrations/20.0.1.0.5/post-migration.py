"""20.0.1.0.5: PAYE reliefs become child sub-rules of KE_PAYE.

Fresh installs get the new state from the XML data files directly. Records
under <data noupdate="1"> are skipped by upgrades, so this migration applies
the same state to databases that already have the 20.0.1.0.x rules:

1. Refresh ``ke_rule_paye`` to the gross-band-tax body (reliefs moved out
   to the ``ke_rule_relief_pers`` / ``ke_rule_relief_ins`` child rules, which
   are new records and therefore created by the upgrade itself).
2. Old slips keep their stored lines (net KE_PAYE, no relief lines); only
   future computes use the split. P9/report readers must treat a missing
   relief line as "not computed", never as zero relief.
"""

NEW_PAYE_BODY = """bands = payslip.ke_get_param('ke_paye_bands')
disability = payslip.ke_get_param('ke_disability')
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
# Gross band tax. Personal + insurance reliefs are child rules
# (KE_RELIEF_PERS / KE_RELIEF_INS) so each relief shows on the slip;
# the KE_PAYE category total stays the net tax payable.
result = -tax"""


def migrate(cr, version):
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    ref = lambda xmlid: env.ref(xmlid, raise_if_not_found=False)

    paye = ref('l10n_ke_hr_payroll_community.ke_rule_paye')
    if paye and paye.amount_python_compute.strip() != NEW_PAYE_BODY.strip():
        paye.write({'amount_python_compute': NEW_PAYE_BODY})

    # Children are new records: created by the data files, but wire the
    # parent link defensively in case the records pre-date this version.
    parent = paye
    for xmlid in ('l10n_ke_hr_payroll_community.ke_rule_relief_pers',
                  'l10n_ke_hr_payroll_community.ke_rule_relief_ins'):
        child = ref(xmlid)
        if child and parent and not child.parent_rule_id:
            child.write({'parent_rule_id': parent.id})
