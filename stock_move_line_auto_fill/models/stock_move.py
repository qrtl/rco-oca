# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2018 David Vidal <david.vidal@tecnativa.com>
# Copyright 2020 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_auto_fill_flag(self):
        return self.picking_id.auto_fill_operation

    def _get_avoid_lot_assignment_flag(self):
        return self.picking_id.picking_type_id.avoid_lot_assignment

    def _check_auto_fill_conditions(self, move_line_vals):
        auto_fill = self._get_auto_fill_flag()
        avoid_lot_assignment = self._get_avoid_lot_assignment_flag()
        lot_id = move_line_vals.get("lot_id")
        return auto_fill and not (avoid_lot_assignment and lot_id)

    def _update_qty_done(self, move_line_vals):
        if self._check_auto_fill_conditions(move_line_vals):
            move_line_vals["qty_done"] = move_line_vals.get("reserved_uom_qty", 0.0)

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """
        Auto-assign as done the quantity proposed for the lots.
        Keep this method to avoid extra write after picking _action_assign
        """
        move_line_vals = super()._prepare_move_line_vals(quantity, reserved_quant)
        self._update_qty_done(move_line_vals)
        return move_line_vals

    def _action_assign(self, force_qty=False):
        """
        Update stock move line quantity done field with reserved quantity.
        This method take into account incoming and outgoing moves.
        We can not use _prepare_move_line_vals method because this method only
        is called for a new lines.
        """
        res = super()._action_assign(force_qty=force_qty)
        for move in self.filtered(
            lambda m: m.state
            in ["confirmed", "assigned", "waiting", "partially_available"]
        ):
            if move._should_bypass_reservation():
                continue
            for move_line in move.move_line_ids.filtered(
                lambda l: l.qty_done != l.reserved_uom_qty
            ):
                move_line_vals = {"lot_id": move_line.lot_id}
                if move._check_auto_fill_conditions(move_line_vals):
                    move_line.write({"qty_done": move_line.reserved_uom_qty})
        return res
