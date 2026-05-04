from odoo import fields, models


class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Etiqueta de Propiedad'
    _order = 'name'

    name = fields.Char(required=True)
    color = fields.Integer()
