from odoo import fields, models


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Tipo de Propiedad'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    property_ids = fields.One2many('estate.property', 'property_type_id', string='Propiedades')
    offer_ids = fields.One2many('estate.property.offer', 'property_type_id', string='Ofertas')
    offer_count = fields.Integer(compute='_compute_offer_count', string='Num. Ofertas')

    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)
