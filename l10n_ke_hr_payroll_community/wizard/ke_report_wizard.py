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
"""Kenya statutory report wizards: NSSF/SHIF monthly XLSX, P9 yearly PDF."""
import base64
import io

from odoo import fields, models
from odoo.exceptions import UserError


def _period_slips(wizard):
    """Done, primary-contract payslips for the wizard's month/year."""
    slips = wizard.env['hr.payslip'].search([('state', '=', 'done')])
    month = int(wizard.month)
    return slips.filtered(
        lambda s: s.date_from
        and s.date_from.month == month
        and s.date_from.year == wizard.year
        and not s.contract_id.ke_secondary
    )


def _line_total(slip, code):
    return abs(sum(slip.line_ids.filtered(lambda l: l.code == code).mapped('total')))


def _xlsx_download(rows, header, filename):
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = filename
    ws.append(header)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return {
        'type': 'ir.actions.act_url',
        'url': 'data:application/vnd.openxmlformats-officedocument.'
               'spreadsheetml.sheet;base64,' + data,
        'target': 'self',
    }


class KeNssfWizard(models.TransientModel):
    _name = 'ke.nssf.wizard'
    _description = 'NSSF report'

    month = fields.Selection(
        [(str(m), str(m)) for m in range(1, 13)],
        required=True,
        default=lambda self: str(fields.Date.today().month),
    )
    year = fields.Integer(
        required=True,
        default=lambda self: fields.Date.today().year,
    )

    def action_export(self):
        slips = _period_slips(self)
        rows = []
        for slip in slips:
            rows.append([
                slip.employee_id.name,
                slip.employee_id.identification_id,
                slip.contract_id.ke_nssf_no,
                _line_total(slip, 'KE_NSSF'),
            ])
        if not rows:
            raise UserError('No Done payslips for period')
        return _xlsx_download(rows, ['Name', 'ID No', 'NSSF No', 'Amount'], 'NSSF')


class KeShifWizard(models.TransientModel):
    _name = 'ke.shif.wizard'
    _description = 'SHIF report'

    month = fields.Selection(
        [(str(m), str(m)) for m in range(1, 13)],
        required=True,
        default=lambda self: str(fields.Date.today().month),
    )
    year = fields.Integer(
        required=True,
        default=lambda self: fields.Date.today().year,
    )

    def action_export(self):
        slips = _period_slips(self)
        rows = []
        for slip in slips:
            rows.append([
                slip.employee_id.name,
                slip.employee_id.identification_id,
                slip.contract_id.ke_shif_no,
                _line_total(slip, 'KE_SHIF'),
            ])
        if not rows:
            raise UserError('No Done payslips for period')
        return _xlsx_download(rows, ['Name', 'ID No', 'SHIF No', 'Amount'], 'SHIF')


class KeP9Wizard(models.TransientModel):
    _name = 'ke.p9.wizard'
    _description = 'P9 tax deduction card'

    year = fields.Integer(
        required=True,
        default=lambda self: fields.Date.today().year,
    )

    def _get_p9_data(self):
        """Per-employee yearly totals from Done slips: gross/nssf/shif/ahl/paye."""
        slips = self.env['hr.payslip'].search([('state', '=', 'done')])
        slips = slips.filtered(
            lambda s: s.date_from
            and s.date_from.year == self.year
            and not s.contract_id.ke_secondary
        )
        if not slips:
            raise UserError('No Done payslips for year')
        by_employee = {}
        for slip in slips:
            emp = slip.employee_id
            agg = by_employee.setdefault(emp.id, {
                'employee': emp.name,
                'kra_pin': slip.contract_id.ke_kra_pin,
                'gross': 0.0,
                'nssf': 0.0,
                'shif': 0.0,
                'ahl': 0.0,
                'paye': 0.0,
            })
            agg['gross'] += sum(
                slip.line_ids.filtered(lambda l: l.code == 'KE_GROSS').mapped('total'))
            agg['nssf'] += _line_total(slip, 'KE_NSSF')
            agg['shif'] += _line_total(slip, 'KE_SHIF')
            agg['ahl'] += _line_total(slip, 'KE_AHL')
            agg['paye'] += _line_total(slip, 'KE_PAYE')
        return sorted(by_employee.values(), key=lambda r: r['employee'] or '')

    def action_print(self):
        self.ensure_one()
        return self.env.ref(
            'l10n_ke_hr_payroll_community.action_ke_p9_report').report_action(self)
