.. image:: https://img.shields.io/badge/licence-AGPL--1-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

Timesheets by Employees v16
===========================

This module allows to print the timesheets of selected employee.

Instructions
=============

To print an employee timesheet:

Menu > Timesheets > Dropdown menu > Reporting > Print timesheet

Configuration
=============

The module is ready to use.
The only thing to tweak to make the reports look cool  (Headers and footers + layout) is the Qweb view.

Settings > Technicals > Database Structure > Views > timesheets_by_employee.report_timesheets

Replace the content of the view with [this custom Qweb view](https://github.com/marcothedood/ODOO-CUSTOM-ADDONS-timesheets_by_employee/blob/master/Qweb-timesheets_by_employee.report_timesheets)
