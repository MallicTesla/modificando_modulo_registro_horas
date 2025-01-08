# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    billable_hours = fields.Float(string='Horas Dedicadas', default=0.0)

    @api.model
    def create(self, vals):
        # Print inicial de valores
        print(f"[CREATE] Valores iniciales: {vals}")

        # Sincronizar el valor de billable_hours al campo unit_amount (Horas Utilizado)
        if 'billable_hours' in vals:
            vals['unit_amount'] = vals['billable_hours']
            print(f"[CREATE] Sincronizando: billable_hours={vals['billable_hours']} -> unit_amount={vals['unit_amount']}")

        # Validar permisos
        if not self.env.user.has_group('timesheet_billable.edit_billable_hours'):
            print(f"[CREATE] Usuario sin permisos para editar billable_hours. Removiendo campo.")
            vals.pop('billable_hours', None)  # Quitar si no tiene permisos

        # Print final de valores antes de crear el registro
        print(f"[CREATE] Valores finales antes de crear: {vals}")
        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        print(f"[WRITE] Valores iniciales: {vals}")
        print(f"[WRITE] Valores actuales antes de modificar: billable_hours={self.billable_hours}, unit_amount={self.unit_amount}")

        if self.env.context.get('prevent_recursion'):
            print("[WRITE] Contexto de recursión detectado. Saltando lógica personalizada.")
            return super(AccountAnalyticLine, self).write(vals)

        # Validar si se debe sincronizar
        if 'billable_hours' in vals:
            if vals['billable_hours'] != 0.0:  # Solo sincroniza si `billable_hours` es mayor a 0
                print(f"[WRITE] Sincronizando: billable_hours={vals['billable_hours']} -> unit_amount={vals['billable_hours']}")
                vals['unit_amount'] = vals['billable_hours']
            else:
                print("[WRITE] No se sincroniza porque billable_hours es 0.0")

        print(f"[WRITE] Valores antes de super().write: {vals}")
        res = super(AccountAnalyticLine, self.with_context(prevent_recursion=True)).write(vals)

        # Actualizar la cantidad entregada en la línea de ventas si es necesario
        if 'billable_hours' in vals and self.filtered(lambda rec: rec.so_line):
            print("[WRITE] Actualizando líneas de ventas a través de _update_so_line_qty_delivered.")
            self._update_so_line_qty_delivered()

        print(f"[WRITE] Valores actuales después de modificar: billable_hours={self.billable_hours}, unit_amount={self.unit_amount}")
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
            print(f"[UPDATE_SO_LINE] Total billable_hours={total_billable_hours} para so_line={line.so_line.id}")

            # Actualizar la cantidad entregada
            line.so_line.sudo().write({'qty_delivered': total_billable_hours})
            print(f"[UPDATE_SO_LINE] Cantidad entregada actualizada: qty_delivered={total_billable_hours}")
