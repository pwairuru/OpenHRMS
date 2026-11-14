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
from odoo import api, fields, models


class HrPayrollStructureTracking(models.Model):
    """Add chatter + field tracking to salary structures.

    Lives in l10n_ke so hr_payroll_community core stays untouched.
    Pattern mirrors om_hr_payroll (mail.thread + tracking=True).
    """
    _name = 'hr.payroll.structure'
    _inherit = ['hr.payroll.structure', 'mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_parent(self):
        return self.env.ref('hr_payroll_community.structure_base', False)

    name = fields.Char(
        required=True, string="Name", tracking=True,
        help="Name for Payroll Structure")
    code = fields.Char(
        string='Reference', required=True, tracking=True,
        help="Code for Payroll Structure")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, tracking=True,
        default=lambda self: self.env.company.id)
    note = fields.Text(
        string='Description', tracking=True,
        help="Description for Payroll Structure")
    parent_id = fields.Many2one(
        'hr.payroll.structure', string='Parent', tracking=True,
        default=_get_parent, help="Choose Payroll Structure")
    rule_ids = fields.Many2many(
        'hr.salary.rule', 'hr_structure_salary_rule_rel', 'struct_id',
        'rule_id', string='Salary Rules', tracking=True,
        help="Choose Salary Rule")


class HrSalaryRuleTracking(models.Model):
    """Add chatter + field tracking to salary rules."""
    _name = 'hr.salary.rule'
    _inherit = ['hr.salary.rule', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        required=True, translate=True, string="Salary Rule Name",
        tracking=True, help="Enter Salary Rule Name")
    code = fields.Char(
        required=True, string="Salary Rule Code", tracking=True,
        help="The code of salary rules can be used as reference"
             "in computation of other rules. "
             "In that case, it is case sensitive.")
    sequence = fields.Integer(
        required=True, index=True, default=5, tracking=True,
        help='Use to arrange calculation sequence',
        string="Sequence")
    quantity = fields.Char(
        default='1.0', string='Quantity', tracking=True,
        help="It is used in computation for percentage"
             "and fixed amount. For e.g. A rule for Meal"
             "Voucher having fixed amount of "
             "1€ per worked day can have its quantity"
             "defined in expression "
             "like worked_days.WORK100.number_of_days.")
    category_id = fields.Many2one(
        'hr.salary.rule.category', string='Category', tracking=True,
        help="Choose Salary Rule Category", required=True)
    active = fields.Boolean(
        default=True, string='Active', tracking=True,
        help="If the active field is set to false, "
             "it will allow you to hide the salary"
             "rule without removing it.")
    appears_on_payslip = fields.Boolean(
        string='Appears on Payslip', default=True, tracking=True,
        help="Used to display the salary"
             "rule on payslip.")
    parent_rule_id = fields.Many2one(
        'hr.salary.rule', string='Parent Salary Rule', index=True,
        tracking=True, help="Choose Hr Salary Rule")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, tracking=True,
        default=lambda self: self.env.company.id)
    condition_select = fields.Selection([
        ('none', 'Always True'),
        ('range', 'Range'),
        ('python', 'Python Expression')
    ], string="Condition Based on", default='none', required=True,
        tracking=True, help="Choose Condition for Salary Rule")
    condition_range = fields.Char(
        string='Range Based on', default='contract.wage', tracking=True,
        help='This will be used to compute the % '
             'fields values; in general it is on '
             'basic, but you can also use categories '
             'code fields in lowercase as a variable'
             ' names (hra, ma, lta, etc.) and the '
             'variable basic.')
    condition_python = fields.Text(
        string='Python Condition', tracking=True,
        default='''
    # Available variables:
    #----------------------
    # payslip: object containing the payslips
    # employee: hr.employee object
    # contract: hr.version object
    # rules: object containing the rules code (previously computed)
    # categories: object containing the computed salary rule categories 
    # (sum of amount of all rules belonging to that category).
    # worked_days: object containing the computed worked days
    # inputs: object containing the computed inputs

    # Note: returned value have to be set in the variable 'result'

    result = rules.NET > categories.NET * 0.10''',
        help='Applied this rule for calculation'
             ' if condition is true. You can specify'
             ' condition like basic > 1000.')
    condition_range_min = fields.Float(
        string='Minimum Range', tracking=True,
        help="The minimum amount, applied for this rule.")
    condition_range_max = fields.Float(
        string='Maximum Range', tracking=True,
        help="The maximum amount, applied for this rule.")
    amount_select = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fix', 'Fixed Amount'),
        ('code', 'Python Code'),
    ], string='Amount Type', index=True, required=True, default='fix',
        tracking=True,
        help="The computation method for the rule amount.")
    amount_fix = fields.Float(
        string='Fixed Amount', digits='Payroll', tracking=True,
        help="Set a Fixed Amount")
    amount_percentage = fields.Float(
        string='Percentage (%)', digits='Payroll Rate', tracking=True,
        help='For example, enter 50.0 to apply a percentage of 50%')
    amount_python_compute = fields.Text(
        string='Python Code', tracking=True,
        default='''
            # Available variables:
            #----------------------
            # payslip: object containing the payslips
            # employee: hr.employee object
            # contract: hr.version object
            # rules: object containing the rules code (previously computed)
            # categories: object containing the computed salary rule categories 
            # (sum of amount of all rules belonging to that category).
            # worked_days: object containing the computed worked days.
            # inputs: object containing the computed inputs.

            # Note: returned value have to be set in the variable 'result'

            result = contract.wage * 0.10''')
    amount_percentage_base = fields.Char(
        string='Percentage based on', tracking=True,
        help='result will be affected to a variable')
    register_id = fields.Many2one(
        'hr.contribution.register', string='Contribution Register',
        tracking=True, help="Eventual third party involved in the"
                            " salary payment of the employees.")
    note = fields.Text(
        string='Description', tracking=True,
        help="Description for Salary Rule")


class HrContributionRegisterTracking(models.Model):
    """Add chatter + field tracking to contribution registers."""
    _name = 'hr.contribution.register'
    _inherit = ['hr.contribution.register', 'mail.thread',
                'mail.activity.mixin']

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, tracking=True,
        default=lambda self: self.env.company.id)
    partner_id = fields.Many2one(
        'res.partner', string='Partner', tracking=True,
        help="Choose Partner for Register")
    name = fields.Char(
        required=True, string="Name", tracking=True,
        help="Contribution Register Name")
    note = fields.Text(
        string='Description', tracking=True,
        help="Set Description for Register")


class HrPayrollStructureTypeTracking(models.Model):
    """Add chatter + field tracking to structure types.

    Base model lives in Odoo core hr; default_struct_id added by
    hr_payroll_community. Redefinitions preserve core defaults/domains.
    """
    _name = 'hr.payroll.structure.type'
    _inherit = ['hr.payroll.structure.type', 'mail.thread',
                'mail.activity.mixin']

    name = fields.Char(
        string='Salary Structure Type', tracking=True)
    default_resource_calendar_id = fields.Many2one(
        'resource.calendar', string='Working Hours', tracking=True,
        default=lambda self: self.env.company.resource_calendar_id,
        domain=lambda self: [('company_id', 'in',
                               [False] + self.env.companies.ids)])
    country_id = fields.Many2one(
        'res.country', string='Country', tracking=True,
        default=lambda self: self.env.company.country_id,
        domain=lambda self: [('id', 'in',
                               self.env.companies.country_id.ids)])
    default_struct_id = fields.Many2one(
        'hr.payroll.structure', string="Pay Structure", tracking=True,
        help="Default structure for this pay category")
