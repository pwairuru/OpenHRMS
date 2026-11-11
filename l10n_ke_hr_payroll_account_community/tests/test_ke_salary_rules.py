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
from odoo.tests.common import TransactionCase


class TestKeRules(TransactionCase):
    """Oracle + mapping tests for the Kenya payroll accounting bridge.

    Oracle vector (wage=100000, March 2026, default contract flags):
    NSSF -6000 / SHIF -2750 / AHL -1500 / PAYE -19308.35 / NET 70441.65.
    """

    # rule xmlid -> (leg field, expected l10n_ke account code)
    MAPPING = {
        'l10n_ke_hr_payroll_community.ke_rule_basic': ('account_debit_id', '5109'),
        'l10n_ke_hr_payroll_community.ke_rule_nssf': ('account_credit_id', '2230'),
        'l10n_ke_hr_payroll_community.ke_rule_shif': ('account_credit_id', '2231'),
        'l10n_ke_hr_payroll_community.ke_rule_ahl': ('account_credit_id', '2102'),
        'l10n_ke_hr_payroll_community.ke_rule_paye': ('account_credit_id', '2210'),
        'l10n_ke_hr_payroll_community.ke_rule_net': ('account_credit_id', '2220'),
        'l10n_ke_hr_payroll_community.ke_rule_helb': ('account_credit_id', '2232'),
    }
    # AHL has no dedicated payable in the core l10n_ke chart: 2102 is the
    # documented fallback (see data/ke_account_mapping_data.xml).

    def _ke_company(self):
        return self.env.ref('base.main_company')

    def _ke_rule(self, xmlid):
        return self.env.ref(xmlid)

    def _ensure_journal(self, company):
        journal = self.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)
        if not journal:
            journal = self.env['account.journal'].create({
                'name': 'KE Salary Journal (test)',
                'code': 'KEPAY',
                'type': 'general',
                'company_id': company.id,
            })
        return journal

    def _ensure_rule_accounts(self, company):
        """Fallback legs so Done slips post with or without the KE chart.

        Only fills legs the mapping left empty; mapped legs are kept, so a
        charted DB exercises the real mapping in the oracle tests too.
        """
        Account = self.env['account.account']
        expense = Account.search(
            [('account_type', '=', 'expense'), ('company_id', '=', company.id)],
            limit=1)
        payable = Account.search(
            [('account_type', '=', 'liability_payable'),
             ('reconcile', '=', True),
             ('company_id', '=', company.id)], limit=1)
        if not expense:
            expense = Account.create({
                'name': 'KE Test Salary Expense', 'code': '998101',
                'account_type': 'expense', 'company_id': company.id,
            })
        if not payable:
            payable = Account.create({
                'name': 'KE Test Salary Payable', 'code': '998102',
                'account_type': 'liability_payable', 'reconcile': True,
                'company_id': company.id,
            })
        for xmlid, (leg, _code) in self.MAPPING.items():
            rule = self._ke_rule(xmlid)
            if not rule[leg]:
                rule[leg] = expense if leg == 'account_debit_id' else payable

    def _make_slip(self, wage, date_from='2026-03-01', date_to='2026-03-31',
                   **ke_fields):
        company = self._ke_company()
        employee = self.env['hr.employee'].create({
            'name': 'KE Test Employee %s' % wage,
            'company_id': company.id,
        })
        contract = self.env['hr.version'].create(dict({
            'employee_id': employee.id,
            'wage': wage,
            'contract_date_start': '2026-01-01',
        }, **ke_fields))
        self._ensure_rule_accounts(company)
        slip = self.env['hr.payslip'].create({
            'employee_id': employee.id,
            'contract_id': contract.id,
            'struct_id': self.env.ref(
                'l10n_ke_hr_payroll_community.ke_structure_regular').id,
            'date_from': date_from,
            'date_to': date_to,
            'company_id': company.id,
            'journal_id': self._ensure_journal(company).id,
        })
        slip.action_payslip_done()
        self.assertEqual(slip.state, 'done')
        return slip

    def _totals(self, slip):
        return {line.code: line.total for line in slip.line_ids}

    def test_oracle_100k(self):
        totals = self._totals(self._make_slip(100000))
        self.assertEqual(totals['KE_BASIC'], 100000.0)
        self.assertEqual(totals['KE_GROSS'], 100000.0)
        self.assertEqual(totals['KE_NSSF'], -6000.0)
        self.assertEqual(totals['KE_SHIF'], -2750.0)
        self.assertEqual(totals['KE_AHL'], -1500.0)
        self.assertAlmostEqual(totals['KE_PAYE'], -19308.35, places=2)
        self.assertAlmostEqual(totals['KE_NET'], 70441.65, places=2)

    def test_nssf_cap_200k(self):
        totals = self._totals(self._make_slip(200000))
        self.assertEqual(totals['KE_NSSF'], -6480.0)

    def test_shif_floor_5k(self):
        totals = self._totals(self._make_slip(5000))
        self.assertEqual(totals['KE_SHIF'], -300.0)

    def test_mapping_accounts(self):
        company = self._ke_company()
        for xmlid, (leg, code) in self.MAPPING.items():
            with self.subTest(rule=xmlid):
                account = self.env['account.account'].search(
                    [('code', '=', code), ('company_id', '=', company.id)],
                    limit=1)
                if not account:
                    self.skipTest(
                        'l10n_ke account %s not installed; mapping leg '
                        'unresolvable here' % code)
                self.assertEqual(self._ke_rule(xmlid)[leg], account)

    def test_info_rules_have_no_accounts(self):
        for xmlid in (
                'l10n_ke_hr_payroll_community.ke_rule_gross',
                'l10n_ke_hr_payroll_community.ke_rule_taxable',
                'l10n_ke_hr_payroll_community.ke_rule_fringe_info'):
            with self.subTest(rule=xmlid):
                rule = self._ke_rule(xmlid)
                self.assertFalse(rule.account_debit_id)
                self.assertFalse(rule.account_credit_id)
