from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    module_l10n_ke_hr_payroll_community = fields.Boolean(string='Kenya Payroll')
    module_hr_payroll_account_community = fields.Boolean(string='Payroll Accounting (Community)')
