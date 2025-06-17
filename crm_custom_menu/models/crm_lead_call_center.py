# from odoo import models, fields, api, _
# from odoo.exceptions import ValidationError, AccessError
# import phonenumbers
# import logging

# _logger = logging.getLogger(__name__)

# class CrmCallCenterPhone(models.Model):
#     _name = 'crm.callcenter.phone'
#     _description = 'Call Center Phone'
#     name = fields.Char(string="Phone Number", required=True)

# class CrmLeadCallCenter(models.Model):
#     _name = 'crm.callcenter'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#     _description = 'Call Center CRM Lead'
#     _rec_name = 'name'

#     name = fields.Char(string='Name', compute="compute_lead_name", store=True)
#     customer_name = fields.Char(string='Customer', tracking=True, required=True)
#     site_ids = fields.Many2many('property.site', string="Site", tracking=True, required=True)
#     country_id = fields.Many2one('res.country', string="Country", 
#                                  default=lambda self: self.env.ref('base.et').id)
#     new_phone = fields.Char(string="Phone No", tracking=True)
#     nominated_supervisor_id = fields.Many2one(
#         'property.sales.supervisor', string="Nominated Supervisor", readonly=True, copy=False
#     )
#     nominated_wing_id = fields.Many2one(
#         'property.wing.config', string="Nominated Wing", readonly=True, copy=False
#     )
#     assigned_supervisor_id = fields.Many2one(
#         'property.sales.supervisor', string="Assigned Supervisor", readonly=True, copy=False
#     )
#     assigned_wing_id = fields.Many2one(
#         'property.wing.config', string="Assigned Wing", readonly=True, copy=False
#     )
#     state_crm = fields.Selection([
#         ('draft', 'Draft'),
#         ('sent', 'Sent'),
#     ], string='Status', default='draft', tracking=True)
#     phone_number = fields.Char(string="Phone Number")
#     full_phone = fields.Many2many('crm.callcenter.phone', string="All Phone no", 
#                                   help="List of all phone numbers.")
#     secondary_phone = fields.Char(string="Secondary Phone", invisible=True)
#     phone_prefix = fields.Char(string="Phone Prefix", compute="_compute_phone_prefix")
#     # "user_id" will be still used as the created lead's default salesperson.
#     user_id = fields.Many2one('res.users', string="Salesperson", 
#                               default=lambda self: self.env.user, readonly=True)
#     full_phone_ids = fields.Many2many('crm.callcenter.phone', store=False, 
#                                       string="Excluded Phone Numbers")
#     source_id = fields.Many2one('utm.source', string="Lead Source",
#                                 default=lambda self: self._default_source_id(),
#                                 help="Indicates the source of the lead (e.g., Website, Campaign, Referral).")
#     is_call_center_user = fields.Boolean(string="Is Call Center User",
#                                          compute="_compute_is_call_center_user", store=False)
#     sales_person = fields.Many2one('res.users', string="Call Center Person", 
#                                    default=lambda self: self.env.user, readonly=True)
#     phone_number_message = fields.Char(string="Phone Number Message", readonly=True, 
#                                        help="Message displayed if the phone number is already registered.")
#     crm_stage_id = fields.Many2one('crm.stage', string="CRM Stage", 
#                                    help="The stage to assign to the lead when it is created.")

#     # New fields for salesperson nomination and assignment
#     nominated_salesperson_id = fields.Many2one(
#         'res.users', string="Nominated Salesperson", compute="_compute_nominated_salesperson", store=True, readonly=True
#     )
#     assigned_salesperson_id = fields.Many2one(
#         'res.users', string="Assigned Salesperson", readonly=True, copy=False
#     )

#     @api.depends('customer_name', 'site_ids')
#     def compute_lead_name(self):
#         for rec in self:
#             site_names = '-'.join(site.name for site in rec.site_ids)
#             rec.name = f'{rec.customer_name}-{site_names}' if rec.customer_name else "New"

#     @api.depends('country_id')
#     def _compute_phone_prefix(self):
#         for rec in self:
#             rec.phone_prefix = f"+{rec.country_id.phone_code}" if rec.country_id and rec.country_id.phone_code else ""

#     @api.depends_context('uid')
#     def _compute_is_call_center_user(self):
#         call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
#         for rec in self:
#             rec.is_call_center_user = call_center_group and self.env.user in call_center_group.users

#     @api.depends('nominated_supervisor_id')
#     def _compute_nominated_salesperson(self):
#         for rec in self:
#             if rec.nominated_supervisor_id:
#                 salesperson = rec._get_next_available_salesperson(rec.nominated_supervisor_id)
#                 # Fallback to supervisor's linked user if no salesperson exists.
#                 rec.nominated_salesperson_id = salesperson.id if salesperson else rec.nominated_supervisor_id.name.id
#             else:
#                 rec.nominated_salesperson_id = False

#     @api.model
#     def _default_source_id(self):
#         call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
#         if call_center_group and self.env.user in call_center_group.users:
#             return self.env['utm.source'].search([('name', '=', '6033')], limit=1).id
#         return False

#     @api.constrains('source_id')
#     def _check_source_id(self):
#         call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
#         for rec in self:
#             if call_center_group and self.env.user in call_center_group.users:
#                 source_6033 = self.env['utm.source'].search([('name', '=', '6033')], limit=1)
#                 if rec.source_id != source_6033:
#                     raise AccessError(_('You cannot change the Lead Source when it is set to 6033.'))

#     @api.onchange('source_id')
#     def _onchange_source_id(self):
#         call_center_group = self.env.ref('base.group_call_center', raise_if_not_found=False)
#         if call_center_group and self.env.user in call_center_group.users:
#             self.source_id = 6033

#     @api.onchange('new_phone')
#     def _onchange_validate_phone(self):
#         for rec in self:
#             if rec.new_phone and rec.country_id and rec.country_id.code:
#                 try:
#                     parsed = phonenumbers.parse(rec.new_phone, rec.country_id.code)
#                     if not phonenumbers.is_valid_number(parsed):
#                         raise ValidationError(_('Invalid phone number for selected country'))
#                 except Exception as e:
#                     raise ValidationError(_('Invalid phone number format: %s') % str(e))

#     @api.onchange('phone_number')
#     def _onchange_validate_phone_number(self):
#         for rec in self:
#             if rec.country_id.code and rec.phone_number:
#                 try:
#                     parsed = phonenumbers.parse(rec.phone_number, rec.country_id.code)
#                     if not phonenumbers.is_valid_number(parsed):
#                         raise ValidationError(_('Invalid phone number for selected country.'))
#                 except Exception:
#                     raise ValidationError(_('Invalid phone number format.'))

