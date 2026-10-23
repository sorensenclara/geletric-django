"""
Mapa de sitio v3 de GELETRIC: menú lateral, submenús y pantallas.

Traducción a datos del documento de diseño «Mapa de sitio · v3 ·
navegable — Sidebar, submenú y tarjetas». Es la única fuente de verdad
para:
  - el menú lateral (bloques → módulos → ítems de submenú),
  - el buscador del menú lateral,
  - las URLs /modulos/<modulo>/[<item>/[<tarjeta>/]] y lo que muestra
    cada una.

Estructura:
  GROUPS  — los cuatro bloques del sidebar (Padrón · Gestión ·
            Administración · Sistema), cada uno con sus módulos.
  módulo  — slug, name, color, ícono y, o bien `view` (módulo sin
            submenú, como Asociados y Órdenes de trabajo), o bien `sub`
            (lista de ítems de submenú).
  ítem    — slug, label, view.
  view    — qué se dibuja en el área de contenido. `kind` es uno de:
              "grid"   grilla: columnas, acciones, filtros rápidos y qué
                       ficha abre la fila (`ficha`; None = solo consulta).
              "cards"  página de tarjetas: no tiene datos propios, solo
                       accesos (`cards`, cada una con slug/label/desc/view).
              "proc"   pantalla de proceso: parámetros → ejecución →
                       resultado.
              "tab"    tablero o reporte: filtros, visualización y
                       exportación.
            Opcionales: `desc`, `handler` (nombre de una vista real que
            reemplaza a la genérica — ver views.NAV_HANDLERS) y
            `url_name` (módulo que ya tiene su propia URL real; el
            sidebar linkea directo ahí).

Íconos: los módulos que ya tienen ilustración propia en
core/static/core/images/SVG/ la usan (icon_tile / icon_white). Los que
el mapa v3 suma y todavía no tienen arte (Suministros e inmuebles,
Órdenes de trabajo, Inventario, Telefonía) usan un ícono del sprite
(`icon_sprite`) hasta que diseño entregue el suyo.

Las slugs se generan solas a partir del texto (slugify) salvo cuando se
pasan explícitas; cambiarlas cambia las URLs.
"""
from django.utils.text import slugify

ACCIONES = ["Filtros", "Búsqueda", "Exportar"]
SVG = "core/images/SVG/"


def _icons(name):
    """Rutas del par de íconos de diseño (tile con fondo / glifo blanco)."""
    white = {
        "Contabilidad": "icon white - Contabilidad.svg",
    }.get(name, f"icon white -{name}.svg")
    return {"icon_tile": f"{SVG}icon - {name}.svg", "icon_white": f"{SVG}{white}", "icon_sprite": None}


def _sprite(icon_id):
    return {"icon_tile": None, "icon_white": None, "icon_sprite": icon_id}


def grid(title, cols, ficha, extra=None, qf="", desc=""):
    """Grilla. `extra`: acciones que se suman a Filtros · Búsqueda ·
    Exportar (la que empieza con Nuevo/Nueva/Crear se dibuja como
    primaria)."""
    return {
        "kind": "grid", "title": title, "cols": cols, "ficha": ficha,
        "acciones": ACCIONES + (extra or []), "qf": qf, "desc": desc,
    }


def proc(title, desc):
    return {"kind": "proc", "title": title, "desc": desc}


def tab(title, desc):
    return {"kind": "tab", "title": title, "desc": desc}


def cards(title, items, desc=""):
    return {"kind": "cards", "title": title, "cards": items, "desc": desc}


def card(label, desc, view, slug=None):
    return {"slug": slug or slugify(label), "label": label, "desc": desc, "view": view}


def item(label, view, slug=None):
    return {"slug": slug or slugify(label), "label": label, "view": view}


# ---------- vistas reutilizadas ----------
V_ALMACENES = grid("Almacenes", ["Código", "Nombre", "Ubicación", "Estado"],
                   "Ficha de almacén (edición)", ["Nuevo almacén"])

# ---------- módulos ----------
ASOCIADOS = {
    "slug": "asociados", "name": "Asociados", "color": "purple",
    **_icons("Asociados y Servicio"),
    "view": {
        **grid("Asociados", ["Nro Asociado", "Nro Usuario", "Nombre", "DNI", "Dirección real / fiscal", "Email"],
               "Ficha de Asociado (edición)", ["Nuevo Asociado"]),
        "url_name": "core:asociados_list",
    },
}

