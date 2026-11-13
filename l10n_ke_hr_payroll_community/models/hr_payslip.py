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
from odoo.exceptions import UserError
import ast


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def ke_get_param(self, code):
        self.ensure_one()
        rec = self.env['ke.hr.rule.parameter'].search([('code', '=', code), ('date_from', '<=', self.date_from)], order='date_from desc', limit=1)
        if not rec:
            raise UserError('Missing KE payroll parameter: %s' % code)
        return ast.literal_eval(rec.value)

    def action_print_p9(self):
        """Print this slip's employee P9 card for the slip's year."""
        self.ensure_one()
        if not self.date_from:
            raise UserError('Set the payslip dates first.')
        wizard = self.env['ke.p9.wizard'].create({
            'year': self.date_from.year,
            'employee_id': self.employee_id.id,
        })
        return self.env.ref(
            'l10n_ke_hr_payroll_community.action_ke_p9_individual_report'
        ).report_action(wizard)
