from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from odoo.osv import expression
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta

class MailActivitySchedule(models.TransientModel):
    _inherit = 'mail.activity.schedule'


#     salesperson_id = fields.Many2one('res.users', string="Salesperson", compute="_compute_salesperson_ids",store=True)
#     supervisor_id = fields.Many2one('property.sales.supervisor', string="Sales Supervisor", readonly=True,store=True, )
#     team_id = fields.Many2one('property.sales.team', string="Sales Team", readonly=True,store=True,  )
#     wing_id = fields.Many2one('property.sales.wing', string="Sales Wing", readonly=True,store=True,)


#     def _search(self, domain, offset=0, limit=None, order=None):
#         """Override search to filter reservations based on user's role"""
#         context = dict(self._context or {})
#         context.update({
#             'active_test': True,
#             'force_active_test': True
#         })
        
#         self = self.with_context(context)
        
#         if not context.get('my_team_activities'):
#             return super()._search(domain, offset=offset, limit=limit, order=order)
        
#         user = self.env.user
#         my_domain = self._get_domain_for_user_role(user)
        
#         if domain:
#             domain = expression.AND([domain, my_domain])
#         else:
#             domain = my_domain
        
#         return super(MailActivitySchedule, self.with_context(context))._search(
#             domain, offset=offset, limit=limit, order=order
#         )

#     def _get_domain_for_user_role(self, user):
#         """Determine the search domain based on the user's role"""
#         if self._is_wing_manager(user):
#             _logger.info("==============User is Wing Manager")
#             _logger.info(self._domain_for_wing_manager(user))
#             return self._domain_for_wing_manager(user)
#         elif self._is_team_manager(user):
#             _logger.info("==============User is Team Manager")
#             _logger.info(self._domain_for_team_manager(user))
#             return self._domain_for_team_manager(user)
#         elif self._is_supervisor(user):
#             _logger.info("==============User is Supervisor")
#             _logger.info(self._domain_for_supervisor(user))
#             return self._domain_for_supervisor(user)
#         else:
#             _logger.info("==============User is Salesperson")
#             _logger.info(self._domain_for_salesperson(user))
#             return self._domain_for_salesperson(user)

#     def _is_wing_manager(self, user):
#         self.env.cr.execute("SELECT id FROM property_sales_wing WHERE manager_id = %s LIMIT 1", (user.id,))
#         return self.env.cr.fetchone()

#     def _domain_for_wing_manager(self, user):
#         wing_id = self._is_wing_manager(user)[0]
#         self.env.cr.execute("""
#             SELECT t.id as team_id, s.id as supervisor_id, pm.user_id as salesperson_id
#             FROM property_sales_wing w
#             JOIN property_wing_team_rel wt ON w.id = wt.wing_id
#             JOIN property_sales_team t ON t.id = wt.team_id
#             LEFT JOIN property_team_supervisor_rel ts ON t.id = ts.team_id
#             LEFT JOIN property_sales_supervisor s ON s.id = ts.supervisor_id
#             LEFT JOIN property_salesperson_mapping pm ON pm.user_id = w.id 
#             WHERE w.id = %s
#         """, (wing_id,))
#         results = self.env.cr.dictfetchall()
#         team_ids = {r['team_id'] for r in results}
#         supervisor_ids = {r['supervisor_id'] for r in results}
#         user_ids = {r['salesperson_id'] for r in results}

#         wing_user_id = self.env['property.sales.wing'].search([('id', '=', wing_id)]).manager_id.id
#         _logger.info(f"==============sales_team_id ID: {wing_user_id}")
        
#         user_ids = list(set(user_ids))
#         user_ids.append(wing_user_id)
#         return ['|','|','|',('wing_id', '=', wing_id), ('team_id', 'in', list(team_ids)), ('supervisor_id', 'in', list(supervisor_ids)), ('salesperson_id', 'in', list(user_ids))]

#     def _is_team_manager(self, user):
#         self.env.cr.execute("SELECT id FROM property_sales_team WHERE manager_id = %s LIMIT 1", (user.id,))
#         return self.env.cr.fetchone()

#     def _domain_for_team_manager(self, user):
#         team_id = self._is_team_manager(user)[0]
#         _logger.info(f"=======***=======Team ID: {team_id}")
#         self.env.cr.execute("""
#             SELECT s.id as supervisor_id, pm.user_id as salesperson_id
#             FROM property_sales_team t
#             LEFT JOIN property_team_supervisor_rel ts ON t.id = ts.team_id
#             LEFT JOIN property_sales_supervisor s ON s.id = ts.supervisor_id
#             LEFT JOIN property_salesperson_mapping pm ON pm.supervisor_id = s.id
#             WHERE t.id = %s
#         """, (team_id,))
#         results = self.env.cr.dictfetchall()
#         supervisor_ids = {r['supervisor_id'] for r in results}
#         user_ids = {r['salesperson_id'] for r in results if r['salesperson_id'] != None}
#         _logger.info(f"==============Supervisor IDs: {supervisor_ids}")
#         _logger.info(f"==============User IDs: {user_ids}")
#         sales_team_id = self.env['property.sales.team'].search([('id', '=', team_id)]).manager_id.id
#         _logger.info(f"==============sales_team_id ID: {sales_team_id}")
        
