from odoo import fields, models


class InmoPropertyType(models.Model):
    _name = 'inmo.property.type'
    _description = 'Tipo de Inmueble'
    _order = 'sequence, name'

    name = fields.Char(string='Tipo', required=True)
    sequence = fields.Integer(default=10)

    property_ids = fields.One2many('inmo.property', 'property_type_id', string='Inmuebles')
    property_count = fields.Integer(compute='_compute_property_count', string='Inmuebles')
    offer_count = fields.Integer(compute='_compute_offer_count', string='Ofertas')

    def _compute_property_count(self):
        for rec in self:
            rec.property_count = len(rec.property_ids)

    def _compute_offer_count(self):
        for rec in self:
            rec.offer_count = self.env['inmo.property.offer'].search_count([
                ('property_id.property_type_id', '=', rec.id)
            ])

    def action_view_offers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ofertas',
            'res_model': 'inmo.property.offer',
            'view_mode': 'list',
            'domain': [('property_id.property_type_id', '=', self.id)],
        }
