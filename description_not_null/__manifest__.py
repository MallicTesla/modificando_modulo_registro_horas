# -*- coding: utf-8 -*-
{
    'name': "Description not null",

    'summary': "Block creation of timesheets without description",

    'description': """
Block creation of timesheets without description    """,

    'author': "Primate",
    'website': "primate.uy",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    'assets': {
        'web.assets_backend': [
            'description_not_null/static/src/js/grid_renderer.js',
            ]
    },

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_project', 'timesheet_billable', 'web_grid'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/mandatory_description_wizard_view.xml',
        'wizard/timesheet_wizard_view.xml',
        'views/assign_sale_order_line_wizard_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}

