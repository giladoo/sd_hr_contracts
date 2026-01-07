# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging


class SdHrdocumentsEmployee(models.Model):
    _inherit = 'hr.employee'

    contract_info = fields.Many2one('sd_hr_contracts.contract_info')

    def update_contract_info(self):
        # print(f">>>>>>>>>>>> emp_no_contract_info: {len(self)}")
        contract_model = self.env['hr.contract']
        contract_info_model = self.env['sd_hr_contracts.contract_info']
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for emp in self:
            if not emp.contract_info:
                employee_url = f'=HYPERLINK("{base_url}/web/login?redirect=/web#model=hr.employee&view_type=form&id={emp.id}","{emp.name}")'
                contract_info = contract_info_model.create({
                    'employee_id': emp.id,
                    'employee_link': employee_url,
                })
                emp.contract_info = contract_info.id
            contract_model.active_contract(emp.contract_info)

    # @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        contract_model = self.env['hr.contract']
        contract_info_model = self.env['sd_hr_contracts.contract_info']
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        employee_url = f'=HYPERLINK("{base_url}/web/login?redirect=/web#model=hr.employee&view_type=form&id={res.id}","{res["name"]}")'
        contract_info = contract_info_model.create({
            'employee_id': res.id,
            'employee_link': employee_url,
        })
        res['contract_info'] = contract_info.id
        # emp_no_contract_info = self.search([('contract_info', '=', False)])
        # # emp_no_contract_info = self.search([('contract_info', '=', False)])
        # print(f">>>>>>>>>>>> emp_no_contract_info: {len(emp_no_contract_info)}")
        # for emp in emp_no_contract_info:
        #     employee_url = f'=HYPERLINK("{base_url}/web/login?redirect=/web#model=hr.employee&view_type=form&id={emp.id}","{emp.name}")'
        #     contract_info = contract_info_model.create({
        #         'employee_id': emp.id,
        #         'employee_link': employee_url,
        #     })
        #
        #     emp.write({'contract_info': contract_info.id})
        #     contract_model.active_contract(contract_info)
        return res

    def write(self, vals):
        if vals.get('name', False):
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            employee_url = f'=HYPERLINK("{base_url}/web/login?redirect=/web#model=hr.employee&view_type=form&id={self.id}","{vals.get("name")}")'
            self.contract_info.write({'employee_link': employee_url, })
        return super().write(vals)

