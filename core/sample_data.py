"""
Datos de ejemplo para el prototipo de Inicio.

Nada de esto lee la base de datos todavía: son los mismos datos de muestra que
el prototipo HTML original, ahora del lado del servidor. Cuando las Historias
de Usuario de cada módulo (Asociados, Abastecimiento, etc.) queden cerradas y
existan modelos reales, estas funciones son el punto para reemplazar por
consultas al ORM sin tocar los templates.
"""
from datetime import timedelta

WEEKDAYS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MONTHS_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
MONTHS_ES_ABBR = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sept", "Oct", "Nov", "Dic"]


def format_today_long(d):
    """'martes, 9 de septiembre de 2026' a partir de un date/datetime."""
    return f"{WEEKDAYS_ES[d.weekday()]}, {d.day} de {MONTHS_ES[d.month - 1]} de {d.year}"


def relative_days_label(n):
    if n <= 0:
        return "hoy"
    if n == 1:
        return "hace 1 día"
    return f"hace {n} días"


def get_stats():
    """Estadísticas de la cabecera. 'module' referencia un slug de MODULES:
    el ícono y el color de cada tarjeta salen siempre de su módulo asociado."""
    return [
        {"label": "Asociados activos", "value": "1.842", "trend": "+2,4%", "module": "asociados"},
        {"label": "Órdenes de compra", "value": "24", "trend": "+14%", "module": "abastecimiento"},
        {"label": "Facturas emitidas", "value": "1.320", "trend": "+6%", "module": "comercial"},
        {"label": "Consumo total (MWh)", "value": "12.468", "trend": "+3,1%", "module": "consumo"},
    ]


def get_tasks():
    return [
        {"title": "Revisar órdenes de compra", "module": "abastecimiento", "due": "Hoy", "urgent": True},
        {"title": "Aprobar facturas de proveedor", "module": "contabilidad", "due": "Hoy", "urgent": True},
        {"title": "Atender reclamos de asociados", "module": "asociados", "due": "Mañana", "urgent": False},
        {"title": "Revisión de mantenimiento", "module": "tecnico", "due": "Próxima semana", "urgent": False},
        {"title": "Cierre contable mensual", "module": "contabilidad", "due": "Próxima semana", "urgent": False},
    ]


def get_news():
    """Cada ítem lleva 'days' (antigüedad) en vez de una fecha fija, para que
    el prototipo se vea vigente sin importar cuándo se lo abra."""
    raw = [
        {"title": "Nuevo padrón de asociados disponible", "module": "asociados", "days": 2},
        {"title": "Actualización de tipos de cambio", "module": "reportes", "days": 3},
        {"title": "Mantenimiento programado del sistema", "module": "tecnico", "days": 6},
        {"title": "Nuevas alícuotas de impuestos", "module": "impuestos", "days": 9},
    ]
    for item in raw:
        item["when"] = relative_days_label(item["days"])
    return raw


QUICK_ACCESS_SLUGS = ["asociados", "abastecimiento", "contabilidad", "impuestos", "consumo", "tecnico"]


def get_network_status():
    """Estado de la red para el donut 'Estado de la red'. 'var' es la variable
    CSS de estado (definida en dashboard.css) que pinta el segmento y el punto
    de referencia — nunca texto, siempre acompañado de su etiqueta."""
    return [
        {"label": "Operativa", "value": 147, "var": "--status-good"},
        {"label": "En mantenimiento", "value": 1, "var": "--status-warning"},
        {"label": "Fuera de servicio", "value": 1, "var": "--status-critical"},
        {"label": "Programadas", "value": 1, "var": "--status-neutral"},
    ]


# Consumo (MWh) real de los últimos 6 meses. El último valor coincide a
# propósito con la tarjeta "Consumo total (MWh)" de arriba.
_CONSUMO_MWH = [10420, 11180, 11950, 12610, 11890, 12468]


def get_consumo_series(today):
    """Devuelve una lista de {label, value} para los últimos 6 meses,
    terminando en el mes de 'today'."""
    labels = []
    for i in range(5, -1, -1):
        month_index = (today.month - 1 - i) % 12
        labels.append(MONTHS_ES_ABBR[month_index])
    return [{"label": label, "value": value} for label, value in zip(labels, _CONSUMO_MWH)]
