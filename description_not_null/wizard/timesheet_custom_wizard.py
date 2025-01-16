from odoo import fields, models, api


class TimesheetCustomWizard(models.TransientModel):
    _name = 'timesheet.custom.wizard'

    _sql_constraints = [('time_positive', 'CHECK(time_spent > 0)', 'The timesheet\'s time must be positive')]


    time_spent = fields.Float()
    date = fields.Date(string="Fecha")
    description = fields.Char(string='Descripción')
    task_id = fields.Many2one(
        'project.task', "Tarea",
    )
    project_id = fields.Many2one(
        'project.project', "Proyecto", required=True,
    )

    def save_timesheet(self):
        values = {
            'task_id': self.task_id.id,
            'project_id': self.project_id.id,
            'date': self.date,
            'name': self.description,
            'user_id': self.env.uid,
            'unit_amount': self.time_spent
        }
        return self.env['account.analytic.line'].create(values)
