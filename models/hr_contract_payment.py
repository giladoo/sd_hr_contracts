# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging


class SdHrContractsPayment(models.Model):
    _name = 'sd_hr_contracts.payment'
    _description = 'Payment'
    _rec_name = 'payment_type'

    contract_id = fields.Many2one('hr.contract', default=lambda self: self.env.context.get('id', False))
    amount = fields.Integer(tracking=True)
    payment_type = fields.Many2one('sd_hr_contracts.payment_type')
    sequence = fields.Integer(default=100)


class SdHrContractsPaymentType(models.Model):
    _name = 'sd_hr_contracts.payment_type'
    _description = 'Payment Type'

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=100)