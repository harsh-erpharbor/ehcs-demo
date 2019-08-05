# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    is_shipment = fields.Boolean(" Is Shipment?", compute='_compute_quality_dept')

    @api.depends('picking_type_id')
    def _compute_quality_dept(self):
        for picking in self:
            if picking.picking_type_id.code not in ['incoming']:
                picking.is_shipment = True


class StockLocaionPath(models.Model):
    _inherit = 'stock.location.path'

    def _prepare_move_copy_values(self, move_to_copy, new_date):
        """Override to pass the Purchase Line reference to new move"""
        res = super(StockLocaionPath, self)._prepare_move_copy_values(move_to_copy, new_date)
        if move_to_copy.purchase_line_id:
            res.update({'purchase_line_id': move_to_copy.purchase_line_id.id})
        return res
