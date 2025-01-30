# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    billable_hours = fields.Float(
        string='Horas Dedicadas',
        default=0.0,
        help="Duración en horas y minutos. Ejemplo: 1.5 equivale a 1 hora y 30 minutos.",
    )

    is_editable = fields.Boolean(compute="_compute_is_editable", store=False)

    def _compute_is_editable(self):
        """Determina si el usuario tiene permisos de edición."""
        has_edit_permission = self.env.user.has_group("timesheet_billable.edit_billable_hours")
        for record in self:
            record.is_editable = has_edit_permission

    @api.model
    def create(self, vals):
        """
        Sincroniza billable_hours con unit_amount al crear un registro.
        """
        # Validar permisos para editar billable_hours
        if 'billable_hours' in vals and not self.env.user.has_group('timesheet_billable.edit_billable_hours'):
            raise AccessError(_("No tienes permisos para editar el campo 'Horas Dedicadas'."))

        # Sincronizar billable_hours con unit_amount
        if 'billable_hours' in vals:
            vals['unit_amount'] = vals['billable_hours']

        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        """
        Sincroniza billable_hours con unit_amount al actualizar un registro.
        """
        # Evitar recursión
        if self.env.context.get('prevent_recursion'):
            return super(AccountAnalyticLine, self).write(vals)

        # Validar permisos para editar billable_hours
        if 'billable_hours' in vals and not self.env.user.has_group('timesheet_billable.edit_billable_hours'):
            raise AccessError(_("No tienes permisos para editar el campo 'Horas Dedicadas'."))

        # Sincronizar billable_hours con unit_amount
        if 'billable_hours' in vals:
            vals['unit_amount'] = vals['billable_hours']

        # Evitar recursión al actualizar el registro
        return super(AccountAnalyticLine, self.with_context(prevent_recursion=True)).write(vals)

    def _update_so_line_qty_delivered(self):
        """
        Actualiza la cantidad entregada (qty_delivered) de las líneas de ventas asociadas.
        """
        for line in self.filtered(lambda rec: rec.so_line):
            # Buscar todas las líneas relacionadas con la misma línea de venta
            related_lines = self.search([('so_line', '=', line.so_line.id)])
            # Calcular la suma total de billable_hours
            total_billable_hours = sum(related_lines.mapped('billable_hours'))
            # Actualizar qty_delivered en la línea de venta asociada
            line.so_line.sudo().write({'qty_delivered': total_billable_hours})
