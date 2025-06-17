from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    internal_rating = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ], string='Internal Rating')

    
