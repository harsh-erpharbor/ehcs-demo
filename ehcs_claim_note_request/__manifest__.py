# -*- coding: utf-8 -*-
{
    'name': 'EHCS Claim Note Request',
    'author': 'ERP Harbor Consulting Services',
    'category': 'Warehouse',
    'summary': 'Claim Note Request',
    'website': 'http://www.erpharbor.com',
    'version': '11.0.1.0.0',
    'description': """
        EHCS Claim Note Request
    """,
    'depends': [
        'purchase',
    ],
    'data': [
        'security/inventory_groups.xml',
        'security/ir.model.access.csv',
        'wizard/stock_picking_replace_view.xml',
        'views/stock_picking_view.xml',
        'views/claim_note_request_view.xml',
    ],
    'installable': True,
}
