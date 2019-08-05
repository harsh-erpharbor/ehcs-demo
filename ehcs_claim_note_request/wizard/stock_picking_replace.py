# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class ReturnPickingLine(models.TransientModel):
    _name = "stock.picking.replace.line"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', "Product", required=True)
    quantity = fields.Float("Quantity", digits=dp.get_precision('Product Unit of Measure'), required=True)
    uom_id = fields.Many2one('product.uom', 'Unit of Measure', related='move_id.product_uom')
    wizard_id = fields.Many2one('stock.picking.replace', "Wizard")
    move_id = fields.Many2one('stock.move', "Move")


class ReturnPicking(models.TransientModel):
    _name = 'stock.picking.replace'

    picking_id = fields.Many2one('stock.picking')
    product_return_moves = fields.One2many('stock.picking.replace.line', 'wizard_id', 'Moves')
    move_dest_exists = fields.Boolean('Chained Move Exists', readonly=True)
    original_location_id = fields.Many2one('stock.location')
    parent_location_id = fields.Many2one('stock.location')
    location_id = fields.Many2one(
        'stock.location', 'Return Location',
        domain="['|', ('id', '=', original_location_id), '&', ('return_location', '=', True), ('id', 'child_of', parent_location_id)]")

    @api.model
    def default_get(self, fields):
        if len(self.env.context.get('active_ids', list())) > 1:
            raise UserError("You may only return one picking at a time!")
        res = super(ReturnPicking, self).default_get(fields)

        move_dest_exists = False
        product_return_moves = []
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if picking:
            res.update({'picking_id': picking.id})
            if picking.state != 'done':
                raise UserError(_("You may only return Done pickings"))
            for move in picking.move_lines:
                if move.scrapped:
                    continue
                if move.move_dest_ids:
                    move_dest_exists = True
                quantity = move.product_qty - sum(move.move_dest_ids.filtered(lambda m: m.state in ['partially_available', 'assigned', 'done']).\
                                                  mapped('move_line_ids').mapped('product_qty'))
                quantity = float_round(quantity, precision_rounding=move.product_uom.rounding)
                product_return_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity, 'move_id': move.id, 'uom_id': move.product_id.uom_id.id}))

            if not product_return_moves:
                raise UserError(_("No products to return (only lines in Done state and not fully returned yet can be returned)!"))
            if 'product_return_moves' in fields:
                res.update({'product_return_moves': product_return_moves})
            if 'move_dest_exists' in fields:
                res.update({'move_dest_exists': move_dest_exists})
            if 'parent_location_id' in fields and picking.location_id.usage == 'internal':
                res.update({'parent_location_id': picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.view_location_id.id or picking.location_id.location_id.id})
            if 'original_location_id' in fields:
                res.update({'original_location_id': picking.location_id.id})
            if 'location_id' in fields:
                location_id = picking.location_id.id
                if picking.picking_type_id.return_picking_type_id.default_location_dest_id.return_location:
                    location_id = picking.picking_type_id.return_picking_type_id.default_location_dest_id.id
                res['location_id'] = location_id
        return res

    @api.multi
    def create_replace_request(self):
        cnr_obj = self.env['claim.note.request']
        for wizard in self:
            request_line_list = []
            for line in wizard.product_return_moves:
                request_line_list.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.quantity,
                    'move_id': line.move_id.id,
                }))
            if wizard.picking_id.picking_type_id.code == 'internal':
                location_dest_id = wizard.picking_id.group_id.partner_id.property_stock_supplier
                if not location_dest_id:
                    customerloc, location_dest_id = self.env['stock.warehouse']._get_partner_locations()
                picking_type_id = wizard.picking_id.picking_type_id.warehouse_id.in_type_id
                partner_id = wizard.picking_id.group_id.partner_id
            else:
                location_dest_id = wizard.picking_id.location_id
                picking_type_id = wizard.picking_id.picking_type_id
                partner_id = wizard.picking_id.partner_id
            claim_request = cnr_obj.create({
                'partner_id': partner_id.id,
                'picking_id': wizard.picking_id.id,
                'location_id': wizard.picking_id.location_dest_id.id,
                'location_dest_id': location_dest_id.id,
                'picking_type_id': picking_type_id.id,
                'group_id': wizard.picking_id.group_id.id,
                'request_line': request_line_list,
            })
            return {
                'name': 'Claim Note Request',
                'type': 'ir.actions.act_window',
                'res_model': 'claim.note.request',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id':claim_request.id,
            }
