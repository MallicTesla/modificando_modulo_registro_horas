# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    billable_hours = fields.Float(string='Horas Dedicadas', default=0.0)

    @api.model
    def create(self, vals):
        # Sincronizar el valor de billable_hours al campo unit_amount (Horas Utilizado)
        if 'billable_hours' in vals:
            vals['unit_amount'] = vals['billable_hours']

        # Validar permisos
        if not self.env.user.has_group('timesheet_billable.edit_billable_hours'):
            vals.pop('billable_hours', None)  # Quitar si no tiene permisos

        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        if self.env.context.get('prevent_recursion'):
            return super(AccountAnalyticLine, self).write(vals)

        user_can_change_billable_hours = self.env.user.has_group('timesheet_billable.edit_billable_hours')

        if 'billable_hours' in vals:
            vals['unit_amount'] = vals['billable_hours']

        if 'billable_hours' in vals and not user_can_change_billable_hours:
            vals['billable_hours'] = self.billable_hours

        # Pasar un contexto para evitar recursión
        res = super(AccountAnalyticLine, self.with_context(prevent_recursion=True)).write(vals)

        if 'billable_hours' in vals and self.filtered(lambda rec: rec.so_line):
            self._update_so_line_qty_delivered()

        return res


    def _update_so_line_qty_delivered(self):
        """
        Actualiza la cantidad entregada (`qty_delivered`) de las líneas de ventas (`so_line`)
        asociadas a los registros actuales.
        """
        for line in self.filtered(lambda rec: rec.so_line):
            # Buscar líneas relacionadas y obtener `billable_hours`
            related_lines = self.search([('so_line', '=', line.so_line.id)])
            total_billable_hours = sum(related_lines.mapped('billable_hours'))
            # Actualizar la cantidad entregada
            line.so_line.sudo().write({'qty_delivered': total_billable_hours})