#     # Domain onchange: filter supervisors whose sales_team_id.wing_id matches the wing in the config.
#     @api.onchange('nominated_wing_id')
#     def _onchange_nominated_wing_id(self):
#         if self.nominated_wing_id:
#             supervisors = self.env['property.sales.supervisor'].search([
#                 ('sales_team_id.wing_id', '=', self.nominated_wing_id.wing_id.id)
#             ])
#             return {'domain': {'nominated_supervisor_id': [('id', 'in', supervisors.ids)]}}
#         else:
#             return {'domain': {'nominated_supervisor_id': []}}

#     def _get_other_salesperson(self, full_phone_number, exclude_ids):
#         callcenter_leads = self.env['crm.callcenter'].search(
#             [('full_phone.name', '=', full_phone_number), ('id', 'not in', exclude_ids)],
#             order='create_date asc', limit=1
#         )
#         if callcenter_leads:
#             return callcenter_leads.user_id.name or "Unknown Salesperson"
#         return "Unknown Salesperson"

#     def _get_other_crm_lead_salesperson(self, full_phone_number):
#         leads = self.env['crm.lead'].search(
#             [('phone_ids', '=', full_phone_number)],
#             order='create_date asc', limit=1
#         )
#         if leads:
#             return leads.user_id.name or "Unknown Salesperson"
#         return "Unknown Salesperson"

#     def _get_next_available_supervisor_and_wing(self):
#         """
#         Round-robin selection of a supervisor that cycles evenly between wings.
#         Supervisors are grouped by wing configuration and then interleaved.
#         """
#         _logger.info("=== RR: Evenly distributed wing and supervisor selection ===")
#         WingConfig = self.env['property.wing.config']
#         Team = self.env['property.sales.team']
#         Supervisor = self.env['property.sales.supervisor']
#         Param = self.env['ir.config_parameter'].sudo()

#         wing_supervisor_map = {}
#         configs = WingConfig.search([], order='id')
#         for config in configs:
#             if not config.wing_id:
#                 continue
#             teams = Team.search([('wing_id', '=', config.wing_id.id)])
#             sup_ids = []
#             for team in teams:
#                 for sup in team.supervisor_ids:
#                     if sup.sales_team_id and sup.sales_team_id.wing_id and sup.sales_team_id.wing_id.id == config.wing_id.id:
#                         sup_ids.append(sup.id)
#             if sup_ids:
#                 wing_supervisor_map[config.id] = sorted(set(sup_ids))

#         if not wing_supervisor_map:
#             _logger.warning("No valid wing-supervisor groups found!")
#             return False, False

#         groups = []
#         for config_id, sup_ids in wing_supervisor_map.items():
#             groups.append([(config_id, sup_id) for sup_id in sup_ids])
#         interleaved = []
#         max_len = max(len(group) for group in groups)
#         for i in range(max_len):
#             for group in groups:
#                 if i < len(group):
#                     interleaved.append(group[i])

#         last_index = int(Param.get_param('crm_custom_menu.last_rr_index', default=-1))
#         next_index = (last_index + 1) % len(interleaved)
#         Param.set_param('crm_custom_menu.last_rr_index', next_index)

#         next_config_id, next_sup_id = interleaved[next_index]
#         config = WingConfig.browse(next_config_id)
#         sup = Supervisor.browse(next_sup_id)
#         _logger.info("Assigned (evenly): WingConfig '%s' (wing: %s), Supervisor '%s'",
#                      config.name, config.wing_id.name, sup.name.name)
#         return sup, config

#     @api.constrains('nominated_supervisor_id', 'nominated_wing_id')
#     def _check_supervisor_in_wing(self):
#         for rec in self:
#             if rec.nominated_supervisor_id and rec.nominated_wing_id:
#                 if not rec.nominated_supervisor_id.sales_team_id:
#                     raise ValidationError(_("Selected supervisor is not linked to any sales team!"))
#                 if rec.nominated_supervisor_id.sales_team_id.wing_id.id != rec.nominated_wing_id.wing_id.id:
#                     raise ValidationError(_("Selected supervisor is not assigned to any team under the selected wing!"))

#     def _get_next_available_salesperson(self, supervisor):
#         """
#         Round-robin selection of a salesperson from those linked to the given supervisor.
#         Assumes that supervisor has a one2many field 'salespersons' (corrected from salesperson_ids).
#         """
#         salespersons = supervisor.salespersons
#         if not salespersons:
#             return False
#         Param = self.env['ir.config_parameter'].sudo()
#         key = "crm_custom_menu.last_rr_salesperson_%s" % supervisor.id
#         last_index = int(Param.get_param(key, default=-1))
#         next_index = (last_index + 1) % len(salespersons)
#         Param.set_param(key, next_index)
#         return salespersons[next_index]

#     @api.model
#     def create(self, vals):
#         sup, wing = self._get_next_available_supervisor_and_wing()
#         vals['nominated_supervisor_id'] = sup.id if sup else False
#         vals['nominated_wing_id'] = wing.id if wing else False

#         if vals.get('new_phone'):
#             clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
#             full_phone_number = f"+251{clean_phone}"
#             message = ""
#             callcenter_person = self._get_other_salesperson(full_phone_number, [])
#             if callcenter_person != "Unknown Salesperson":
#                 message += f'In Call Center registered by : {callcenter_person}. '
#             lead_person = self._get_other_crm_lead_salesperson(full_phone_number)
#             if lead_person != "Unknown Salesperson":
#                 message += f'\nIn CRM Leads registered by : {lead_person}.'
#             if message:
#                 vals['phone_number_message'] = message
#             phone_entry = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
#             if not phone_entry:
#                 phone_entry = self.env['crm.callcenter.phone'].create({'name': full_phone_number})
#             vals['full_phone'] = [(4, phone_entry.id)]
#         return super().create(vals)

#     def write(self, vals):
#         for rec in self:
#             if rec.state_crm == 'draft' and any(key in vals for key in ('customer_name', 'site_ids', 'new_phone')):
#                 sup, wing = rec._get_next_available_supervisor_and_wing()
#                 vals['nominated_supervisor_id'] = sup.id if sup else False
#                 vals['nominated_wing_id'] = wing.id if wing else False
#         for rec in self:
#             if vals.get('new_phone'):
#                 clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
#                 full_phone_number = f"+251{clean_phone}"
#                 message = ""
#                 callcenter_person = rec._get_other_salesperson(full_phone_number, [rec.id])
#                 if callcenter_person != "Unknown Salesperson":
#                     message += f'In Call Center registered by : {callcenter_person}. '
#                 lead_person = rec._get_other_crm_lead_salesperson(full_phone_number)
#                 if lead_person != "Unknown Salesperson":
#                     message += f'\nIn CRM Leads registered by : {lead_person}.'
#                 vals['phone_number_message'] = message if message else False
#                 phone_entry = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
#                 if not phone_entry:
#                     phone_entry = self.env['crm.callcenter.phone'].create({'name': full_phone_number})
#                 vals['full_phone'] = [(4, phone_entry.id)]
#         return super().write(vals)

