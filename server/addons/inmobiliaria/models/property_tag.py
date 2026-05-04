from odoo import fields, models


class InmoPropertyTag(models.Model):
    _name = 'inmo.property.tag'
    _description = 'Etiqueta de Inmueble'
    _order = 'name'

    name = fields.Char(string='Etiqueta', required=True)
    color = fields.Integer(string='Color')
