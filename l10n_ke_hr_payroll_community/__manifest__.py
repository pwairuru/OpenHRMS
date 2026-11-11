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
{
    'name': 'Kenya - Payroll (Community)',
    'version': '20.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Kenya statutory payroll for hr_payroll_community',
    'description': 'Salary structures, rules, registers and reports for Kenya (PAYE, NSSF, SHIF, AHL).',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.openhrms.com',
    'countries': ['ke'],
    'depends': ['hr_payroll_community'],
    'data': [
        'security/ir.access.csv',
        'data/ke_rule_parameter_data.xml',
        'data/hr_salary_rule_category_data.xml',
        'data/hr_contribution_register_data.xml',
        'data/hr_payroll_structure_type_data.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_salary_rule_data.xml',
        'views/hr_version_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/ke_report_wizard_views.xml',
        'report/ke_p9_report.xml',
        'report/ke_p9_template.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
