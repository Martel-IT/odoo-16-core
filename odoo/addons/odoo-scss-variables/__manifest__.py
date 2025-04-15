{
    'name': 'Odoo SCSS Global Variables',
    'version': '16.0.1.0.0',
    'category': 'Technical',
     'license': 'LGPL-3',
    'summary': 'Global SCSS variables for Odoo',
    'description': 'Provides global SCSS variables to be used across Odoo modules',
    'author': 'Your Company Name',
    'website': 'https://yourcompany.com',
    'depends': ['web'],
    'assets': {
        'web.assets_backend': [
            '/odoo-scss-variables/static/src/scss/global_variables.scss',
        ],
        'web.assets_frontend': [
            '/odoo-scss-variables/static/src/scss/global_variables.scss',
        ],
    },
    'installable': True,
    'auto_install': True,
}
