from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessError, UserError
import phonenumbers
import logging
_logger = logging.getLogger(__name__)

class CrmWebsitePhone(models.Model):
    _name = 'crm.website.phone'
    _description = 'Website Phone Numbers'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Phone Number", required=True, tracking=True)
    crm_lead_id = fields.Many2one('crm.lead', string="CRM Lead")
    website_record_id = fields.Many2one('crm.website', string="Website Record")
    is_walk_in = fields.Boolean(string="Walk-in Customer", default=True)


class CrmWebsite(models.Model):
    _name = 'crm.website'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Website CRM Lead'
    _rec_name = 'name'

    # Fields
    name = fields.Char(string='Lead Reference', compute="_compute_lead_name", store=True)
    customer_name = fields.Char(string='Customer Name', required=True, tracking=True)
    site_ids = fields.Many2many('property.site', string="Preferred Sites", tracking=True, required=True)
    country_id = fields.Many2one('res.country', string="Country", default=lambda self: self.env.ref('base.et').id)
    new_phone = fields.Char(string="Phone no", tracking=True)
    secondary_phone = fields.Char(string="Secondary Phone")
    phone_prefix = fields.Char(string="Phone Prefix", compute="_compute_phone_prefix")
    phone_number = fields.Char(string="Phone Number")
    state_crm = fields.Selection([
                ('draft', 'Draft'),
                ('sent', 'Sent'),
                ], string='Status', default='draft', tracking=True)

    # Phone number tracking
    full_phone = fields.Many2many(
        'crm.website.phone', 
        string="All Phone Numbers",
        help="List of all phone numbers associated with this customer"
    )
    
    # Source and user info
    source_id = fields.Many2one(
        'utm.source',
        string="Lead Source",
        default=lambda self: self._default_source_id(),
        tracking=True
    )
    is_website_user = fields.Boolean(
        string="Is Website User",
        compute="_compute_is_website_user"
    )
    sales_person = fields.Many2one(
        'res.users',
        string="Website Admin",
        default=lambda self: self.env.user,
        readonly=True
    )
    
    # Assignment fields
    wing_id = fields.Many2one(
        'property.wing.config',
        string="Sales Wing",
        readonly=True
    )
    assigned_manager_id = fields.Many2one(
        'res.users',
        string="Assigned Manager",
        readonly=True
    )
    crm_stage_id = fields.Many2one(
        'crm.stage',
        string="CRM Stage",
        help="The stage to assign to the lead when it is created."
    )
    # Status and messaging
    phone_number_message = fields.Char(string="Phone Alert", readonly=True)
    state = fields.Selection([
        ('draft', 'New'),
        ('progress', 'In Progress'),
        ('done', 'Completed')
    ], string="Status", default='draft', tracking=True)


    crm_website_phone_id = fields.Many2one(
        'crm.website.phone',
        string="Phone",
        required=False  # or not
    )

    # Computed Methods
    @api.depends('customer_name', 'site_ids')
    def _compute_lead_name(self):
        for rec in self:
            if rec.customer_name:
                site_names = '-'.join([site.name for site in rec.site_ids]) if rec.site_ids else ''
                rec.name = f'{rec.customer_name}-{site_names}' if site_names else rec.customer_name
            else:
                rec.name = "New Website Lead"

    @api.depends('country_id')
    def _compute_phone_prefix(self):
        for rec in self:
            rec.phone_prefix = f"+{rec.country_id.phone_code}" if rec.country_id and rec.country_id.phone_code else ""

    @api.depends_context('uid')
    def _compute_is_website_user(self):
        website_group = self.env.ref('crm_custom_menu.group_Crmwebsite', raise_if_not_found=False)
        for record in self:
            record.is_website_user = website_group and self.env.user in website_group.users

    # Default Methods
    @api.model
    def _default_source_id(self):
        website_group = self.env.ref('crm_custom_menu.group_Crmwebsite', raise_if_not_found=False)
        if website_group and self.env.user in website_group.users:
            return self.env['utm.source'].search([('name', '=', 'Website')], limit=1).id
        return False

    # Constraints and Validations
    @api.constrains('source_id')
    def _check_source_id(self):
        website_group = self.env.ref('crm_custom_menu.group_Crmwebsite', raise_if_not_found=False)
        for record in self:
            if website_group and self.env.user in website_group.users:
                walk_in_source = self.env['utm.source'].search([('name', '=', 'Website')], limit=1)
                if record.source_id != walk_in_source:
                    raise AccessError(_('Website users must keep the source as "Website"'))

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

    def action_create_crm_lead(self):
        """Create a CRM Lead assigned to the manager, but track as created by the logged-in user."""
        self.ensure_one()

        if not self.assigned_manager_id:
            raise ValidationError("No assigned manager for this website record.")

        assigned_user = self.assigned_manager_id

        if not self.customer_name or not self.customer_name.strip():
            raise ValidationError(_("Customer name is required"))
        
        if not self.new_phone:
            raise ValidationError(_("Primary phone number is required"))

        clean_phone = self.new_phone.replace('+251', '').replace('251', '').strip()
        if not clean_phone:
            raise ValidationError(_("Invalid phone number format"))

        source_id = self.source_id.id or self.env['utm.source'].search([('name', '=', 'Website')], limit=1).id
        stage_id = self.crm_stage_id.id or self.env['crm.stage'].search([], limit=1).id

        lead_values = {
            'name': self.name or f"Lead from {self.customer_name.strip()}",
            'customer_name': self.customer_name.strip(),
            'phone_no': clean_phone,
            'site_ids': [(6, 0, self.site_ids.ids)],
            'country_id': self.country_id.id,
            'source_id': source_id,
            'user_id': assigned_user.id,  # Assigned manager
            'stage_id': stage_id,
            'type': 'opportunity',
            
        }

        
        lead = self.env['crm.lead'].with_user(assigned_user).create(lead_values)


        # Optional: Subscribe the manager to the lead updates
        if assigned_user.partner_id:
            lead.message_subscribe(partner_ids=[assigned_user.partner_id.id])

        # Optional: Log message in chatter saying who created it
        lead.message_post(
            body=_("Lead was created by %s and assigned to %s.") % (
                self.env.user.name,
                assigned_user.name
            ),
            message_type="comment"
        )

        self.state_crm = 'sent'
        return True
                     

    # Helper Methods
    def _clean_phone_number(self, phone):
        """Clean and standardize phone number format"""
        return phone.replace('+251', '').replace('251', '').strip()

    def _get_or_create_phone_record(self, phone_number):
        """Find or create phone record"""
        phone_record = self.env['crm.website.phone'].search([
            ('name', 'ilike', phone_number)
        ], limit=1)
        
        if not phone_record:
            formatted_phone = f"+251{phone_number}"
            phone_record = self.env['crm.website.phone'].create({
                'name': formatted_phone,
                'is_walk_in': True
            })
        return phone_record

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

    # CRUD Methods
    @api.model
    def create(self, vals):
        if 'new_phone' in vals and vals['new_phone']:
            clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
            full_phone_number = f"+251{clean_phone}"
            
            # message = ""
            # existing_phone = self.env['crm.website.phone'].search([('name', '=', full_phone_number)], limit=1)
            # if existing_phone:
            #     callcenter_record = self.search([('full_phone', 'in', existing_phone.ids)], limit=1)
            #     customer_name = callcenter_record.customer_name if callcenter_record else "Unknown Customer"
            #     message += f'Phone number already registered with {customer_name} Customer in Call Center CRM. '
            
            # existing_lead = self.env['crm.lead'].search([('phone_ids', '=', full_phone_number)], limit=1)
            # if existing_lead:
            #     customer_name = existing_lead.contact_name or existing_lead.partner_id.name or "Unknown Customer"
            #     message += f'Phone number already registered with {customer_name} Customer in CRM Leads.'
            
            # if message:
            #     vals['phone_number_message'] = message

            message = ""
            existing_phone = self.env['crm.website.phone'].search([('name', '=', full_phone_number)], limit=1)
            if existing_phone:
                callcenter_record = self.search([('full_phone', 'in', existing_phone.ids)], limit=1)
                if callcenter_record:
                    customer_name = callcenter_record.customer_name or "Unknown Customer"
                    sales_person = callcenter_record.sales_person.name or "Unknown Salesperson"
                else:
                    customer_name, sales_person = "Unknown Customer", "Unknown Salesperson"
                message += f'In Website CRM registerd by Sales Person: {sales_person}. '

            existing_lead = self.env['crm.lead'].search([('phone_ids', '=', full_phone_number)], limit=1)
            if existing_lead:
                customer_name = existing_lead.contact_name or existing_lead.partner_id.name or "Unknown Customer"
                sales_person = existing_lead.user_id.name or "Unknown Salesperson"
                message += f'\nIn CRM Leads registered by Sales Person: {sales_person}.'
            
            if message:
                vals['phone_number_message'] = message
            
            phone_entry = self.env['crm.website.phone'].search([('name', '=', full_phone_number)], limit=1)
            if not phone_entry:
                phone_entry = self.env['crm.website.phone'].create({'name': full_phone_number})
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
        
        return super(CrmWebsite, self).create(vals)


    def write(self, vals):
        if 'new_phone' in vals and vals['new_phone']:
            for record in self:
                # Clean the phone number
                clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
                full_phone_number = f"+251{clean_phone}"
                
                # Check for duplicates
                # message = ""
                # existing_phone = self.env['crm.website.phone'].search([('name', '=', full_phone_number)], limit=1)
                # if existing_phone:
                #     callcenter_record = self.search([('full_phone', 'in', existing_phone.ids)], limit=1)
                #     customer_name = callcenter_record.customer_name if callcenter_record else "Unknown Customer"
                #     message += f'Phone number already registered with {customer_name} Customer in Call Center CRM. '
                
                # existing_lead = self.env['crm.lead'].search([('phone_ids', '=', full_phone_number)], limit=1)
                # if existing_lead:
                #     customer_name = existing_lead.contact_name or existing_lead.partner_id.name or "Unknown Customer"
                #     message += f'Phone number already registered with {customer_name} Customer in CRM Leads.'
                
                # if message:
                #     vals['phone_number_message'] = message
                # else:
                #     vals['phone_number_message'] = False


                message = ""
                existing_phone = self.env['crm.website.phone'].search([('name', '=', full_phone_number)], limit=1)
                if existing_phone:
                    callcenter_record = self.search([('full_phone', 'in', existing_phone.ids)], limit=1)
                    if callcenter_record:
                        customer_name = callcenter_record.customer_name or "Unknown Customer"
                        sales_person = callcenter_record.sales_person.name or "Unknown Salesperson"
                    else:
                        customer_name, sales_person = "Unknown Customer", "Unknown Salesperson"
                    message += f'In Website CRM registered by Sales Person: {sales_person}. '

                existing_lead = self.env['crm.lead'].search([('phone_ids', '=', full_phone_number)], limit=1)
                if existing_lead:
                    customer_name = existing_lead.contact_name or existing_lead.partner_id.name or "Unknown Customer"
                    sales_person = existing_lead.user_id.name or "Unknown Salesperson"
                message += f'\nIn CRM Leads registered by Sales Person: {sales_person}.'
                
                if message:
                    vals['phone_number_message'] = message
                else:
                    vals['phone_number_message'] = False
                
                # Add to full_phone if needed
                phone_entry = self.env['crm.website.phone'].search([('name', '=', full_phone_number)], limit=1)
                if not phone_entry:
                    phone_entry = self.env['crm.website.phone'].create({'name': full_phone_number})
                vals['full_phone'] = [(4, phone_entry.id)]
        
        return super(CrmWebsite, self).write(vals)


    def _check_duplicate_phones(self, phone_number):
        """Check for duplicate phone numbers across system"""
        clean_phone = self._clean_phone_number(phone_number)
        message = ""
        
        # Check in website records
        website_phone = self.env['crm.website.phone'].search([
            ('name', 'ilike', clean_phone)
        ], limit=1)
        
        if website_phone:
            website_record = self.search([
                ('full_phone', 'in', website_phone.ids)
            ], limit=1)
            if website_record:
                message += _('Phone already registered with website record for %s. ') % (
                    website_record.customer_name or 'unknown customer')
        
        # Check in CRM leads
        crm_lead = self.env['crm.lead'].search([
            ('phone_no', 'ilike', clean_phone)
        ], limit=1)
        
        if crm_lead:
            message += _('Phone already registered in CRM for %s.') % (
                crm_lead.customer_name or 'unknown lead')
        
        return message if message else False