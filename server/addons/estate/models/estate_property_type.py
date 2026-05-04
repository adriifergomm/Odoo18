from odoo import fields, models


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Tipo de Propiedad'
    _order = 'sequence, name'

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    property_ids = fields.One2many('estate.property', 'property_type_id', string='Propiedades')
    # offer_count via search_count porque property_type_id en offer es un campo related
    offer_count = fields.Integer(compute='_compute_offer_count', string='Num. Ofertas')

    def _compute_offer_count(self):
        for record in self:
            record.offer_count = self.env['estate.property.offer'].search_count([
                ('property_id.property_type_id', '=', record.id)
            ])

    def action_view_offers(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ofertas',
            'res_model': 'estate.property.offer',
            'view_mode': 'list',
            'domain': [('property_type_id', '=', self.id)],
        }
