# Copyright 2023 Quartile Limited
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    action_op_auto_fill_allowed = fields.Boolean(
        compute="_compute_action_operation_auto_fill_allowed"
    )
    auto_fill_operation = fields.Boolean(
        string="Auto fill operations",
        related="picking_type_id.auto_fill_operation",
    )

    @api.depends("state", "move_raw_ids")
    def _compute_action_operation_auto_fill_allowed(self):
        """
        The auto fill button is allowed only in confrim state, and the
        MO has component lines.
        """
        for rec in self:
            rec.action_op_auto_fill_allowed = (
                rec.state == "confirmed" and rec.move_raw_ids
            )

    def _check_action_operation_auto_fill_allowed(self):
        if any(not r.action_op_auto_fill_allowed for r in self):
            raise UserError(
                _(
                    "Filling the operations automatically is not possible, "
                    "perhaps the productions aren't in the right state "
                )
            )

    def action_operation_auto_fill(self):
        self._check_action_operation_auto_fill_allowed()
        operations_to_auto_fill = self.mapped("move_raw_ids").filtered(
            lambda move: (
                move.product_id
                and not move.quantity_done
                and (
                    not move.product_id.tracking != 'none'
                    or not move.picking_id.picking_type_id.avoid_lot_assignment
                )
            )
        )
        for move in operations_to_auto_fill:
            move.quantity_done = move.reserved_availability