#         user_ids = list(set(user_ids))
#         user_ids.append(sales_team_id)
#         if  supervisor_ids != None and user_ids != None:
#             return ['|','|', ('team_id', '=', team_id), ('supervisor_id', 'in', list(supervisor_ids)), ('salesperson_id', 'in', user_ids)]
#         elif  user_ids != None:
#             return [ ('salesperson_id', 'in', user_ids)]

#     def _is_supervisor(self, user):
#         self.env.cr.execute("SELECT id FROM property_sales_supervisor WHERE name = %s LIMIT 1", (user.id,))
#         return self.env.cr.fetchone()

#     def _domain_for_supervisor(self, user):
#         supervisor_id = self._is_supervisor(user)[0]
#         self.env.cr.execute("SELECT user_id FROM property_salesperson_mapping WHERE supervisor_id = %s", (supervisor_id,))
#         user_ids = [r[0] for r in self.env.cr.fetchall()]
#         _logger.info(f"==============User IDs: {user_ids}")
#         # user_ids.append(user.id)
#         sup_id = self.env['property.sales.supervisor'].search([('id', '=', supervisor_id)]).name.id
#         _logger.info(f"==============Supervisor ID: {sup_id}")
#         user_ids.append(sup_id)
#         return ['|',('supervisor_id', '=', supervisor_id), ('salesperson_id', 'in', user_ids)]

#     def _domain_for_salesperson(self, user):
#         return [('salesperson_id', '=', user.id)]
#     # @api.model
#     # def search(self, args, offset=0, limit=None, order=None, count=False):
#     #     user = self.env.user
#     #     domain = list(args)  # Create a copy of args

#     #     # Check if user is Wing Manager
#     #     wing = self.env['property.sales.wing'].search([('manager_id', '=', user.id)], limit=1)
#     #     if wing:
#     #         teams = self.env['property.sales.team'].search([('wing_id', '=', wing.id)])
#     #         supervisors = self.env['property.sales.supervisor'].search([('team_id', 'in', teams.ids)])
#     #         salespersons = self.env['property.salesperson.mapping'].search([('supervisor_id', 'in', supervisors.ids)])
#     #         domain += [('salesperson_id', 'in', salespersons.mapped('user_id').ids + supervisors.mapped('name').ids + teams.mapped('manager_id').ids)]
#     #         return super().search(domain, offset=offset, limit=limit, order=order, count=count)

#     #     # Check if user is Team Manager
#     #     team = self.env['property.sales.team'].search([('manager_id', '=', user.id)], limit=1)
#     #     if team:
#     #         supervisors = self.env['property.sales.supervisor'].search([('team_id', '=', team.id)])
#     #         salespersons = self.env['property.salesperson.mapping'].search([('supervisor_id', 'in', supervisors.ids)])
#     #         domain += [('salesperson_id', 'in', salespersons.mapped('user_id').ids + supervisors.mapped('name').ids + [user.id])]
#     #         return super().search(domain, offset=offset, limit=limit, order=order, count=count)

#     #     # Check if user is Supervisor
#     #     supervisor = self.env['property.sales.supervisor'].search([('name', '=', user.id)], limit=1)
#     #     if supervisor:
#     #         salespersons = self.env['property.salesperson.mapping'].search([('supervisor_id', '=', supervisor.id)])
#     #         domain += [('salesperson_id', 'in', salespersons.mapped('user_id').ids + [user.id])]
#     #         return super().search(domain, offset=offset, limit=limit, order=order, count=count)

#     #     # Regular salesperson - see only their own activities
#     #     domain += [('salesperson_id', '=', user.id)]
#     #     return super().search(domain, offset=offset, limit=limit, order=order, count=count)

#     @api.depends('res_model_id', 'res_ids')
#     def _compute_salesperson_ids(self):
#         for rec in self:
#             if rec.res_model_id.model == 'crm.lead':
#                 res_ids_str = rec.res_ids.strip('[]')
#                 res_ids_array = [int(x.strip()) for x in res_ids_str.split(',') if x.strip()]
#                 first_id = res_ids_array[0] if res_ids_array else False
#                 rec.salesperson_id = self.env['crm.lead'].search([('id', '=', first_id)]).user_id.id
#             else:
#                 rec.salesperson_id = False
    

#     @api.depends('salesperson_id', 'supervisor_id')
#     def _compute_team_id(self):
#         for record in self:
#             team_id = False
#             if record.supervisor_id:
#                 # Find team through supervisor
#                 team = self.env['property.sales.team'].search(
#                     [('supervisor_ids', 'in', record.supervisor_id.id)], limit=1)
#                 team_id = team.id if team else False
#             elif record.salesperson_id:
#                 # Check if salesperson is a team manager
#                 team = self.env['property.sales.team'].search(
#                     [('manager_id', '=', record.salesperson_id.id)], limit=1)
#                 team_id = team.id if team else False
            
#             record.team_id = team_id

#     @api.depends('team_id')
#     def _compute_wing_id(self):
#         for record in self:
#             wing_id = False
#             if record.team_id:
#                 wing = self.env['property.sales.wing'].search(
#                     [('team_ids', 'in', record.team_id.id)], limit=1)
#                 wing_id = wing.id if wing else False
            
#             record.wing_id = wing_id

