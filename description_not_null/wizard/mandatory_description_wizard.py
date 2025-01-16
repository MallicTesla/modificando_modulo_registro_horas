from odoo import fields, models, api
from odoo.exceptions import UserError


class MandatoryDescriptionWizard(models.TransientModel):
    _name = 'mandatory.description.wizard'

    description = fields.Char(string="Descripción")



    def confirm(self):
        if self.description and self.description != '/':
            context = self._context.copy()
            context['description'] = self.description
            self.env['account.analytic.line'].with_context(context).grid_update_cell(self._context['domain'], self._context['measure_field_name'], self._context['value'])
        else:
            raise UserError("Debe ingresar una descripción")
