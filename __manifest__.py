# -*- coding: utf-8 -*-
{
    'name': 'SD HR Contracts',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': """ """,
    'author': 'Arash Homayounfar',
    'company': 'Giladoo',
    'maintainer': 'Giladoo',
    'website': "https://www.giladoo.com",
    'installable': True,
    'auto_install': False,
    'application': False,
    'depends': ['base', 'hr', 'hr_contract', 'sd_hr'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/hr_employee_views.xml',
        'views/hr_contract_doc_template_views.xml',
        'views/hr_contract_views.xml',
        'data/hr_contract_sequence.xml',
        # 'wizard/contract_duplicate.xml',
        'wizard/contract_report.xml',
        # 'wizard/employees_report.xml',
    ],
'assets': {
        'web.assets_backend':[
            # 'sd_hr_contracts/static/src/components/**/*'
        ],

    },
    'demo': [

    ],
	'external_dependencies': {
    	'python': ['jdatetimext','docx',]
    },
    'license': 'LGPL-3',
}
