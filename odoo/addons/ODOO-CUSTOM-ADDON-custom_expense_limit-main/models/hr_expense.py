from odoo import models, api, _
from odoo.exceptions import UserError

class HrExpense(models.Model):
   _inherit = 'hr.expense'
   
   @api.onchange('analytic_distribution')
   def _onchange_analytic_distribution(self):
       if self.analytic_distribution:
           try:
               # Se si tenta di aggiungere un secondo progetto
               if len(self.analytic_distribution.keys()) > 1:
                   # Reset al primo progetto al 100%
                   first_key = list(self.analytic_distribution.keys())[0]
                   self.analytic_distribution = {first_key: '100'}
                   return {
                       'warning': {
                           'title': 'Warning',
                           'message': 'Only one project can be selected per expense.'
                       }
                   }
           except Exception as e:
               return {
                   'warning': {
                       'title': 'Error',
                       'message': str(e)
                   }
               }
