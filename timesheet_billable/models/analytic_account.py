# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    billable_hours = fields.Float(string='Horas Dedicadas', default=0.0)

    @api.model
    def create(self, vals):
        """
        Controla la sincronización y valida el estado facturable al crear un registro.
        """
        # Sincronizar billable_hours con unit_amount
        if 'billable_hours' in vals:
            vals['unit_amount'] = vals['billable_hours']

        # Validar si el proyecto es facturable
        project_id = vals.get('project_id')
        if project_id:
            allow_billable = self.env['project.project'].browse(project_id).allow_billable
            if not allow_billable:
                vals['billable_hours'] = 0.0

        # Validar permisos para editar billable_hours
        if 'billable_hours' in vals and not self.env.user.has_group('timesheet_billable.edit_billable_hours'):
            vals.pop('billable_hours', None)

        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        """
        Controla la sincronización y valida el estado facturable al actualizar un registro.
        """
        # Prevenir recursión
        if self.env.context.get('prevent_recursion'):
            return super(AccountAnalyticLine, self).write(vals)

        for record in self:
            # Sincronizar billable_hours con unit_amount
            if 'billable_hours' in vals:
                vals['unit_amount'] = vals['billable_hours']

            # Validar si el proyecto es facturable
            if record.project_id and not record.project_id.allow_billable:
                vals['billable_hours'] = 0.0

            # Validar permisos para editar billable_hours
            if 'billable_hours' in vals and not self.env.user.has_group('timesheet_billable.edit_billable_hours'):
                raise AccessError(_("No tienes permisos para editar el campo 'Horas Dedicadas'."))

        # Actualizar evitando recursión
        return super(AccountAnalyticLine, self.with_context(prevent_recursion=True)).write(vals)

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
