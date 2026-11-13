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
        """Single-sided move lines for KE rules.

        The inherited helper posts *both* legs of every rule that carries
        debit and credit accounts, so each employee deduction books twice
        (Dr 630000 expense + Cr authority payable) and the leftover
        debit is balanced with a partner-less credit to the journal
        default account: expense and         liabilities both overstated by
        total deductions. KE deductions are pure employee withholdings,
        so each KE rule posts exactly one line: earnings debit the
        debit leg, withholdings and net pay credit the credit leg. Scoped to ``KE_`` codes; other structures keep
        the inherited behaviour.
        """
        if not (line.code or '').startswith('KE_'):
            return super()._get_salary_rule_move_lines(line, amount)
        if line.code == 'KE_PAYE':
            # Parent holds the gross band tax; KE_RELIEF_PERS / KE_RELIEF_INS
            # are account-less display lines in the same category. Post the
            # category total (net tax payable) so the KRA liability is right.
            amount = sum(
                payslip_line.total
                for payslip_line in line.slip_id.line_ids
                if payslip_line.category_id.code == 'KE_PAYE'
            )
        debit_id = line.salary_rule_id.account_debit_id.id
        credit_id = line.salary_rule_id.account_credit_id.id
        if amount > 0.0 and debit_id:
            # Earnings (KE_BASIC): Dr expense.
            account_id, debit, credit = debit_id, amount, 0.0
            partner_id = line._get_partner_id(credit_account=False)
        elif credit_id:
            # Withholdings (negative: Cr authority payable) and net pay
            # (positive KE_NET: Cr 230000) both credit the credit leg.
            account_id, debit, credit = credit_id, 0.0, abs(amount)
            partner_id = line._get_partner_id(credit_account=True)
        elif debit_id:
            # Negative amount, debit leg only: Cr the debit leg.
            account_id, debit, credit = debit_id, 0.0, abs(amount)
            partner_id = line._get_partner_id(credit_account=False)
        else:
            return []
        return [(0, 0, {
            'name': line.name,
            'partner_id': partner_id,
            'account_id': account_id,
            'journal_id': self.journal_id.id,
            'date': self.date or self.date_to,
            'debit': debit,
            'credit': credit,
            'tax_line_id': line.salary_rule_id.account_tax_id.id,
        })]
