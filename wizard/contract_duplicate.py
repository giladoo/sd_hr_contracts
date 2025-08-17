from odoo import models, fields, api, _
import json

from odoo.exceptions import ValidationError
from icecream import ic

class SdHrContractDuplacate(models.TransientModel):
    _name = 'sd_hr_contracts.duplicate'
    # _rec_name = 'employee_id'

    name = fields.Char()
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    representative = fields.Many2one('hr.employee')
    contract_type_id = fields.Many2one('hr.contract.type')
    doc_template = fields.Many2one('hr.contract.doc_template')

    convert_state = fields.Selection([('draft', 'Draft'),
                                      ('close', 'Close'),
                                      ('cancel', 'Cancel')],
                                     default='close', required=True)

    def duplicate_selected_contract(self):
        context = self.env.context
        active_ids = context.get('active_ids', [])
        contracts = self.env['hr.contract'].browse(active_ids)
        for record in contracts:
            if record.state in ['draft', 'open']:
                record.write({'state': self.convert_state})
            record.copy({'issue_date': self.start_date,
                         'date_start': self.start_date,
                         'date_end': self.end_date,
                         'representative': self.representative.id if self.representative else False,
                         'contract_type_id': self.contract_type_id.id if self.contract_type_id else record.contract_type_id.id,
                         'doc_template': self.doc_template.id if self.contract_type_id and self.doc_template else record.doc_template.id,
                         })

        # print(f">>>>>>>>>>>>>\n context:{context} \n start_date: {self.start_date}    end_date: {self.end_date}")


    # # @api.onchange('documents')
    # @api.onchange('employee_id')
    # def _documents_count(self):
    #     documents_model = self.env['sd_hr_documents.attachments']
    #     relatives_model = self.env['sd_hr_relatives.members']
    #     domain = [('employee_id', '=', self.employee_id.id)]
    #
    #     self.documents = documents_model.search(domain)
    #     self.documents_count = documents_model.sudo().search_count(domain)
    #     self.relatives = relatives_model.search(domain)
    #
    # @api.depends('relatives')
    # def _compute_helper_field(self):
    #     print(f"\n RELATIVES documents: {self.documents}")
    #     self.helper_field = not self.helper_field
    #     documents_model = self.env['sd_hr_documents.attachments']
    #     domain = [('employee_id', '=', self.employee_id.id)]
    #     #
    #     # self.documents = documents_model.search(domain)
    #     self.documents_count = documents_model.sudo().search_count(domain)
    #
    # def employee_action_view(self):
    #     if self.employee_id:
    #         view_id = self.env.ref('hr.view_employee_form').sudo().read()[0]
    #         domain = []
    #         context = {}
    #         return {
    #             'name': _('Documents'),
    #             'domain': domain,
    #             'res_model': 'hr.employee',
    #             'type': 'ir.actions.act_window',
    #             'res_id': self.employee_id.id,
    #             'view_id': False,
    #             'view_mode': 'form',
    #             'context': context
    #         }
    #     else:
    #         return {}


    def employee_action_document_view(self):
        action =False
        return action

