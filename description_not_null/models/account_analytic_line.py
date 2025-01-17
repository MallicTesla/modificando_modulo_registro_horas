# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _, fields
from odoo.exceptions import UserError


class Project(models.Model):
    _inherit = 'project.project'

    # Indica si el proyecto es facturable
    is_billable = fields.Boolean(string="Facturable", default=False)

    # Relaciona las órdenes de venta asociadas con este proyecto
    sale_order_ids = fields.One2many('sale.order', 'project_id', string="Órdenes de Venta")


class AnalyticLine(models.Model):
    _name = 'account.analytic.line'
    _inherit = ['account.analytic.line', 'timer.mixin']

    # Campo para rastrear si el registro fue creado desde la interfaz del frontend y está en ejecución
    created_from_front_and_running = fields.Boolean(default=False)

    @api.model
    def grid_update_cell(self, domain, measure_field_name, value):
        """
        Actualiza el valor de una celda en la vista de cuadrícula. 
        Si falta la descripción, muestra un asistente para ingresarla.
        """
        if not self._context.get('description', False):
            context = self._context.copy()
            context['domain'] = domain
            context['measure_field_name'] = measure_field_name
            context['value'] = value

            return {
                'type': 'ir.actions.act_window',
                'name': 'Ingrese una descripción',
                'res_model': 'mandatory.description.wizard',
                'view_mode': 'form',
                'context': context,
                'target': 'new',
                'views': [[False, 'form']],
            }
        else:
            description = self._context['description']
            if value == 0:
                return  # No se realiza ninguna acción si el valor es 0.

            timesheets = self.search(domain, limit=2)

            if timesheets.project_id and not all(timesheets.project_id.sudo().mapped("allow_timesheets")):
                raise UserError(_("You cannot adjust the time of the timesheet for a project with timesheets disabled."))

            # Lógica para manejar las hojas de tiempo no validadas
            non_validated_timesheets = timesheets.filtered(lambda timesheet: not timesheet.validated)
            if len(non_validated_timesheets) > 1 or (len(timesheets) == 1 and timesheets.validated):
                timesheets[0].copy({
                    'name': description,
                    measure_field_name: value,
                })
            elif len(non_validated_timesheets) == 1:
                non_validated_timesheets[measure_field_name] += value
            else:
                # Crear una nueva hoja de tiempo si no existen registros válidos
                project_id = self._context.get('default_project_id', False)
                field_name, model_name = self._get_timesheet_field_and_model_name()
                field_value = self._context.get(f'default_{field_name}', False)
                if not project_id and field_value:
                    project_id = self.env[model_name].browse(field_value).project_id.id
                if not project_id:
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': _("Your timesheet entry is missing a project. Please either group the Grid view by project or enter your timesheets through another view."),
                            'type': 'danger',
                            'sticky': False,
                        }
                    }
                if not self.env['project.project'].browse(project_id).sudo().allow_timesheets:
                    raise UserError(_("You cannot adjust the time of the timesheet for a project with timesheets disabled."))

                self.create({
                    'name': description,
                    'project_id': project_id,
                    field_name: field_value,
                    measure_field_name: value,
                })

    @api.model
    def action_start_new_timesheet_timer(self, vals):
        self = self.with_context(from_front=True)
        return super(AnalyticLine, self).action_start_new_timesheet_timer(vals)

    def action_timer_stop(self, try_to_match=False):
        self = self.with_context(from_front_stop=True)
        self.created_from_front_and_running = False
        return super(AnalyticLine, self).action_timer_stop()

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """
        Ajusta el dominio del campo 'sale_line_id' según si el proyecto es facturable.
        """
        if self.project_id and self.project_id.is_billable:
            return {
                'domain': {
                    'sale_line_id': [
                        ('order_id', 'in', self.project_id.sale_order_ids.ids),
                        ('product_id.type', '=', 'service')
                    ]
                }
            }
        else:
            return {
                'domain': {
                    'sale_line_id': []
                }
            }

    @api.model
    def action_assign_sale_order_lines(self, sale_order_line_id):
        """
        Asigna una línea de orden de venta a las líneas analíticas seleccionadas.
        """
        sale_order_line = self.env['sale.order.line'].browse(sale_order_line_id)
        if sale_order_line.exists():
            self.write({'so_line': sale_order_line.id})
        return True

    @api.model
    def create(self, vals_list):
        """
        Valida que se proporcione una descripción antes de crear una nueva línea analítica.
        """
        if self._context.get('from_front', 'NOKEY') == 'NOKEY':
            if not vals_list.get('name', False) or vals_list.get('name') == '/':
                raise UserError('Por favor, proporcione una descripción para guardar las horas.')
        else:
            vals_list['created_from_front_and_running'] = True
        return super(AnalyticLine, self).create(vals_list)

    def write(self, vals):
        """
        Valida la descripción antes de guardar los cambios en las líneas analíticas.
        """
        if self:
            if not self._context.get('from_front_stop', False) and not self.created_from_front_and_running:
                if (vals.get('name', 'NOKEY') in ['NOKEY', '/', False] and not vals.get('name', 'NOKEY')) or ((not self.name or self.name == '/') and (not vals.get('name') or vals.get('name') == '/')):
                    raise UserError('Por favor, proporcione una descripción para guardar las horas.')
            elif not self.created_from_front_and_running:
                if (not self.name or self.name == '/') and not vals.get('name'):
                    raise UserError('Por favor, proporcione una descripción para guardar las horas.')
        return super(AnalyticLine, self).write(vals)
