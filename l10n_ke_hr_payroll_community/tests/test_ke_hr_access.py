# -*- coding: utf-8 -*-
"""HR-role access: a system user with HR access (hr.group_hr_user, no
payroll groups, no linked employee) must be able to print payslips and
P9 cards and export statutory extracts. RED: currently fails -- the HR
user has no hr.payslip(-line) read and no KE wizard access.
"""
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestKeHrAccess(TransactionCase):
    def _company(self):
        return self.env.ref('base.main_company')

    def _hr_user(self):
        return self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'KE HR Officer',
                'login': 'ke_hr_officer',
                'email': 'ke_hr_officer@example.com',
                'group_ids': [(6, 0, [
                    self.env.ref('base.group_user').id,
                    self.env.ref('hr.group_hr_user').id,
                ])],
            })

    def _slip(self, state='done'):
        company = self._company()
        employee = self.env['hr.employee'].create({
            'name': 'KE HR Slip Emp',
            'identification_id': '30000002',
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
            'ke_kra_pin': 'A123456789Z',
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
        if state in ('done', 'paid'):
            slip.action_payslip_done()
        return slip

    def test_hr_user_reads_done_slip_and_lines(self):
        user, slip = self._hr_user(), self._slip('done')
        got = self.env['hr.payslip'].with_user(user).browse(slip.id)
        self.assertEqual(got.employee_id.name, 'KE HR Slip Emp')
        self.assertTrue(got.line_ids, 'HR must see slip lines to print')

    def test_hr_user_draft_p9_refused(self):
        user, slip = self._hr_user(), self._slip('draft')
        with self.assertRaises(UserError):
            slip.with_user(user).action_print_p9()

    def test_hr_user_prints_p9(self):
        user, slip = self._hr_user(), self._slip('done')
        action = slip.with_user(user).action_print_p9()
        self.assertEqual(action['type'], 'ir.actions.report')
        wiz = self.env['ke.p9.wizard'].browse(action['context']['active_ids'])
        pdf, _ = self.env['ir.actions.report'].with_user(user)._render_qweb_pdf(
            action['report_name'], res_ids=wiz.ids)
        self.assertTrue(pdf)

    def test_hr_user_exports_p10(self):
        user = self._hr_user()
        self._slip('paid')
        result = self.env['ke.p10.wizard'].with_user(user).create(
            {'month': '11', 'year': 2026}).action_export_csv()
        self.assertEqual(result.get('type'), 'ir.actions.act_url')

    def test_hr_user_runs_nssf_shif(self):
        user = self._hr_user()
        self._slip('paid')
        for model in ('ke.nssf.wizard', 'ke.shif.wizard'):
            wiz = self.env[model].with_user(user).create(
                {'month': '11', 'year': 2026})
            result = wiz.action_export()
            self.assertEqual(result.get('type'), 'ir.actions.act_url')

    def test_employee_form_exposes_ke_identifiers(self):
        """KRA PIN / NSSF / SHIF must sit on the employee form itself:
        related (writable) to the current contract, where payroll reads
        them. HR enters them on the employee; reports read the contract.
        """
        employee = self.env['hr.employee'].create({
            'name': 'KE IDs Emp',
            'company_id': self._company().id,
        })
        employee.write({
            'ke_kra_pin': 'A111111111Z',
            'ke_nssf_no': 'NSSF-1',
            'ke_shif_no': 'SHIF-1',
        })
        contract = self.env['hr.version'].search(
            [('employee_id', '=', employee.id)], limit=1)
        self.assertEqual(contract.ke_kra_pin, 'A111111111Z')
        self.assertEqual(contract.ke_nssf_no, 'NSSF-1')
        self.assertEqual(contract.ke_shif_no, 'SHIF-1')
        view = self.env.ref(
            'l10n_ke_hr_payroll_community.view_employee_form_ke')
        for fname in ('ke_kra_pin', 'ke_nssf_no', 'ke_shif_no'):
            self.assertIn(fname, view.arch_db)

    def test_lay_user_wizard_isolation(self):
        """No cross-employee P9 disclosure via wizard enumeration: a
        non-payroll user can read only wizards pinned to their own
        employee; payroll-created wizards for others are invisible."""
        lay = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'KE Lay Iso',
                'login': 'ke_lay_iso',
                'email': 'ke_lay_iso@example.com',
                'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
            })
        other = self.env['hr.employee'].create({
            'name': 'KE Other Emp',
            'company_id': self._company().id,
        })
        foreign = self.env['ke.p9.wizard'].create({
            'year': 2026, 'employee_id': other.id})
        with self.assertRaises(AccessError):
            self.env['ke.p9.wizard'].with_user(lay).browse(
                foreign.id).employee_id.name