SUMINISTROS = {
    "slug": "suministros-inmuebles", "name": "Suministros e inmuebles", "color": "blue",
    **_sprite("i-plug"),
    "sub": [
        item("Suministros", {
            **grid("Suministros", ["Código", "Servicio", "Titular", "Tarifa", "Inmueble", "Estado"],
                   "Ficha de Suministro (edición) · acción: Cambio de titularidad",
                   ["Nuevo Suministro"], qf="Servicio · Activos (por defecto)"),
            "handler": "suministros",
        }),
        item("Inmuebles", grid("Inmuebles", ["Calle", "Número", "Depto", "Piso", "Municipio", "Partido"],
                               "Ficha de Inmueble (edición)", ["Nuevo Inmueble"])),
    ],
}

CONSUMOS = {
    "slug": "consumos", "name": "Consumos", "color": "blue",
    **_icons("Consumo"),
    "sub": [
        item("Consumos", grid("Consumos",
             ["Periodo", "Servicio", "Suministro", "Medidor", "Estado anterior", "Estado actual", "Consumo", "Estado del consumo"],
             "Ficha de Consumo (edición)", ["Nuevo Consumo"], qf="Servicio · Estado")),
        item("Medidores", grid("Medidores", ["Número", "Servicio", "Marca", "Modelo", "Suministro", "Estado"],
             "Ficha de Medidor (edición) · campos según el servicio", ["Nuevo Medidor"], qf="Servicio · Estado")),
        item("Estimación T4", proc("Estimación de consumos de T4",
             "Parámetros de periodo y servicio, previsualización del cálculo, confirmación."), slug="estimacion-t4"),
        item("Control previo a facturar", proc("Control de consumos antes de facturar",
             "Ex prefacturación. Revisión de consumos con alertas antes de habilitar la facturación del periodo.")),
        item("Memocolectores", cards("Memocolectores", [
            card("Exportar consumos", "Comunes e industriales",
                 proc("Exportar consumos", "Generación del archivo para el memocolector.")),
            card("Importar consumos", "Comunes e industriales",
                 proc("Importar consumos", "Carga del archivo, validación y reporte de errores.")),
        ])),
    ],
}

COMERCIAL = {
    "slug": "comercial", "name": "Comercial", "color": "pink",
    **_icons("Comercial"),
    "sub": [
        item("Cuadros tarifarios", grid("Cuadros tarifarios",
             ["Servicio", "Vigencia desde", "Vigencia hasta", "Categoría", "Estado"],
             "Ficha de cuadro tarifario (edición)", qf="Servicio · Fecha")),
        item("Facturación", cards("Facturación", [
            card("Facturas de servicios", "Listado de las facturas generadas masivamente",
                 grid("Facturas de servicios", ["Nro", "Periodo", "Servicio", "Socio", "Importe", "Estado"],
                      "Ficha de factura (edición)", qf="Servicio · Estado")),
            card("Facturas individuales", "Emisión manual y listado",
                 grid("Facturas individuales", ["Nro", "Fecha", "Socio", "Concepto", "Importe", "Estado"],
                      "Ficha de factura (edición)", ["Nueva factura individual"], qf="Socio · Fecha")),
            card("Generación masiva", "Facturas de servicios del periodo",
                 proc("Generación masiva de facturas de servicios",
                      "Selección de periodo y servicio, simulación, ejecución y resumen del lote generado.")),
        ])),
        item("Cuentas corrientes", cards("Cuentas corrientes y deudas", [
            card("Deudas", "Solo consulta y reportes",
                 grid("Deudas", ["Socio", "Suministro", "Periodo", "Importe", "Días de mora"], None)),
            card("Reportes de cuenta corriente", "Movimientos por socio",
                 tab("Reportes de cuenta corriente",
                     "Selección de socio y periodo, detalle de movimientos, salida a PDF / Excel.")),
            card("Generación de avisos de deuda", "Proceso por lote",
                 proc("Generación de avisos de deuda", "Criterios de selección, previsualización del lote, emisión.")),
            card("Avisos de deuda", "Listado y administración",
                 grid("Avisos de deuda", ["Nro", "Socio", "Periodo", "Importe", "Estado", "Fecha de emisión"],
                      "Ficha de aviso (edición)", ["Administración de avisos"])),
        ])),
        item("Cobranzas", cards("Cobranzas", [
            card("Cajas diarias", "Apertura, movimientos y cierre",
                 grid("Cajas diarias", ["Fecha", "Caja", "Cajero", "Apertura", "Total cobrado", "Estado"],
                      "Ficha de caja diaria (edición)", ["Imprimir", "Nueva caja (apertura)"])),
            card("Importar rendición de cobros", "Pagos externos · archivo del ente recaudador",
                 proc("Importar rendición de cobros", "Carga del archivo, validación e imputación de pagos.")),
            card("Exportar archivo de deudas", "Pagos externos · para enviar al recaudador",
                 proc("Exportar archivo de deudas", "Generación del archivo de deudas vigentes.")),
            card("Errores de importación", "Pagos externos · revisión y corrección",
                 grid("Errores de importación de cobros", ["Fecha", "Archivo", "Línea", "Error", "Estado"],
                      "Detalle del error")),
        ])),
        item("Reclamos", grid("Reclamos", ["Nro", "Fecha", "Socio", "Suministro", "Tipo", "Estado"],
                              "Ficha de reclamo (edición)", ["Nuevo Reclamo"])),
    ],
}