#     def action_create_crm_lead(self):
#         self.ensure_one()
#         if not self.nominated_supervisor_id:
#             raise ValidationError(_("No nominated supervisor set. Save first!"))
#         if not self.nominated_wing_id:
#             raise ValidationError(_("Nominated supervisor does not have a wing. Save first!"))
#         self.write({
#             'assigned_supervisor_id': self.nominated_supervisor_id.id,
#             'assigned_wing_id': self.nominated_wing_id.id,
#         })

#         clean_phone = self.new_phone.replace('+251', '').replace('251', '').strip() if self.new_phone else ''
#         if not self.customer_name or not self.customer_name.strip():
#             raise ValidationError(_("Customer name is required"))
#         if not clean_phone:
#             raise ValidationError(_("Primary phone number is required"))

#         source_id = self.source_id.id or self.env['utm.source'].search([('name', '=', '6033')], limit=1).id
#         stage_id = self.crm_stage_id.id or self.env['crm.stage'].search([], limit=1).id
#         sup = self.nominated_supervisor_id

#         # Round-robin selection of a salesperson under the nominated supervisor.
#         salesperson = self._get_next_available_salesperson(sup)
#         assigned_user = salesperson.id if salesperson else sup.name.id
#         self.write({'assigned_salesperson_id': assigned_user})

#         lead_values = {
#             'name': self.name or f"Lead from {self.customer_name.strip()}",
#             'customer_name': self.customer_name.strip(),
#             'phone_no': clean_phone,
#             'site_ids': [(6, 0, self.site_ids.ids)],
#             'country_id': self.country_id.id,
#             'source_id': source_id,
#             'user_id': assigned_user,  # Assigned salesperson
#             'stage_id': stage_id,
#             'type': 'opportunity',
#         }
#         lead = self.env['crm.lead'].with_user(sup.name).create(lead_values)
#         if sup.name.partner_id:
#             lead.message_subscribe(partner_ids=[sup.name.partner_id.id])
#         lead.message_post(
#             body=_("Lead was created by %s and assigned to salesperson %s under supervisor %s.") % (
#                 self.env.user.name,
#                 (salesperson.display_name if salesperson else sup.name.display_name),
#                 sup.name.display_name
#             ),
#             message_type="comment"
#         )
#         return True
# from odoo import models, fields, api, _
# from odoo.exceptions import ValidationError, AccessError
# import phonenumbers
# import logging

# _logger = logging.getLogger(__name__)

# class CrmCallCenterPhone(models.Model):
#     _name = 'crm.callcenter.phone'
#     _description = 'Call Center Phone'
#     name = fields.Char(string="Phone Number", required=True)

# class CrmLeadCallCenter(models.Model):
#     _name = 'crm.callcenter'
#     _inherit = ['mail.thread', 'mail.activity.mixin']
#     _description = 'Call Center CRM Lead'
#     _rec_name = 'name'

#     name = fields.Char(string='Name', compute="compute_lead_name", store=True)
#     customer_name = fields.Char(string='Customer', tracking=True, required=True)
#     site_ids = fields.Many2many('property.site', string="Site", tracking=True, required=True)
#     country_id = fields.Many2one('res.country', string="Country", 
#                                  default=lambda self: self.env.ref('base.et').id)
#     new_phone = fields.Char(string="Phone No", tracking=True)

#     # --- Supervisor & Wing Nominations/Assignments ---
#     nominated_supervisor_id = fields.Many2one(
#         'property.sales.supervisor', string="Nominated Supervisor", readonly=True, copy=False
#     )
#     nominated_wing_id = fields.Many2one(
#         'property.wing.config', string="Nominated Wing", readonly=True, copy=False
#     )
#     assigned_supervisor_id = fields.Many2one(
#         'property.sales.supervisor', string="Assigned Supervisor", readonly=True, copy=False
#     )
#     assigned_wing_id = fields.Many2one(
#         'property.wing.config', string="Assigned Wing", readonly=True, copy=False
#     )

#     # --- Salesperson Nominations/Assignments ---
#     nominated_salesperson_id = fields.Many2one(
#         'res.users', string="Nominated Salesperson", readonly=True, copy=False
#     )
#     assigned_salesperson_id = fields.Many2one(
#         'res.users', string="Assigned Salesperson", readonly=True, copy=False
#     )

#     state_crm = fields.Selection([
#         ('draft', 'Draft'),
#         ('sent', 'Sent'),
#     ], string='Status', default='draft', tracking=True)
#     phone_number = fields.Char(string="Phone Number")
#     full_phone = fields.Many2many('crm.callcenter.phone', string="All Phone no", 
#                                   help="List of all phone numbers.")
#     secondary_phone = fields.Char(string="Secondary Phone", invisible=True)
#     phone_prefix = fields.Char(string="Phone Prefix", compute="_compute_phone_prefix")
#     user_id = fields.Many2one('res.users', string="Salesperson", 
#                               default=lambda self: self.env.user, readonly=True)
#     full_phone_ids = fields.Many2many('crm.callcenter.phone', store=False, 
#                                       string="Excluded Phone Numbers")
#     source_id = fields.Many2one('utm.source', string="Lead Source",
#                                 default=lambda self: self._default_source_id(),
#                                 help="Indicates the source of the lead (e.g., Website, Campaign, Referral).")
#     is_call_center_user = fields.Boolean(string="Is Call Center User",
#                                          compute="_compute_is_call_center_user", store=False)
#     sales_person = fields.Many2one('res.users', string="Call Center Person", 
#                                    default=lambda self: self.env.user, readonly=True)
#     phone_number_message = fields.Char(string="Phone Number Message", readonly=True, 
#                                        help="Message displayed if the phone number is already registered.")
#     crm_stage_id = fields.Many2one('crm.stage', string="CRM Stage", 
#                                    help="The stage to assign to the lead when it is created.")

#     # --- Compute the display name for the lead ---
#     @api.depends('customer_name', 'site_ids')
#     def compute_lead_name(self):
#         for rec in self:
#             site_names = '-'.join(site.name for site in rec.site_ids)
#             rec.name = f'{rec.customer_name}-{site_names}' if rec.customer_name else "New"

#     @api.depends('country_id')
#     def _compute_phone_prefix(self):
#         for rec in self:
#             rec.phone_prefix = f"+{rec.country_id.phone_code}" if rec.country_id and rec.country_id.phone_code else ""

#     @api.depends_context('uid')
#     def _compute_is_call_center_user(self):
#         call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
#         for rec in self:
#             rec.is_call_center_user = call_center_group and self.env.user in call_center_group.users

