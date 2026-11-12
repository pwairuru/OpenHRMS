# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import models

# (rule xmlid, leg field, l10n_ke_hr_payroll_account_community account code).
# Mirrors data/ke_account_mapping_data.xml. Deduction rules carry both legs
# (debit 630000 Salary Expenses, credit per-authority payable) so Done
# slips post balanced, correctly-sided moves; the upstream adjustment entry
# absorbs the gross-up difference on the journal default account. The XML
# alone cannot resolve the legs reliably: company accounts are generated
# after the module graph loads, and noupdate salary-rule records are skipped
# by later upgrades. This hook re-applies the mapping at every registry
# setup instead: it only fills legs that are still empty, so user
# customizations are kept and the hook is a no-op once everything
# resolved.
KE_RULE_ACCOUNT_MAPPING = [
    ('l10n_ke_hr_payroll_community.ke_rule_basic', 'account_debit_id', '630000'),
    ('l10n_ke_hr_payroll_community.ke_rule_nssf_t1', 'account_debit_id', '630000'),
    ('l10n_ke_hr_payroll_community.ke_rule_nssf_t1', 'account_credit_id', '230110'),
    ('l10n_ke_hr_payroll_community.ke_rule_nssf_t2', 'account_debit_id', '630000'),
    ('l10n_ke_hr_payroll_community.ke_rule_nssf_t2', 'account_credit_id', '230110'),
    ('l10n_ke_hr_payroll_community.ke_rule_shif', 'account_debit_id', '630000'),
    ('l10n_ke_hr_payroll_community.ke_rule_shif', 'account_credit_id', '230120'),
    ('l10n_ke_hr_payroll_community.ke_rule_ahl', 'account_debit_id', '630000'),
    ('l10n_ke_hr_payroll_community.ke_rule_ahl', 'account_credit_id', '230130'),
    ('l10n_ke_hr_payroll_community.ke_rule_paye', 'account_debit_id', '630000'),
    ('l10n_ke_hr_payroll_community.ke_rule_paye', 'account_credit_id', '230140'),
    ('l10n_ke_hr_payroll_community.ke_rule_net', 'account_credit_id', '230000'),
    ('l10n_ke_hr_payroll_community.ke_rule_helb', 'account_debit_id', '630000'),
    ('l10n_ke_hr_payroll_community.ke_rule_helb', 'account_credit_id', '230150'),
]


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    def _register_hook(self):
        super()._register_hook()
        company = self.env.ref('base.main_company', raise_if_not_found=False)
        if not company:
            return
        Account = self.env['account.account']
        for xmlid, leg, code in KE_RULE_ACCOUNT_MAPPING:
            rule = self.env.ref(xmlid, raise_if_not_found=False)
            if not rule or rule[leg]:
                continue
            account = Account.search(
                [('code', '=', code), ('company_ids', '=', company.id)],
                limit=1)
            if account:
                rule[leg] = account.id
