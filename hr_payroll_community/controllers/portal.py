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
#############################################################################
from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PayslipPortal(CustomerPortal):
    """Employee portal: list own payslips, view detail, download PDF."""

    def _get_employee(self):
        return request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.user.id)], limit=1)

    def _get_own_payslip(self, payslip_id):
        payslip = request.env['hr.payslip'].browse(int(payslip_id))
        if not payslip.exists():
            return request.not_found()
        employee = self._get_employee()
        if not employee or payslip.employee_id.id != employee.id:
            return request.not_found()
        try:
            payslip.check_access('read')
        except AccessError:
            return request.not_found()
        return payslip

    @http.route(['/my/payslips'], type='http', auth='user', website=True)
    def portal_my_payslips(self, **kw):
        employee = self._get_employee()
        payslips = request.env['hr.payslip'].search(
            [('employee_id', '=', employee.id)] if employee else [('id', '=', 0)],
            order='date_to desc, id desc',
        )
        return request.render(
            'hr_payroll_community.portal_my_payslips', {
                'payslips': payslips,
                'page_name': 'payslips',
            })

    @http.route(['/my/payslip/<int:payslip_id>'],
                type='http', auth='user', website=True)
    def portal_my_payslip(self, payslip_id, **kw):
        payslip = self._get_own_payslip(payslip_id)
        if hasattr(payslip, 'status_code'):
            return payslip
        return request.render(
            'hr_payroll_community.portal_my_payslip_detail', {
                'payslip': payslip,
                'page_name': 'payslips',
            })

    @http.route(['/my/payslip/<int:payslip_id>/pdf'],
                type='http', auth='user', website=True)
    def portal_my_payslip_pdf(self, payslip_id, **kw):
        payslip = self._get_own_payslip(payslip_id)
        if hasattr(payslip, 'status_code'):
            return payslip
        pdf, _ = request.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'hr_payroll_community.hr_payslip_report_action',
            res_ids=[payslip.id])
        return request.make_response(
            pdf,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition',
                 'attachment; filename=%s' % payslip.sudo()._get_payslip_pdf_filename()),
            ])
