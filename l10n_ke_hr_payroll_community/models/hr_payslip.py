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
from odoo import fields, models
import ast


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def ke_get_param(self, code):
        self.ensure_one()
        rec = self.env['ke.hr.rule.parameter'].search([('code', '=', code), ('date_from', '<=', self.date_from)], order='date_from desc', limit=1)
        return ast.literal_eval(rec.value) if rec else None
