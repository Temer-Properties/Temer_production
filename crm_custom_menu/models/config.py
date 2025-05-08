
from odoo import models, fields, api

class PropertyWingConfig(models.Model):
    _name = 'property.wing.config'
    _description = 'Wing Configuration'

    source = fields.Selection([
        ('wing', 'Wing'),
        ('supervisor', 'Supervisor')
    ], string="Select Source", required=True)

    wing_id = fields.Many2one('property.sales.wing', string="Wing")
    supervisor_id = fields.Many2one('property.sales.supervisor', string="Supervisor")

    last_assignment = fields.Datetime(
        string="Last Assignment",
        help="When this configuration was last assigned a lead"
    )

    name = fields.Char(string="Name", compute='_compute_config_data', store=True)
    manager_id = fields.Many2one('res.users', string="Manager", compute='_compute_config_data', store=True)
    last_assignment = fields.Datetime(
    string="Last Assignment",
    help="When this configuration was last assigned a lead",
    default=lambda self: fields.Datetime.now()
)
    team_ids = fields.Many2many(
        'property.sales.team',
        'property_wing_config_team_rel',
        'config_id',
        'team_id',
        string="Teams",
        compute='_compute_config_data',
        store=True
    )

    @api.depends('source', 'wing_id', 'supervisor_id')
    def _compute_config_data(self):
        for record in self:
            if record.source == 'wing' and record.wing_id:
                record.name = record.wing_id.name
                record.manager_id = record.wing_id.manager_id
                record.team_ids = record.wing_id.team_ids
            elif record.source == 'supervisor' and record.supervisor_id:
                record.name = record.supervisor_id.name.name
                record.manager_id = record.supervisor_id.name
                if record.supervisor_id.sales_team_id:
                    record.team_ids = record.supervisor_id.sales_team_id
            else:
                record.name = False
                record.manager_id = False
                record.team_ids = False

