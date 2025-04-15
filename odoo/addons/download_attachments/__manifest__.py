{
    'name': 'Expense Attachments Downloader',
    'author': 'Martel Innovate IT',
    'version': '16.0.1.0.0',
    'category': 'Human Resources/Expenses',
    'summary': 'Download all expense report attachments as single PDF',
    'depends': ['base', 'hr_expense'],
    'data': [
        'wizard/download_attachments.xml',
        'security/ir.model.access.csv',
    ],
    'assets': {
        'web.assets_backend': [
            'download_attachment/controllers/*.py',  # Include controllers for backend handling
        ],
    },
    'installable': True,
    'application': False,
}
