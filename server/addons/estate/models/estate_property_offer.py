from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class EstatePropertyOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Oferta de Propiedad'
    _order = 'price desc'

    price = fields.Float(string='Precio Ofertado', required=True)
    status = fields.Selection(
        string='Estado',
        copy=False,
        selection=[
            ('accepted', 'Aceptada'),
            ('refused', 'Rechazada'),
        ],
    )
    partner_id = fields.Many2one('res.partner', string='Comprador', required=True)
    property_id = fields.Many2one('estate.property', string='Propiedad', required=True)
    property_type_id = fields.Many2one(
        related='property_id.property_type_id',
        string='Tipo de Propiedad',
        store=True,
    )
    validity = fields.Integer(string='Validez (dias)', default=7)
    date_deadline = fields.Date(
        string='Fecha Limite',
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline',
    )

    @api.depends('validity', 'create_date')
    def _compute_date_deadline(self):
        for record in self:
            base = record.create_date.date() if record.create_date else fields.Date.today()
            record.date_deadline = base + timedelta(days=record.validity)

    def _inverse_date_deadline(self):
        for record in self:
            base = record.create_date.date() if record.create_date else fields.Date.today()
            record.validity = (record.date_deadline - base).days

    def action_accept(self):
        for record in self:
            accepted = record.property_id.offer_ids.filtered(lambda o: o.status == 'accepted')
            if accepted:
                raise UserError('Ya existe una oferta aceptada para esta propiedad.')
            record.status = 'accepted'
            record.property_id.write({
                'state': 'offer_accepted',
                'selling_price': record.price,
                'buyer_id': record.partner_id.id,
            })
        return True

    def action_refuse(self):
        for record in self:
            if record.status == 'accepted':
                record.property_id.write({
                    'state': 'offer_received',
                    'selling_price': 0.0,
                    'buyer_id': False,
                })
            record.status = 'refused'
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            prop = self.env['estate.property'].browse(vals.get('property_id'))
            if prop.state == 'sold':
                raise UserError('No se pueden crear ofertas para una propiedad vendida.')
            existing_max = max(prop.offer_ids.mapped('price'), default=0)
            if vals.get('price', 0) < existing_max:
                raise UserError(
                    f'La oferta debe ser superior a la mejor oferta existente ({existing_max:,.2f} €).'
                )
            prop.state = 'offer_received'
        return super().create(vals_list)
