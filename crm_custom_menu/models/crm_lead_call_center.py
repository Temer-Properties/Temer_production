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

    name = fields.Char(string='Name', compute="compute_lead_name", required=False)
    customer_name = fields.Char(string='Customer',tracking=True, required=True)
    site_ids = fields.Many2many('property.site', string="site", tracking=True)
    country_id = fields.Many2one('res.country', string="Country", default=lambda self: self.env.ref('base.et').id)
    phone_number = fields.Char(string="Phone Number")
    full_phone = fields.Many2many('crm.callcenter.phone', string="All Phone no", help="List of all phone numbers.", domain="[('id', 'not in', full_phone_ids)]" )
    secondary_phone = fields.Char(string="Secondary Phone", invisible=True)
    phone_prefix = fields.Char(string="Phone Prefix", compute="_compute_phone_prefix")
    full_phone_ids = fields.Many2many(
        'crm.callcenter.phone',
        store=False,
        string="Excluded Phone Numbers"
    )

    new_phone = fields.Char(string="Phone No", tracking=True)
    source_id = fields.Many2one(
        'utm.source',
        string="Lead Source",
        help="Indicates the source of the lead (e.g., Website, Campaign, Referral).",
        default=lambda self: self._default_source_id(),
    )
    is_call_center_user = fields.Boolean(
        string="Is Call Center User",
        compute="_compute_is_call_center_user",
        store=False
    )
    sales_person = fields.Many2one(
        'res.users',
        string="Call Center Person",
        default=lambda self: self.env.user,
        readonly=True,
        help="The logged-in user who created this record."
    )
    wing_id = fields.Many2one(
        'property.wing.config',
        string="Sales Wing / Supervisor",
        readonly=True,
        help="The sales wing responsible for this lead."
    )
    assigned_manager_id = fields.Many2one(
        'res.users',
        string="Assigned Manager",
        readonly=True,
        help="The wing manager assigned to this lead."
    )
    phone_number_message = fields.Char(string="Phone Number Message", readonly=True, help="Message displayed if the phone number is already registered.")
    state_crm = fields.Selection([
                ('draft', 'Draft'),
                ('sent', 'Sent'),
                ], string='Status', default='draft', tracking=True)
    crm_stage_id = fields.Many2one(
        'crm.stage',
        string="CRM Stage",
        help="The stage to assign to the lead when it is created."
    )
    
    
    # Action Methods
    def action_create_crm_lead(self):
        """Create a CRM Lead and assign explicitly to the assigned manager."""
        self.ensure_one()

        if not self.assigned_manager_id:
            raise ValidationError("No assigned manager for this reception record.")

        assigned_user = self.assigned_manager_id

        
    
        # Validate required fields
        if not self.customer_name or not self.customer_name.strip():
            raise ValidationError(_("Customer name is required"))
        
        if not self.new_phone:
            raise ValidationError(_("Primary phone number is required"))

        # Clean the phone number explicitly
        clean_phone = self.new_phone.replace('+251', '').replace('251', '').strip()
        if not clean_phone:
            raise ValidationError(_("Invalid phone number format"))

        # Handle source_id explicitly
        source_id = self.source_id.id if self.source_id else self.env['utm.source'].search([('name', '=', '6033')], limit=1).id

        # Determine the stage (crm_stage_id)
        stage_id = self.crm_stage_id.id if self.crm_stage_id else self.env['crm.stage'].search([], limit=1).id

        # Prepare lead values explicitly assigning user_id to assigned_manager_id
        lead_values = {
            'name': self.name or f"Lead from {self.customer_name.strip()}",
            'customer_name': self.customer_name.strip(),
            'phone_no': clean_phone,
            'site_ids': [(6, 0, self.site_ids.ids)],
            'country_id': self.country_id.id,
            'source_id': source_id,
            'user_id': assigned_user.id,  # explicitly assigned manager id
            'stage_id': stage_id,  # explicitly assign the stage
            'type': 'opportunity',
        }

      
        # Create the CRM lead explicitly
        # lead = self.env['crm.lead'].sudo().create(lead_values)
        lead = self.env['crm.lead'].with_user(assigned_user).create(lead_values)

        if assigned_user.partner_id:
                    lead.message_subscribe(partner_ids=[assigned_user.partner_id.id])

        # Mark the record as sent explicitly
        self.state_crm = 'sent'

        return {
            'name': _('CRM Lead'),
            'view_mode': 'form',
            'res_model': 'crm.lead',
            'res_id': lead.id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_user_id': assigned_user.id
            }
        }

    @api.constrains('source_id')
    def _check_source_id(self):
        """Ensure that the source_id cannot be changed if the user belongs to the Call Center group and the source is 6033."""
        call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
        for record in self:
            if call_center_group and self.env.user in call_center_group.users:
                source_6033 = self.env['utm.source'].search([('name', '=', '6033')], limit=1)
                if record.source_id != source_6033:
                    raise AccessError(_('You cannot change the Lead Source when it is set to 6033.'))
    @api.depends_context('uid')
    def _compute_is_call_center_user(self):
        """Compute if the current user belongs to the Call Center group."""
        call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
        for record in self:
            record.is_call_center_user = call_center_group and self.env.user in call_center_group.users

    @api.model
    def _default_source_id(self):
        """Set the default value of source_id to the record with name 6033 if the user belongs to the Call Center group."""
        call_center_group = self.env.ref('crm_custom_menu.group_call_center', raise_if_not_found=False)
        if call_center_group and self.env.user in call_center_group.users:
            return self.env['utm.source'].search([('name', '=', '6033')], limit=1).id
        return False

    @api.onchange('source_id')
    def _onchange_source_id(self):
        """Set source_id to 6033 if the user belongs to the Call Center group."""
        call_center_group = self.env.ref('base.group_call_center', raise_if_not_found=False)
        if call_center_group and self.env.user in call_center_group.users:
            self.source_id = 6033

    @api.onchange('new_phone')
    def _onchange_validate_phone(self):
            for record in self:
                if record.new_phone and record.country_id and record.country_id.code:
                    try:
                        parsed = phonenumbers.parse(record.new_phone, record.country_id.code)
                        if not phonenumbers.is_valid_number(parsed):
                            raise ValidationError(_('Invalid phone number for selected country'))
                    except Exception as e:
                        raise ValidationError(_('Invalid phone number format: %s') % str(e))
                
    @api.onchange('phone_number')
    def _onchange_validate_phone(self):
        for record in self:
            if record.country_id.code and record.phone_number:
                try:
                    parsed = phonenumbers.parse(record.phone_number, record.country_id.code)
                    if not phonenumbers.is_valid_number(parsed):
                        raise ValidationError(_('Invalid phone number for selected country.'))
                except Exception:
                    raise ValidationError(_('Invalid phone number format.'))
    
    @api.depends('customer_name','site_ids')
    def compute_lead_name(self):
        for rec in self:
            site_names = '-'.join([site.name for site in rec.site_ids])
            if rec.customer_name:
                rec.name= f'{rec.customer_name}-{site_names}'
            else:
                rec.name ="New"

    @api.depends('country_id')
    def _compute_phone_prefix(self):
     for rec in self:
         rec.phone_prefix = f"+{rec.country_id.phone_code}" if rec.country_id and rec.country_id.phone_code else ""



    def write(self, vals):
        if 'new_phone' in vals and vals['new_phone']:
            for record in self:
                # Clean the phone number
                clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
                full_phone_number = f"+251{clean_phone}"
                
                # Check for duplicates
                message = ""
                existing_phone = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
                if existing_phone:
                    callcenter_record = self.search([('full_phone', 'in', existing_phone.ids)], limit=1)
                    customer_name = callcenter_record.customer_name if callcenter_record else "Unknown Customer"
                    message += f'Phone number already registered with {customer_name} Customer in Call Center CRM. '
                
                existing_lead = self.env['crm.lead'].search([('phone_ids', '=', full_phone_number)], limit=1)
                if existing_lead:
                    customer_name = existing_lead.contact_name or existing_lead.partner_id.name or "Unknown Customer"
                    message += f'Phone number already registered with {customer_name} Customer in CRM Leads.'
                
                if message:
                    vals['phone_number_message'] = message
                else:
                    vals['phone_number_message'] = False
                
                # Add to full_phone if needed
                phone_entry = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
                if not phone_entry:
                    phone_entry = self.env['crm.callcenter.phone'].create({'name': full_phone_number})
                vals['full_phone'] = [(4, phone_entry.id)]
        
        return super(CrmLeadCallCenter, self).write(vals)

    @api.model
    def create(self, vals):
        if 'new_phone' in vals and vals['new_phone']:
            clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
            full_phone_number = f"+251{clean_phone}"
            
            message = ""
            existing_phone = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
            if existing_phone:
                callcenter_record = self.search([('full_phone', 'in', existing_phone.ids)], limit=1)
                customer_name = callcenter_record.customer_name if callcenter_record else "Unknown Customer"
                message += f'Phone number already registered with {customer_name} Customer in Call Center CRM. '
            
            existing_lead = self.env['crm.lead'].search([('phone_ids', '=', full_phone_number)], limit=1)
            if existing_lead:
                customer_name = existing_lead.contact_name or existing_lead.partner_id.name or "Unknown Customer"
                message += f'Phone number already registered with {customer_name} Customer in CRM Leads.'
            
            if message:
                vals['phone_number_message'] = message
            
            phone_entry = self.env['crm.callcenter.phone'].search([('name', '=', full_phone_number)], limit=1)
            if not phone_entry:
                phone_entry = self.env['crm.callcenter.phone'].create({'name': full_phone_number})
            vals['full_phone'] = [(4, phone_entry.id)]
        
        # Handle other create logic (wing, source, etc.)
        call_center_group = self.env.ref('base.group_call_center', raise_if_not_found=False)
        if call_center_group and self.env.user in call_center_group.users:
            vals['source_id'] = 6033
        
        wing = self._get_next_available_wing()
        if not wing:
            raise ValidationError(_('No sales wings are available. Please configure at least one sales wing.'))
        
        vals['wing_id'] = wing.id
        vals['assigned_manager_id'] = wing.manager_id.id if wing.manager_id else False
        
        return super(CrmLeadCallCenter, self).create(vals)

    def _get_next_available_wing(self):
            """
            Get the next available wing based on the number of leads assigned to its manager.
            Distribute leads evenly among managers.
            """
            wings = self.env['property.wing.config'].search([], order='id')

            if not wings:
                return False

            # Calculate the number of leads assigned to each wing manager
            wing_manager_lead_counts = {}
            for wing in wings:
                if not wing.manager_id:
                    continue  # Skip wings without managers
                wing_manager_lead_counts[wing.id] = self.search_count([
                    ('assigned_manager_id', '=', wing.manager_id.id)
                ])

            if not wing_manager_lead_counts:
                return False

            # Find the minimum number of leads assigned to any wing manager
            min_leads = min(wing_manager_lead_counts.values())

            # Get a list of wings whose managers have the minimum number of leads
            available_wings = [wing for wing in wings if wing.id in wing_manager_lead_counts and wing_manager_lead_counts[wing.id] == min_leads]

            # System parameter to store last assigned wing
            Param = self.env['ir.config_parameter'].sudo()
            last_wing_id = Param.get_param('crm_custom_menu.last_assigned_wing_id', default=False)

            if last_wing_id:
                try:
                    last_wing_id = int(last_wing_id)
                    last_wing = self.env['property.wing.config'].browse(last_wing_id)
                    if not last_wing.exists() or last_wing.id not in [wing.id for wing in available_wings]:
                        last_wing = False
                except ValueError:
                    last_wing = False
            else:
                last_wing = False

            # Determine the next wing
            if last_wing:
                candidate_wings = [wing for wing in available_wings if wing.id > last_wing.id]
                if candidate_wings:
                    next_wing = candidate_wings[0]
                else:
                    next_wing = available_wings[0]  # Cycle back to the first wing
            else:
                next_wing = available_wings[0]  # Start with the first wing

            # Save the ID of the next assigned wing to system parameters
            Param.set_param('crm_custom_menu.last_assigned_wing_id', next_wing.id)

            return next_wing