CONTABILIDAD = {
    "slug": "contabilidad", "name": "Contabilidad", "color": "teal",
    **_icons("Contabilidad"),
    "sub": [
        item("Tablero general", tab("Tablero de contabilidad general",
             "Indicadores del ejercicio, accesos rápidos y estado de cierres.")),
        item("Asientos contables", grid("Asientos contables",
             ["Nro", "Fecha", "Diario", "Concepto", "Debe", "Haber", "Estado"],
             "Ficha de asiento (edición)", ["Crear asiento manual"])),
        item("Reportes contables", cards("Reportes contables", [
            card("Libro diario", "Por periodo", tab("Libro diario", "Filtros por fecha y diario. Exportación.")),
            card("Libro mayor", "Por cuenta", tab("Libro mayor", "Filtros por cuenta y periodo. Exportación.")),
            card("Balance de sumas y saldos", "Por periodo",
                 tab("Balance de sumas y saldos", "Totales por cuenta. Exportación.")),
        ])),
        item("Consolidación de facturas", proc("Consolidación de facturas",
             "Agrupación de facturas del periodo y generación del asiento (pase a contabilidad).")),
        item("Ajuste por inflación", proc("Ajuste por inflación (RT 6)",
             "Parámetros, índices, simulación y aplicación.")),
        item("Cierre de ejercicio", proc("Cierre de ejercicio",
             "Validaciones previas, generación de asientos de cierre y apertura.")),
    ],
}

