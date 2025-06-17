# -*- coding: utf-8 -*-
"""
Lead-Analysis PDF Wizard – v2.1
Odoo 17  © 2025
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class LeadAnalysisWizard(models.TransientModel):
    _name = "lead.analysis.wizard"
    _description = "Lead Analysis Report Wizard"

    date_from = fields.Date(
        string="From",
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )
    date_to = fields.Date(
        string="To",
        required=True,
        default=lambda self: fields.Date.context_today(self),
    )
    report_by = fields.Selection(
        selection='_get_report_by_selection',
        string='Report By',
        required=True,
    )
    wing_id = fields.Selection(
        selection='_get_wing_selection',
        string='Wing',
        required=True,
    )

    @api.onchange('report_by')
    def _onchange_report_by(self):
        pass

    @api.model
    def _get_report_by_selection(self):
        user = self.env.user
        if user.has_group('custom_report_wizard.lead_analysis_report'):
            return [
                ('wing', 'Wing'),
                ('supervisor', 'Supervisor'),
                ('salesperson', 'Salesperson'),
            ]
        elif user.has_group('temer_structure.access_property_sales_supervisor_group'):
            return [
                ('supervisor', 'Supervisor'),
                ('salesperson', 'Salesperson'),
            ]
        else:
            return []
        
    @api.model
    def _get_wing_selection(self):
        """
        Dynamically show wings based on user group access.
        """
        user = self.env.user
        wings = []
        # Always add No Wing if allowed
        if user.has_group('custom_report_wizard.group_no_wing_access'):
            wings.append(('no_wing', 'No Wing'))
        # Fetch from DB
        self.env.cr.execute("SELECT id, name FROM property_sales_wing ORDER BY name")
        for w_id, w_name in self.env.cr.fetchall():
            name_lower = w_name.strip().lower()
            # Match against lowercase strings!
            if name_lower == "team - ajwa" and user.has_group('custom_report_wizard.group_team_ajwa_access'):
                wings.append((str(w_id), w_name))
            if name_lower == "team - taj" and user.has_group('custom_report_wizard.group_team_taj_access'):
                wings.append((str(w_id), w_name))
            if name_lower == "team - raha" and user.has_group('custom_report_wizard.group_team_Raha_access'):
                wings.append((str(w_id), w_name))
        return wings


    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        selection = self._get_report_by_selection()
        if selection:
            res['report_by'] = selection[0][0]
        return res

    def _validate(self):
        self.ensure_one()
        allowed = [x[0] for x in self._get_report_by_selection()]
        if self.report_by not in allowed:
            raise UserError(_("You are not allowed to select this report type."))
        if self.date_from > self.date_to:
            raise UserError(_("`From` date must be before `To` date."))
        if not self.wing_id:
            raise UserError(_("Please select a Wing to view its analysis."))
    
    def _fetch_raw(self):
        self.ensure_one()
        self._validate()

        wing_condition = ""
        params = [self.date_from]

        # Handle 'No Wing' selection
        if self.wing_id:
            if self.wing_id == 'no_wing':
                wing_condition = " AND cl.wing_id IS NULL"
            else:
                wing_condition = " AND cl.wing_id = %s"
                params.append(int(self.wing_id))

        query = f"""
                WITH filtered_leads AS (
                    SELECT cl.id, cl.stage_id, cl.user_id, cl.supervisor_id, cl.wing_id
                    FROM crm_lead cl
                    WHERE cl.create_date >= %s {wing_condition}
                ),
                lead_events AS (
                    SELECT
                        fl.id AS lead_id,
                        rp.name AS sales_person,
                        rp_sup.name AS supervisor_name,
                        rp_wing.name AS wing_manager_name,
                        COALESCE(psw.name, 'No Wing') AS wing_name,
                        CASE 
                            WHEN stage.name::jsonb ->> 'en_US' ILIKE '%%expired%%' THEN 'Expired'
                            WHEN stage.name::jsonb ->> 'en_US' ILIKE '%%reservation%%' THEN 'Reservation'
                            WHEN stage.name::jsonb ->> 'en_US' ILIKE '%%follow%%' THEN 'Follow Up'
                            WHEN stage.name::jsonb ->> 'en_US' ILIKE '%%prospect%%' THEN 'Prospect'
                            WHEN stage.name::jsonb ->> 'en_US' ILIKE '%%lost%%' THEN 'Lost'
                            ELSE NULL
                        END AS event_type
                    FROM filtered_leads fl
                    JOIN crm_stage stage ON fl.stage_id = stage.id
                    JOIN res_users ru ON fl.user_id = ru.id
                    JOIN res_partner rp ON ru.partner_id = rp.id
                    JOIN property_sales_supervisor pss ON fl.supervisor_id = pss.id
                    JOIN res_users ru_sup ON pss.name = ru_sup.id
                    JOIN res_partner rp_sup ON ru_sup.partner_id = rp_sup.id
                    LEFT JOIN property_sales_wing psw ON fl.wing_id = psw.id
                    LEFT JOIN res_users ru_wing ON psw.manager_id = ru_wing.id
                    LEFT JOIN res_partner rp_wing ON ru_wing.partner_id = rp_wing.id
                ),
                activity_events AS (
                    SELECT 
                        cl.id AS lead_id,
                        rp.name AS sales_person,
                        rp_sup.name AS supervisor_name,
                        rp_wing.name AS wing_manager_name,
                        COALESCE(psw.name, 'No Wing') AS wing_name,
                        CASE 
                            WHEN mtv.new_value_char = 'Lost' THEN 'Lost'
                            ELSE NULL
                        END AS event_type
                    FROM crm_lead cl
                    JOIN filtered_leads fl ON cl.id = fl.id
                    JOIN res_users ru ON cl.user_id = ru.id
                    JOIN res_partner rp ON ru.partner_id = rp.id
                    JOIN mail_message mm ON mm.model = 'crm.lead' AND mm.res_id = cl.id
                    LEFT JOIN mail_tracking_value mtv ON mm.id = mtv.mail_message_id
                    JOIN property_sales_supervisor pss ON cl.supervisor_id = pss.id
                    JOIN res_users ru_sup ON pss.name = ru_sup.id
                    JOIN res_partner rp_sup ON ru_sup.partner_id = rp_sup.id
                    LEFT JOIN property_sales_wing psw ON cl.wing_id = psw.id
                    LEFT JOIN res_users ru_wing ON psw.manager_id = ru_wing.id
                    LEFT JOIN res_partner rp_wing ON ru_wing.partner_id = rp_wing.id
                    WHERE 
                        TRIM(BOTH FROM LOWER(COALESCE(mtv.old_value_char, ''))) <> 'sales'
                        AND mm.subtype_id <> 5
                ),
                unioned_events AS (
                    SELECT * FROM lead_events
                    UNION ALL
                    SELECT * FROM activity_events
                ),
                event_counts AS (
                    SELECT 
                        wing_name,
                        wing_manager_name,
                        supervisor_name,
                        sales_person,
                        event_type,
                        COUNT(*) AS count
                    FROM unioned_events
                    WHERE event_type IS NOT NULL
                    GROUP BY wing_name, wing_manager_name, supervisor_name, sales_person, event_type
                ),
                reservation_summary AS (
                    SELECT 
                        rp.name AS sales_person,
                        rp_sup.name AS supervisor_name,
                        rp_wing.name AS wing_manager_name,
                        COALESCE(psw.name, 'No Wing') AS wing_name,
                        COUNT(pr.id) AS reservation_count,
                        SUM(CASE WHEN pr.status = 'sold' THEN 1 ELSE 0 END) AS sold_reservation_count
                    FROM property_reservation pr
                    JOIN crm_lead cl ON pr.crm_lead_id = cl.id
                    JOIN res_users ru ON cl.user_id = ru.id
                    JOIN res_partner rp ON ru.partner_id = rp.id
                    JOIN property_sales_supervisor pss ON cl.supervisor_id = pss.id
                    JOIN res_users ru_sup ON pss.name = ru_sup.id
                    JOIN res_partner rp_sup ON ru_sup.partner_id = rp_sup.id
                    LEFT JOIN property_sales_wing psw ON cl.wing_id = psw.id
                    LEFT JOIN res_users ru_wing ON psw.manager_id = ru_wing.id
                    LEFT JOIN res_partner rp_wing ON ru_wing.partner_id = rp_wing.id
                    WHERE cl.create_date >= %s {wing_condition}
                    GROUP BY wing_name, wing_manager_name, supervisor_name, sales_person
                )
                SELECT
                    COALESCE(ec.wing_name, rs.wing_name, 'No Wing') AS wing_name,
                    COALESCE(ec.wing_manager_name, rs.wing_manager_name) AS wing_manager_name,
                    COALESCE(ec.supervisor_name, rs.supervisor_name) AS supervisor_name,
                    COALESCE(ec.sales_person, rs.sales_person) AS sales_person,
                    COALESCE(MAX(CASE WHEN ec.event_type = 'Prospect' THEN ec.count END), 0) AS prospect,
                    COALESCE(MAX(CASE WHEN ec.event_type = 'Follow Up' THEN ec.count END), 0) AS follow_up,
                    COALESCE(MAX(rs.reservation_count), 0) AS reservation_count,
                    COALESCE(MAX(rs.sold_reservation_count), 0) AS sold_reservation_count,
                    COALESCE(MAX(CASE WHEN ec.event_type = 'Expired' THEN ec.count END), 0) AS expired,
                    COALESCE(MAX(CASE WHEN ec.event_type = 'Lost' THEN ec.count END), 0) AS lost,
                    (COALESCE(MAX(CASE WHEN ec.event_type = 'Prospect' THEN ec.count END), 0) + 
                    COALESCE(MAX(CASE WHEN ec.event_type = 'Follow Up' THEN ec.count END), 0) +
                    COALESCE(MAX(rs.reservation_count), 0) + 
                    COALESCE(MAX(rs.sold_reservation_count), 0) + 
                    COALESCE(MAX(CASE WHEN ec.event_type = 'Expired' THEN ec.count END), 0) +
                    COALESCE(MAX(CASE WHEN ec.event_type = 'Lost' THEN ec.count END), 0)) AS total,
                    CASE 
                        WHEN COALESCE(ec.wing_name, rs.wing_name, 'No Wing') = 'No Wing' AND COALESCE(ec.wing_manager_name, rs.wing_manager_name) IS NOT NULL THEN '🟡 Missing wing_name'
                        ELSE '✅ OK'
                    END AS data_flag
                FROM event_counts ec
                FULL OUTER JOIN reservation_summary rs 
                    ON ec.sales_person = rs.sales_person
                    AND ec.supervisor_name = rs.supervisor_name
                    AND ec.wing_name = rs.wing_name
                    AND ec.wing_manager_name = rs.wing_manager_name
                GROUP BY 
                    COALESCE(ec.wing_name, rs.wing_name, 'No Wing'),
                    COALESCE(ec.wing_manager_name, rs.wing_manager_name),
                    COALESCE(ec.supervisor_name, rs.supervisor_name),
                    COALESCE(ec.sales_person, rs.sales_person)
                ORDER BY 
                    COALESCE(ec.wing_name, rs.wing_name, 'No Wing'),
                    COALESCE(ec.wing_manager_name, rs.wing_manager_name),
                    COALESCE(ec.supervisor_name, rs.supervisor_name),
                    COALESCE(ec.sales_person, rs.sales_person);
            """
        params.append(self.date_from)
        # Only add the wing_id if it's not 'no_wing'
        if wing_condition.endswith("= %s"):
            params.append(int(self.wing_id))
        self.env.cr.execute(query, tuple(params))
        return self.env.cr.fetchall()



    def action_print(self):
        self._validate()
        rows_raw = self._fetch_raw()
        rows = []
        totals = {
            "prospect": 0,
            "follow_up": 0,
            "reservation_count": 0,
            "sold_reservation_count": 0,
            "expired": 0,
            "lost": 0,
            "total": 0,
        }
        all_fields = ['wing_name', 'wing_manager_name', 'supervisor_name', 'sales_person']
        if self.report_by == 'wing':
            group_fields = ['wing_name', 'wing_manager_name']
        elif self.report_by == 'supervisor':
            group_fields = ['wing_name', 'wing_manager_name', 'supervisor_name']
        else:
            group_fields = ['wing_name', 'wing_manager_name', 'supervisor_name', 'sales_person']

        grouped = {}
        for row in rows_raw:
            row_dict = {
                "wing_name": row[0] or '',
                "wing_manager_name": row[1] or '',
                "supervisor_name": row[2] or '',
                "sales_person": row[3] or '',
                "prospect": int(row[4] or 0),
                "follow_up": int(row[5] or 0),
                "reservation_count": int(row[6] or 0),
                "sold_reservation_count": int(row[7] or 0),
                "expired": int(row[8] or 0),  
                "lost": int(row[9] or 0),
                "total": int(row[10] or 0),
                "data_flag": row[11],
            }
            totals["prospect"] += row_dict["prospect"]
            totals["follow_up"] += row_dict["follow_up"]
            totals["reservation_count"] += row_dict["reservation_count"]
            totals["sold_reservation_count"] += row_dict["sold_reservation_count"]
            totals["expired"] += row_dict["expired"]
            totals["lost"] += row_dict["lost"]
            totals["total"] += row_dict["total"]
            key = tuple(row_dict[field] for field in group_fields)
            if key in grouped:
                grouped[key]["prospect"] += row_dict["prospect"]
                grouped[key]["follow_up"] += row_dict["follow_up"]
                grouped[key]["reservation_count"] += row_dict["reservation_count"]
                grouped[key]["sold_reservation_count"] += row_dict["sold_reservation_count"]
                grouped[key]["expired"] += row_dict["expired"]
                grouped[key]["lost"] += row_dict["lost"]
                grouped[key]["total"] += row_dict["total"]
            else:
                grouped[key] = {f: row_dict[f] for f in all_fields}
                grouped[key].update({
                    "prospect": row_dict["prospect"],
                    "follow_up": row_dict["follow_up"],
                    "reservation_count": row_dict["reservation_count"],
                    "sold_reservation_count": row_dict["sold_reservation_count"],
                    "expired": row_dict["expired"],
                    "lost": row_dict["lost"],
                    "total": row_dict["total"],
                    "data_flag": row_dict["data_flag"],
                })
                for unused in set(all_fields) - set(group_fields):
                    if unused not in grouped[key]:
                        grouped[key][unused] = ''
        rows = list(grouped.values())

        wing_dict = dict(self._get_wing_selection())
        selected_wing_name = wing_dict.get(self.wing_id, '') if self.wing_id else ''

        data = {
            "rows": rows,
            "totals": totals,
            "date_from": str(self.date_from),
            "date_to": str(self.date_to),
            "report_by": self.report_by,
            "wing_name": selected_wing_name,
        }
        return self.env.ref('custom_report_wizard.lead_analysis_pdf').report_action(self, data=data)