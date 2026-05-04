from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class InmoProperty(models.Model):
    _name = 'inmo.property'
    _description = 'Inmueble'
    _order = 'id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ── Identificacion ──────────────────────────────────────────────────────
    reference = fields.Char(string='Ref.', default='Nuevo', readonly=True, copy=False, index=True)
    name = fields.Char(string='Titulo del Anuncio', required=True, tracking=True)
    active = fields.Boolean(default=True)

    # ── Imagen ───────────────────────────────────────────────────────────────
    image = fields.Image(string='Foto Principal', max_width=1920, max_height=1080)
    image_128 = fields.Image('Miniatura', related='image', max_width=128, max_height=128, store=True)

    # ── Clasificacion ────────────────────────────────────────────────────────
    property_type_id = fields.Many2one('inmo.property.type', string='Tipo de Inmueble', tracking=True)
    tag_ids = fields.Many2many('inmo.property.tag', string='Etiquetas')
    listing_type = fields.Selection(
        string='Operacion',
        required=True,
        default='sale',
        tracking=True,
        selection=[
            ('sale', 'Venta'),
            ('rent', 'Alquiler'),
            ('sale_rent', 'Venta y Alquiler'),
        ],
    )

    # ── Ubicacion ────────────────────────────────────────────────────────────
    street = fields.Char(string='Calle y Numero')
    city = fields.Char(string='Municipio')
    province = fields.Char(string='Provincia')
    zip_code = fields.Char(string='Codigo Postal')

    # ── Caracteristicas ──────────────────────────────────────────────────────
    living_area = fields.Integer(string='Sup. Construida (m²)')
    usable_area = fields.Integer(string='Sup. Util (m²)')
    bedrooms = fields.Integer(string='Habitaciones', default=2)
    bathrooms = fields.Integer(string='Banos', default=1)
    floor = fields.Integer(string='Planta')
    facades = fields.Integer(string='Fachadas')
    year_built = fields.Integer(string='Ano Construccion')
    condition = fields.Selection(
        string='Estado',
        selection=[
            ('new', 'Obra Nueva'),
            ('excellent', 'Muy Buen Estado'),
            ('good', 'Buen Estado'),
            ('needs_work', 'Para Reformar'),
        ],
    )

    # Extras
    elevator = fields.Boolean(string='Ascensor')
    garage = fields.Boolean(string='Garaje')
    parking_spaces = fields.Integer(string='Plazas Garaje')
    storage_room = fields.Boolean(string='Trastero')
    terrace = fields.Boolean(string='Terraza')
    pool = fields.Boolean(string='Piscina')
    garden = fields.Boolean(string='Jardin')
    garden_area = fields.Integer(string='Sup. Jardin (m²)')
    garden_orientation = fields.Selection(
        string='Orientacion',
        selection=[
            ('north', 'Norte'), ('south', 'Sur'),
            ('east', 'Este'), ('west', 'Oeste'),
            ('northeast', 'Noreste'), ('northwest', 'Noroeste'),
            ('southeast', 'Sureste'), ('southwest', 'Suroeste'),
        ],
    )
    air_conditioning = fields.Boolean(string='Aire Acondicionado')
    heating = fields.Selection(
        string='Calefaccion',
        selection=[
            ('none', 'Sin Calefaccion'), ('gas', 'Gas Natural'),
            ('electric', 'Electrica'), ('heat_pump', 'Bomba de Calor'),
            ('fuel', 'Gasoil'),
        ],
    )

    # Superficies calculadas
    total_area = fields.Integer(string='Sup. Total (m²)', compute='_compute_total_area')
    price_per_sqm = fields.Float(string='€/m²', compute='_compute_price_per_sqm', digits=(10, 0))

    # ── Calificacion energetica ───────────────────────────────────────────────
    energy_rating = fields.Selection(
        string='Calif. Energetica',
        selection=[
            ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'),
            ('E', 'E'), ('F', 'F'), ('G', 'G'), ('exempt', 'Exento'),
        ],
    )

    # ── Precios ──────────────────────────────────────────────────────────────
    expected_price = fields.Float(string='Precio Venta (€)', tracking=True)
    selling_price = fields.Float(string='Precio Acordado (€)', readonly=True, copy=False, tracking=True)
    best_offer = fields.Float(string='Mejor Oferta (€)', compute='_compute_best_offer')
    rental_price = fields.Float(string='Alquiler/mes (€)', tracking=True)
    deposit = fields.Float(string='Fianza (€)')
    ibi = fields.Float(string='IBI Anual (€)')
    community_fee = fields.Float(string='Comunidad/mes (€)')
    commission = fields.Float(string='Comision (%)', default=3.0)
    commission_amount = fields.Float(string='Importe Comision (€)', compute='_compute_commission', store=True)

    date_availability = fields.Date(string='Disponible desde', default=fields.Date.today, copy=False)

    # ── Estado ───────────────────────────────────────────────────────────────
    state = fields.Selection(
        string='Estado',
        required=True,
        copy=False,
        default='available',
        tracking=True,
        selection=[
            ('available', 'Disponible'),
            ('with_offer', 'Con Ofertas'),
            ('reserved', 'Reservado'),
            ('closed', 'Cerrado'),
            ('cancelled', 'Retirado'),
        ],
    )

    # ── Personas ─────────────────────────────────────────────────────────────
    salesperson_id = fields.Many2one('res.users', string='Agente', default=lambda self: self.env.user)
    buyer_id = fields.Many2one('res.partner', string='Comprador / Inquilino', copy=False)
    owner_id = fields.Many2one('res.partner', string='Propietario')

    # ── Relaciones ───────────────────────────────────────────────────────────
    offer_ids = fields.One2many('inmo.property.offer', 'property_id', string='Ofertas')
    offer_count = fields.Integer(compute='_compute_offer_count', string='Ofertas')
    visit_ids = fields.One2many('inmo.property.visit', 'property_id', string='Visitas')
    visit_count = fields.Integer(compute='_compute_visit_count', string='Visitas')

    # =========================================================================
    # Compute
    # =========================================================================

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        for rec in self:
            rec.total_area = (rec.living_area or 0) + (rec.garden_area or 0)

    @api.depends('expected_price', 'living_area')
    def _compute_price_per_sqm(self):
        for rec in self:
            rec.price_per_sqm = (rec.expected_price / rec.living_area) if rec.living_area else 0.0

    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        for rec in self:
            prices = rec.offer_ids.mapped('price')
            rec.best_offer = max(prices) if prices else 0.0

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for rec in self:
            rec.offer_count = len(rec.offer_ids)

    @api.depends('visit_ids')
    def _compute_visit_count(self):
        for rec in self:
            rec.visit_count = len(rec.visit_ids)

    @api.depends('commission', 'selling_price', 'expected_price')
    def _compute_commission(self):
        for rec in self:
            base = rec.selling_price if rec.selling_price else rec.expected_price
            rec.commission_amount = base * rec.commission / 100.0

    # =========================================================================
    # Onchange
    # =========================================================================

    @api.onchange('garden')
    def _onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.garden_orientation = 'south'
        else:
            self.garden_area = 0
            self.garden_orientation = False

    @api.onchange('garage')
    def _onchange_garage(self):
        if not self.garage:
            self.parking_spaces = 0

    # =========================================================================
    # CRUD
    # =========================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('reference', 'Nuevo') == 'Nuevo':
                vals['reference'] = (
                    self.env['ir.sequence'].next_by_code('inmo.property') or 'Nuevo'
                )
        return super().create(vals_list)

    # =========================================================================
    # Acciones
    # =========================================================================

    def action_close(self):
        for rec in self:
            if rec.state == 'cancelled':
                raise UserError('Un inmueble retirado no puede cerrarse.')
            rec.state = 'closed'
        return True

    def action_cancel(self):
        for rec in self:
            if rec.state == 'closed':
                raise UserError('Un inmueble cerrado no puede retirarse.')
            rec.state = 'cancelled'
        return True

    def action_republish(self):
        for rec in self:
            rec.write({'state': 'available', 'selling_price': 0.0, 'buyer_id': False})
        return True

    def action_view_visits(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Visitas',
            'res_model': 'inmo.property.visit',
            'view_mode': 'list,calendar,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    def action_view_offers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ofertas',
            'res_model': 'inmo.property.offer',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    # =========================================================================
    # Constraints
    # =========================================================================

    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for rec in self:
            if (
                not float_is_zero(rec.selling_price, precision_rounding=0.01)
                and float_compare(
                    rec.selling_price, rec.expected_price * 0.9, precision_rounding=0.01
                ) < 0
            ):
                raise ValidationError(
                    'El precio acordado no puede ser inferior al 90% del precio solicitado.'
                )

    @api.constrains('commission')
    def _check_commission(self):
        for rec in self:
            if not (0 <= rec.commission <= 100):
                raise ValidationError('La comision debe estar entre 0% y 100%.')