#     @api.model
#     def _default_source_id(self):
#         call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
#         if call_center_group and self.env.user in call_center_group.users:
#             return self.env['utm.source'].search([('name', '=', '6033')], limit=1).id
#         return False

#     @api.constrains('source_id')
#     def _check_source_id(self):
#         call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
#         for rec in self:
#             if call_center_group and self.env.user in call_center_group.users:
#                 source_6033 = self.env['utm.source'].search([('name', '=', '6033')], limit=1)
#                 if rec.source_id != source_6033:
#                     raise AccessError(_('You cannot change the Lead Source when it is set to 6033.'))

#     @api.onchange('source_id')
#     def _onchange_source_id(self):
#         call_center_group = self.env.ref('base.group_call_center', raise_if_not_found=False)
#         if call_center_group and self.env.user in call_center_group.users:
#             self.source_id = 6033

#     @api.onchange('new_phone')
#     def _onchange_validate_phone(self):
#         for rec in self:
#             if rec.new_phone and rec.country_id and rec.country_id.code:
#                 try:
#                     parsed = phonenumbers.parse(rec.new_phone, rec.country_id.code)
#                     if not phonenumbers.is_valid_number(parsed):
#                         raise ValidationError(_('Invalid phone number for selected country'))
#                 except Exception as e:
#                     raise ValidationError(_('Invalid phone number format: %s') % str(e))

#     @api.onchange('phone_number')
#     def _onchange_validate_phone_number(self):
#         for rec in self:
#             if rec.country_id.code and rec.phone_number:
#                 try:
#                     parsed = phonenumbers.parse(rec.phone_number, rec.country_id.code)
#                     if not phonenumbers.is_valid_number(parsed):
#                         raise ValidationError(_('Invalid phone number for selected country.'))
#                 except Exception:
#                     raise ValidationError(_('Invalid phone number format.'))

#     @api.onchange('nominated_wing_id')
#     def _onchange_nominated_wing_id(self):
#         if self.nominated_wing_id:
#             supervisors = self.env['property.sales.supervisor'].search([
#                 ('sales_team_id.wing_id', '=', self.nominated_wing_id.wing_id.id)
#             ])
#             return {'domain': {'nominated_supervisor_id': [('id', 'in', supervisors.ids)]}}
#         else:
#             return {'domain': {'nominated_supervisor_id': []}}

#     def _get_other_salesperson(self, full_phone_number, exclude_ids):
#         callcenter_leads = self.env['crm.callcenter'].search(
#             [('full_phone.name', '=', full_phone_number), ('id', 'not in', exclude_ids)],
#             order='create_date asc', limit=1
#         )
#         if callcenter_leads:
#             return callcenter_leads.user_id.name or "Unknown Salesperson"
#         return "Unknown Salesperson"

#     def _get_other_crm_lead_salesperson(self, full_phone_number):
#         leads = self.env['crm.lead'].search(
#             [('phone_ids', '=', full_phone_number)],
#             order='create_date asc', limit=1
#         )
#         if leads:
#             return leads.user_id.name or "Unknown Salesperson"
#         return "Unknown Salesperson"

#     def _get_next_available_supervisor_and_wing(self):
#         _logger.info("=== RR: Evenly distributed wing and supervisor selection ===")
#         WingConfig = self.env['property.wing.config']
#         Team = self.env['property.sales.team']
#         Supervisor = self.env['property.sales.supervisor']
#         Param = self.env['ir.config_parameter'].sudo()

#         wing_supervisor_map = {}
#         configs = WingConfig.search([], order='id')
#         for config in configs:
#             if not config.wing_id:
#                 continue
#             teams = Team.search([('wing_id', '=', config.wing_id.id)])
#             sup_ids = []
#             for team in teams:
#                 for sup in team.supervisor_ids:
#                     if sup.sales_team_id and sup.sales_team_id.wing_id and sup.sales_team_id.wing_id.id == config.wing_id.id:
#                         sup_ids.append(sup.id)
#             if sup_ids:
#                 wing_supervisor_map[config.id] = sorted(set(sup_ids))

#         if not wing_supervisor_map:
#             _logger.warning("No valid wing-supervisor groups found!")
#             return False, False

#         groups = []
#         for config_id, sup_ids in wing_supervisor_map.items():
#             groups.append([(config_id, sup_id) for sup_id in sup_ids])
#         interleaved = []
#         max_len = max(len(group) for group in groups)
#         for i in range(max_len):
#             for group in groups:
#                 if i < len(group):
#                     interleaved.append(group[i])

#         last_index = int(Param.get_param('crm_custom_menu.last_rr_index', default=-1))
#         next_index = (last_index + 1) % len(interleaved)
#         Param.set_param('crm_custom_menu.last_rr_index', next_index)

#         next_config_id, next_sup_id = interleaved[next_index]
#         config = WingConfig.browse(next_config_id)
#         sup = Supervisor.browse(next_sup_id)
#         _logger.info("Assigned (evenly): WingConfig '%s' (wing: %s), Supervisor '%s'",
#                      config.name, config.wing_id.name, sup.name.name)
#         return sup, config

#     @api.constrains('nominated_supervisor_id', 'nominated_wing_id')
#     def _check_supervisor_in_wing(self):
#         for rec in self:
#             if rec.nominated_supervisor_id and rec.nominated_wing_id:
#                 if not rec.nominated_supervisor_id.sales_team_id:
#                     raise ValidationError(_("Selected supervisor is not linked to any sales team!"))
#                 if rec.nominated_supervisor_id.sales_team_id.wing_id.id != rec.nominated_wing_id.wing_id.id:
#                     raise ValidationError(_("Selected supervisor is not assigned to any team under the selected wing!"))

#     def _get_next_available_salesperson(self, supervisor):
#         """
#         Round-robin selection of a salesperson from mapping records linked to the supervisor.
#         """
#         if not supervisor:
#             return False
#         # If using a mapping table, collect users via mapped('user_id')
#         salespersons = supervisor.salespersons.mapped('user_id').filtered(lambda u: u.active)
#         if not salespersons:
#             # Fallback to supervisor's user if that user exists and is active
#             if supervisor.name and supervisor.name.exists() and supervisor.name.active:
#                 return supervisor.name
#             return False
#         Param = self.env['ir.config_parameter'].sudo()
#         key = "crm_custom_menu.last_rr_salesperson_%s" % supervisor.id
#         last_index = int(Param.get_param(key, default=-1))
#         next_index = (last_index + 1) % len(salespersons)
#         Param.set_param(key, next_index)
#         return salespersons[next_index]

