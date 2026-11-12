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
"""Wizard report tests: paid slips count, legacy NSSF lines count.

Regression cover for the empty-November-2026 NSSF statement: the report
filtered ``state == 'done'`` so paid slips were invisible, and after the
Tier I/II split it summed only the new codes, zeroing pre-split slips.
"""
from odoo.tests.common import TransactionCase

from ..wizard.ke_report_wizard import _nssf_total, _period_slips


class TestKeWizards(TransactionCase):
    def _company(self):
        return self.env.ref('base.main_company')

    def _journal(self, company):
        journal = self.env['account.journal'].search(
            [('code', '=', 'KEWIZ'), ('company_id', '=', company.id)],
            limit=1)
        if journal:
            return journal
        expense = self.env['account.account'].search(
            [('account_type', '=', 'expense'),
             ('company_ids', '=', company.id)], limit=1)
        if not expense:
            expense = self.env['account.account'].create({
                'name': 'KE Wizard Test Expense', 'code': '998103',
                'account_type': 'expense',
                'company_ids': [(6, 0, [company.id])],
            })
        return self.env['account.journal'].create({
            'name': 'KE Wizard Journal', 'code': 'KEWIZ', 'type': 'general',
            'company_id': company.id, 'default_account_id': expense.id,
        })

    def _slip(self, wage, date_from, date_to, state='draft'):
        company = self._company()
        employee = self.env['hr.employee'].create({
            'name': 'KE Wizard %s %s' % (wage, date_from),
            'company_id': company.id,
        })
        contract = self.env['hr.version'].search(
            [('employee_id', '=', employee.id)], limit=1)
        contract.write({
            'wage': wage,
            'contract_date_start': '2026-01-01',
            'structure_type_id': self.env.ref(
                'l10n_ke_hr_payroll_community.'
                'structure_type_ke_employee').id,
        })
        slip = self.env['hr.payslip'].create({
            'employee_id': employee.id,
            'contract_id': contract.id,
            'struct_id': self.env.ref(
                'l10n_ke_hr_payroll_community.ke_structure_regular').id,
            'date_from': date_from,
            'date_to': date_to,
            'company_id': company.id,
            'journal_id': self._journal(company).id,
        })
        if state in ('done', 'paid'):
            slip.action_payslip_done()
            self.assertEqual(slip.state, 'done')
        if state == 'paid':
            slip.action_mark_as_paid()
            self.assertEqual(slip.state, 'paid')
        return slip

    def _nssf_wizard(self, month, year):
        return self.env['ke.nssf.wizard'].create({
            'month': str(month), 'year': year})

    def test_period_slips_includes_paid(self):
        done = self._slip(100000, '2026-11-01', '2026-11-30', 'done')
        paid = self._slip(100000, '2026-11-01', '2026-11-30', 'paid')
        draft = self._slip(100000, '2026-11-01', '2026-11-30', 'draft')
        oct_paid = self._slip(100000, '2026-10-01', '2026-10-31', 'paid')
        got = {s.id for s in _period_slips(self._nssf_wizard(11, 2026))}
        # Superset: the DB may already hold real slips for the period.
        self.assertLessEqual({done.id, paid.id}, got)
        self.assertNotIn(draft.id, got)
        self.assertNotIn(oct_paid.id, got)

    def test_nssf_total_falls_back_to_legacy_line(self):
        slip = self._slip(100000, '2026-03-01', '2026-03-31', 'done')
        # Simulate a pre-split slip: tier lines replaced by one legacy line.
        slip.line_ids.filtered(
            lambda l: l.code in ('KE_NSSF_T1', 'KE_NSSF_T2')).unlink()
        self.env['hr.payslip.line'].create({
            'slip_id': slip.id,
            'salary_rule_id': self.env.ref(
                'l10n_ke_hr_payroll_community.ke_rule_nssf_t1').id,
            'code': 'KE_NSSF',
            'name': 'NSSF (legacy)',
            'category_id': self.env.ref(
                'l10n_ke_hr_payroll_community.ke_cat_nssf').id,
            'quantity': 1.0,
            'amount': -6000.0,
            'rate': 100.0,
        })
        self.assertEqual(6000.0, _nssf_total(slip))

    def test_nssf_export_runs_on_paid_period(self):
        self._slip(100000, '2026-11-01', '2026-11-30', 'paid')
        result = self._nssf_wizard(11, 2026).action_export()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
        # Real download URL, not a blocked data: URI.
        self.assertIn('/web/content/ir.attachment/', result.get('url'))

    def test_shif_export_runs_on_paid_period(self):
        self._slip(100000, '2026-11-01', '2026-11-30', 'paid')
        result = self.env['ke.shif.wizard'].create(
            {'month': '11', 'year': 2026}).action_export()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
        self.assertIn('/web/content/ir.attachment/', result.get('url'))

    def test_payslip_report_select_maps_ke_codes(self):
        select = self.env['hr.payslip.report']._select()
        self.assertIn('KE_BASIC', select)
        self.assertIn('KE_GROSS', select)
        self.assertIn('KE_NET', select)

    def test_p9_template_renders_cells(self):
        self._slip(100000, '2026-11-01', '2026-11-30', 'paid')
        wiz = self.env['ke.p9.wizard'].create({'year': 2026})
        html = self.env['ir.qweb']._render(
            'l10n_ke_hr_payroll_community.ke_p9_template', {'docs': wiz})
        self.assertIn('100000.00', html)
