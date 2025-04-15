from odoo import models, fields, api

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    @api.onchange('analytic_distribution')
    def _onchange_analytic_distribution(self):
        if self.analytic_distribution:
            # Get the first analytic account
            accounts = list(self.analytic_distribution.keys())
            if accounts:
                # Force 100% allocation to the first account
                self.analytic_distribution = {accounts[0]: 100}

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    @api.onchange('expense_line_ids.analytic_distribution')
    def _onchange_expense_lines_analytic(self):
        for expense in self.expense_line_ids:
            if expense.analytic_distribution:
                accounts = list(expense.analytic_distribution.keys())
                if accounts:
                    expense.analytic_distribution = {accounts[0]: 100}