#     @api.model
#     def create(self, vals):
#         sup, wing = self._get_next_available_supervisor_and_wing()
#         vals['nominated_supervisor_id'] = sup.id if sup else False
#         vals['nominated_wing_id'] = wing.id if wing else False

#         # Always lock in the nominated_salesperson at create!
#         if sup:
#             nominated_salesperson = self._get_next_available_salesperson(sup)
#             vals['nominated_salesperson_id'] = nominated_salesperson.id if nominated_salesperson else (sup.name.id if sup.name else False)

#         # Phone handling and phone_number_message (unchanged)
#         if vals.get('new_phone'):
#             clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
#             full_phone_number = f"+251{clean_phone}"
#             message = ""
#             callcenter_person = self._get_other_salesperson(full_phone_number, [])
#             if callcenter_person != "Unknown Salesperson":
#                 message += f'In Call Center registered by : {callcenter_person}. '
#             lead_person = self._get_other_crm_lead_salesperson(full_phone_number)
#             if lead_person != "Unknown Salesperson":
#                 message += f'\nIn CRM Leads registered by : {lead_person}.'
#             if message:
#                 vals['phone_number_message'] = message
#             phone_entry = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
#             if not phone_entry:
#                 phone_entry = self.env['crm.callcenter.phone'].create({'name': full_phone_number})
#             vals['full_phone'] = [(4, phone_entry.id)]
#         return super().create(vals)

#     def write(self, vals):
#         for rec in self:
#             if rec.state_crm == 'draft' and any(key in vals for key in ('customer_name', 'site_ids', 'new_phone')):
#                 sup, wing = rec._get_next_available_supervisor_and_wing()
#                 vals['nominated_supervisor_id'] = sup.id if sup else False
#                 vals['nominated_wing_id'] = wing.id if wing else False
#                 # Always lock in the nominated_salesperson on update!
#                 if sup:
#                     nominated_salesperson = rec._get_next_available_salesperson(sup)
#                     vals['nominated_salesperson_id'] = nominated_salesperson.id if nominated_salesperson else (sup.name.id if sup.name else False)
#         for rec in self:
#             if vals.get('new_phone'):
#                 clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
#                 full_phone_number = f"+251{clean_phone}"
#                 message = ""
#                 callcenter_person = rec._get_other_salesperson(full_phone_number, [rec.id])
#                 if callcenter_person != "Unknown Salesperson":
#                     message += f'In Call Center registered by : {callcenter_person}. '
#                 lead_person = rec._get_other_crm_lead_salesperson(full_phone_number)
#                 if lead_person != "Unknown Salesperson":
#                     message += f'\nIn CRM Leads registered by : {lead_person}.'
#                 vals['phone_number_message'] = message if message else False
#                 phone_entry = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
#                 if not phone_entry:
#                     phone_entry = self.env['crm.callcenter.phone'].create({'name': full_phone_number})
#                 vals['full_phone'] = [(4, phone_entry.id)]
#         return super().write(vals)

#     def action_create_crm_lead(self):
#         self.ensure_one()
#         if not self.nominated_supervisor_id:
#             raise ValidationError(_("No nominated supervisor set. Save first!"))
#         if not self.nominated_wing_id:
#             raise ValidationError(_("Nominated supervisor does not have a wing. Save first!"))

#         # Assign the nominated supervisor/wing as "assigned"
#         self.write({
#             'assigned_supervisor_id': self.nominated_supervisor_id.id,
#             'assigned_wing_id': self.nominated_wing_id.id,
#         })

#         # Only assign from nominated_salesperson_id (do not rerun round robin)
#         assigned_salesperson = self.nominated_salesperson_id
#         if not assigned_salesperson and self.nominated_supervisor_id.name:
#             assigned_salesperson = self.nominated_supervisor_id.name
#         if not assigned_salesperson:
#             raise ValidationError(_("No available salesperson under the nominated supervisor."))
#         self.write({'assigned_salesperson_id': assigned_salesperson.id})

#         clean_phone = self.new_phone.replace('+251', '').replace('251', '').strip() if self.new_phone else ''
#         if not self.customer_name or not self.customer_name.strip():
#             raise ValidationError(_("Customer name is required"))
#         if not clean_phone:
#             raise ValidationError(_("Primary phone number is required"))

#         source_id = self.source_id.id or self.env['utm.source'].search([('name', '=', '6033')], limit=1).id
#         stage_id = self.crm_stage_id.id or self.env['crm.stage'].search([], limit=1).id

#         lead_values = {
#             'name': self.name or f"Lead from {self.customer_name.strip()}",
#             'customer_name': self.customer_name.strip(),
#             'phone_no': clean_phone,
#             'site_ids': [(6, 0, self.site_ids.ids)],
#             'country_id': self.country_id.id,
#             'source_id': source_id,
#             'user_id': assigned_salesperson.id,  # Always the nominated one
#             'stage_id': stage_id,
#             'type': 'opportunity',
#         }

#         lead = self.env['crm.lead'].with_user(assigned_salesperson).create(lead_values)
#         if self.nominated_supervisor_id.name and self.nominated_supervisor_id.name.partner_id:
#             lead.message_subscribe(partner_ids=[self.nominated_supervisor_id.name.partner_id.id])
#         lead.message_post(
#             body=_("Lead was created by %s and assigned to salesperson %s under supervisor %s.") % (
#                 self.env.user.name,
#                 assigned_salesperson.display_name,
#                 self.nominated_supervisor_id.name.display_name
#             ),
#             message_type="comment"
#         )
#         # >>> THIS IS THE KEY LINE <<<
#         self.write({'state_crm': 'sent'})
#         return True

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError
import phonenumbers
import logging

_logger = logging.getLogger(__name__)

class CrmCallCenterPhone(models.Model):
    _name = 'crm.callcenter.phone'
    _description = 'Call Center Phone'
    name = fields.Char(string="Phone Number", required=True)

