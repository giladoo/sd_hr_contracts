# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging


class SdHrContractsEmployee(models.Model):
    _inherit = 'hr.employee'

    first_contract = fields.Date()

