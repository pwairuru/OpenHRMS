# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#############################################################################
from odoo.tests.common import TransactionCase


class TestPayslipAccountSelfService(TransactionCase):
    """Plain employee opens own slip form: accounting badges must not block."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = cls.env['res.users'].with_context(no_reset_password=True)
        cls.user = User.create({
            'name': 'Payslip Acct Employee',
            'login': 'payslip_acct_employee',
            'email': 'payslip_acct@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })
        cls.employee = cls.user.employee_id
        assert cls.employee, "auto employee creation expected"
        cls.slip = cls.env['hr.payslip'].create({
            'name': 'Payslip Acct 2026-01',
            'number': 'SLIP/ACCTEST',
            'employee_id': cls.employee.id,
            'date_from': '2026-01-01',
            'date_to': '2026-01-31',
            'state': 'done',
        })

    def test_accounting_badges_readable(self):
        slip = self.slip.with_user(self.user)
        slip.read(['payment_count', 'paid', 'journal_id', 'move_id'])
