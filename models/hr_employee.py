# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging


class SdHrdocumentsEmployee(models.Model):
    _inherit = 'hr.employee'

    document_ids = fields.One2many('sd_hr_contracts.attachments',
                                   'employee_id',
                                   string="documents")


    document_count = fields.Integer(compute='_compute_document_count',
                                    string='documents',
                                    help='Count of documents.')

    def _compute_document_count(self):
        for rec in self:
            rec.document_count = len(rec.document_ids)


    def action_document_view(self):
        self.ensure_one()
        context = dict(self.env.context)
        context['default_employee_id'] = self.id
        domain = [('employee_id', '=', self.id)]
        # return {}
        return {
            'name': _('documents'),
            'domain': domain,
            'res_model': 'sd_hr_contracts.attachments',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'context': context,
        }


    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        documents = self.create_documents(res.id, False)
        if not documents:
            logging.error(f"Default documents for new employee failed, res_id: {res.id}")
        return res

    def create_documents(self, employee_id, res_id):
        documents_model = self.env['sd_hr_contracts.attachments']
        auto_create = self.env['sd_hr_contracts.document_type'].search([('auto_create', '=', True)])
        try:
            for rec in auto_create:
                documents_model.create({
                    'employee_id': employee_id,
                    'relative_id': res_id,
                    'document_type': rec.id,
                    'name': rec.name,
                })
            done = True
        except Exception as e:
            done = False

        return done