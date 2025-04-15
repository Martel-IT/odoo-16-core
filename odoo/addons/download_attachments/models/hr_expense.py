from odoo import api, fields, models, _

class HrExpense(models.Model):
    _inherit = 'hr.expense'
    
    @api.model
    def run_vacuum_cleaner(self):
        self.env['ir.attachment'].search([
            ('name', 'ilike', 'expense_report_%'),
            ('res_model', '=', False),
            ('mimetype', '=', 'application/pdf'),
            ('res_id', '=', False),
            ('type', '=', 'binary')
        ]).unlink()
