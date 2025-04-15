{
    'name': 'Custom Menu Style',
    'version': '16.0.1.0.0',
    'category': 'Theme/Backend',
    'summary': 'Custom styling for Odoo apps menu',
    'description': """
        Customizes the appearance of the Odoo apps menu with:
        - Modern dark theme
        - App icons
        - Improved visibility
    """,
    'depends': ['base', 'web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            'custom_menu_style/static/src/scss/style.scss',
            'custom_menu_style/static/src/js/dropdown_position.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
