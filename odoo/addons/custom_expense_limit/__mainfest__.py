{
    'name': 'Custom Expense Analytics',
    'version': '1.0',
    'category': 'Human Resources/Expenses',
    'summary': 'Customizes expense analytics to force 100% allocation to single project',
    'description': """
        This module modifies the expense form to:
        - Force 100% allocation to a single analytic account
        - Remove percentage input field
        - Prevent adding multiple analytic distributions
    """,
    'depends': ['hr_expense'],
    'data': [
        'views/hr_expense_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_expense_analytics/static/src/js/analytic_field.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
