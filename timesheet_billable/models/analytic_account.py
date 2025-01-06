# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.osv import expression


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    # Cambiar etiqueta del campo para reflejar el cambio a "Horas Dedicadas"
    billable_hours = fields.Float(string='Horas Dedicadas', default=0.0)

    @api.model
    def create(self, vals):
        # Sincronizar el valor de billable_hours al campo unit_amount (Horas Facturables)
        if vals.get('billable_hours', 0.0):
            if self.env.user.has_group('timesheet_billable.edit_billable_hours'):
                billable_hours = vals.get('billable_hours', 0.0)
                vals['unit_amount'] = billable_hours  # Copiar valor a unit_amount

        if vals.get('unit_amount', False) and not vals.get('billable_hours', False):
            unit_amount = vals.get('unit_amount', 0.0)
            vals['billable_hours'] = unit_amount  # Sincronizar valores si no está definido billable_hours

        elif vals.get('unit_amount', False) and vals.get('billable_hours', False) and not self.env.user.has_group(
                'timesheet_billable.edit_billable_hours'):
            unit_amount = vals.get('unit_amount', 0.0)
            vals['billable_hours'] = unit_amount  # Mantener consistencia de valores

        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        user_can_change_billable_hours = self.env.user.has_group('timesheet_billable.edit_billable_hours')
        if vals.get('billable_hours', 0.0):
            if user_can_change_billable_hours:
                billable_hours = vals.get('billable_hours', 0.0)
                vals['unit_amount'] = billable_hours  # Copiar valor a unit_amount
            else:
                vals['billable_hours'] = self.billable_hours  # Preservar valor original si no tiene permiso

        if vals.get('unit_amount', False):
            unit_amount = vals.get('unit_amount', 0.0)
            vals['billable_hours'] = unit_amount  # Sincronizar valores

        res = super(AccountAnalyticLine, self).write(vals)

        # Actualizar qty_delivered basado en billable_hours si es necesario
        if user_can_change_billable_hours and vals.get('billable_hours', 0.0) and self.so_line:
            to_sum = self.search_read([('so_line', '=', self.so_line.id)], fields=['billable_hours'])
            self.so_line.qty_delivered = sum(billable_hours['billable_hours'] for billable_hours in to_sum)
        return res
