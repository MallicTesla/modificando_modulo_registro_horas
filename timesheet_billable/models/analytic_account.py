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
        # Sincronizar el valor de billable_hours al campo unit_amount (Horas Utilizado)
        if 'billable_hours' in vals:
            vals['unit_amount'] = vals['billable_hours']  # Copiar valor a unit_amount
        
        # Mantener comportamiento original para permisos
        if 'billable_hours' in vals:
            if self.env.user.has_group('timesheet_billable.edit_billable_hours'):
                billable_hours = vals.get('billable_hours', 0.0)
                vals['billable_hours'] = billable_hours

        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        user_can_change_billable_hours = self.env.user.has_group('timesheet_billable.edit_billable_hours')

        # Si se modifica "billable_hours", actualizar "unit_amount"
        if 'billable_hours' in vals:
            vals['unit_amount'] = vals['billable_hours']  # Sincronizar unidireccional: billable_hours → unit_amount

        # Evitar que "unit_amount" modifique "billable_hours"
        if 'unit_amount' in vals and 'billable_hours' not in vals:
            vals['billable_hours'] = self.billable_hours  # Mantener el valor original de billable_hours

        # Mantener comportamiento original de permisos
        if 'billable_hours' in vals and not user_can_change_billable_hours:
            vals['billable_hours'] = self.billable_hours  # Preservar valor original si no tiene permiso

        res = super(AccountAnalyticLine, self).write(vals)

        # Actualizar qty_delivered basado en billable_hours si es necesario
        if user_can_change_billable_hours and 'billable_hours' in vals and self.so_line:
            to_sum = self.search_read([('so_line', '=', self.so_line.id)], fields=['billable_hours'])
            self.so_line.qty_delivered = sum(billable_hours['billable_hours'] for billable_hours in to_sum)

        return res
