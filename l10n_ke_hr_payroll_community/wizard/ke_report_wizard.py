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
import io

from odoo import fields, models
from odoo.exceptions import UserError


def _period_slips(wizard):
    """Done or paid, primary-contract payslips for the wizard's month/year.

    Paid slips are final payroll records and must appear in statutory
    statements; filtering on done-only hid every paid month.
    """
    slips = wizard.env['hr.payslip'].search(
        [('state', 'in', ('done', 'paid'))])
    month = int(wizard.month)
    return slips.filtered(
        lambda s: s.date_from
        and s.date_from.month == month
        and s.date_from.year == wizard.year
        and not s.contract_id.ke_secondary
    )


def _nssf_total(slip):
    """Employee NSSF on a slip: Tier I + Tier II, plus the pre-split
    KE_NSSF line so statements stay correct for slips computed before
    the 20.0.1.0.2 tier split (a slip never carries both)."""
    return abs(sum(slip.line_ids.filtered(
        lambda l: l.code in ('KE_NSSF_T1', 'KE_NSSF_T2', 'KE_NSSF')
    ).mapped('total')))


def _line_total(slip, code):
    return abs(sum(slip.line_ids.filtered(lambda l: l.code == code).mapped('total')))


def _xlsx_download(wizard, rows, header, filename):
    """XLSX download via a stored attachment.

    A ``data:`` URL previously carried the whole workbook in the action
    URL, which browsers block (CSP/popup/size limits) so the Export
    button appeared to do nothing. Store the file and return a real
    ``/web/content`` download URL instead.
    """
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = filename
    ws.append(header)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    attachment = wizard.env['ir.attachment'].create({
        'name': '%s.xlsx' % filename,
        'type': 'binary',
        'raw': buf.getvalue(),
        'mimetype': 'application/vnd.openxmlformats-officedocument.'
                    'spreadsheetml.sheet',
    })
    return {
        'type': 'ir.actions.act_url',
        'url': '/web/content/ir.attachment/%s/raw/%s?download=true'
               % (attachment.id, attachment.name),
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
            total = _nssf_total(slip)
            rows.append([
                slip.employee_id.name,
                slip.employee_id.identification_id,
                slip.contract_id.ke_nssf_no,
                _line_total(slip, 'KE_NSSF_T1'),
                _line_total(slip, 'KE_NSSF_T2'),
                total,
            ])
        if not rows:
            raise UserError('No Done payslips for period')
        return _xlsx_download(
            self,
            rows,
            ['Name', 'ID No', 'NSSF No', 'Tier I', 'Tier II', 'Total'],
            'NSSF')


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
        return _xlsx_download(
            self, rows, ['Name', 'ID No', 'SHIF No', 'Amount'], 'SHIF')


class KeP9Wizard(models.TransientModel):
    _name = 'ke.p9.wizard'
    _description = 'P9 tax deduction card'

    year = fields.Integer(
        required=True,
        default=lambda self: fields.Date.today().year,
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee',
        help='Leave empty for the all-employees summary. '
             'Set for the detailed individual P9 card.') 

    def _get_p9_data(self):
        """Per-employee yearly totals from done/paid slips: gross/nssf/shif/ahl/paye."""
        slips = self.env['hr.payslip'].sudo().search(
            [('state', 'in', ('done', 'paid'))])
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
            agg['nssf'] += _nssf_total(slip)
            agg['shif'] += _line_total(slip, 'KE_SHIF')
            agg['ahl'] += _line_total(slip, 'KE_AHL')
            # Net PAYE = KE_PAYE category total (parent line is the gross
            # band tax since the relief split; old slips carry net only).
            agg['paye'] += abs(sum(
                slip.line_ids.filtered(
                    lambda l: l.category_id.code == 'KE_PAYE').mapped('total')))
        return sorted(by_employee.values(), key=lambda r: r['employee'] or '')

    def action_print(self):
        self.ensure_one()
        if self.employee_id:
            return self.env.ref(
                'l10n_ke_hr_payroll_community.action_ke_p9_individual_report'
            ).report_action(self)
        return self.env.ref(
            'l10n_ke_hr_payroll_community.action_ke_p9_report').report_action(self)

    def _p9_param(self, code, date):
        # Dated statutory rates are public data; sudo so the individual
        # card also renders for non-payroll users on /report/download,
        # where the builder runs in the clicking user's env.
        return self.env['ke.hr.rule.parameter'].sudo().get_value(code, date)

    def _p9_recompute_lmno(self, chargeable, contract, date, pension_ded,
                           mortgage, post_med):
        """L/M/N/O fallback for slips computed before the relief split.

        Old slips store only the net KE_PAYE line, so gross tax and the two
        reliefs are re-derived from the stored chargeable pay with the same
        dated parameters and contract flags the rules use.
        """
        bands = self._p9_param('ke_paye_bands', date)
        disability = self._p9_param('ke_disability', date)
        pay_taxable = chargeable
        if contract.ke_disabled and contract.ke_disability_cert:
            pay_taxable = max(chargeable - disability, 0.0)
        if bool(contract.ke_nonresident):
            pay_taxable = (pay_taxable + pension_ded + mortgage + post_med)
        tax = 0.0
        base = 0.0
        for width, rate in bands:
            w = width if width > 0 else float('inf')
            chunk = min(max(pay_taxable - base, 0.0), w)
            tax += chunk * rate
            base += w
            if pay_taxable <= base:
                break
        pers = ins = 0.0
        if not contract.ke_secondary and not bool(contract.ke_nonresident):
            pers = self._p9_param('ke_personal_relief', date)
            ins_param = self._p9_param('ke_insurance', date)
            ins = min(ins_param['rate'] * (
                contract.ke_insurance_life + contract.ke_insurance_health
                + contract.ke_insurance_edu), ins_param['monthly_max'])
        pers_applied = min(pers, max(tax, 0.0))
        ins_applied = min(ins, max(tax - pers_applied, 0.0))
        return tax, pers_applied, ins_applied, tax - pers_applied - ins_applied

    def _get_p9_monthly(self, employee, year):
        """Per-month KRA P9 rows for one employee (Jan..Dec + TOTAL).

        Column letters follow the KRA Appendix 2A card: A basic, B
        non-cash benefits (engine has none), C quarters (none), D gross,
        E pension deducted, F SHIF, G AHL, H post-retirement medical,
        I owner-occupied interest, J total deductions, K chargeable pay,
        L tax charged, M personal relief, N insurance relief, O PAYE.
        New slips read L/M/N from their lines; older net-only slips
        re-derive them (same math, documented in each TOTAL row note).
        """
        slips = self.env['hr.payslip'].sudo().search([
            ('employee_id', '=', employee.id),
            ('state', 'in', ('done', 'paid')),
        ]).filtered(
            lambda s: s.date_from
            and s.date_from.year == year
            and not s.contract_id.ke_secondary
        )
        if not slips:
            raise UserError('No Done payslips for employee and year')
        # Report-internal reads (ID number, contracts) run as sudo: the
        # wizard already pins the employee, and the caller established
        # authorization (slip visibility / portal ownership).
        employee = employee.sudo()
        months = []
        latest_contract = slips.sorted('date_from')[-1].contract_id
        for m in range(1, 13):
            mslips = slips.filtered(lambda s: s.date_from.month == m)
            row = {'month': m, 'recomputed': False}
            if not mslips:
                row.update({k: 0.0 for k in (
                    'basic', 'benefits', 'quarters', 'gross', 'pension',
                    'shif', 'ahl', 'prmf', 'mortgage', 'deduct', 'charge',
                    'tax', 'pers', 'ins', 'paye')})
                months.append(row)
                continue
            contract = mslips[0].contract_id
            date = mslips[0].date_from
            mortgage = min(contract.ke_mortgage or 0.0,
                           self._p9_param('ke_mortgage_cap', date))
            post_med = min(contract.ke_post_med or 0.0,
                           self._p9_param('ke_post_med_cap', date))
            basic = sum(mslips.mapped('line_ids').filtered(
                lambda l: l.code == 'KE_BASIC').mapped('total'))
            gross = sum(mslips.mapped('line_ids').filtered(
                lambda l: l.code == 'KE_GROSS').mapped('total'))
            shif = _line_total(mslips, 'KE_SHIF')
            ahl = _line_total(mslips, 'KE_AHL')
            charge = sum(mslips.mapped('line_ids').filtered(
                lambda l: l.code == 'KE_TAXABLE').mapped('total'))
            pension = (gross - shif - ahl - mortgage - post_med - charge)
            relief_pers = sum(mslips.mapped('line_ids').filtered(
                lambda l: l.code == 'KE_RELIEF_PERS').mapped('total'))
            relief_ins = sum(mslips.mapped('line_ids').filtered(
                lambda l: l.code == 'KE_RELIEF_INS').mapped('total'))
            paye_lines = sum(mslips.mapped('line_ids').filtered(
                lambda l: l.code == 'KE_PAYE').mapped('total'))
            if 'KE_RELIEF_PERS' in mslips.mapped('line_ids.code'):
                tax, pers, ins = abs(paye_lines), relief_pers, relief_ins
                paye = tax - pers - ins
            else:
                row['recomputed'] = True
                tax, pers, ins, paye = self._p9_recompute_lmno(
                    charge, contract, mslips[0].date_from, pension,
                    mortgage, post_med)
            row.update({
                'basic': basic, 'benefits': 0.0, 'quarters': 0.0,
                'gross': gross, 'pension': pension, 'shif': shif,
                'ahl': ahl, 'prmf': post_med, 'mortgage': mortgage,
                'deduct': pension + shif + ahl + post_med + mortgage,
                'charge': charge, 'tax': tax, 'pers': pers, 'ins': ins,
                'paye': paye,
            })
            months.append(row)
        total = {'month': 'TOTAL', 'recomputed': any(
            r['recomputed'] for r in months)}
        for key in ('basic', 'benefits', 'quarters', 'gross', 'pension',
                    'shif', 'ahl', 'prmf', 'mortgage', 'deduct', 'charge',
                    'tax', 'pers', 'ins', 'paye'):
            total[key] = sum(r[key] for r in months)
        return {
            'employee': employee.name,
            'kra_pin': latest_contract.ke_kra_pin,
            'id_no': employee.identification_id,
            'employer': self.env.company.name,
            'employer_pin': self.env.company.vat,
            'year': year,
            'months': months,
            'total': total,
        }
