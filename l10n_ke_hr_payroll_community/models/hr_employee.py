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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Statutory identifiers live on the contract (hr.version), where the
    # payroll engine and every extract (P9/P10/NSSF/SHIF) read them -- but
    # HR looks for them on the employee. Related (writable) so both stay
    # one value: entered on the employee, stored on the current contract.
    ke_kra_pin = fields.Char(
        string='KRA PIN', related='current_version_id.ke_kra_pin',
        readonly=False)
    ke_nssf_no = fields.Char(
        string='NSSF number', related='current_version_id.ke_nssf_no',
        readonly=False)
    ke_shif_no = fields.Char(
        string='SHIF number', related='current_version_id.ke_shif_no',
        readonly=False)
