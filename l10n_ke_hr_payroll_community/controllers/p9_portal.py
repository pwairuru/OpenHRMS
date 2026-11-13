# -*- coding: utf-8 -*-
"""Employee self-service: download own detailed P9 card (landscape PDF)."""
import re

from odoo import http
from odoo.exceptions import UserError
from odoo.http import request


def _safe_filename(name):
    """Strip anything outside word chars, space, dash, dot: quotes,
    semicolons and newlines must never reach Content-Disposition."""
    return re.sub(r'[^\w\-. ]', '_', name or 'employee').strip() or 'employee'


class KeP9Portal(http.Controller):
    def _get_employee(self):
        return request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.user.id)], limit=1)

    @http.route(['/my/p9'], type='http', auth='user', website=True)
    def portal_my_p9_list(self, **kw):
        employee = self._get_employee()
        if not employee:
            return request.not_found()
        slips = request.env['hr.payslip'].sudo().search(
            [('employee_id', '=', employee.id),
             ('state', 'in', ('done', 'paid')),
             ('company_id', 'in', request.env.user.company_ids.ids)])
        years = sorted(
            {s.date_from.year for s in slips if s.date_from}, reverse=True)
        return request.render(
            'l10n_ke_hr_payroll_community.portal_my_p9_list', {
                'years': years,
                'page_name': 'payslips',
            })

    @http.route(['/my/p9/<int:year>/pdf'], type='http', auth='user',
                website=True)
    def portal_my_p9_pdf(self, year, **kw):
        employee = self._get_employee()
        if not employee:
            return request.not_found()
        if not request.env['hr.payslip'].sudo().search_count(
                [('employee_id', '=', employee.id),
                 ('state', 'in', ('done', 'paid')),
                 ('company_id', 'in', request.env.user.company_ids.ids),
                 ('date_from', '>=', '%d-01-01' % year),
                 ('date_from', '<', '%d-01-01' % (year + 1))]):
            return request.not_found()
        wizard = request.env['ke.p9.wizard'].sudo().create({
            'year': year,
            'employee_id': employee.id,
        })
        try:
            wizard._get_p9_monthly(employee, year)
        except UserError:
            return request.not_found()
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'l10n_ke_hr_payroll_community.action_ke_p9_individual_report',
            res_ids=[wizard.id])
        filename = 'P9_%s_%s.pdf' % (year, _safe_filename(employee.name))
        return request.make_response(
            pdf,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ])
