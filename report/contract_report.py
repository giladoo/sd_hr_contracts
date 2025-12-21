# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from icecream import ic

class SdContractReport(models.AbstractModel):
    _name = 'report.sd_hr_contracts.contract_report_template'
    _description = 'Generate Contract reprot.'

    @api.model
    def _get_report_values(self, docids, data=None):
        print(f">>>>>>>>>>>>\n{docids}\n>>>>>>>>>>")
        hr_contract = self.env['hr.contract']
        hr_employee = self.env['hr.employee']
        contracts = hr_contract.browse(docids)
        contracts_group = contracts.grouped('employee_id')
        ic(contracts_group)
        # TODO: 

        for contract in contracts:
            print(contract)


        return {
            'doc_ids' : docids,
            # 'doc_model' : self.env['res.company'],
            # 'data' : data,
            # 'docs' : self.env['res.company'].browse(self.env.company.id),
        }