#     def create(self, vals):
#         _logger.info("--------------------****************------------create")
#         _logger.info(vals)
#         user_id = self.env.user.id
#         _logger.info("----------**************----------------------user_id")
#         _logger.info(user_id)
#         wing_id  = self.env['property.sales.wing'].search([('manager_id', '=',user_id)], limit=1).id
#         team_id  = self.env['property.sales.team'].search([('manager_id', '=',user_id)], limit=1).id
#         supervisor_id  = self.env['property.sales.supervisor'].search([('name', '=',user_id)], limit=1).id
#         salesperson_id  = self.env['property.salesperson.mapping'].search([('user_id', '=',user_id)], limit=1).id
        
#         if salesperson_id:
#             vals['salesperson_id'] = salesperson_id
#             supervisor_id = self.env['property.salesperson.mapping'].search([('user_id', '=', salesperson_id)], limit=1).supervisor_id.id
#             _logger.info("--------------------------------supervisor_id")
#             _logger.info(supervisor_id)
#             if supervisor_id:
#                 vals['supervisor_id'] = supervisor_id.id
#                 team_id = self.env['property.sales.team'].search([('supervisor_ids', 'in', supervisor_id)], limit=1).id
#                 _logger.info("--------------------------------team_id")
#                 _logger.info(team_id)
#                 if team_id:
#                     vals['team_id'] = team_id
#                     wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
#                     _logger.info("--------------------------------wing_id")
#                     _logger.info(wing_id)
#                     if wing_id:
#                         vals['wing_id'] = wing_id
#         elif supervisor_id:
#             vals['supervisor_id'] = supervisor_id
#             team_id = self.env['property.sales.team'].search([('supervisor_ids', 'in', supervisor_id)], limit=1).id
#             _logger.info("--------------------------------team_id")
#             _logger.info(team_id)
#             if team_id:
#                 vals['team_id'] = team_id
#                 wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
#                 _logger.info("--------------------------------wing_id")
#                 _logger.info(wing_id)
#                 if wing_id:
#                     vals['wing_id'] = wing_id

#         elif team_id:
#             vals['team_id'] = team_id
#             wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
#             _logger.info("--------------------------------wing_id")
#             _logger.info(wing_id)
#             if wing_id:
#                 vals['wing_id'] = wing_id
#         else:
#             vals['wing_id'] = wing_id

#         return super(MailActivitySchedule, self).create(vals)

        
        
    def create(self, vals):
        val= super(MailActivitySchedule, self).create(vals)
        self.env['crm.activity.report'].update_activity_report_copy()
        return val



