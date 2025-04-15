from odoo import api, fields, models
from collections import defaultdict
from datetime import datetime


class ReportTimesheet(models.AbstractModel):
    _name = 'report.timesheets_by_employee.report_timesheets'
    _description = 'Timesheet Report'

    def format_time_24h(self, hours):
        """Convert float hours to 24h format string"""
        total_minutes = int(hours * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    def get_timesheets(self, docs):
        domain = [
            ('user_id', '=', docs.user_id[0].id),
            ('project_id', '!=', False)
        ]
        if docs.from_date:
            domain.append(('date', '>=', docs.from_date))
        if docs.to_date:
            domain.append(('date', '<=', docs.to_date))

        record = self.env['account.analytic.line'].search(domain, order='project_id, task_id, date')

        timesheet_data = {
            'projects': defaultdict(lambda: {'tasks': defaultdict(lambda: {'entries': [], 'subtotal': 0.0}), 'subtotal': 0.0}),
            'total': 0.0,
            'total_hours_display': '00:00'
        }

        for rec in record:
            project_name = rec.project_id.name
            task_name = rec.task_id.name or 'No Task'

            entry = {
                'date': rec.date,
                'description': rec.name or '',
                'duration': self.format_time_24h(rec.unit_amount),
                'hours': rec.unit_amount
            }

            timesheet_data['projects'][project_name]['tasks'][task_name]['entries'].append(entry)
            timesheet_data['projects'][project_name]['tasks'][task_name]['subtotal'] += rec.unit_amount
            timesheet_data['projects'][project_name]['subtotal'] += rec.unit_amount
            timesheet_data['total'] += rec.unit_amount

        # Format subtotals
        for project in timesheet_data['projects'].values():
            project['subtotal_display'] = self.format_time_24h(project['subtotal'])
            for task in project['tasks'].values():
                task['subtotal_display'] = self.format_time_24h(task['subtotal'])

        timesheet_data['total_hours_display'] = self.format_time_24h(timesheet_data['total'])

        return timesheet_data

    def get_timesheet_submission_approval_info(self, user_id, from_date, to_date):
        """
        Get timesheet submission and approval information from hr_timesheet.sheet
        and associated messages/tracking for accurate reviewer and dates
        """
        result = {
            'submitted_date': False,
            'approved_date': False,
            'reviewer_name': 'Not Assigned'
        }
        
        # Find timesheet sheet data that matches the period
        domain = [('user_id', '=', user_id)]
        if from_date:
            domain.append(('date_start', '>=', from_date))
        if to_date:
            domain.append(('date_end', '<=', to_date))
        
        timesheet_sheet = self.env['hr_timesheet.sheet'].search(domain, order='date_end DESC', limit=1)
        
        if timesheet_sheet:
            # Look for 'state' change message to find when it was submitted or approved
            message_domain = [
                ('model', '=', 'hr_timesheet.sheet'),
                ('res_id', '=', timesheet_sheet.id),
            ]
            messages = self.env['mail.message'].search(message_domain, order='date')
            
            # Look for tracking values related to state changes
            for message in messages:
                if message.tracking_value_ids:
                    for tracking in message.tracking_value_ids:
                        if tracking.field_desc == 'Status' and tracking:
                            # If status changed to "Waiting Review" - it was submitted
                            if tracking.new_value_char == 'Waiting Review' or tracking.new_value_char == 'waiting_review':
                                result['submitted_date'] = message.date
                                
                            # If status changed to "Approved" - it was approved
                            if tracking.new_value_char == 'Approved' or tracking.new_value_char == 'done':
                                result['approved_date'] = message.date
                                if message.author_id:
                                    result['reviewer_name'] = message.author_id.name
            
            # No longer use creation date as fallback for submission date
            # if not result['submitted_date'] and timesheet_sheet.create_date:
            #     result['submitted_date'] = timesheet_sheet.create_date
            
            # Try to get reviewer information from various sources if not found in messages
            if not result['reviewer_name'] or result['reviewer_name'] == 'Not Assigned':
                if hasattr(timesheet_sheet, 'reviewer_id') and timesheet_sheet.reviewer_id:
                    reviewer = self.env['hr.employee'].search([('user_id', '=', timesheet_sheet.reviewer_id.id)], limit=1)
                    result['reviewer_name'] = reviewer.name if reviewer else timesheet_sheet.reviewer_id.name
                elif hasattr(timesheet_sheet, 'manager_id') and timesheet_sheet.manager_id:
                    result['reviewer_name'] = timesheet_sheet.manager_id.name
        
        # If we still don't have a reviewer name, try to get from the employee's manager
        if not result['reviewer_name'] or result['reviewer_name'] == 'Not Assigned':
            employee = self.env['hr.employee'].search([('user_id', '=', user_id)], limit=1)
            if employee and employee.parent_id:
                result['reviewer_name'] = employee.parent_id.name
        
        # If all else fails and we have tracking of approval but no reviewer name,
        # check if there's a latest change message that might indicate who approved it
        if result['approved_date'] and (not result['reviewer_name'] or result['reviewer_name'] == 'Not Assigned'):
            # Look for the most recent status change message near the approval date
            approval_messages = self.env['mail.message'].search([
                ('model', '=', 'hr_timesheet.sheet'),
                ('res_id', '=', timesheet_sheet.id),
                ('date', '<=', result['approved_date']),
            ], order='date desc', limit=5)
            
            for message in approval_messages:
                if message.author_id and message.author_id.id != employee.user_id.partner_id.id:
                    result['reviewer_name'] = message.author_id.name
                    break
        
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['timesheet.report'].browse(self.env.context.get('active_id'))
        company = self.env.company.sudo()
        logo = False
        if company.logo:
            logo = company.logo
        company_data = {
            'name': company.name,
            'email': company.email,
            'city': company.city,
            'street': company.street,
            'zip': company.zip,
            'state_id': company.state_id and company.state_id.name,
            'phone': company.phone,
            'website': company.website,
        }

        employee = self.env['hr.employee'].search([('user_id', '=', docs.user_id[0].id)], limit=1)

        period = None
        if docs.from_date and docs.to_date:
            period = f"From {docs.from_date} To {docs.to_date}"
        elif docs.from_date:
            period = f"From {docs.from_date}"
        elif docs.to_date:
            period = f"To {docs.to_date}"

        timesheet_data = self.get_timesheets(docs)
        
        # Get submission and approval information
        timesheet_info = self.get_timesheet_submission_approval_info(
            docs.user_id[0].id, docs.from_date, docs.to_date
        )

        return {
            'doc_ids': self.ids,
            'doc_model': 'timesheet.report',
            'docs': docs,
            'employee': employee,
            'period': period,
            'timesheet_data': timesheet_data,
            'res_company': company,
            'company_data': company_data,
            'timesheet_submitted_date': timesheet_info['submitted_date'],
            'timesheet_approved_date': timesheet_info['approved_date'],
            'reviewer_name': timesheet_info['reviewer_name'],
        }