SUELDOS = {
    "slug": "sueldos", "name": "Sueldos", "color": "green",
    **_icons("Sueldos"),
    "sub": [
        item("Empleados", grid("Empleados",
             ["Legajo", "Nombre", "CUIL", "Convenio", "Categoría", "Fecha de ingreso", "Estado"],
             "Legajo del empleado (datos personales, contrato, familiares, historial)",
             ["Nuevo empleado"], qf="Convenio · Estado")),
        item("Novedades", grid("Novedades del periodo",
             ["Periodo", "Legajo", "Empleado", "Concepto", "Cantidad / Importe", "Estado"],
             "Ficha de novedad (horas extra, ausencias, licencias, adelantos)",
             ["Nueva novedad", "Importar novedades"], qf="Periodo · Tipo de novedad")),
        item("Liquidar sueldos", proc("Liquidación de sueldos",
             "Selección del periodo y del tipo de liquidación (mensual, quincenal, SAC, vacaciones, "
             "liquidación final), selección de empleados o convenio, simulación y confirmación. "
             "Genera los recibos del lote.")),
        item("Recibos", grid("Recibos de sueldo",
             ["Periodo", "Legajo", "Empleado", "Convenio", "Bruto", "Descuentos", "Neto", "Estado"],
             "Ficha de recibo (detalle de conceptos) · acción: Reimprimir",
             ["Imprimir recibos", "Enviar por email"], qf="Periodo · Tipo de liquidación · Estado")),
        item("Libro de sueldos digital", cards("Libro de sueldos digital (LSD)", [
            card("Generar archivo LSD", "Presentación ante ARCA",
                 proc("Generación del archivo LSD",
                      "Selección de liquidación, validación de conceptos contra códigos ARCA, "
                      "generación del TXT para el F.931.")),
            card("Presentaciones LSD", "Historial y estado",
                 grid("Presentaciones LSD", ["Periodo", "Liquidación", "Fecha de generación", "Nro de envío", "Estado"],
                      "Detalle de la presentación", qf="Periodo · Estado")),
            card("Impresión del libro", "Libro de sueldos (art. 52 LCT)",
                 tab("Impresión del libro de sueldos",
                     "Selección de periodo y rango de legajos, foliado, salida a PDF.")),
        ])),
        item("Reportes", cards("Reportes de sueldos", [
            card("Resumen de liquidación", "Totales por concepto",
                 tab("Resumen de liquidación", "Totales por concepto, convenio y centro de costo. Exportación.")),
            card("Aportes y contribuciones", "Seguridad social / F.931",
                 tab("Aportes y contribuciones", "Control de bases imponibles, aportes y contribuciones del periodo.")),
            card("Aportes sindicales", "Por convenio y sindicato",
                 tab("Aportes sindicales", "Detalle por sindicato para presentación y pago.")),
            card("Ganancias 4ª categoría", "Retenciones y F.1357",
                 tab("Impuesto a las Ganancias 4ª categoría",
                     "Retenciones por empleado, liquidación anual / final, F.1357."), slug="ganancias-4a-categoria"),
            card("Acumulados por empleado", "Histórico de conceptos",
                 tab("Acumulados por empleado", "Evolución de conceptos por legajo y periodo.")),
            card("Provisiones", "SAC y vacaciones",
                 tab("Provisiones de SAC y vacaciones", "Devengamiento mensual por empleado.")),
        ])),
        item("Interfaces", cards("Interfaces de sueldos", [
            card("Asiento de sueldos", "Pase a contabilidad",
                 proc("Asiento contable de sueldos", "Agrupación por concepto y centro de costo, generación del asiento.")),
            card("Acreditación bancaria", "Archivo para el banco",
                 proc("Archivo de acreditación de haberes",
                      "Selección de liquidación y banco, generación del archivo de pago.")),
        ])),
    ],
}

ORDENES_TRABAJO = {
    "slug": "ordenes-trabajo", "name": "Órdenes de trabajo", "color": "gray",
    **_sprite("i-wrench"),
    "view": grid("Órdenes de trabajo", ["Nro", "Fecha", "Tipo", "Suministro", "Responsable", "Estado"],
                 "Ficha de OT (edición)", ["Nueva OT"]),
}

COMPRAS = {
    "slug": "compras", "name": "Compras", "color": "coral",
    **_icons("Abastecimiento"),
    "sub": [
        item("Órdenes de compra", grid("Órdenes de compra", ["Nro", "Fecha", "Proveedor", "Importe", "Estado"],
                                       "Ficha de OC (edición)", ["Nueva OC"])),
        item("Proveedores", grid("Proveedores", ["Razón social", "CUIT", "Condición IVA", "Contacto", "Estado"],
                                 "Ficha de proveedor (edición)", ["Nuevo proveedor"])),
        item("Facturas de proveedor", grid("Facturas de proveedor", ["Tipo", "Nro", "Fecha", "Proveedor", "Importe", "Estado"],
                                           "Ficha de factura (edición)", ["Nueva factura"])),
    ],
}

INVENTARIO = {
    "slug": "inventario", "name": "Inventario", "color": "coral",
    **_sprite("i-bars"),
    "sub": [
        item("Tablero", tab("Tablero de inventario y stock",
             "Existencias por almacén, alertas de stock mínimo, últimos movimientos.")),
        item("Movimientos de stock", grid("Movimientos de stock",
             ["Fecha", "Tipo", "Material / SKU", "Almacén", "Cantidad", "Origen"], "Detalle del movimiento",
             qf="Tipo: ingreso (remito de compra) · egreso (consumo de OT)")),
        item("Almacenes", V_ALMACENES),
        item("Productos", grid("Productos",
             ["Código / SKU", "Descripción", "Tipo", "Servicio", "Unidad", "Stock", "Estado"],
             "Ficha de producto (edición) · stock y stock mínimo solo para materiales",
             ["Nuevo producto"], qf="Tipo: material (stockeable) · concepto facturable · Servicio")),
        item("Ajustes e inventarios físicos", cards("Ajustes e inventarios físicos", [
            card("Crear inventario físico", "Nuevo conteo",
                 proc("Crear inventario físico", "Selección de almacén y materiales a contar.")),
            card("Detalle de conteo", "Carga de cantidades",
                 proc("Detalle de conteo", "Carga del conteo real contra el stock del sistema, con diferencias.")),
            card("Confirmar ajustes", "Impacta el stock",
                 proc("Guardar / confirmar ajustes",
                      "Aplicación de las diferencias y generación del movimiento de ajuste.")),
        ])),
        item("Libro Kárdex", tab("Libro Kárdex completo",
             "Historial de movimientos por material con saldos acumulados."), slug="kardex"),
    ],
}

