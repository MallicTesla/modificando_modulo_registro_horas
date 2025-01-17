/** @odoo-module */

import { GridRenderer } from "@web_grid/views/grid_renderer";
import { patch } from "@web/core/utils/patch";

patch(GridRenderer.prototype, {
    async openRecords(actionTitle, domain, context) {
        const vals = {
            'project_id': context.default_project_id,
            'task_id': context.default_task_id,
            'date': context.default_date
        };

        let orm_prop = this.orm || this.props.model.orm;

        const timeSheetID = await orm_prop.create('timesheet.custom.wizard', [vals]);

        const action = {
            type: 'ir.actions.act_window',
            name: 'Create timesheet',
            res_model: 'timesheet.custom.wizard',
            views: [[false, 'form']],
            res_id: timeSheetID[0],
            target: 'new',
        };

        this.actionService.doAction(action);
    }
});