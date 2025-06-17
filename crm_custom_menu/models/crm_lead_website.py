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

    full_phone = fields.Many2many('crm.website.phone', string="All Phone Numbers")
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
    nominated_salesperson_id = fields.Many2one(
        'res.users', string="Nominated Person", readonly=True, copy=False
    )
    assigned_salesperson_id = fields.Many2one(
        'res.users', string="Assigned Person", readonly=True, copy=False
    )                   
    # Supervisor nomination & assignment fields (NEW, like Call Center)
    nominated_supervisor_id = fields.Many2one(
        'property.sales.supervisor', string="Nominated Supervisor", readonly=True, copy=False
    )
    nominated_wing_id = fields.Many2one(
        'property.wing.config', string="Nominated Wing", readonly=True, copy=False
    )
    assigned_supervisor_id = fields.Many2one(
        'property.sales.supervisor', string="Assigned Supervisor", readonly=True, copy=False
    )
    assigned_wing_id = fields.Many2one(
        'property.wing.config', string="Assigned Wing", readonly=True, copy=False
    )

    crm_stage_id = fields.Many2one('crm.stage', string="CRM Stage")
    phone_number_message = fields.Char(string="Phone Alert", readonly=True)
    crm_website_phone_id = fields.Many2one('crm.website.phone', string="Phone")

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

    @api.model
    def _default_source_id(self):
        website_group = self.env.ref('crm_custom_menu.group_Crmwebsite', raise_if_not_found=False)
        if website_group and self.env.user in website_group.users:
            return self.env['utm.source'].search([('name', '=', 'Website')], limit=1).id
        return False

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


    # def _get_next_available_rr_user_and_config(self):
    #     Param = self.env['ir.config_parameter'].sudo()
    #     WingConfig = self.env['property.wing.config']
    #     configs = WingConfig.search([('source_id.name', '=', 'Website')])
    #     if not configs:
    #         _logger.warning("No config found for source 'Website'")
    #         return False, False

    #     # Combine all selected users from all configs with source 'Website'
    #     rr_pool = []
    #     config_map = []
    #     for config in configs:
    #         pool = config.get_selected_rr_pool()
    #         for user in pool:
    #             rr_pool.append(user)
    #             config_map.append(config)

    #     _logger.info("Website RR Pool: %s", rr_pool)
    #     if not rr_pool:
    #         _logger.warning("No users selected in Website config for round robin")
    #         return False, False

    #     key = 'crm_custom_menu.last_rr_user_website'
    #     last_index = int(Param.get_param(key, default=-1))

    #     # --- only check the LAST lead for this user ---
    #     last_lead = self.env['crm.website'].search(
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
        configs = WingConfig.search([('source_id.name', '=', 'Website')])
        if not configs:
            _logger.warning("No config found for source 'Website'")
            return False, False

        # Step 1: Build pools of users for each config
        user_pools = []
        configs_list = []
        for config in configs:
            pool = list(config.get_selected_rr_pool())
            if pool:
                user_pools.append(pool)
                configs_list.append(config)
        if not user_pools:
            _logger.warning("No users selected in Website config for round robin")
            return False, False

        # Step 2: Interleave pools (zig-zag)
        user_config_pairs = []
        max_len = max(len(pool) for pool in user_pools)
        for i in range(max_len):
            for pool_idx, pool in enumerate(user_pools):
                if i < len(pool):
                    user = pool[i]
                    config = configs_list[pool_idx]
                    user_config_pairs.append((user, config))

        _logger.info("Website RR Interleaved Pool: %s", user_config_pairs)
        if not user_config_pairs:
            _logger.warning("No users found for Website round robin after interleaving")
            return False, False

        key = 'crm_custom_menu.last_rr_user_website'
        last_index = int(Param.get_param(key, default='-1'))

        # If index is out of bounds, reset
        if last_index < 0 or last_index >= len(user_config_pairs):
            next_index = 0
        else:
            last_user, last_config = user_config_pairs[last_index]
            last_lead = self.env['crm.website'].search(
                [('nominated_salesperson_id', '=', last_user.id)],
                order='id desc', limit=1
            )
            last_unsent = last_lead and last_lead.state_crm == 'draft'
            if last_unsent:
                next_index = last_index
            else:
                next_index = (last_index + 1) % len(user_config_pairs)

        Param.set_param(key, str(next_index))

        return user_config_pairs[next_index]

    
    def _get_next_available_supervisor_and_wing(self):
        Wing = self.env['property.wing.config']
        Supervisor = self.env['property.sales.supervisor']
        wings = Wing.search([], order='id')

        wing_sup_map = []
        for wing in wings:
            sups = Supervisor.search([])
            sups_for_this_wing = sups.filtered(
                lambda sup: sup.sales_team_id and sup.sales_team_id.wing_id and sup.sales_team_id.wing_id.id == wing.id
            )
            wing_sup_map.append(list(sups_for_this_wing))

        max_len = max(len(lst) for lst in wing_sup_map) if wing_sup_map else 0
        interleaved = []
        for i in range(max_len):
            for group in wing_sup_map:
                if i < len(group):
                    interleaved.append(group[i])

        if not interleaved:
            return False, False

        Param = self.env['ir.config_parameter'].sudo()
        last_sup_id = Param.get_param('crm_custom_menu.last_nominated_supervisor_id', default=False)
        sup_ids = [sup.id for sup in interleaved]
        if last_sup_id and int(last_sup_id) in sup_ids:
            idx = sup_ids.index(int(last_sup_id))
            next_idx = (idx + 1) % len(interleaved)
            sup = interleaved[next_idx]
        else:
            sup = interleaved[0]
        Param.set_param('crm_custom_menu.last_nominated_supervisor_id', sup.id)
        wing = sup.sales_team_id.wing_id if sup.sales_team_id and sup.sales_team_id.wing_id else False
        return sup, wing

    # --- CRM LEAD ACTION: assign, update state, create lead ---
    def action_create_crm_lead(self):
        self.ensure_one()
        if not self.nominated_wing_id:
            raise ValidationError(_("Nominated wing is not set. Please Save first!"))
        if not self.nominated_salesperson_id:
            raise ValidationError(_("No nominated user set. Please Save first!"))

        supervisor = self.env['property.sales.supervisor'].search([('name', '=', self.nominated_salesperson_id.id)], limit=1)
        self.write({
            'assigned_salesperson_id': self.nominated_salesperson_id.id,
            'assigned_wing_id': self.nominated_wing_id.id,
            'assigned_supervisor_id': supervisor.id if supervisor else False,
            'state_crm': 'sent',
        })

        clean_phone = self.new_phone.replace('+251', '').replace('251', '').strip() if self.new_phone else ''
        if not self.customer_name or not self.customer_name.strip():
            raise ValidationError(_("Customer name is required"))
        if not clean_phone:
            raise ValidationError(_("Primary phone number is required"))

        source_id = self.source_id.id or self.env['utm.source'].search([('name', '=', 'Website')], limit=1).id
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
        return True

    # --- PHONE DUPLICATION LOGIC ---
    def _get_other_website_salesperson(self, full_phone_number, exclude_ids):
        leads = self.env['crm.website'].search([
            ('full_phone.name', '=', full_phone_number),
            ('id', 'not in', exclude_ids),
        ], order='create_date asc', limit=1)
        if leads:
            return leads.sales_person.name or "Unknown Salesperson"
        return None

    def _get_other_crm_lead_salesperson(self, full_phone_number):
        leads = self.env['crm.lead'].search([
            ('phone_ids', '=', full_phone_number)
        ], order='create_date asc', limit=1)
        if leads:
            return leads.user_id.name or "Unknown Salesperson"
        return None

    @api.model
    def create(self, vals):
        rr_user, config = self._get_next_available_rr_user_and_config()
        vals['nominated_salesperson_id'] = rr_user.id if rr_user else False
        vals['nominated_wing_id'] = config.id if config else False

        # If the chosen user is a supervisor, set nominated_supervisor_id as well
        supervisor = self.env['property.sales.supervisor'].search([('name', '=', rr_user.id)], limit=1) if rr_user else False
        vals['nominated_supervisor_id'] = supervisor.id if supervisor else False

        # Phone duplication and message logic (unchanged)
        if vals.get('new_phone'):
            clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
            full_phone_number = f"+251{clean_phone}"
            message = self._get_duplicate_phone_message(full_phone_number)
            if message:
                vals['phone_number_message'] = message
            phone_entry = self.env['crm.website.phone'].search([('name', '=', full_phone_number)], limit=1)
            if not phone_entry:
                phone_entry = self.env['crm.website.phone'].create({'name': full_phone_number})
            vals['full_phone'] = [(4, phone_entry.id)]


        return super().create(vals)

    def write(self, vals):
        for rec in self:
            if rec.state_crm == 'draft' and any(key in vals for key in ('customer_name', 'site_ids', 'new_phone')):
                rr_user, config = rec._get_next_available_rr_user_and_config()
                vals['nominated_salesperson_id'] = rr_user.id if rr_user else False
                vals['nominated_wing_id'] = config.id if config else False
                supervisor = rec.env['property.sales.supervisor'].search([('name', '=', rr_user.id)], limit=1) if rr_user else False
                vals['nominated_supervisor_id'] = supervisor.id if supervisor else False

        # Phone duplication/message logic (unchanged)
        for record in self:
            if 'new_phone' in vals and vals['new_phone']:
                        clean_phone = vals['new_phone'].replace('+251', '').replace('251', '').strip()
                        full_phone_number = f"+251{clean_phone}"
                        message = record._get_duplicate_phone_message(full_phone_number, [record.id])
                        if message:
                            vals['phone_number_message'] = message
                        phone_entry = record.env['crm.website.phone'].search([('name', '=', full_phone_number)], limit=1)
                        if not phone_entry:
                            phone_entry = record.env['crm.website.phone'].create({'name': full_phone_number})
                        vals['full_phone'] = [(4, phone_entry.id)]



        return super().write(vals)
    
    def _get_duplicate_phone_message(self, full_phone_number, exclude_ids=None):
        
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