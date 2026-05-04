{
    'name': 'Inmobiliaria',
    'version': '18.0.2.0.0',
    'category': 'Real Estate',
    'summary': 'Gestion completa de propiedades, visitas y ofertas para inmobiliarias',
    'description': '''
        Modulo profesional para inmobiliarias:
        - Catalogo de inmuebles con imagen, tipo, etiquetas y estado
        - Gestion de venta y alquiler
        - Agenda de visitas con calendario
        - Sistema de ofertas con aceptar/rechazar
        - Calificacion energetica y caracteristicas completas
        - Comisiones, IBI y gastos de comunidad
        - Referencias automaticas (INM-0001)
        - Tipos e etiquetas precargados
    ''',
    'author': 'adriifergomm',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/estate_sequences.xml',
        'data/estate_property_data.xml',
        'views/estate_property_offer_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_tag_views.xml',
        'views/estate_property_visit_views.xml',
        'views/estate_property_views.xml',
        'views/estate_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
