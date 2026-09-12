"""
Los 10 módulos de primer nivel de GELETRIC (ver guía de diseño de la Cooperativa
San Manuel). Cada módulo tiene un color de identificación consistente en toda la
interfaz y un slug estable usado en las URLs.

icon_tile / icon_white son rutas relativas a STATIC_URL, hacia los assets reales
de diseño (core/static/core/images/SVG/): icon_tile es el ícono ya con su fondo
y color propio (para usar sobre superficies claras); icon_white es el mismo
glifo en blanco, sin fondo (para usar sobre la barra lateral u otro fondo de
color).

Este archivo es la única fuente de verdad para el menú lateral, los accesos
rápidos y las vistas de módulo. Cuando una funcionalidad quede confirmada por
una Historia de Usuario cerrada, actualizar/expandir su entrada acá.
"""

MODULES = [
    {
        "slug": "asociados",
        "name": "Asociados y servicios",
        "icon_tile": "core/images/SVG/icon - Asociados y Servicio.svg",
        "icon_white": "core/images/SVG/icon white -Asociados y Servicio.svg",
        "color": "purple",
        "items": [
            "Ficha del asociado (ventana con 8 solapas)",
            "ABM de asociado (rol múltiple)",
            "Cuota capital y excepciones",
            "Retorno de excedentes",
            "Reintegro al darse de baja",
            "Reportes societarios (Padrón, Libro societario)",
            "Reclamos",
            "Órdenes de trabajo",
        ],
    },
    {
        "slug": "abastecimiento",
        "name": "Abastecimiento",
        "icon_tile": "core/images/SVG/icon - Abastecimiento.svg",
        "icon_white": "core/images/SVG/icon white -Abastecimiento.svg",
        "color": "coral",
        "items": [
            "Órdenes de compra",
            "Proveedores",
            "Facturas de proveedor",
            "Retenciones (Ganancias, IIBB)",
            "Orden de pago a proveedores",
            "Otros pagos",
            "Inventario y almacenes",
            "Importación RASE",
            "Cobros externos (import/export)",
            "Débitos automáticos",
            "Cobro erróneo",
            "Autorización ARCA",
        ],
    },
    {
        "slug": "contabilidad",
        "name": "Contabilidad y Finanzas",
        "icon_tile": "core/images/SVG/icon - Contabilidad.svg",
        "icon_white": "core/images/SVG/icon white - Contabilidad.svg",
        "color": "teal",
        "items": [
            "Caja",
            "Bancos y cheques",
            "Plan de cuentas",
            "Asientos automáticos",
            "Comprobantes internos (plantillas)",
            "Bienes de uso",
            "Ajuste por inflación (RECPAM)",
            "Flujo de fondos",
            "Plan de pagos",
            "Reportes contables",
        ],
    },
    {
        "slug": "comercial",
        "name": "Comercial",
        "icon_tile": "core/images/SVG/icon - Comercial.svg",
        "icon_white": "core/images/SVG/icon white -Comercial.svg",
        "color": "pink",
        "items": [
            "Tarifas",
            "Flujo venta → factura",
            "Facturación masiva",
            "Autorización de facturas electrónicas",
            "Notas de crédito masivas",
            "Cobranzas",
            "Deuda y totalizador",
            "Vencimientos e intereses por mora",
            "Avisos de deuda y corte",
            "Categorías de cliente",
            "Comunicaciones y envíos masivos",
        ],
    },
    {
        "slug": "reportes",
        "name": "Reportes",
        "icon_tile": "core/images/SVG/icon - Reportes.svg",
        "icon_white": "core/images/SVG/icon white -Reportes.svg",
        "color": "blue",
        "items": [
            "Contables clásicos",
            "Regulatorios AFIP/ARCA",
            "Regulatorios por servicio",
            "Varios (asociados, conexiones, deudas)",
            "Impresión masiva de facturas",
        ],
    },
    {
        "slug": "impuestos",
        "name": "Impuestos",
        "icon_tile": "core/images/SVG/icon - Impuestos.svg",
        "icon_white": "core/images/SVG/icon white -Impuestos.svg",
        "color": "amber",
        "items": [
            "IVA",
            "Retención de Ganancias",
            "Ingresos Brutos (IIBB)",
            "Impuestos internos",
            "SUSS / cargas sociales",
            "Exportaciones regulatorias",
        ],
    },
    {
        "slug": "sueldos",
        "name": "Sueldos",
        "icon_tile": "core/images/SVG/icon - Sueldos.svg",
        "icon_white": "core/images/SVG/icon white -Sueldos.svg",
        "color": "green",
        "items": [
            "Liquidación mensual",
            "Categorías y convenios",
            "BAE",
            "Vacaciones",
            "Retenciones judiciales",
            "Libro de Sueldos Digital",
            "Ganancias 4ta categoría",
            "Vinculación con suministros",
            "Asiento contable de sueldos",
            "Anticipo de sueldo",
        ],
    },
    {
        "slug": "integraciones",
        "name": "Integraciones",
        "icon_tile": "core/images/SVG/icon - Integraciones.svg",
        "icon_white": "core/images/SVG/icon white -Integraciones.svg",
        "color": "gray",
        "items": [
            "Telemedición Plataforma A",
            "Telemedición Plataforma B",
            "SIC Móvil",
            "Terminal posnet",
            "Cobros externos",
            "Débitos automáticos",
            "Exportador GIS",
            "Exportador SINTYS",
        ],
    },
    {
        "slug": "consumo",
        "name": "Consumo",
        "icon_tile": "core/images/SVG/icon - Consumo.svg",
        "icon_white": "core/images/SVG/icon white -Consumo.svg",
        "color": "blue",
        "items": [
            "Medición y estado",
            "Estimación de consumo",
            "Cambios de medidor",
            "Vuelta al contador",
            "Indicadores especiales (tildes)",
            "Energías Renovables — VAD",
            "Histórico de tarifas",
            "Cambio de titularidad",
        ],
    },
    {
        "slug": "tecnico",
        "name": "Técnico",
        "icon_tile": "core/images/SVG/icon - Tecnico.svg",
        "icon_white": "core/images/SVG/icon white -Tecnico.svg",
        "color": "gray",
        "items": [
            "Usuarios del sistema",
            "Parámetros generales",
            "Inmuebles",
        ],
    },
]

_MODULES_BY_SLUG = {m["slug"]: m for m in MODULES}


def get_module(slug):
    """Devuelve el módulo con ese slug, o None si no existe."""
    return _MODULES_BY_SLUG.get(slug)
