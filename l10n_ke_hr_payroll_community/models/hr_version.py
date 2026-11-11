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


class HrVersion(models.Model):
    _inherit = 'hr.version'

    ke_pension = fields.Monetary(string='Pension / month')
    ke_mortgage = fields.Monetary(string='Mortgage interest / month')
    ke_post_med = fields.Monetary(string='Post-retirement medical / month')
    ke_insurance_life = fields.Monetary(string='Life premium / month')
    ke_insurance_health = fields.Monetary(string='Health premium / month')
    ke_insurance_edu = fields.Monetary(string='Education premium / month')
    ke_disabled = fields.Boolean(string='Disabled (certified)')
    ke_disability_cert = fields.Char(string='Disability cert no')
    ke_secondary = fields.Boolean(string='Secondary employer contract')
    ke_nonresident = fields.Boolean(string='Non-resident (no reliefs)')
    ke_kra_pin = fields.Char(string='KRA PIN')
    ke_nssf_no = fields.Char(string='NSSF number')
    ke_shif_no = fields.Char(string='SHIF number')
    ke_pension_remit = fields.Selection([('nssf', 'NSSF'), ('insurance', 'Insurance')], default='nssf', string='Pension remit to')
    ke_helb = fields.Monetary(string='HELB / month')
    ke_loan_rate = fields.Float(string='Staff loan rate')
    ke_loan_balance = fields.Monetary(string='Staff loan balance')
