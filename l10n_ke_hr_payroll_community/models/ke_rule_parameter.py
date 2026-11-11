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
import ast

from odoo import api, fields, models


class KeHrRuleParameter(models.Model):
    _name = 'ke.hr.rule.parameter'
    _description = 'Kenya payroll parameter with dated values'
    _order = 'code, date_from'

    name = fields.Char(required=True)
    code = fields.Char(required=True, index=True)
    date_from = fields.Date(required=True, default=fields.Date.today)
    value = fields.Text(required=True, help="Python literal: number, list of bands, or dict")
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company.id,
        index=True,
        check_company=True,
    )

    _sql_constraints = [('code_date_company_uniq', 'unique(code, date_from, company_id)', 'Duplicate parameter value')]

    @api.model
    def get_value(self, code, date=None):
        date = date or fields.Date.today()
        rec = self.search([('code', '=', code), ('date_from', '<=', date)], order='date_from desc', limit=1)
        if not rec:
            return None
        return ast.literal_eval(rec.value)
