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
"""Kenya measures for the payslip analysis report.

The base ``hr.payslip.report`` SQL view only maps rule codes
``BASIC``/``GROSS``/``NET`` into the ``basic_wage``/``gross_wage``/
``net_wage`` pivot measures. Kenya rules use ``KE_BASIC``/``KE_GROSS``/
``KE_NET``, so every KE slip contributed 0.0 and the pivot showed all
zeros. Map both code families.
"""
from odoo import models


class HrPayslipReport(models.Model):
    _inherit = 'hr.payslip.report'

    def _select(self):
        select_str = super()._select()
        select_str = select_str.replace(
            "rlu.code = 'BASIC'", "rlu.code IN ('BASIC', 'KE_BASIC')")
        select_str = select_str.replace(
            "rlu.code = 'GROSS'", "rlu.code IN ('GROSS', 'KE_GROSS')")
        select_str = select_str.replace(
            "rlu.code = 'NET'", "rlu.code IN ('NET', 'KE_NET')")
        return select_str
