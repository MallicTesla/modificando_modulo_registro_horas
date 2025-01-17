from odoo import models, fields, api

class AssignSaleOrderLineWizard(models.TransientModel):
    _name = 'assign.sale.order.line.wizard'
    _description = 'Asignar Línea de Orden de Venta'

    sale_order_line_id = fields.Many2one('sale.order.line', string="Línea de Orden de Venta", required=True)

    def action_assign_lines(self):
        """
        Asigna la línea seleccionada a las líneas analíticas activas.
        """
        active_ids = self.env.context.get('active_ids', [])
        analytic_lines = self.env['account.analytic.line'].browse(active_ids)
        analytic_lines.action_assign_sale_order_lines(self.sale_order_line_id.id)
