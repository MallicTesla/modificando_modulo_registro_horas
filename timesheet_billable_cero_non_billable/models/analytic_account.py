# -*- coding: utf-8 -*-
from odoo import models, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model
    def create(self, vals):
        """
        Respeta los valores ingresados para billable_hours y unit_amount al crear.
        """
        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        """
        Respeta los valores ingresados para billable_hours y unit_amount al actualizar.
        """
        return super(AccountAnalyticLine, self).write(vals)
