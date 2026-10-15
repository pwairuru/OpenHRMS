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
    'name': "Open HRMS HR Dashboard",
    'version': '20.0.1.0.0',
    'summary': """Comprehensive Dashboard for Managing HR Activities in Open HRMS""",
    'description': """Provides a dashboard to view key HR information such as attendance, leaves, payroll, and more. Helps HR teams track activities in one place.""",
    'category': 'Generic Modules/Human Resources',
    'live_test_url': 'https://youtu.be/XwGGvZbv6sc',
    'author': 'Cybrosys Techno solutions,Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['hr', 'hr_holidays', 'hr_timesheet', 'hr_payroll_community',
                # Hoteli lean install: commented out, not installed
                # 'hr_attendance', 'hr_timesheet_attendance',
                # 'hr_recruitment', 'hr_resignation',
                'event',
                'hr_reward_warning', 'hr_expense'],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'security/ir.access.csv',
        'report/broadfactor.xml',
        'views/hr_leave_views.xml',
        'views/hrms_dashboard_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hrms_dashboard/static/src/css/dashboard.css',
            'hrms_dashboard/static/src/js/dashboard.js',
            'hrms_dashboard/static/src/xml/dashboard.xml',
            # 20.0 port: single Chart.js v3 for the whole backend (v2 xAxes
            # syntax removed from dashboard.js; inventory dashboard needs v3).
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js',
        ],
    },
    'images': ["static/description/banner.jpg"],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
