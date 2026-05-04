from odoo import api, fields, models


class InmoPropertyVisit(models.Model):
    _name = 'inmo.property.visit'
    _description = 'Visita a Inmueble'
    _order = 'date desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Asunto', compute='_compute_name', store=True)
    property_id = fields.Many2one(
        'inmo.property', string='Inmueble', required=True, ondelete='cascade', index=True
    )
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, index=True)
    agent_id = fields.Many2one('res.users', string='Agente', default=lambda self: self.env.user)
    date = fields.Datetime(string='Fecha y Hora', required=True, default=fields.Datetime.now)
    duration = fields.Float(string='Duracion (h)', default=1.0)
    notes = fields.Text(string='Observaciones')
    result = fields.Selection(
        string='Resultado',
        default='pending',
        tracking=True,
        selection=[
            ('pending', 'Pendiente'),
            ('interested', 'Interesado'),
            ('not_interested', 'No Interesado'),
            ('offer_made', 'Ha Hecho Oferta'),
        ],
    )

    @api.depends('property_id', 'partner_id')
    def _compute_name(self):
        for rec in self:
            parts = []
            if rec.property_id:
                parts.append(rec.property_id.reference or rec.property_id.name)
            if rec.partner_id:
                parts.append(rec.partner_id.name)
            rec.name = ' - '.join(parts) if parts else 'Visita'
