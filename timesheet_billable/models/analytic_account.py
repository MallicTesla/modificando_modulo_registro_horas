# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    billable_hours = fields.Float(string='Horas Dedicadas', default=0.0)

    @api.model
    def create(self, vals):
        """
        Sobrescribe el método create para sincronizar 'billable_hours' con 'unit_amount' 
        y validar permisos antes de crear el registro.
        """
        # Sincronizar el valor de 'billable_hours' con 'unit_amount'
        if 'billable_hours' in vals:
            vals['unit_amount'] = vals['billable_hours']

        # Validar si el usuario tiene permisos para editar 'billable_hours'
        if not self.env.user.has_group('timesheet_billable.edit_billable_hours'):
            # Si no tiene permisos, eliminar 'billable_hours' de los valores
            vals.pop('billable_hours', None)

        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        """
        Sobrescribe el método write para sincronizar campos y actualizar líneas de ventas asociadas.
        """
        # Evitar recursión al actualizar el registro
        if self.env.context.get('prevent_recursion'):
            return super(AccountAnalyticLine, self).write(vals)

        # Sincronizar 'billable_hours' con 'unit_amount' si se incluye en los valores
        if 'billable_hours' in vals and vals['billable_hours'] != 0.0:
            vals['unit_amount'] = vals['billable_hours']

        # Actualizar el registro con los valores proporcionados
        res = super(AccountAnalyticLine, self.with_context(prevent_recursion=True)).write(vals)

        # Actualizar 'qty_delivered' en líneas de ventas relacionadas si es necesario
        if 'billable_hours' in vals and self.filtered(lambda rec: rec.so_line):
            self._update_so_line_qty_delivered()

        return res

    def _update_so_line_qty_delivered(self):
        """
        Actualiza la cantidad entregada ('qty_delivered') de las líneas de ventas ('so_line') 
        asociadas a los registros actuales, basándose en el total de 'billable_hours'.
        """
        for line in self.filtered(lambda rec: rec.so_line):
            # Buscar todas las líneas relacionadas con la misma línea de venta
            related_lines = self.search([('so_line', '=', line.so_line.id)])
            # Calcular la suma total de 'billable_hours'
            total_billable_hours = sum(related_lines.mapped('billable_hours'))
            # Actualizar 'qty_delivered' en la línea de venta asociada
            line.so_line.sudo().write({'qty_delivered': total_billable_hours})