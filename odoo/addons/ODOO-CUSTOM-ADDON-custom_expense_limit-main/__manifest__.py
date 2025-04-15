{
    'name': 'Custom Expense Limit',
    'version': '16.0.1.0.0',
    'depends': ['hr_expense'],
    'author': 'Your Company',
    'category': 'Human Resources/Expenses',
    'description': """
        Limits analytic distribution to exactly 100% in expense lines.
    """,
    'data': [],
    'assets': {
        'web.assets_backend': [
            'custom_expense_limit/static/src/js/analytic_field.js',
        ],
    },
    'installable': True,
    'application': False,
}
