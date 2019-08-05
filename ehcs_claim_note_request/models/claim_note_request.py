# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models, _


class ClaimNoteRequest(models.Model):
    _name = 'claim.note.request'
    _description = 'Claim Note Request'
    _rec_name='picking_id'

    picking_id = fields.Many2one('stock.picking', 'Shipment', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner')
    po_origin = fields.Char('Source PO', related='picking_id.origin', store=True, readonly=True)
    state = fields.Selection([('draft', 'To Do'),
                              ('confirmed', 'Confirmed'),
                              ('cancel', 'Cancel')], string='Status', default='draft')
    location_id = fields.Many2one('stock.location', 'Source Location', required=True)
    location_dest_id = fields.Many2one('stock.location', 'Destination Location', required=True)
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type', required=True)
    group_id = fields.Many2one('procurement.group', 'Procurement Group')
    date = fields.Date('Request Date', default=date.today())
    request_line = fields.One2many('claim.note.request.line', 'request_id', 'Request Line')

    @api.multi
    def cancel_replace_picking(self):
        for request in self:
            request.write({
                'state': 'cancel',
            })

    @api.multi
    def draft_replace_picking(self):
        for request in self:
            request.write({
                'state': 'draft',
            })

    @api.multi
    def create_replace_picking(self):
#        purchase_order = self.env['purchase.order'].search([('name', '=', self.po_origin)])
        move_line_list = []
        for request in self:
            partner_id = request.partner_id
            picking_type = request.picking_type_id
            procurement_group = request.group_id
            location_id = request.location_id
            location_dest_id = request.location_dest_id
            po_origin = request.po_origin
            picking_id = request.picking_id

            stock_picking_receipts = self.env['stock.picking'].create({
                'partner_id': partner_id.id,
                'origin': _(" (%s) Return of %s") % (po_origin, picking_id.name),
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id,
                'picking_type_id': picking_type.return_picking_type_id.id or picking_type.id,
    #            'purchase_id': purchase_order.id,
                'move_lines': [],
            })

            for line in request.request_line:
                move_src_loc = line.move_id.location_id
                for dest_line in line.move_id.move_dest_ids:
                    # 2 Step : Retrieve those destination ids in which destination location is not matched with the current move's source location.
                    if move_src_loc != dest_line.location_dest_id:
                        dest_line.product_uom_qty -= line.product_qty
                        dest_src_loc = dest_line.location_id
                        for child_dest_line in dest_line.move_dest_ids:
                            # 3 Step: Retrieve those destination ids in which destination location is not matched with the current move's source location.
                            if dest_src_loc != child_dest_line.location_dest_id:
                                child_dest_line.product_uom_qty -= line.product_qty

                vals = {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'product_uom_qty': line.product_qty,
                    'picking_id': stock_picking_receipts.id,
                    'state': 'draft',
                    'group_id': procurement_group.id,
                    'location_id': location_id.id, 
                    'location_dest_id': location_dest_id.id,
                    'origin_returned_move_id': line.move_id.id,
                    'procure_method': 'make_to_stock',
                    'rule_id': False,
                    'picking_type_id': picking_type.id,
                    'warehouse_id': False,
                }
                r = line.move_id.copy(vals)
                vals = {}
                move_orig_to_link = line.move_id.move_dest_ids.mapped('returned_move_ids')
                move_dest_to_link = line.move_id.move_orig_ids.mapped('returned_move_ids')
                vals['move_orig_ids'] = [(4, m.id) for m in move_orig_to_link | line.move_id]
                vals['move_dest_ids'] = [(4, m.id) for m in move_dest_to_link]
                r.write(vals)
            stock_picking_do = stock_picking_receipts.copy({
                'picking_type_id': picking_type.id,
                'origin': _("(%s) : Replacement of %s") % (po_origin, picking_id.name),
                'location_id': location_dest_id.id,
                'location_dest_id': location_id.id,
            })
        self.write({'state': 'confirmed'})
        return True


class ClaimNoteRequestLine(models.Model):
    _name = 'claim.note.request.line'
    _description = 'Claim Note Request Line'

    request_id = fields.Many2one('claim.note.request', 'Request', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    product_qty = fields.Float('Quantity')
    move_id = fields.Many2one('stock.move', 'Stock Move')

