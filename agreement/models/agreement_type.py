from odoo import models, fields


class AgreementType(models.Model):
    _name = "agreement.type"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "The type of agreement"

    name = fields.Char(string="Name", copy=False, required=True, tracking=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)

    _sql_constraints = [("name_uniq", "unique(name)", "Agreement type with the same name already exists")]
