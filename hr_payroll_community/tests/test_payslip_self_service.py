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
#############################################################################
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestPayslipSelfService(TransactionCase):
    """Employee sees only own validated payslips. No cross-talk."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = cls.env['res.users'].with_context(no_reset_password=True)
        Employee = cls.env['hr.employee']
        Payslip = cls.env['hr.payslip']

        cls.user_a = User.create({
            'name': 'Payslip Employee A',
            'login': 'payslip_employee_a',
            'email': 'payslip_a@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.user_b = User.create({
            'name': 'Payslip Employee B',
            'login': 'payslip_employee_b',
            'email': 'payslip_b@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        # oh_employee_creation_from_user auto-creates one employee per user.
        cls.emp_a = cls.user_a.employee_id
        cls.emp_b = cls.user_b.employee_id
        assert cls.emp_a and cls.emp_b, "auto employee creation expected"
        cls.slip_a = Payslip.create({
            'name': 'Payslip A 2026-01',
            'employee_id': cls.emp_a.id,
            'date_from': '2026-01-01',
            'date_to': '2026-01-31',
            'state': 'done',
        })
        cls.slip_b = Payslip.create({
            'name': 'Payslip B 2026-01',
            'employee_id': cls.emp_b.id,
            'date_from': '2026-01-01',
            'date_to': '2026-01-31',
            'state': 'done',
        })
        cls.slip_a_draft = Payslip.create({
            'name': 'Payslip A draft',
            'employee_id': cls.emp_a.id,
            'date_from': '2026-02-01',
            'date_to': '2026-02-28',
            'state': 'draft',
        })
        Version = cls.env['hr.version']
        calendar = cls.env.ref('resource.resource_calendar_std')
        cls.contract_a = Version.create({
            'name': 'Contract A',
            'employee_id': cls.emp_a.id,
            'date_version': '2026-01-01',
            'resource_calendar_id': calendar.id,
            'hr_responsible_id': cls.env.ref('base.user_admin').id,
            'wage': 100000.0,
        })
        cls.slip_a.write({'contract_id': cls.contract_a.id})

    def _payslip_as(self, user):
        return self.env['hr.payslip'].with_user(user)

    def test_search_returns_only_own(self):
        found = self._payslip_as(self.user_a).search([])
        self.assertIn(self.slip_a, found)
        self.assertNotIn(self.slip_b, found)
        self.assertNotIn(self.slip_a_draft, found)

    def test_read_other_raises(self):
        with self.assertRaises(AccessError):
            self.slip_b.with_user(self.user_a).read(['name'])

    def test_draft_own_hidden(self):
        with self.assertRaises(AccessError):
            self.slip_a_draft.with_user(self.user_a).read(['name'])

    def test_lines_follow_payslip(self):
        line_model = self.env['hr.payslip.line'].with_user(self.user_a)
        own_lines = line_model.search([('slip_id', '=', self.slip_a.id)])
        for line in own_lines:
            self.assertEqual(line.slip_id.employee_id.user_id, self.user_a)
        other_lines = self.env['hr.payslip.line'].search(
            [('slip_id', '=', self.slip_b.id)])
        for line in other_lines:
            with self.assertRaises(AccessError):
                line.with_user(self.user_a).read(['name'])

    def test_own_contract_readable(self):
        """Form shows own contract link. Others stay hidden."""
        contract = self.env['hr.version'].with_user(self.user_a).search(
            [('employee_id', '=', self.emp_a.id)], limit=1)
        self.assertTrue(contract)
        contract.read(['name'])
        other = self.env['hr.version'].search(
            [('employee_id', '=', self.emp_b.id)], limit=1)
        if other:
            with self.assertRaises(AccessError):
                other.with_user(self.user_a).read(['name'])

    def test_print_own_payslip_url(self):
        action = self.slip_a.with_user(self.user_a).action_print_own_payslip()
        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertIn('/my/payslip/%s/pdf' % self.slip_a.id, action['url'])
        with self.assertRaises(AccessError):
            self.slip_b.with_user(self.user_a).action_print_own_payslip()

    def test_reference_data_readable(self):
        """Form render needs rule/category/structure names. No manual grants."""
        self.env['hr.salary.rule.category'].with_user(self.user_a).search(
            [], limit=1).read(['name'])
        self.env['hr.salary.rule'].with_user(self.user_a).search(
            [], limit=1).read(['name'])
        self.env['hr.payroll.structure'].with_user(self.user_a).search(
            [], limit=1).read(['name'])

    def test_officer_still_sees_all(self):
        officer_group = self.env.ref(
            'hr_payroll_community.group_hr_payroll_community_user')
        officer = self.env['res.users'].with_context(
            no_reset_password=True).create({
                'name': 'Payroll Officer',
                'login': 'payroll_officer_selftest',
                'email': 'officer_selftest@example.com',
                'group_ids': [(6, 0, [
                    self.env.ref('base.group_user').id,
                    officer_group.id,
                ])],
            })
        found = self.env['hr.payslip'].with_user(officer).search([])
        self.assertIn(self.slip_a, found)
        self.assertIn(self.slip_b, found)
