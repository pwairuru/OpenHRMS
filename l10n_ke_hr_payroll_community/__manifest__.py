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
    'version': '20.0.1.0.10',
    'category': 'Accounting/Localization',
    'summary': 'Kenya statutory payroll for hr_payroll_community',
    'description': """Kenya statutory payroll for hr_payroll_community.

Computes PAYE, NSSF (Tier I/II), SHIF, Affordable Housing Levy, HELB
and net pay on every slip, and produces the monthly statutory extracts
plus yearly tax cards.

Computation chain (Kenya: Regular Pay structure)
================================================
BASIC (contract wage) -> GROSS -> NSSF Tier I (6% up to the Lower
Earnings Limit) + Tier II (6% of the band up to the Upper Earnings
Limit) -> SHIF (2.75% of gross, minimum 300) -> AHL housing levy
(1.5% of gross) -> TAXABLE (gross less NSSF/SHIF/AHL and the capped
pension, mortgage and post-retirement medical deductions) -> PAYE
(graduated monthly bands with personal and insurance reliefs) ->
NET. HELB posts as a fixed monthly deduction; employer fringe-benefit
tax inputs ride along on an informational line.

Rules evaluate in sequence order; deduction categories hold negative
totals so NET = GROSS + deductions. A Kenya: Bonus structure runs the
tax chain only (no NSSF/SHIF/AHL/HELB). Secondary-employer contracts
get no personal or insurance relief; non-resident contracts get no
reliefs and no pension/mortgage/post-med deduction; certified
disability exempts the first slice of taxable pay.

Dated parameters, no code changes
=================================
All statutory figures live in dated KE rule parameters, so new legal
years take effect by adding rows, not by editing rules: PAYE bands,
personal relief, NSSF LEL/UEL/rate history, SHIF rate/minimum, AHL
rate, pension/mortgage/post-med monthly caps, insurance-relief
rate/cap, disability exemption and fringe market rates. Each slip reads
the parameter row valid on its start date.

Contract fields
===============
Pension/month (voluntary, NSSF added automatically inside the joint
cap), mortgage interest, post-retirement medical, life/health/education
premiums, HELB, staff-loan rate/balance, KRA PIN, NSSF and SHIF
numbers, pension remit-to, and the secondary-employer, non-resident,
disability and certificate flags.

Statutory reports (Payroll -> Reports)
======================================
* NSSF schedule (XLSX): ID, NSSF number, Tier I / Tier II / total.
* SHIF schedule (XLSX): ID, SHIF number, amount.
* AHL schedule (XLSX): ID, amount (KRA keys AHL by national ID).
* P9 tax deduction card (PDF): per-employee yearly gross/NSSF/SHIF/
  AHL/PAYE, plus a detailed individual card per employee.
* P10 Sheet B import CSV: monthly PAYE return in the KRA iTax layout.
* Payslip Analysis pivot understands the KE_BASIC/KE_GROSS/KE_NET
  lines, and printed codes drop the KE_ engine prefix.

Paid slips count as final payroll records and are included in every
extract; pre-split slips carrying the legacy single NSSF line are
still totalled correctly.

Setup
=====
Payroll -> Configuration -> Settings, tick Kenya Payroll. Assign
contracts the Kenya structure (Regular or Bonus) and fill the
statutory numbers on the contract. Pair with the KE payroll-account
module to post the matching journal entries.
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://wwww.hopesting.com',
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
        'views/hr_employee_views.xml',
        'views/hr_payslip_views.xml',
        'views/res_config_settings_views.xml',
        'views/portal_templates.xml',
        'wizard/ke_report_wizard_views.xml',
        'report/ke_p9_report.xml',
        'report/ke_p9_template.xml',
        'report/ke_code_display_templates.xml',
        'report/ke_p9_individual_template.xml',
        'report/ke_payslip_ids_template.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