class CrmLeadCallCenter(models.Model):
    _name = 'crm.callcenter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Call Center CRM Lead'
    _rec_name = 'name'

    name = fields.Char(string='Name', compute="compute_lead_name", store=True)
    customer_name = fields.Char(string='Customer', tracking=True, required=True)
    site_ids = fields.Many2many('property.site', string="Site", tracking=True, required=True)
    country_id = fields.Many2one('res.country', string="Country", 
                                 default=lambda self: self.env.ref('base.et').id)
    new_phone = fields.Char(string="Phone No", tracking=True)
    nominated_supervisor_id = fields.Many2one('property.sales.supervisor', string="Nominated Supervisor", readonly=True, copy=False)
    nominated_wing_id = fields.Many2one('property.wing.config', string="Nominated Wing", readonly=True, copy=False)
    assigned_supervisor_id = fields.Many2one('property.sales.supervisor', string="Assigned Supervisor", readonly=True, copy=False)
    assigned_wing_id = fields.Many2one('property.wing.config', string="Assigned Wing", readonly=True, copy=False)
    nominated_salesperson_id = fields.Many2one('res.users', string="Nominated Person", readonly=True, copy=False)
    assigned_salesperson_id = fields.Many2one('res.users', string="Assigned Person", readonly=True, copy=False)
    state_crm = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
    ], string='Status', default='draft', tracking=True)
    phone_number = fields.Char(string="Phone Number")
    full_phone = fields.Many2many('crm.callcenter.phone', string="All Phone no", help="List of all phone numbers.")
    secondary_phone = fields.Char(string="Secondary Phone", invisible=True)
    phone_prefix = fields.Char(string="Phone Prefix", compute="_compute_phone_prefix")
    user_id = fields.Many2one('res.users', string="Salesperson", default=lambda self: self.env.user, readonly=True)
    full_phone_ids = fields.Many2many('crm.callcenter.phone', store=False, string="Excluded Phone Numbers")
    source_id = fields.Many2one('utm.source', string="Lead Source", default=lambda self: self._default_source_id(), help="Indicates the source of the lead (e.g., Website, Campaign, Referral).")
    is_call_center_user = fields.Boolean(string="Is Call Center User", compute="_compute_is_call_center_user", store=False)
    sales_person = fields.Many2one('res.users', string="Call Center Person", default=lambda self: self.env.user, readonly=True)
    phone_number_message = fields.Char(string="Phone Number Message", readonly=True, help="Message displayed if the phone number is already registered.")
    crm_stage_id = fields.Many2one('crm.stage', string="CRM Stage", help="The stage to assign to the lead when it is created.")

    @api.depends('customer_name', 'site_ids')
    def compute_lead_name(self):
        for rec in self:
            site_names = '-'.join(site.name for site in rec.site_ids)
            rec.name = f'{rec.customer_name}-{site_names}' if rec.customer_name else "New"

    @api.depends('country_id')
    def _compute_phone_prefix(self):
        for rec in self:
            rec.phone_prefix = f"+{rec.country_id.phone_code}" if rec.country_id and rec.country_id.phone_code else ""

    @api.depends_context('uid')
    def _compute_is_call_center_user(self):
        call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
        for rec in self:
            rec.is_call_center_user = call_center_group and self.env.user in call_center_group.users

    @api.model
    def _default_source_id(self):
        call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
        if call_center_group and self.env.user in call_center_group.users:
            return self.env['utm.source'].search([('name', '=', '6033')], limit=1).id
        return False

    @api.constrains('source_id')
    def _check_source_id(self):
        call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
        for rec in self:
            if call_center_group and self.env.user in call_center_group.users:
                source_6033 = self.env['utm.source'].search([('name', '=', '6033')], limit=1)
                if rec.source_id != source_6033:
                    raise AccessError(_('You cannot change the Lead Source when it is set to 6033.'))

    @api.onchange('source_id')
    def _onchange_source_id(self):
        call_center_group = self.env.ref('base.group_call_center', raise_if_not_found=False)
        if call_center_group and self.env.user in call_center_group.users:
            self.source_id = 6033

    @api.onchange('new_phone')
    def _onchange_validate_phone(self):
        for rec in self:
            if rec.new_phone and rec.country_id and rec.country_id.code:
                try:
                    parsed = phonenumbers.parse(rec.new_phone, rec.country_id.code)
                    if not phonenumbers.is_valid_number(parsed):
                        raise ValidationError(_('Invalid phone number for selected country'))
                except Exception as e:
                    raise ValidationError(_('Invalid phone number format: %s') % str(e))

    @api.onchange('phone_number')
    def _onchange_validate_phone_number(self):
        for rec in self:
            if rec.country_id.code and rec.phone_number:
                try:
                    parsed = phonenumbers.parse(rec.phone_number, rec.country_id.code)
                    if not phonenumbers.is_valid_number(parsed):
                        raise ValidationError(_('Invalid phone number for selected country.'))
                except Exception:
                    raise ValidationError(_('Invalid phone number format.'))

    @api.onchange('nominated_wing_id')
    def _onchange_nominated_wing_id(self):
        if self.nominated_wing_id:
            supervisors = self.env['property.sales.supervisor'].search([
                ('sales_team_id.wing_id', '=', self.nominated_wing_id.wing_id.id)
            ])
            return {'domain': {'nominated_supervisor_id': [('id', 'in', supervisors.ids)]}}
        else:
            return {'domain': {'nominated_supervisor_id': []}}

    def _get_other_salesperson(self, full_phone_number, exclude_ids):
        callcenter_leads = self.env['crm.callcenter'].search(
            [('full_phone.name', '=', full_phone_number), ('id', 'not in', exclude_ids)],
            order='create_date asc', limit=1
        )
        if callcenter_leads:
            return callcenter_leads.user_id.name or "Unknown Salesperson"
        return "Unknown Salesperson"

    def _get_other_crm_lead_salesperson(self, full_phone_number):
        leads = self.env['crm.lead'].search(
            [('phone_ids', '=', full_phone_number)],
            order='create_date asc', limit=1
        )
        if leads:
            return leads.user_id.name or "Unknown Salesperson"
        return "Unknown Salesperson"

    # --- PAUSING LOGIC: check only the last lead ---
    # def _get_next_available_supervisor_and_wing(self):
    #     _logger.info("=== RR: Evenly distributed wing and supervisor selection ===")
    #     WingConfig = self.env['property.wing.config']
    #     Team = self.env['property.sales.team']
    #     Supervisor = self.env['property.sales.supervisor']
    #     Param = self.env['ir.config_parameter'].sudo()

    #     wing_supervisor_map = {}
    #     configs = WingConfig.search([], order='id')
    #     for config in configs:
    #         if not config.wing_id:
    #             continue
    #         teams = Team.search([('wing_id', '=', config.wing_id.id)])
    #         sup_ids = []
    #         for team in teams:
    #             for sup in team.supervisor_ids:
    #                 if sup.sales_team_id and sup.sales_team_id.wing_id and sup.sales_team_id.wing_id.id == config.wing_id.id:
    #                     sup_ids.append(sup.id)
    #         if sup_ids:
    #             wing_supervisor_map[config.id] = sorted(set(sup_ids))

    #     if not wing_supervisor_map:
    #         _logger.warning("No valid wing-supervisor groups found!")
    #         return False, False

    #     groups = []
    #     for config_id, sup_ids in wing_supervisor_map.items():
    #         groups.append([(config_id, sup_id) for sup_id in sup_ids])
    #     interleaved = []
    #     max_len = max(len(group) for group in groups)
    #     for i in range(max_len):
    #         for group in groups:
    #             if i < len(group):
    #                 interleaved.append(group[i])

    #     last_index = int(Param.get_param('crm_custom_menu.last_rr_index', default=-1))

    #     # --- only check the LAST lead ---
    #     last_lead = self.env['crm.callcenter'].search([], order='id desc', limit=1)
    #     last_unsent = last_lead and last_lead.state_crm == 'draft'

    #     if last_unsent and last_index != -1:
    #         next_index = last_index
    #     else:
    #         next_index = (last_index + 1) % len(interleaved)
    #         Param.set_param('crm_custom_menu.last_rr_index', next_index)

    #     next_config_id, next_sup_id = interleaved[next_index]
    #     config = WingConfig.browse(next_config_id)
    #     sup = Supervisor.browse(next_sup_id)
    #     _logger.info("Assigned (evenly): WingConfig '%s' (wing: %s), Supervisor '%s'",
    #                  config.name, config.wing_id.name, sup.name.name)
    #     return sup, config

    def _get_next_available_supervisor_and_wing(self):
        Param = self.env['ir.config_parameter'].sudo()
        WingConfig = self.env['property.wing.config']
        # Only configs with source '6033'
        config = WingConfig.search([('source_id.name', '=', '6033')], limit=1)
        if not config:
            return False, False
        selected_supers = config.get_selected_supervisors()
        if not selected_supers:
            return False, config
        key = f'crm_custom_menu.last_rr_supervisor_{config.id}'
        last_index = int(Param.get_param(key, default=-1))
        next_index = (last_index + 1) % len(selected_supers)
        Param.set_param(key, next_index)
        return selected_supers[next_index], config

    # def _get_next_available_salesperson(self, supervisor):
    #     if not supervisor:
    #         return False
    #     salespersons = supervisor.salespersons.mapped('user_id').filtered(lambda u: u.active)
    #     if not salespersons:
    #         if supervisor.name and supervisor.name.exists() and supervisor.name.active:
    #             return supervisor.name
    #         return False

    #     Param = self.env['ir.config_parameter'].sudo()
    #     key = "crm_custom_menu.last_rr_salesperson_%s" % supervisor.id
    #     last_index = int(Param.get_param(key, default=-1))

    #     # --- only check the LAST lead for this supervisor ---
    #     last_lead = self.env['crm.callcenter'].search(
    #         [('nominated_supervisor_id', '=', supervisor.id)],
    #         order='id desc', limit=1
    #     )
    #     last_unsent = last_lead and last_lead.state_crm == 'draft'

    #     if last_unsent and last_index != -1:
    #         next_index = last_index
    #     else:
    #         next_index = (last_index + 1) % len(salespersons)
    #         Param.set_param(key, next_index)

    #     return salespersons[next_index]

    # def _get_next_available_rr_user_and_config(self):
    #     Param = self.env['ir.config_parameter'].sudo()
    #     WingConfig = self.env['property.wing.config']
    #     configs = WingConfig.search([('source_id.name', '=', '6033')])
    #     if not configs:
    #         return False, False

    #     # Combine all selected users from all configs with source 6033
    #     rr_pool = []
    #     config_map = []
    #     for config in configs:
    #         pool = config.get_selected_rr_pool()
    #         for user in pool:
    #             rr_pool.append(user)
    #             config_map.append(config)

    #     if not rr_pool:
    #         return False, False

    #     key = 'crm_custom_menu.last_rr_user_6033'
    #     last_index = int(Param.get_param(key, default=-1))

    #     # --- only check the LAST lead for this user ---
    #     last_lead = self.env['crm.callcenter'].search(
    #         [('nominated_salesperson_id', '=', rr_pool[last_index].id)] if last_index != -1 else [],
    #         order='id desc', limit=1
    #     ) if last_index != -1 else False
    #     last_unsent = last_lead and last_lead.state_crm == 'draft'

    #     if last_unsent and last_index != -1:
    #         next_index = last_index
    #     else:
    #         next_index = (last_index + 1) % len(rr_pool)
    #         Param.set_param(key, next_index)

    #     return rr_pool[next_index], config_map[next_index]


    def _get_next_available_rr_user_and_config(self):
        Param = self.env['ir.config_parameter'].sudo()
        WingConfig = self.env['property.wing.config']
        configs = WingConfig.search([('source_id.name', '=', '6033')])
        if not configs:
            return False, False

        # Step 1: Build a list of pools (each pool = list of users for a config)
        user_pools = []
        configs_list = []
        for config in configs:
            pool = list(config.get_selected_rr_pool())
            if pool:
                user_pools.append(pool)
                configs_list.append(config)
        if not user_pools:
            return False, False

        # Step 2: Interleave the pools (zig-zag order)
        user_config_pairs = []
        max_len = max(len(pool) for pool in user_pools)
        for i in range(max_len):
            for pool_idx, pool in enumerate(user_pools):
                if i < len(pool):
                    user = pool[i]
                    config = configs_list[pool_idx]
                    user_config_pairs.append((user, config))

        if not user_config_pairs:
            return False, False

        key = 'crm_custom_menu.last_rr_user_6033'
        last_index = int(Param.get_param(key, default='-1'))

        # If index is out of bounds, reset
        if last_index < 0 or last_index >= len(user_config_pairs):
            next_index = 0
        else:
            last_user, last_config = user_config_pairs[last_index]
            last_lead = self.env['crm.callcenter'].search(
                [('nominated_salesperson_id', '=', last_user.id)],
                order='id desc', limit=1
            )
            last_unsent = last_lead and last_lead.state_crm == 'draft'
            if last_unsent:
                next_index = last_index  # Keep assigning to this user
            else:
                next_index = (last_index + 1) % len(user_config_pairs)

        # Save new index
        Param.set_param(key, str(next_index))

        return user_config_pairs[next_index]


    @api.constrains('nominated_supervisor_id', 'nominated_wing_id')
    def _check_supervisor_in_wing(self):
        for rec in self:
            if rec.nominated_supervisor_id and rec.nominated_wing_id:
                if not rec.nominated_supervisor_id.sales_team_id:
                    raise ValidationError(_("Selected supervisor is not linked to any sales team!"))
                if rec.nominated_supervisor_id.sales_team_id.wing_id.id != rec.nominated_wing_id.wing_id.id:
                    raise ValidationError(_("Selected supervisor is not assigned to any team under the selected wing!"))

    # @api.model
    # def create(self, vals):
    #     Get the config (you may want to use a context or a field to get the right config)
    #     rr_user, config = self._get_next_available_rr_user_and_config()
    #     vals['nominated_salesperson_id'] = rr_user.id if rr_user else False
    #     vals['nominated_wing_id'] = config.id if config else False

    #     if sup and wing:
    #         nominated_salesperson = self._get_next_available_salesperson(wing)
    #         vals['nominated_salesperson_id'] = nominated_salesperson.id if nominated_salesperson else (sup.name.id if sup.name else False)

    #     if vals.get('new_phone'):
    #         clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
    #         full_phone_number = f"+251{clean_phone}"
    #         message = ""
    #         callcenter_person = self._get_other_salesperson(full_phone_number, [])
    #         if callcenter_person != "Unknown Salesperson":
    #             message += f'In Call Center registered by : {callcenter_person}. '
    #         lead_person = self._get_other_crm_lead_salesperson(full_phone_number)
    #         if lead_person != "Unknown Salesperson":
    #             message += f'\nIn CRM Leads registered by : {lead_person}.'
    #         if message:
    #             vals['phone_number_message'] = message
    #         phone_entry = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
    #         if not phone_entry:
    #             phone_entry = self.env['crm.callcenter.phone'].create({'name': full_phone_number})
    #         vals['full_phone'] = [(4, phone_entry.id)]
    #     return super().create(vals)

    @api.model
    def create(self, vals):
        rr_user, config = self._get_next_available_rr_user_and_config()
        vals['nominated_salesperson_id'] = rr_user.id if rr_user else False
        vals['nominated_wing_id'] = config.id if config else False

        # If the chosen user is a supervisor, set nominated_supervisor_id as well
        supervisor = self.env['property.sales.supervisor'].search([('name', '=', rr_user.id)], limit=1) if rr_user else False
        vals['nominated_supervisor_id'] = supervisor.id if supervisor else False

        # ...phone logic unchanged...
        if vals.get('new_phone'):
                clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
                full_phone_number = f"+251{clean_phone}"
                message = self._get_duplicate_phone_message(full_phone_number)
                if message:
                    vals['phone_number_message'] = message
                phone_entry = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
                if not phone_entry:
                    phone_entry = self.env['crm.callcenter.phone'].create({'name': full_phone_number})
                vals['full_phone'] = [(4, phone_entry.id)]
        return super().create(vals)

    def write(self, vals):
        for rec in self:
            if rec.state_crm == 'draft' and any(key in vals for key in ('customer_name', 'site_ids', 'new_phone')):
                sup, wing = rec._get_next_available_supervisor_and_wing()
                vals['nominated_supervisor_id'] = sup.id if sup else False
                vals['nominated_wing_id'] = wing.id if wing else False
                if sup:
                    nominated_salesperson = rec._get_next_available_salesperson(sup)
                    vals['nominated_salesperson_id'] = nominated_salesperson.id if nominated_salesperson else (sup.name.id if sup.name else False)
        for rec in self:
            if vals.get('new_phone'):
                clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
                full_phone_number = f"+251{clean_phone}"
                message = self._get_duplicate_phone_message(full_phone_number)
                if message:
                    vals['phone_number_message'] = message
                phone_entry = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
                if not phone_entry:
                    phone_entry = self.env['crm.callcenter.phone'].create({'name': full_phone_number})
                vals['full_phone'] = [(4, phone_entry.id)]
        return super().write(vals)

    def _get_duplicate_phone_message(self, full_phone_number, exclude_ids=None):
        """Check for duplicate phone in crm.lead, crm.reception, crm.website and return a message with salesperson names."""
        exclude_ids = exclude_ids or []

        # Check in crm.lead
        crm_lead = self.env['crm.lead'].search([
            ('phone_ids', '=', full_phone_number),
            ('id', 'not in', exclude_ids)
        ], order='create_date asc', limit=1)
        crm_lead_msg = ""
        if crm_lead:
            crm_lead_msg = f"In CRM Leads registered by: {crm_lead.user_id.name or 'Unknown Salesperson'}."

        # Check in crm.reception
        crm_reception = self.env['crm.reception'].search([
            ('full_phone.name', '=', full_phone_number),
            ('id', 'not in', exclude_ids)
        ], order='create_date asc', limit=1)
        crm_reception_msg = ""
        if crm_reception:
            crm_reception_msg = f"In Reception CRM registered by: {crm_reception.sales_person.name or 'Unknown Salesperson'}."

        # Check in crm.website
        crm_website = self.env['crm.website'].search([
            ('full_phone.name', '=', full_phone_number),
            ('id', 'not in', exclude_ids)
        ], order='create_date asc', limit=1)
        crm_website_msg = ""
        if crm_website:
            crm_website_msg = f"In Website CRM registered by: {crm_website.sales_person.name or 'Unknown Salesperson'}."

        # Combine messages
        messages = [msg for msg in [crm_lead_msg, crm_reception_msg, crm_website_msg] if msg]
        return "\n".join(messages) if messages else False

    def action_create_crm_lead(self):
        self.ensure_one()
        if not self.nominated_wing_id:
            raise ValidationError(_("Nominated wing is not set. Save first!"))
        if not self.nominated_salesperson_id:
            raise ValidationError(_("No nominated user set. Save first!"))

        # If the nominated user is a supervisor, assign both fields
        supervisor = self.env['property.sales.supervisor'].search([('name', '=', self.nominated_salesperson_id.id)], limit=1)
        self.write({
            'assigned_salesperson_id': self.nominated_salesperson_id.id,
            'assigned_wing_id': self.nominated_wing_id.id,
            'assigned_supervisor_id': supervisor.id if supervisor else False,
        })

        clean_phone = self.new_phone.replace('+251', '').replace('251', '').strip() if self.new_phone else ''
        if not self.customer_name or not self.customer_name.strip():
            raise ValidationError(_("Customer name is required"))
        if not clean_phone:
            raise ValidationError(_("Primary phone number is required"))

        source_id = self.source_id.id or self.env['utm.source'].search([('name', '=', '6033')], limit=1).id
        stage_id = self.crm_stage_id.id or self.env['crm.stage'].search([], limit=1).id
        lead_values = {
            'name': self.name or f"Lead from {self.customer_name.strip()}",
            'customer_name': self.customer_name.strip(),
            'phone_no': clean_phone,
            'site_ids': [(6, 0, self.site_ids.ids)],
            'country_id': self.country_id.id,
            'source_id': source_id,
            'user_id': self.assigned_salesperson_id.id,
            'stage_id': stage_id,
            'type': 'opportunity',
        }
        lead = self.env['crm.lead'].with_user(self.assigned_salesperson_id).create(lead_values)
        if supervisor and supervisor.name and supervisor.name.partner_id:
            lead.message_subscribe(partner_ids=[supervisor.name.partner_id.id])
        lead.message_post(
            body=_("Lead was created by %s and assigned to user %s.") % (
                self.env.user.name,
                self.assigned_salesperson_id.display_name,
            ),
            message_type="comment"
        )
        self.write({'state_crm': 'sent'})
        return True