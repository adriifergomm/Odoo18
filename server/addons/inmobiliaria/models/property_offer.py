from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError


class InmoPropertyOffer(models.Model):
    _name = 'inmo.property.offer'
    _description = 'Oferta sobre Inmueble'
    _order = 'price desc'

    price = fields.Float(string='Precio Ofertado (€)', required=True)
    status = fields.Selection(
        string='Estado',
        copy=False,
        selection=[('accepted', 'Aceptada'), ('refused', 'Rechazada')],
    )
    partner_id = fields.Many2one('res.partner', string='Comprador', required=True)
    property_id = fields.Many2one('inmo.property', string='Inmueble', required=True, ondelete='cascade')
    validity = fields.Integer(string='Validez (dias)', default=7)
    date_deadline = fields.Date(
        string='Caduca el',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
    )

    @api.depends('validity', 'create_date')
    def _compute_date_deadline(self):
        for rec in self:
            base = rec.create_date.date() if rec.create_date else fields.Date.today()
            rec.date_deadline = base + timedelta(days=rec.validity)

    def _inverse_date_deadline(self):
        for rec in self:
            base = rec.create_date.date() if rec.create_date else fields.Date.today()
            rec.validity = (rec.date_deadline - base).days

    def action_accept(self):
        for rec in self:
            if rec.property_id.offer_ids.filtered(lambda o: o.status == 'accepted'):
                raise UserError('Ya existe una oferta aceptada para este inmueble.')
            rec.status = 'accepted'
            rec.property_id.write({
                'state': 'reserved',
                'selling_price': rec.price,
                'buyer_id': rec.partner_id.id,
            })
        return True

    def action_refuse(self):
        for rec in self:
            if rec.status == 'accepted':
                rec.property_id.write({
                    'state': 'with_offer',
                    'selling_price': 0.0,
                    'buyer_id': False,
                })
            rec.status = 'refused'
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            prop = self.env['inmo.property'].browse(vals.get('property_id'))
            if prop.state == 'closed':
                raise UserError('No se pueden crear ofertas para un inmueble cerrado.')
            existing_max = max(prop.offer_ids.mapped('price'), default=0)
            if vals.get('price', 0) < existing_max:
                raise UserError(
                    f'La oferta debe superar la mejor oferta existente ({existing_max:,.0f} €).'
                )
            if prop.state not in ('with_offer', 'reserved', 'closed'):
                prop.state = 'with_offer'
        return super().create(vals_list)
