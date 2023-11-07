# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        res = super()._prepare_move_line_vals(quantity, reserved_quant)
        if not self.raw_material_production_id.auto_fill_operation:
            return res
        elif self.raw_material_production_id.picking_type_id.avoid_lot_assignment and res.get("lot_id"):
            return res
        if self.quantity_done != self.product_uom_qty:
            # Not assign qty_done for extra moves in over processed quantities
            res.update({"qty_done": res.get("reserved_uom_qty", 0.0)})
        return res

    def _action_assign(self, force_qty=False):
        res = super()._action_assign(force_qty=force_qty)
        for line in self.filtered(
            lambda m: m.state
            in ["confirmed", "assigned", "waiting", "partially_available"]
        ):
            if (
                line._should_bypass_reservation()
                or not line.raw_material_production_id.auto_fill_operation
            ):
                return res
            lines_to_update = line.move_line_ids.filtered(
                lambda l: l.qty_done != l.reserved_uom_qty
            )
            for move_line in lines_to_update:
                if (
                    not line.raw_material_production_id.picking_type_id.avoid_lot_assignment
                    or not move_line.lot_id
                ):
                    move_line.qty_done = move_line.reserved_uom_qty
        return res
