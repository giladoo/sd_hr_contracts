from odoo import models, fields, api, _
from odoo.fields import Boolean


class SdHrContractsContractInfo(models.Model):
    _name = "sd_hr_contracts.contract_info"
    _description = "sd_hr_contracts.contract_info"


    employee_id = fields.Many2one("hr.employee")
    employee_link = fields.Char()
    contract_link = fields.Char()
    state = fields.Char()
    is_valid = fields.Char()
    date_end = fields.Date()