class CrmActivityReportCopy(models.Model):
    _name = 'crm.activity.report.copy'

    date = fields.Datetime('Completion Date', readonly=True)

    lead_id = fields.Many2one('crm.lead', "Opportunity", readonly=True)

    user_id = fields.Many2one('res.users', 'Salesperson', readonly=True)

    stage_id = fields.Many2one('crm.stage', 'Stage', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    lead_type = fields.Selection(
        string='Type',
        selection=[('lead', 'Lead'), ('opportunity', 'Opportunity')],
        help="Type is used to separate Leads and Opportunities")
    active = fields.Boolean('Active', readonly=True)
    tag_ids = fields.Many2many(related="lead_id.tag_ids", readonly=True)

    mail_activity_type_id = fields.Many2one('mail.activity.type', 'Activity Type', readonly=True)

    salesperson_id = fields.Many2one('res.users', string="Salesperson")
    
    supervisor_id = fields.Many2one('property.sales.supervisor', string="Sales Supervisor", readonly=True,store=True, compute="_compute_supervisor_ids")
    team_id = fields.Many2one('property.sales.team', string="Sales Team", readonly=True,store=True, compute="_compute_team_ids" )
    wing_id = fields.Many2one('property.sales.wing', string="Sales Wing", readonly=True,store=True, compute="_compute_wing_ids")
    # sync_sales_team = fields.Char(string="Sync Sales Team",  compute="_compute_supervisor_ids")

    # supervisor_id = fields.Many2one('property.sales.supervisor', string="Sales Supervisor", readonly=True, compute="_compute_supervisor_ids")
    # team_id = fields.Many2one('property.sales.team', string="Sales Team", readonly=True, compute="_compute_team_ids" )
    # wing_id = fields.Many2one('property.sales.wing', string="Sales Wing", readonly=True, compute="_compute_wing_ids")

    

    # @api.depends('user_id')
    # def _compute_salesperson_ids(self):
    #     # user_id = self.env.user.id
    #     for record in self:
    #         salesperson_id = self.env['property.salesperson.mapping'].search([('user_id', '=', record.user_id.id)], limit=1).user_id.id

    #         _logger.info("------------Compute Salesperson ID--------****************------------")
    #         _logger.info(salesperson_id)
    #         record.salesperson_id = salesperson_id
    #         record.sync_sales_team = str(salesperson_id)

# execute tis for not synced sales and Supervisor 
    # @api.depends('salesperson_id')
    # def _compute_supervisor_ids(self):
    #     _logger.info("------------Compute _compute_supervisor_ids ID--------****************------------")
    #     for record in self:
    #         _logger.info(record)
    #         _logger.info(record.salesperson_id)
    #         _logger.info(record.user_id)
    #         _logger.info(record.supervisor_id)
    #         _logger.info("++++START")
    #         if not record.supervisor_id and record.salesperson_id :
    #             supervisor_id = self.env['property.salesperson.mapping'].search([('user_id', '=', record.user_id.id)], limit=1).supervisor_id.id
    #             _logger.info(supervisor_id)
    #             record.supervisor_id = supervisor_id
    #             record.sync_sales_team = str(supervisor_id)
    #         else:
    #             record.supervisor_id = record.supervisor_id.id
    #             record.sync_sales_team = str(record.supervisor_id.id)

    #         if record.user_id:
    #             supervisor_id  = self.env['property.sales.supervisor'].search([('name', '=',record.user_id.id)], limit=1).id
    #             if not record.supervisor_id and supervisor_id:
    #                 record.supervisor_id = supervisor_id





                # team_id = self.env['property.sales.team'].search([('supervisor_ids', 'in', supervisor_id)], limit=1).id
                # _logger.info("--------------------------------team_id")
                # _logger.info(team_id)
                # if team_id:
                #     record.team_id = team_id
                #     wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
                #     _logger.info("--------------------------------wing_id")
                #     _logger.info(wing_id)
                #     if wing_id:
                #         record.wing_id = wing_id


    # @api.depends('supervisor_id')
    # def _compute_team_ids(self):
    #     for record in self:
    #         if record.supervisor_id:
    #             team_id = self.env['property.sales.team'].search([('supervisor_ids', 'in', record.supervisor_id.id)], limit=1).id
    #             record.team_id = team_id

    # @api.depends('team_id')
    # def _compute_wing_ids(self):
    #     for record in self:
    #         if record.team_id:
    #             wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', record.team_id.id)], limit=1).id
    #             record.wing_id = wing_id

    def create(self, vals):
        # _logger.info("------------ONCREATE--------****************-----*****-------create")
        # _logger.info(vals)
        user_id = self.env.user.id
        user_id = vals['user_id']
        user_id = vals['user_id']
        # _logger.info("----------**************----------------------user_id")
        # _logger.info(user_id)
        wing_id  = self.env['property.sales.wing'].search([('manager_id', '=',user_id)], limit=1).id
        team_id  = self.env['property.sales.team'].search([('manager_id', '=',user_id)], limit=1).id
        supervisor_id  = self.env['property.sales.supervisor'].search([('name', '=',user_id)], limit=1).id
        # salesperson_id  = vals['salesperson_id']

        salesperson_id  = self.env['property.salesperson.mapping'].search([('user_id', '=',user_id)], limit=1).user_id.id
        
        # _logger.info(f"=========CrmActivityReportCopy=====salesperson_id: {salesperson_id}")
        # _logger.info(f"=========CrmActivityReportCopy=====supervisor_id: {supervisor_id}")
        # _logger.info(f"=========CrmActivityReportCopy=====team_id: {team_id}")
        # _logger.info(f"=========CrmActivityReportCopy=====wing_id: {wing_id}")
        if salesperson_id:
            vals['salesperson_id'] = salesperson_id
            supervisor_id = self.env['property.salesperson.mapping'].search([('user_id', '=', salesperson_id)], limit=1).supervisor_id.id
            # _logger.info("--------------------------------supervisor_id")
            # _logger.info(supervisor_id)
            if supervisor_id:
                vals['supervisor_id'] = supervisor_id
                team_id = self.env['property.sales.team'].search([('supervisor_ids', 'in', supervisor_id)], limit=1).id
                # _logger.info("--------------------------------team_id")
                # _logger.info(team_id)
                if team_id:
                    vals['team_id'] = team_id
                    wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
                    # _logger.info("--------------------------------wing_id")
                    # _logger.info(wing_id)
                    if wing_id:
                        vals['wing_id'] = wing_id
        elif supervisor_id:
            vals['supervisor_id'] = supervisor_id
            team_id = self.env['property.sales.team'].search([('supervisor_ids', 'in', supervisor_id)], limit=1).id
            # _logger.info("--------------------------------team_id")
            # _logger.info(team_id)
            if team_id:
                vals['team_id'] = team_id
                wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
                # _logger.info("--------------------------------wing_id")
                # _logger.info(wing_id)
                if wing_id:
                    vals['wing_id'] = wing_id

        elif team_id:
            vals['team_id'] = team_id
            wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
            # _logger.info("--------------------------------wing_id")
            # _logger.info(wing_id)
            if wing_id:
                vals['wing_id'] = wing_id
        else:
            vals['wing_id'] = wing_id

        # _logger.info(f"=========CrmActivityReportCopy=====vals: {vals}")
        
        return super(CrmActivityReportCopy, self).create(vals)




    def _search(self, domain, offset=0, limit=None, order=None):
        """Override search to filter reservations based on user's role"""
        context = dict(self._context or {})
        context.update({
            'active_test': True,
            'force_active_test': True
        })
        
        self = self.with_context(context)
        
        if not context.get('my_team_activities_copy'):
            return super()._search(domain, offset=offset, limit=limit, order=order)
        
        user = self.env.user
        my_domain = self._get_domain_for_user_role(user)
        
        if domain:
            domain = expression.AND([domain, my_domain])
        else:
            domain = my_domain

        # _logger.info(f"=========CrmActivityReportCopy=====domain: {domain}")
        
        return super(CrmActivityReportCopy, self.with_context(context))._search(
            domain, offset=offset, limit=limit, order=order
        )

    def _get_domain_for_user_role(self, user):
        """Determine the search domain based on the user's role"""
        if self._is_wing_manager(user):
            # _logger.info("==============User is Wing Manager")
            # _logger.info(self._domain_for_wing_manager(user))
            return self._domain_for_wing_manager(user)
        elif self._is_team_manager(user):
            # _logger.info("==============User is Team Manager")
            # _logger.info(self._domain_for_team_manager(user))
            return self._domain_for_team_manager(user)
        elif self._is_supervisor(user):
            # _logger.info("==============User is Supervisor")
            # _logger.info(self._domain_for_supervisor(user))
            return self._domain_for_supervisor(user)
        else:
            # _logger.info("==============User is Salesperson")
            # _logger.info(self._domain_for_salesperson(user))
            return self._domain_for_salesperson(user)

    def _is_wing_manager(self, user):
        self.env.cr.execute("SELECT id FROM property_sales_wing WHERE manager_id = %s LIMIT 1", (user.id,))
        return self.env.cr.fetchone()

    def _domain_for_wing_manager(self, user):
        wing_id = self._is_wing_manager(user)[0]
        self.env.cr.execute("""
            SELECT t.id as team_id, s.id as supervisor_id, pm.user_id as salesperson_id
            FROM property_sales_wing w
            JOIN property_wing_team_rel wt ON w.id = wt.wing_id
            JOIN property_sales_team t ON t.id = wt.team_id
            LEFT JOIN property_team_supervisor_rel ts ON t.id = ts.team_id
            LEFT JOIN property_sales_supervisor s ON s.id = ts.supervisor_id
            LEFT JOIN property_salesperson_mapping pm ON pm.user_id = w.id 
            WHERE w.id = %s
        """, (wing_id,))
        results = self.env.cr.dictfetchall()
        team_ids = {r['team_id'] for r in results}
        supervisor_ids = {r['supervisor_id'] for r in results}
        user_ids = {r['salesperson_id'] for r in results}

        wing_user_id = self.env['property.sales.wing'].search([('id', '=', wing_id)]).manager_id.id
        # _logger.info(f"==============sales_team_id ID: {wing_user_id}")
        
        user_ids = list(set(user_ids))
        user_ids.append(wing_user_id)
        return ['|','|','|',('wing_id', '=', wing_id), ('team_id', 'in', list(team_ids)), ('supervisor_id', 'in', list(supervisor_ids)), ('salesperson_id', 'in', list(user_ids))]

    def _is_team_manager(self, user):
        self.env.cr.execute("SELECT id FROM property_sales_team WHERE manager_id = %s LIMIT 1", (user.id,))
        return self.env.cr.fetchone()

    def _domain_for_team_manager(self, user):
        team_id = self._is_team_manager(user)[0]
        # _logger.info(f"=======***=======Team ID: {team_id}")
        self.env.cr.execute("""
            SELECT s.id as supervisor_id, pm.user_id as salesperson_id
            FROM property_sales_team t
            LEFT JOIN property_team_supervisor_rel ts ON t.id = ts.team_id
            LEFT JOIN property_sales_supervisor s ON s.id = ts.supervisor_id
            LEFT JOIN property_salesperson_mapping pm ON pm.supervisor_id = s.id
            WHERE t.id = %s
        """, (team_id,))
        results = self.env.cr.dictfetchall()
        supervisor_ids = {r['supervisor_id'] for r in results}
        user_ids = {r['salesperson_id'] for r in results if r['salesperson_id'] != None}
        _logger.info(f"==============Supervisor IDs: {supervisor_ids}")
        _logger.info(f"==============User IDs: {user_ids}")
        sales_team_id = self.env['property.sales.team'].search([('id', '=', team_id)]).manager_id.id
        _logger.info(f"==============sales_team_id ID: {sales_team_id}")
        
        user_ids = list(set(user_ids))
        user_ids.append(sales_team_id)
        if  supervisor_ids != None and user_ids != None:
            return ['|','|', ('team_id', '=', team_id), ('supervisor_id', 'in', list(supervisor_ids)), ('salesperson_id', 'in', user_ids)]
        elif  user_ids != None:
            return [ ('salesperson_id', 'in', user_ids)]

    def _is_supervisor(self, user):
        self.env.cr.execute("SELECT id FROM property_sales_supervisor WHERE name = %s LIMIT 1", (user.id,))
        return self.env.cr.fetchone()

    def _domain_for_supervisor(self, user):
        supervisor_id = self._is_supervisor(user)[0]
        self.env.cr.execute("SELECT user_id FROM property_salesperson_mapping WHERE supervisor_id = %s", (supervisor_id,))
        user_ids = [r[0] for r in self.env.cr.fetchall()]
        # _logger.info(f"==============User IDs: {user_ids}")
        # user_ids.append(user.id)
        sup_id = self.env['property.sales.supervisor'].search([('id', '=', supervisor_id)]).name.id
        # _logger.info(f"==============Supervisor ID: {sup_id}")
        user_ids.append(sup_id)
        return ['|',('supervisor_id', '=', supervisor_id), ('salesperson_id', 'in', user_ids)]

    def _domain_for_salesperson(self, user):
        return [('salesperson_id', '=', user.id)]


class CrmActivityReport(models.Model):
    _inherit = 'crm.activity.report'



    def update_activity_report_copy(self):
        # Fetch current data from the view
        records = self.search([])
        # 

        # one_hour_ago = datetime.now() - timedelta(hours=1)
        one_hour_ago = fields.Datetime.now() - timedelta(hours=1)
        # _logger.info(f"============***==one_hour_ago: {one_hour_ago}")

        records = self.search([('date', '>=', one_hour_ago)])

        # records = self.search([('create_date', '>=', fields.Datetime.to_string(one_hour_ago))])
        # _logger.info(f"===@@@@@@@========NEW3=***=-------@@@@@@@-=records: {records}")
        copy_model = self.env['crm.activity.report.copy']
        for record in records:
            # Define a domain to search for existing records
            domain = [
                ('lead_id', '=', record.lead_id.id),
                ('date', '=', record.date),
                ('user_id', '=', record.user_id.id),
            ]
            existing_record = copy_model.search(domain, limit=1)
            


            if not existing_record:
                # Only create a new record if it does not exist
                copy_model.create({
                    'date': record.date,
                'lead_id': record.lead_id.id,
                'user_id': record.user_id.id,
                'salesperson_id': record.user_id.id,
                'stage_id': record.stage_id.id,
                'partner_id': record.partner_id.id,
                'lead_type': record.lead_type,
                'active': record.active,
                'tag_ids': [(6, 0, record.tag_ids.ids)],
                'mail_activity_type_id': record.mail_activity_type_id.id,
                })
            # else:
            #     # Optionally update the existing record if needed
            #     existing_record.write({
            #         'date': record.date,
            #         # Update other fields as necessary
            #     })



#             this is to delete old record and create a new one

                # domain = [
                #                 ('lead_id', '=', record.lead_id.id),
                #                 ('date', '=', record.date),
                #                 ('user_id', '=', record.user_id.id),
                #                 ('supervisor_id', '=', False),
                #             ]
                #             existing_record = copy_model.search(domain, limit=1)
                #             _logger.info(f"=====!!!!!=======***=--------=existing_record: {existing_record}")
                #             if existing_record:
                            
                                
                #                 # break


                # new_record = copy_model.create({
                #                     'date': existing_record.date,
                #                     'lead_id': existing_record.lead_id.id,
                #                     'user_id': existing_record.user_id.id,
                #                     'salesperson_id': existing_record.user_id.id,
                #                     'stage_id': existing_record.stage_id.id,
                #                     'partner_id': existing_record.partner_id.id,
                #                     'lead_type': existing_record.lead_type,
                #                     'active': existing_record.active,
                #                     'tag_ids': [(6, 0, existing_record.tag_ids.ids)],
                #                     'mail_activity_type_id': existing_record.mail_activity_type_id.id,
                #                 })

                #                 _logger.info(f"New record created===============: {new_record.id}")

                #                 existing_record.unlink()
    def copy_to_report_copy(self):
        activity_ids = self.env['crm.activity.report'].search([('id', '>', 0)])
        for activity_id in activity_ids:
            # Fetch the existing record
            # _logger.info(f"==============activity_id: {activity_id}")
            existing_record = activity_id
            if not existing_record:
                return False  # Record not found

        # Prepare the values to copy
            copy_vals = {
                'date': existing_record.date,
                'lead_id': existing_record.lead_id.id,
                'user_id': existing_record.user_id.id,
                'salesperson_id': existing_record.user_id.id,
                'stage_id': existing_record.stage_id.id,
                'partner_id': existing_record.partner_id.id,
                'lead_type': existing_record.lead_type,
                'active': existing_record.active,
                'tag_ids': [(6, 0, existing_record.tag_ids.ids)],
                'mail_activity_type_id': existing_record.mail_activity_type_id.id,
            }

            # Create a new record in crm.activity.report.copy with the copied values
            self.env['crm.activity.report.copy'].create(copy_vals)
        return True

    # @api.model
    # def create(self, vals):
    #     # Create the original record
    #     new_record = super(CrmActivityReport, self).create(vals)
    #     _logger.info(f"==============new_record: {new_record}")
    #     # Copy data to crm.activity.report.copy
    #     copy_vals = {
    #         'date': new_record.date,
    #         'lead_id': new_record.lead_id.id,
    #         'user_id': new_record.user_id.id,
    #         'salesperson_id': new_record.user_id.id,
    #         'stage_id': new_record.stage_id.id,
    #         'partner_id': new_record.partner_id.id,
    #         'lead_type': new_record.lead_type,
    #         'active': new_record.active,
    #         'tag_ids': [(6, 0, new_record.tag_ids.ids)],
    #         'mail_activity_type_id': new_record.mail_activity_type_id.id,
    #         # Add all other necessary fields
    #     }
    #     _logger.info(f"==============copy_vals: {copy_vals}")
    #     self.env['crm.activity.report.copy'].create(copy_vals)

    #     return new_record
#     # salesperson_id = fields.Many2one('res.users', string="Salesperson", compute="_compute_salesperson_ids",store=True)
    # supervisor_id = fields.Many2one('property.sales.supervisor', string="Sales Supervisor", readonly=True,store=True, compute="_compute_supervisor_ids")
    # team_id = fields.Many2one('property.sales.team', string="Sales Team", readonly=True,store=True, compute="_compute_team_ids" )
    # wing_id = fields.Many2one('property.sales.wing', string="Sales Wing", readonly=True,store=True, compute="_compute_wing_ids")


    # @api.depends('user_id')
    # def _compute_salesperson_id(self):
    #     user_id = self.env.user.id
    #     salesperson_id = self.env['property.salesperson.mapping'].search([('user_id', '=', user_id)], limit=1).id
    #     for record in self:
    #         record.salesperson_id = salesperson_id

    # @api.depends('salesperson_id')
    # def _compute_supervisor_id(self):
    #     for record in self:
    #         if record.salesperson_id:
    #             supervisor_id = self.env['property.salesperson.mapping'].search([('user_id', '=', record.salesperson_id)], limit=1).supervisor_id.id
    #             record.supervisor_id = supervisor_id

    # @api.depends('supervisor_id')
    # def _compute_team_id(self):
    #     for record in self:
    #         if record.supervisor_id:
    #             team_id = self.env['property.sales.team'].search([('supervisor_ids', 'in', record.supervisor_id)], limit=1).id
    #             record.team_id = team_id

    # @api.depends('team_id')
    # def _compute_wing_id(self):
    #     for record in self:
    #         if record.team_id:
    #             wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', record.team_id)], limit=1).id
    #             record.wing_id = wing_id


#     def _search(self, domain, offset=0, limit=None, order=None):
#         """Override search to filter reservations based on user's role"""
#         context = dict(self._context or {})
#         context.update({
#             'active_test': True,
#             'force_active_test': True
#         })
        
#         self = self.with_context(context)
        
#         if not context.get('my_team_activities'):
#             return super()._search(domain, offset=offset, limit=limit, order=order)
        
#         user = self.env.user
#         my_domain = self._get_domain_for_user_role(user)
        
#         if domain:
#             domain = expression.AND([domain, my_domain])
#         else:
#             domain = my_domain
        
#         return super(CrmActivityReport, self.with_context(context))._search(
#             domain, offset=offset, limit=limit, order=order
#         )

#     def _get_domain_for_user_role(self, user):
#         """Determine the search domain based on the user's role"""
#         if self._is_wing_manager(user):
#             _logger.info("==============User is Wing Manager")
#             _logger.info(self._domain_for_wing_manager(user))
#             return self._domain_for_wing_manager(user)
#         elif self._is_team_manager(user):
#             _logger.info("==============User is Team Manager")
#             _logger.info(self._domain_for_team_manager(user))
#             return self._domain_for_team_manager(user)
#         elif self._is_supervisor(user):
#             _logger.info("==============User is Supervisor")
#             _logger.info(self._domain_for_supervisor(user))
#             return self._domain_for_supervisor(user)
#         else:
#             _logger.info("==============User is Salesperson")
#             _logger.info(self._domain_for_salesperson(user))
#             return self._domain_for_salesperson(user)

#     def _is_wing_manager(self, user):
#         self.env.cr.execute("SELECT id FROM property_sales_wing WHERE manager_id = %s LIMIT 1", (user.id,))
#         return self.env.cr.fetchone()

#     def _domain_for_wing_manager(self, user):
#         wing_id = self._is_wing_manager(user)[0]
#         self.env.cr.execute("""
#             SELECT t.id as team_id, s.id as supervisor_id, pm.user_id as salesperson_id
#             FROM property_sales_wing w
#             JOIN property_wing_team_rel wt ON w.id = wt.wing_id
#             JOIN property_sales_team t ON t.id = wt.team_id
#             LEFT JOIN property_team_supervisor_rel ts ON t.id = ts.team_id
#             LEFT JOIN property_sales_supervisor s ON s.id = ts.supervisor_id
#             LEFT JOIN property_salesperson_mapping pm ON pm.user_id = w.id 
#             WHERE w.id = %s
#         """, (wing_id,))
#         results = self.env.cr.dictfetchall()
#         team_ids = {r['team_id'] for r in results}
#         supervisor_ids = {r['supervisor_id'] for r in results}
#         user_ids = {r['salesperson_id'] for r in results}

#         wing_user_id = self.env['property.sales.wing'].search([('id', '=', wing_id)]).manager_id.id
#         _logger.info(f"==============sales_team_id ID: {wing_user_id}")
        
#         user_ids = list(set(user_ids))
#         user_ids.append(wing_user_id)
#         return ['|','|','|',('wing_id', '=', wing_id), ('team_id', 'in', list(team_ids)), ('supervisor_id', 'in', list(supervisor_ids)), ('user_id', 'in', list(user_ids))]

#     def _is_team_manager(self, user):
#         self.env.cr.execute("SELECT id FROM property_sales_team WHERE manager_id = %s LIMIT 1", (user.id,))
#         return self.env.cr.fetchone()

#     def _domain_for_team_manager(self, user):
#         team_id = self._is_team_manager(user)[0]
#         _logger.info(f"=======***=======Team ID: {team_id}")
#         self.env.cr.execute("""
#             SELECT s.id as supervisor_id, pm.user_id as salesperson_id
#             FROM property_sales_team t
#             LEFT JOIN property_team_supervisor_rel ts ON t.id = ts.team_id
#             LEFT JOIN property_sales_supervisor s ON s.id = ts.supervisor_id
#             LEFT JOIN property_salesperson_mapping pm ON pm.supervisor_id = s.id
#             WHERE t.id = %s
#         """, (team_id,))
#         results = self.env.cr.dictfetchall()
#         supervisor_ids = {r['supervisor_id'] for r in results}
#         user_ids = {r['salesperson_id'] for r in results if r['salesperson_id'] != None}
#         _logger.info(f"==============Supervisor IDs: {supervisor_ids}")
#         _logger.info(f"==============User IDs: {user_ids}")
#         sales_team_id = self.env['property.sales.team'].search([('id', '=', team_id)]).manager_id.id
#         _logger.info(f"==============sales_team_id ID: {sales_team_id}")
        
#         user_ids = list(set(user_ids))
#         user_ids.append(sales_team_id)
#         if  supervisor_ids != None and user_ids != None:
#             return ['|','|', ('team_id', '=', team_id), ('supervisor_id', 'in', list(supervisor_ids)), ('user_id', 'in', user_ids)]
#         elif  user_ids != None:
#             return [ ('user_id', 'in', user_ids)]

#     def _is_supervisor(self, user):
#         self.env.cr.execute("SELECT id FROM property_sales_supervisor WHERE name = %s LIMIT 1", (user.id,))
#         return self.env.cr.fetchone()

#     def _domain_for_supervisor(self, user):
#         supervisor_id = self._is_supervisor(user)[0]
#         self.env.cr.execute("SELECT user_id FROM property_salesperson_mapping WHERE supervisor_id = %s", (supervisor_id,))
#         user_ids = [r[0] for r in self.env.cr.fetchall()]
#         _logger.info(f"==============User IDs: {user_ids}")
#         # user_ids.append(user.id)
#         sup_id = self.env['property.sales.supervisor'].search([('id', '=', supervisor_id)]).name.id
#         _logger.info(f"==============Supervisor ID: {sup_id}")
#         user_ids.append(sup_id)
#         return ['|',('supervisor_id', '=', supervisor_id), ('user_id', 'in', user_ids)]

#     def _domain_for_salesperson(self, user):
#         return [('user_id', '=', user.id)]
  
#     @api.depends('lead_id')
#     def _compute_salesperson_ids(self):
#         for rec in self:
#             # if rec.res_model_id.model == 'crm.lead':
#             #     res_ids_str = rec.res_ids.strip('[]')
#             #     res_ids_array = [int(x.strip()) for x in res_ids_str.split(',') if x.strip()]
#             #     first_id = res_ids_array[0] if res_ids_array else False
#             rec.salesperson_id = rec.lead_id.user_id.id
#             # else:
#             #     rec.salesperson_id = False
    

#     @api.depends('salesperson_id', 'supervisor_id')
#     def _compute_team_id(self):
#         for record in self:
#             team_id = False
#             if record.supervisor_id:
#                 # Find team through supervisor
#                 team = self.env['property.sales.team'].search(
#                     [('supervisor_ids', 'in', record.supervisor_id.id)], limit=1)
#                 team_id = team.id if team else False
#             elif record.user_id:
#                 # Check if salesperson is a team manager
#                 team = self.env['property.sales.team'].search(
#                     [('manager_id', '=', record.user_id.id)], limit=1)
#                 team_id = team.id if team else False
            
#             record.team_id = team_id

#     @api.depends('team_id')
#     def _compute_wing_id(self):
#         for record in self:
#             wing_id = False
#             if record.team_id:
#                 wing = self.env['property.sales.wing'].search(
#                     [('team_ids', 'in', record.team_id.id)], limit=1)
#                 wing_id = wing.id if wing else False
            
#             record.wing_id = wing_id

#     def create(self, vals):
#         _logger.info("--------------------****************------------create")
#         _logger.info(vals)
#         user_id = self.env.user.id
#         _logger.info("----------**************----------------------user_id")
#         _logger.info(user_id)
#         wing_id  = self.env['property.sales.wing'].search([('manager_id', '=',user_id)], limit=1).id
#         team_id  = self.env['property.sales.team'].search([('manager_id', '=',user_id)], limit=1).id
#         supervisor_id  = self.env['property.sales.supervisor'].search([('name', '=',user_id)], limit=1).id
#         salesperson_id  = self.env['property.salesperson.mapping'].search([('user_id', '=',user_id)], limit=1).id
        
#         if salesperson_id:
#             vals['salesperson_id'] = salesperson_id
#             supervisor_id = self.env['property.salesperson.mapping'].search([('user_id', '=', salesperson_id)], limit=1).supervisor_id.id
#             _logger.info("--------------------------------supervisor_id")
#             _logger.info(supervisor_id)
#             if supervisor_id:
#                 vals['supervisor_id'] = supervisor_id.id
#                 team_id = self.env['property.sales.team'].search([('supervisor_ids', 'in', supervisor_id)], limit=1).id
#                 _logger.info("--------------------------------team_id")
#                 _logger.info(team_id)
#                 if team_id:
#                     vals['team_id'] = team_id
#                     wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
#                     _logger.info("--------------------------------wing_id")
#                     _logger.info(wing_id)
#                     if wing_id:
#                         vals['wing_id'] = wing_id
#         elif supervisor_id:
#             vals['supervisor_id'] = supervisor_id
#             team_id = self.env['property.sales.team'].search([('supervisor_ids', 'in', supervisor_id)], limit=1).id
#             _logger.info("--------------------------------team_id")
#             _logger.info(team_id)
#             if team_id:
#                 vals['team_id'] = team_id
#                 wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
#                 _logger.info("--------------------------------wing_id")
#                 _logger.info(wing_id)
#                 if wing_id:
#                     vals['wing_id'] = wing_id

#         elif team_id:
#             vals['team_id'] = team_id
#             wing_id = self.env['property.sales.wing'].search([('team_ids', 'in', team_id)], limit=1).id
#             _logger.info("--------------------------------wing_id")
#             _logger.info(wing_id)
#             if wing_id:
#                 vals['wing_id'] = wing_id
#         else:
#             vals['wing_id'] = wing_id

        
        
#         return super(CrmActivityReport, self).create(vals)



