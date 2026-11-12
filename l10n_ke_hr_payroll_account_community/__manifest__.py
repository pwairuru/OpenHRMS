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
    'name': 'Kenya - Payroll Accounting (Community)',
    'version': '20.0.1.0.4',
    'category': 'Human Resources/Payroll',
    'summary': 'Kenya statutory salary rules mapped to ledger accounts',
    'description': 'Maps the Kenya payroll salary rules (PAYE, NSSF, SHIF, '
                   'AHL, HELB, Net) onto l10n_ke chart accounts so Done '
                   'payslips post balanced journal entries. Includes the '
                   '100k oracle, NSSF-cap, SHIF-floor and mapping tests.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.openhrms.com',
    'countries': ['ke'],
    'depends': [
        'l10n_ke_hr_payroll_community',
        'hr_payroll_account_community',
        'l10n_ke',
    ],
    'data': [
        'data/ke_payable_accounts_data.xml',
        'data/ke_authority_partners_data.xml',
        'data/ke_account_mapping_data.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