REPORTES = {
    "slug": "reportes", "name": "Reportes", "color": "blue",
    **_icons("Reportes"),
    "sub": [
        item("OCEBA", tab("Reportes OCEBA", "Presentaciones al ente regulador provincial.")),
        item("INAES", tab("Reportes INAES", "Presentaciones al instituto de cooperativas.")),
        item("ARBA", tab("Reportes ARBA", "Regímenes de información y retenciones.")),
        item("Por módulo", tab("Reportes por módulo", "Listado de reportes agrupados por módulo del sistema.")),
    ],
}

TELEFONIA = {
    "slug": "telefonia", "name": "Telefonía", "color": "gray",
    **_sprite("i-phone"),
    "sub": [
        item("Importación de llamadas", proc("Importación de llamadas",
             "Carga del archivo de la central, validación y procesamiento.")),
        item("Llamadas", grid("Llamadas", ["Fecha", "Interno", "Destino", "Duración", "Tipo", "Importe"],
                              "Detalle de la llamada", qf="Periodo · Interno · Tipo")),
        item("Consumos internacionales", grid("Consumos internacionales",
             ["Periodo", "Interno", "País", "Minutos", "Importe"], "Detalle del consumo", qf="Periodo")),
        item("Generación de consumos", proc("Generación de consumos internacionales",
             "Cálculo del periodo según valores y franjas configuradas.")),
    ],
}

CONFIGURACION = {
    "slug": "configuracion", "name": "Configuración", "color": "gray",
    **_icons("Tecnico"),
    "sub": [
        item("Contable", cards("Configuración contable", [
            card("Plan de cuentas", "Estructura de cuentas",
                 grid("Plan de cuentas", ["Código", "Denominación", "Tipo", "Imputable"], "Ficha de cuenta", ["Nueva cuenta"])),
            card("Diarios", "Libros de registración",
                 grid("Diarios", ["Código", "Nombre", "Tipo"], "Ficha de diario", ["Nuevo diario"])),
            card("Impuestos", "Alícuotas y tratamientos",
                 grid("Impuestos", ["Código", "Nombre", "Alícuota", "Cuenta"], "Ficha de impuesto", ["Nuevo impuesto"])),
            card("Bancos", "Cuentas bancarias",
                 grid("Bancos", ["Banco", "Cuenta", "CBU", "Cuenta contable"], "Ficha de banco", ["Nuevo banco"])),
            card("Migración y carga masiva", "Importación inicial",
                 proc("Migración y carga masiva", "Carga de saldos y estructuras desde archivo.")),
            card("Configuración general", "Parámetros del módulo",
                 proc("Configuración contable general", "Ejercicio activo, cuentas por defecto, reglas de imputación.")),
        ])),
        item("Servicios", grid("Servicios", ["Código", "Nombre", "Tipo", "Estado"], "Ficha de servicio", ["Nuevo servicio"])),
        item("Tarifas", grid("Tarifas", ["Código", "Nombre", "Servicio", "Categoría", "Estado"], "Ficha de tarifa", ["Nueva tarifa"])),
        item("Inventario", cards("Configuración de inventario", [
            card("Almacenes", "Alta y parámetros", V_ALMACENES),
        ])),
        item("Cobranzas", cards("Configuración de cobranzas", [
            card("Cajas", "Puntos de cobro",
                 grid("Cajas", ["Código", "Nombre", "Sucursal", "Estado"], "Ficha de caja", ["Nueva caja"])),
            card("Cobros externos", "Entes recaudadores",
                 grid("Cobros externos", ["Ente", "Formato de archivo", "Comisión", "Estado"], "Ficha del ente", ["Nuevo ente"])),
        ])),
        item("Telefonía", cards("Configuración de telefonía", [
            card("Valores y franjas", "Tarifario de llamadas",
                 grid("Valores y franjas", ["Franja", "Desde", "Hasta", "Destino", "Valor"], "Ficha del valor", ["Nuevo valor"])),
        ])),
        item("Consumos", cards("Configuración de consumos", [
            card("Memocolectores", "Equipos y formatos",
                 grid("Memocolectores", ["Equipo", "Formato", "Rutas asignadas", "Estado"], "Ficha del equipo", ["Nuevo equipo"])),
        ])),
        item("Sueldos", cards("Configuración de sueldos", [
            card("Convenios", "Convenios colectivos aplicables",
                 grid("Convenios", ["Código", "Nombre", "Sindicato", "Vigencia desde", "Estado"],
                      "Ficha de convenio (edición)", ["Nuevo convenio"])),
            card("Contratos", "Modalidades de contratación",
                 grid("Contratos", ["Código", "Modalidad", "Jornada", "Convenio", "Estado"],
                      "Ficha de contrato (edición)", ["Nuevo contrato"])),
            card("Escalas", "Valores por categoría y vigencia",
                 grid("Escalas salariales", ["Convenio", "Categoría", "Vigencia desde", "Básico", "Adicionales"],
                      "Ficha de escala (edición)", qf="Convenio · Vigencia")),
            card("Conceptos de liquidación", "Haberes, descuentos y fórmulas",
                 grid("Conceptos de liquidación", ["Código", "Descripción", "Tipo", "Fórmula", "Código ARCA (LSD)", "Estado"],
                      "Ficha de concepto (edición)", ["Nuevo concepto"], qf="Tipo · Convenio")),
            card("Parámetros LSD", "Datos del empleador y códigos ARCA",
                 proc("Parámetros del Libro de sueldos digital",
                      "Datos del empleador, tablas de códigos ARCA y mapeo con conceptos internos.")),
        ])),
        item("Energía", cards("Configuración de energía", [
            card("Subestaciones", "Red de distribución",
                 grid("Subestaciones", ["Código", "Nombre", "Potencia", "Zona", "Estado"],
                      "Ficha de subestación", ["Nueva subestación"])),
            card("Pérdidas de transformador", "Coeficientes",
                 grid("Pérdidas de transformador", ["Transformador", "Potencia", "Pérdida %", "Vigencia"],
                      "Ficha del coeficiente", ["Nuevo coeficiente"])),
        ])),
    ],
}

