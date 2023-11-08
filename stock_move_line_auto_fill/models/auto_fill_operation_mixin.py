# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AutoFillOperationMixin(models.AbstractModel):
    _name = 'auto.fill.operation.mixin'
    _description = 'Auto Fill Operation Mixin'

    def _get_auto_fill_flag(self):
        """ Should be overridden by inheriting models. """
        raise NotImplementedError("Expected to be overridden in inheriting models.")

    def _get_avoid_lot_assignment_flag(self):
        """ Should be overridden by inheriting models. """
        raise NotImplementedError("Expected to be overridden in inheriting models.")

    def _check_auto_fill_conditions(self, move_line_vals):
        auto_fill = self._get_auto_fill_flag()
        avoid_lot_assignment = self._get_avoid_lot_assignment_flag()
        lot_id = move_line_vals.get('lot_id')
        return auto_fill and not (avoid_lot_assignment and lot_id)

    def _update_qty_done(self, move_line_vals):
        if self._check_auto_fill_conditions(move_line_vals):
            move_line_vals['qty_done'] = move_line_vals.get('reserved_uom_qty', 0.0)
