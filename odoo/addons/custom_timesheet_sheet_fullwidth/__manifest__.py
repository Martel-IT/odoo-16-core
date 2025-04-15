{
    'name': 'Timesheet Sheet Fullwidth',
    'version': '16.0.1.0.0',
    'category': 'Human Resources/Timesheets',
    'summary': 'Full width layout for timesheet sheets',
    'description': """
        Makes timesheet sheets use full width of the screen.
    """,
    'depends': ['hr_timesheet_sheet'],
    'data': [
        'views/timesheet_sheet_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'custom_timesheet_sheet_fullwidth/static/src/scss/styles.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
