from odoo import http
from odoo.http import request
import werkzeug

class DownloadAttachmentController(http.Controller):
    @http.route('/download/expense_attachments', type='http', auth='user')
    def download_expense_attachments(self, active_ids=None):
        if not active_ids:
            return werkzeug.exceptions.NotFound()

        active_ids = [int(id) for id in active_ids.split(',')]
        
        # Fetch the expense report records based on the active IDs
        expense_reports = request.env['hr.expense.sheet'].browse(active_ids)
        
        if not expense_reports:
            return werkzeug.exceptions.NotFound()

        # Use the first report to extract the employee's name and report ID
        report = expense_reports[0]
        employee_name = report.employee_id.name
        report_id = report.id
        
        # Generate the filename dynamically with the employee name and report ID
        filename = f"Expense Report - {employee_name} - {report_id}.pdf"
        
        # Create the wizard and generate the PDF data
        wizard = request.env['download_exp_attachment'].create({})
        pdf_data = wizard.with_context(active_ids=active_ids).generate_pdf_data()

        # Set headers with the dynamically generated filename
        headers = [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'attachment; filename="{filename}"'),
        ]
        
        # Return the response with the correct PDF data and headers
        return request.make_response(pdf_data, headers=headers)
