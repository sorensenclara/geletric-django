"""
Datos de ejemplo para el listado y la Ficha del asociado (módulo Asociados
y servicios).

Boceto provisto por el equipo de desarrollo: una ficha con encabezado,
resumen rápido y 8 solapas navegables. Dos de esas solapas (Familiares,
Proveedor) están marcadas como "a confirmar" en el boceto original porque
su origen de datos todavía no está cerrado — se muestran con un estilo
distinto (borde punteado) para que quede claro que son tentativas.

Nada de esto lee la base de datos todavía: es un directorio fijo de
asociados de muestra (ver _ASOCIADOS_MUESTRA). Cuando la Historia de
Usuario del listado/ficha quede cerrada, get_asociados_list() y
get_associate(numero_asociado) son las funciones a reemplazar por consultas
al ORM (con su paginación/búsqueda real) sin tocar los templates. Los
valores de "resumen" (deuda total, reclamos abiertos) y el resto del cuerpo
de la ficha (aportes, suministros, reclamos, etc.) son de ejemplo visual y
se repiten iguales para todos los asociados de muestra — si esos datos no
existen todavía en el backend, no hay que inventar consultas: conectarlos
acá cuando existan.
"""

# Directorio de asociados de muestra para el listado (buscador + filtros de
# estado/rol/localidad) y para resolver la ficha de cada uno por
# numero_asociado. "roles" alimenta es_asociado/es_usuario/es_proveedor.
_ASOCIADOS_MUESTRA = [
    {"numero_asociado": "00184", "numero_usuario": "00231", "nombre_completo": "Juan Carlos Pérez",
     "estado": "Activo", "localidad": "Posadas", "roles": ["Asociado", "Usuario"]},
    {"numero_asociado": "00212", "numero_usuario": "00256", "nombre_completo": "María Elena Gómez",
     "estado": "Activo", "localidad": "Posadas", "roles": ["Asociado"]},
    {"numero_asociado": "00305", "numero_usuario": "00340", "nombre_completo": "Roberto Daniel Fernández",
     "estado": "Inactivo", "localidad": "Garupá", "roles": ["Asociado", "Usuario"]},
    {"numero_asociado": "00147", "numero_usuario": "00190", "nombre_completo": "Ana Lucía Benítez",
     "estado": "Activo", "localidad": "Candelaria", "roles": ["Asociado", "Usuario", "Proveedor"]},
    {"numero_asociado": "00098", "numero_usuario": "00121", "nombre_completo": "Carlos Alberto Duarte",
     "estado": "Activo", "localidad": "Posadas", "roles": ["Usuario"]},
    {"numero_asociado": "00276", "numero_usuario": "00298", "nombre_completo": "Silvia Beatriz Acosta",
     "estado": "Inactivo", "localidad": "Garupá", "roles": ["Asociado"]},
    {"numero_asociado": "00341", "numero_usuario": "00366", "nombre_completo": "Miguel Ángel Rojas",
     "estado": "Activo", "localidad": "Candelaria", "roles": ["Asociado", "Proveedor"]},
    {"numero_asociado": "00059", "numero_usuario": "00082", "nombre_completo": "Laura Patricia Ríos",
     "estado": "Activo", "localidad": "Posadas", "roles": ["Asociado", "Usuario"]},
    {"numero_asociado": "00412", "numero_usuario": "00430", "nombre_completo": "Jorge Luis Cabrera",
     "estado": "Activo", "localidad": "Garupá", "roles": ["Asociado"]},
    {"numero_asociado": "00133", "numero_usuario": "00168", "nombre_completo": "Verónica Soledad Torres",
     "estado": "Inactivo", "localidad": "Posadas", "roles": ["Asociado", "Usuario"]},
    {"numero_asociado": "00287", "numero_usuario": "00311", "nombre_completo": "Diego Alejandro Silva",
     "estado": "Activo", "localidad": "Candelaria", "roles": ["Usuario"]},
    {"numero_asociado": "00019", "numero_usuario": "00044", "nombre_completo": "Marta Noemí Villalba",
     "estado": "Activo", "localidad": "Posadas", "roles": ["Asociado", "Usuario", "Proveedor"]},
]


