# -*- coding: utf-8 -*-
"""P10 Sheet B import-CSV tests: KRA iTax monthly PAYE return extract.

RED: KeP10Wizard does not exist yet. The CSV must carry one row per
done/paid primary-contract slip with the Sheet B fields from KRA's
step-by-step guide (PIN, name, resident/PWD flags, pay, capped
deductions, chargeable, gross tax, reliefs, self-assessed PAYE), so HR
can IMPORT CSV straight into the iTax Excel return.
"""
import base64
import csv
import io

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestKeP10(TransactionCase):
    def _company(self):
        return self.env.ref('base.main_company')

    def _journal(self, company):
        journal = self.env['account.journal'].search(
            [('code', '=', 'KEP10'), ('company_id', '=', company.id)],
            limit=1)
        if journal:
            return journal
        expense = self.env['account.account'].search(
            [('account_type', '=', 'expense'),
             ('company_ids', '=', company.id)], limit=1)
        if not expense:
            expense = self.env['account.account'].create({
                'name': 'KE P10 Test Expense', 'code': '998104',
                'account_type': 'expense',
                'company_ids': [(6, 0, [company.id])],
            })
        return self.env['account.journal'].create({
            'name': 'KE P10 Journal', 'code': 'KEP10', 'type': 'general',
            'company_id': company.id, 'default_account_id': expense.id,
        })

    def _slip(self, wage, date_from, date_to, state='paid', pin='A123456789Z'):
        company = self._company()
        employee = self.env['hr.employee'].create({
            'name': 'KE P10 %s %s' % (wage, date_from),
            'identification_id': '30000001',
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
            'ke_kra_pin': pin,
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

    def _csv_rows(self, month, year):
        from ..wizard.ke_report_wizard import KE_P10_SHEET_B_HEADER
        result = self.env['ke.p10.wizard'].create(
            {'month': str(month), 'year': year}).action_export_csv()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
        self.assertIn('/web/content/ir.attachment/', result.get('url'))
        att = self.env['ir.attachment'].search(
            [('name', 'like', 'P10_%')], order='id desc', limit=1)
        data = att.raw
        if hasattr(data, 'content'):  # LocalBinaryFile (filestore-backed)
            data = data.content
        elif hasattr(data, 'read_bytes'):
            data = data.read_bytes()
        elif hasattr(data, 'read'):
            data = data.read()
        raw = data.decode('utf-8') if isinstance(data, bytes) else data
        rows = list(csv.reader(io.StringIO(raw)))
        self.assertEqual(rows[0], KE_P10_SHEET_B_HEADER)
        return rows[1:]

    def test_p10_header_and_row_values(self):
        slip = self._slip(100000, '2026-11-01', '2026-11-30', 'paid')
        rows = self._csv_rows(11, 2026)
        row = [r for r in rows if r[0] == 'A123456789Z']
        self.assertTrue(row, 'own slip PIN row must be present')
        row = row[0]
        from ..wizard.ke_report_wizard import KE_P10_SHEET_B_HEADER as H
        got = dict(zip(H, row))
        self.assertEqual(got['Employee Name'], slip.employee_id.name)
        self.assertEqual(got['ID Number'], '30000001')
        self.assertEqual(got['Resident'], 'Yes')
        self.assertEqual(float(got['Gross Pay']), 100000.00)
        # Relief path: personal relief applies, PAYE reconciles.
        self.assertEqual(float(got['Personal Relief']), 2400.00)
        tax = float(got['Tax Charged'])
        self.assertGreater(tax, 0.0)
        self.assertAlmostEqual(
            float(got['Self-Assessed PAYE']), tax - 2400.00, places=2)

    def test_p10_excludes_draft_and_other_month(self):
        self._slip(100000, '2026-11-01', '2026-11-30', 'paid',
                   pin='A123456789Z')
        self._slip(100000, '2026-11-01', '2026-11-30', 'draft',
                   pin='A000000001D')
        self._slip(100000, '2026-10-01', '2026-10-31', 'paid',
                   pin='A000000002D')
        rows = self._csv_rows(11, 2026)
        pins = [r[0] for r in rows]
        self.assertNotIn('A000000001D', pins)
        self.assertNotIn('A000000002D', pins)

    def test_p10_no_slips_raises(self):
        with self.assertRaises(UserError):
            self.env['ke.p10.wizard'].create(
                {'month': '2', 'year': 1999}).action_export_csv()


class TestKeAhl(TransactionCase):
    def _company(self):
        return self.env.ref('base.main_company')

    def test_ahl_export_runs_on_paid_period(self):
        company = self._company()
        employee = self.env['hr.employee'].create({
            'name': 'KE AHL Emp',
            'identification_id': '30000003',
            'company_id': company.id,
        })
        contract = self.env['hr.version'].search(
            [('employee_id', '=', employee.id)], limit=1)
        contract.write({
            'wage': 100000.0,
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
            'date_from': '2026-11-01',
            'date_to': '2026-11-30',
            'company_id': company.id,
        })
        slip.action_payslip_done()
        slip.action_mark_as_paid()
        result = self.env['ke.ahl.wizard'].create(
            {'month': '11', 'year': 2026}).action_export()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')
        self.assertIn('/web/content/ir.attachment/', result.get('url'))
