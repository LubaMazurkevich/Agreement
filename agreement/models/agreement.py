from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class Agreement(models.Model):
    _name = "agreement.agreement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Agreement"

    number = fields.Char(string="Number", readonly=True, tracking=True)
    name = fields.Char(string="Name", related="number")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Client", required=True, tracking=True)
    kind_id = fields.Many2one(comodel_name="agreement.type", string="Agreement type", required=True, tracking=True)
    state = fields.Selection(selection=[
        ("draft", "Draft"),
        ("approving", "Approving"),
        ("active", "Active"),
        ("done", "Done")], string="State", default="draft", required=True, tracking=True)
    start_date = fields.Date(string="Start Date", default=fields.Date.today, required=True, tracking=True)
    end_date = fields.Date(string="End Date", required=True, tracking=True)
    author_id = fields.Many2one(comodel_name="res.users", string="Author", required=True,
                                default=lambda self: self.env.user, help="The user who created the contract",
                                tracking=True)
    is_show_send_to_approval = fields.Boolean(string="Is can send to approval",
                                              compute="_compute_is_show_send_to_approval", tracking=True)

    def _compute_is_show_send_to_approval(self):
        """Compute is show button' send to approval' depends on state and author_id"""
        for rec in self:
            if rec.author_id == self.env.user and rec.state == "draft":
                rec.is_show_send_to_approval = True
            else:
                rec.is_show_send_to_approval = False

    @api.constrains("start_date", "end_date")
    def _constrains_start_end_dates(self):
        """Method check dates"""
        if self.filtered(lambda rec: rec.end_date and rec.start_date > rec.end_date):
            raise ValidationError(_("Contract start date must be earlier than contract end date."))

    @api.model
    def create(self, vals):
        """Create agreement with special number"""
        number = self.env["ir.sequence"].next_by_code("agreement.agreement") or ""
        vals["number"] = "{}/{}/{}".format(_("AN"), fields.Date.today().year, number)
        res = super().create(vals)
        return res

    def button_send_for_approval(self):
        """Change state to approving """
        self.state = "approving"

    def button_approve(self):
        """Change state to active"""
        self.state = "active"

    def button_send_for_revision(self):
        """Change state to draft and send email to author_id"""
        self.state = "draft"
        body = _("Agreement %s sent to revision.") % self.number,
        values = {
            "subject": self.number,
            "email_to": self.author_id.partner_id.email,
            "body_html": body,
            "res_id": self.id,
            "model": self._name,
        }
        self.env["mail.mail"].sudo().create(values).send()

    def change_agreements_state_to_done(self):
        """This method is called from a cron job.Change state to 'done' for agreements"""
        agreement_to_done_ids = self.search([("state", "=", "active"), ("end_date", "<", date.today())])
        agreement_to_done_ids.write({"state": "done"})