def _iniciales(nombre_completo):
    partes = nombre_completo.split()
    if len(partes) < 2:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def get_asociados_list():
    """Datos de muestra para el listado de asociados (paso previo a la
    ficha). El buscador (nombre o N° de asociado) y los filtros de
    estado/rol/localidad de la vista actúan sobre esta misma lista."""
    return [dict(a) for a in _ASOCIADOS_MUESTRA]


def get_localidades():
    """Localidades disponibles para el filtro del listado."""
    return sorted({a["localidad"] for a in _ASOCIADOS_MUESTRA})


def get_associate(numero_asociado=None):
    """Ficha completa de un asociado. numero_asociado busca en el
    directorio de muestra; si no se pasa (o no se encuentra), devuelve el
    primero como default. El cuerpo de la ficha (personal/contacto/
    domicilio/administrativa y las solapas) es el mismo boceto visual para
    todos — solo se personalizan los campos que identifican a la persona
    (nombre, estado, localidad, roles)."""
    directorio = {a["numero_asociado"]: a for a in _ASOCIADOS_MUESTRA}
    base = directorio.get(numero_asociado) or _ASOCIADOS_MUESTRA[0]

    nombre_completo = base["nombre_completo"]
    estado = base["estado"]
    localidad = base["localidad"]
    roles = base["roles"]

    return {
        "nombre_completo": nombre_completo,
        "iniciales": _iniciales(nombre_completo),
        "numero_asociado": base["numero_asociado"],
        "numero_usuario": base["numero_usuario"],
        "estado": estado,
        "activo": estado == "Activo",
        "es_asociado": "Asociado" in roles,
        "es_usuario": "Usuario" in roles,
        "es_proveedor": "Proveedor" in roles,
        # Resumen compacto (4 indicadores) — NO son "cards gigantes", son
        # tiles chicos. suministros/deuda_total/reclamos_abiertos son de
        # ejemplo visual: conectar al dato real de backend cuando exista.
        "resumen": [
            {"id": "estado", "label": "Estado", "value": estado, "kind": "status"},
            {"id": "suministros", "label": "Suministros", "value": "1 activo"},
            {"id": "deuda", "label": "Deuda total", "value": "$0", "chevron": True},
            {"id": "reclamos", "label": "Reclamos abiertos", "value": "0", "chevron": True},
        ],
        # Los siguientes 4 grupos alimentan las 4 tarjetas de la solapa
        # "General". Son datos de ejemplo visual — usar los campos reales
        # que ya llegan del contexto Django cuando existan; no crear campos
        # nuevos en modelos solo para replicar el mockup.
        "personal": [
            {"label": "Nombre y apellido", "value": nombre_completo},
            {"label": "DNI", "value": "28.451.902"},
            {"label": "CUIT/CUIL", "value": "20-28451902-3"},
            {"label": "Fecha de nacimiento", "value": "14/05/1980"},
            {"label": "Género", "value": "—"},
        ],
        "contacto": [
            {"label": "Teléfono fijo", "value": "03795 42-1180"},
            {"label": "Celular", "value": "+54 9 3795 55-0192"},
            {"label": "Email", "value": "—"},
            {"label": "Email alternativo", "value": "—"},
        ],
        "domicilio_general": [
            {"label": "Domicilio fiscal", "value": "Av. San Martín 450"},
            {"label": "Ruta / subruta", "value": "R3 / S12"},
            {"label": "Localidad", "value": localidad},
            {"label": "Código postal", "value": "3300"},
            {"label": "Provincia", "value": "Misiones"},
        ],
        "administrativa": [
            {"label": "N° usuario", "value": base["numero_usuario"]},
            {"label": "Fecha de ingreso", "value": "12/03/2019"},
            {"label": "Estado societario", "value": estado},
            {"label": "Categoría", "value": "Categoría A"},
            {"label": "Observaciones", "value": "—"},
        ],
    }