GROUPS = [
    {"slug": "padron", "name": "Padrón", "modules": [ASOCIADOS, SUMINISTROS]},
    {"slug": "gestion", "name": "Gestión", "modules": [CONSUMOS, COMERCIAL, ORDENES_TRABAJO]},
    {"slug": "administracion", "name": "Administración", "modules": [CONTABILIDAD, SUELDOS, COMPRAS, INVENTARIO]},
    {"slug": "sistema", "name": "Sistema", "modules": [REPORTES, TELEFONIA, CONFIGURACION]},
]

MODULES = [m for g in GROUPS for m in g["modules"]]
_MODULES_BY_SLUG = {m["slug"]: m for m in MODULES}

# Slugs del menú anterior (10 módulos) que siguen teniendo un equivalente
# en el mapa v3 — /modulos/<viejo>/ redirige al nuevo para no romper
# links guardados. Impuestos e Integraciones salieron del mapa.
LEGACY_SLUGS = {
    "consumo": "consumos",
    "abastecimiento": "compras",
    "tecnico": "configuracion",
}


def get_module(slug):
    """El módulo con ese slug, o None."""
    return _MODULES_BY_SLUG.get(slug)


def get_item(module, item_slug):
    for it in module.get("sub", []):
        if it["slug"] == item_slug:
            return it
    return None


def get_card(view, card_slug):
    for cd in view.get("cards", []) if view else []:
        if cd["slug"] == card_slug:
            return cd
    return None


def _check_unique_slugs():
    """Falla al importar si dos hermanos comparten slug (rompería la URL)."""
    def dup(seq):
        seen = set()
        for s in seq:
            if s in seen:
                raise ValueError(f"nav_map: slug repetido «{s}»")
            seen.add(s)
    dup(m["slug"] for m in MODULES)
    for m in MODULES:
        dup(it["slug"] for it in m.get("sub", []))
        for it in m.get("sub", []):
            dup(cd["slug"] for cd in it["view"].get("cards", []))


_check_unique_slugs()
