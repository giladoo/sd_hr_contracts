# -*- coding: utf-8 -*-
{
    'name': 'SD HR Contracts',
    'version': '18.0.1.0.0',
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
        'views/hr_contract_payment.xml',
        'views/hr_contract_views.xml',
        'views/contract_location_views.xml',
        'data/hr_contract_sequence.xml',
        'data/location_data.xml',
        'wizard/contract_duplicate.xml',
    ],
'assets': {
        'web.assets_backend':[
            # 'sd_hr_contracts/static/src/components/**/*'
        ],

    },
    'demo': [

    ],
	'external_dependencies': {
    	'python': ['jdatetimext','python-docx', 'num2words', 'num2fawords']
    },
    'license': 'LGPL-3',
}
