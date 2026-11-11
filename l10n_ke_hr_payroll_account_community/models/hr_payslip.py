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


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_salary_rule_move_lines(self, line, amount):
        """Fixed-side move lines for KE rules.

        The inherited helper assigns debit/credit by amount sign, which
        inverts both legs of negative-amount rules (deductions post their
        credit leg as a debit and vice versa). KE deduction amounts are
        negative by design, so post ``abs(amount)`` on the leg's natural
        side instead. Scoped to ``KE_`` codes; other structures keep the
        inherited behaviour.
        """
        if not (line.code or '').startswith('KE_'):
            return super()._get_salary_rule_move_lines(line, amount)
        res = []
        debit_account_id = line.salary_rule_id.account_debit_id.id
        credit_account_id = line.salary_rule_id.account_credit_id.id
        if debit_account_id:
            res.append((0, 0, {
                'name': line.name,
                'partner_id': line._get_partner_id(credit_account=False),
                'account_id': debit_account_id,
                'journal_id': self.journal_id.id,
                'date': self.date or self.date_to,
                'debit': abs(amount),
                'credit': 0.0,
                'tax_line_id': line.salary_rule_id.account_tax_id.id,
            }))
        if credit_account_id:
            res.append((0, 0, {
                'name': line.name,
                'partner_id': line._get_partner_id(credit_account=True),
                'account_id': credit_account_id,
                'journal_id': self.journal_id.id,
                'date': self.date or self.date_to,
                'debit': 0.0,
                'credit': abs(amount),
                'tax_line_id': line.salary_rule_id.account_tax_id.id,
            }))
        return res