def get_asociados_cards():
    """Tarjetas de la pantalla principal de Asociados y servicios: cada una
    linkea a su propia pantalla interna (ver core:asociado_sub). Salvo
    "Ficha del asociado" —que ya tiene pantalla real (a través del listado)—,
    el resto abre una vista "en construcción" genérica hasta que se
    confirme su Historia de Usuario."""
    return [
        {"slug": "ficha", "label": "Ficha del asociado", "icon": "i-idcard",
         "description": "Consulta y edición de la ficha del asociado"},
        {"slug": "abm", "label": "ABM de asociado (rol múltiple)", "icon": "i-user-plus",
         "description": "Alta, baja y modificación de asociados, usuarios y proveedores"},
        {"slug": "cuota-capital", "label": "Cuota capital y excepciones", "icon": "i-coins",
         "description": "Gestión de aportes, cuotas y excepciones"},
        {"slug": "retorno-excedentes", "label": "Retorno de excedentes", "icon": "i-bars",
         "description": "Cálculo y liquidación de excedentes"},
        {"slug": "reintegro-baja", "label": "Reintegro al darse de baja", "icon": "i-file-out",
         "description": "Administración de reintegros de capital"},
        {"slug": "reportes-societarios", "label": "Reportes societarios", "icon": "i-book",
         "description": "Padrón, Libro societario y otros informes"},
        {"slug": "reclamos", "label": "Reclamos", "icon": "i-alert-bubble",
         "description": "Gestión de reclamos de asociados y usuarios"},
        {"slug": "ordenes-trabajo", "label": "Órdenes de trabajo", "icon": "i-wrench",
         "description": "Gestión de órdenes de trabajo y servicios"},
    ]


def get_associate_tabs(associate=None):
    """Solapas de la ficha, ya renombradas 1:1 según el mockup de referencia:
    General, Societario, Suscripción, Aportes, Suministros, Reclamos y OT,
    Familiares*, Proveedor*.

    "Proveedor*" solo se incluye si el asociado tiene el rol de proveedor
    activo (ver associate["es_proveedor"]) — si no, se oculta directamente
    de la lista de solapas, sin inventar más lógica que ese chequeo."""
    tabs = [
        {
            "id": "general",
            "label": "General",
            "kind": "general",
        },
        {
            "id": "societario",
            "label": "Societario",
            "kind": "fields",
            "fields": [
                {"label": "Fecha de ingreso", "value": "12/03/2019"},
                {"label": "Estado societario", "value": "Activo"},
            ],
        },
        {
            "id": "suscripcion",
            "label": "Suscripción",
            "kind": "fields_button",
            "fields": [
                {"label": "Acciones suscriptas", "value": "50"},
                {"label": "Capital integrado", "value": "$0,50"},
            ],
            "button_label": "Imprimir solicitud de alta",
        },
        {
            "id": "aportes",
            "label": "Aportes",
            "kind": "table",
            "headers": ["Período", "Servicio", "Cuota capital"],
            "rows": [
                ["07/2026", "Energía", "$1.240"],
            ],
        },
        {
            "id": "suministros",
            "label": "Suministros",
            "kind": "suministros",
            "items": [
                {"nis": "004521", "tipo": "Energía eléctrica",
                 "direccion": "Av. San Martín 450, Posadas", "activo": True},
            ],
        },
        {
            "id": "reclamos",
            "label": "Reclamos y OT",
            "kind": "reclamos",
            "headers": ["Tipo", "Descripción", "Fecha", "Estado"],
            "items": [
                {"tipo": "Reclamo técnico", "descripcion": "Falta de suministro",
                 "fecha": "03/06/2026", "estado": "Cerrado", "estado_kind": "good"},
                {"tipo": "OT", "descripcion": "Cambio de medidor",
                 "fecha": "22/07/2026", "estado": "En proceso", "estado_kind": "warning"},
            ],
        },
        {
            "id": "familiares",
            "label": "Familiares*",
            "dashed": True,
            "note": "*A confirmar — origen: sistema actual",
            "kind": "rows",
            "items": [
                {"label": "Hijo/a — sin obra social", "value": None},
            ],
        },
        {
            "id": "proveedor",
            "label": "Proveedor*",
            "dashed": True,
            "note": "*Solo si “Es proveedor” está activo — a confirmar",
            "kind": "fields",
            "fields": [
                {"label": "Tipo de proveedor", "value": "—", "disabled": True},
            ],
        },
    ]

    if associate is not None and not associate.get("es_proveedor"):
        tabs = [t for t in tabs if t["id"] != "proveedor"]

    return tabs
