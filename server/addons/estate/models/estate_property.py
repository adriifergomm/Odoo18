from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Propiedad Inmobiliaria'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Informacion basica
    name = fields.Char(string='Referencia', required=True, tracking=True)
    description = fields.Text(string='Descripcion')
    property_type_id = fields.Many2one('estate.property.type', string='Tipo', tracking=True)
    tag_ids = fields.Many2many('estate.property.tag', string='Etiquetas')

    # Ubicacion
    street = fields.Char(string='Calle')
    city = fields.Char(string='Ciudad')
    zip_code = fields.Char(string='Codigo Postal')
    province = fields.Char(string='Provincia')

    # Caracteristicas
    living_area = fields.Integer(string='Superficie (m²)')
    bedrooms = fields.Integer(string='Habitaciones', default=2)
    bathrooms = fields.Integer(string='Banos', default=1)
    facades = fields.Integer(string='Fachadas')
    garage = fields.Boolean(string='Garaje')
    garden = fields.Boolean(string='Jardin')
    garden_area = fields.Integer(string='Superficie Jardin (m²)')
    garden_orientation = fields.Selection(
        string='Orientacion Jardin',
        selection=[
            ('north', 'Norte'),
            ('south', 'Sur'),
            ('east', 'Este'),
            ('west', 'Oeste'),
        ],
    )
    elevator = fields.Boolean(string='Ascensor')
    total_area = fields.Integer(
        string='Superficie Total (m²)',
        compute='_compute_total_area',
    )

    # Precio y fechas
    expected_price = fields.Float(string='Precio Esperado', required=True, tracking=True)
    selling_price = fields.Float(string='Precio de Venta', readonly=True, copy=False, tracking=True)
    best_offer = fields.Float(string='Mejor Oferta', compute='_compute_best_offer')
    date_availability = fields.Date(
        string='Disponible desde',
        default=fields.Date.today,
        copy=False,
    )

    # Estado
    state = fields.Selection(
        string='Estado',
        required=True,
        copy=False,
        default='new',
        tracking=True,
        selection=[
            ('new', 'Nuevo'),
            ('offer_received', 'Oferta Recibida'),
            ('offer_accepted', 'Oferta Aceptada'),
            ('sold', 'Vendido'),
            ('cancelled', 'Cancelado'),
        ],
    )
    active = fields.Boolean(default=True)

    # Personas
    salesperson_id = fields.Many2one(
        'res.users',
        string='Agente',
        default=lambda self: self.env.user,
    )
    buyer_id = fields.Many2one('res.partner', string='Comprador', copy=False)
    owner_id = fields.Many2one('res.partner', string='Propietario')

    # Ofertas
    offer_ids = fields.One2many('estate.property.offer', 'property_id', string='Ofertas')
    offer_count = fields.Integer(compute='_compute_offer_count', string='Num. Ofertas')

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        for record in self:
            prices = record.offer_ids.mapped('price')
            record.best_offer = max(prices) if prices else 0.0

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for record in self:
            record.offer_count = len(record.offer_ids)

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'north'
        else:
            self.garden_area = 0
            self.garden_orientation = False

    def action_sold(self):
        for record in self:
            if record.state == 'cancelled':
                raise UserError('Una propiedad cancelada no puede venderse.')
            record.state = 'sold'
        return True

    def action_cancel(self):
        for record in self:
            if record.state == 'sold':
                raise UserError('Una propiedad vendida no puede cancelarse.')
            record.state = 'cancelled'
        return True

    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for record in self:
            if (
                not float_is_zero(record.selling_price, precision_rounding=0.01)
                and float_compare(record.selling_price, record.expected_price * 0.9, precision_rounding=0.01) < 0
            ):
                raise ValidationError(
                    'El precio de venta no puede ser inferior al 90% del precio esperado.'
                )

    @api.constrains('expected_price')
    def _check_expected_price(self):
        for record in self:
            if record.expected_price <= 0:
                raise ValidationError('El precio esperado debe ser mayor que cero.')
