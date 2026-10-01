"""
Listado y Ficha del asociado (módulo Asociados y servicios).

Hasta el 14/09/2026 este archivo era un directorio fijo de asociados de
muestra (_ASOCIADOS_MUESTRA): ni el listado ni la ficha leían la base de
datos. A pedido de Clara, get_asociados_list(), get_localidades() y
get_associate(numero_asociado) ahora consultan el modelo real (core.models
.Asociado, más SuscripcionAcciones para la solapa "Suscripción") — mismo
patrón que seed_demo.py en el proyecto de San Cayetano: primero cargar
datos reales, después conectar la pantalla a ellos.

Se mantiene EXACTAMENTE la misma forma de diccionario que consumían los
templates (asociados_list.html, asociado_ficha.html), así que ninguno de
los dos necesitó cambios.

Lo que sigue siendo de ejemplo, documentado en cada lugar donde aparece,
son los datos de módulos que todavía no existen como tales: aportes,
suministros, reclamos/OT y familiares. Esos no tienen modelo propio
todavía — conectarlos cuando su Historia de Usuario se confirme, sin
inventar la lógica acá.

Nota sobre "roles": HU-ASO-01 asigna numero_asociado y numero_usuario a
TODO alta, sin excepción (ver forms.AsociadoAltaForm.save) — por eso todo
Asociado real es a la vez "Asociado" y "Usuario"; "Proveedor" se agrega
solo si es_proveedor está tildado. No hay todavía una forma de dar de alta
un asociado que sea nada más "Usuario" (como sí había en los datos de
muestra) — si el DEV confirma ese caso como real, hay que revisar acá.
"""
import datetime

from django.db.models import Q

from .models import Asociado, SuscripcionAcciones


def _iniciales(nombre_completo):
    partes = nombre_completo.split()
    if not partes:
        return "—"
    if len(partes) < 2:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


def _formato_fecha(fecha):
    if not fecha:
        return "—"
    return fecha.strftime("%d/%m/%Y")


def _formato_dni(numero):
    if not numero or not numero.isdigit():
        return numero or "—"
    return f"{int(numero):,}".replace(",", ".")


def _formato_cuit(numero):
    if not numero or len(numero) != 11:
        return numero or "—"
    return f"{numero[:2]}-{numero[2:10]}-{numero[10]}"


def _roles_de(asociado):
    # Ver nota de módulo: HU-ASO-01 siempre asigna ambos números.
    roles = ["Asociado", "Usuario"]
    if asociado.es_proveedor:
        roles.append("Proveedor")
    return roles


def _asociado_a_dict_listado(asociado):
    return {
        "numero_asociado": asociado.numero_asociado,
        "numero_usuario": asociado.numero_usuario,
        "nombre_completo": asociado.nombre_o_razon_social,
        "estado": asociado.get_estado_societario_display(),
        "localidad": asociado.localidad or "—",
        "direccion": asociado.domicilio,
        "roles": _roles_de(asociado),
    }


def get_asociados_list():
    """Listado real de asociados (buscador + filtros de estado/rol/
    localidad de la vista actúan sobre esta misma lista)."""
    return [_asociado_a_dict_listado(a) for a in Asociado.objects.all()]


def get_localidades():
    """Localidades presentes entre los asociados reales, para el filtro
    del listado (vacío hasta que haya al menos un asociado cargado con
    localidad)."""
    localidades = (
        Asociado.objects.exclude(localidad="")
        .values_list("localidad", flat=True)
        .distinct()
    )
    return sorted(set(localidades))


def get_categorias():
    """Categorías presentes entre los asociados reales, para el filtro de
    categoría del listado — mismo criterio que get_localidades(): es un
    CharField de texto libre en el modelo, pero el filtro solo ofrece los
    valores que ya están en uso."""
    categorias = (
        Asociado.objects.exclude(categoria="")
        .values_list("categoria", flat=True)
        .distinct()
    )
    return sorted(set(categorias))


# ---------- Buscador general + filtros avanzados del listado ----------
# Definición de los filtros que el listado de asociados ofrece agregar con
# "+ Agregar filtro" (ver asociados_list.html / dashboard.js,
# initDynamicFilterBuilder). Cada entrada define:
#   key     — también el nombre del parámetro GET (salvo "daterange", que
#             usa "params" en su lugar porque necesita dos).
#   label   — lo que ve el usuario.
#   type    — "select" | "boolean" | "text" | "daterange": decide qué
#             control se dibuja (ver el template y el JS).
#   options — solo para "select"/"boolean": [{"value", "label"}, ...].
#   params  — solo para "daterange": [param_desde, param_hasta].
# Se arma de nuevo en cada pedido (no es una constante de módulo) porque
# "localidad" y "categoria" dependen de los datos reales cargados en ese
# momento — igual que ya hacía el <select> de localidad del listado
# anterior con get_localidades().
def get_filtros_disponibles():
    # "icon" es solo una referencia al sprite de íconos ya existente
    # (core/templates/core/_icon_sprite.html) — ayuda a escanear el menú
    # "+ Agregar filtro" del listado, no afecta el filtrado en absoluto.
    return [
        {
            "key": "estado",
            "label": "Estado societario",
            "type": "select",
            "icon": "i-check",
            "options": [
                {"value": value, "label": label}
                for value, label in Asociado.ESTADO_SOCIETARIO_CHOICES
            ],
        },
        {
            "key": "localidad",
            "label": "Localidad",
            "type": "select",
            "icon": "i-map",
            "options": [{"value": loc, "label": loc} for loc in get_localidades()],
        },
        {
            "key": "tipo_persona",
            "label": "Tipo de persona",
            "type": "select",
            "icon": "i-user",
            "options": [
                {"value": value, "label": label}
                for value, label in Asociado.TIPO_PERSONA_CHOICES
            ],
        },
        {
            "key": "condicion_iva",
            "label": "Condición de IVA",
            "type": "select",
            "icon": "i-file",
            "options": [
                {"value": value, "label": label}
                for value, label in Asociado.CONDICION_IVA_CHOICES
            ],
        },
        {
            "key": "categoria",
            "label": "Categoría",
            "type": "select",
            "icon": "i-flag",
            "options": [{"value": cat, "label": cat} for cat in get_categorias()],
        },
        {
            "key": "es_proveedor",
            "label": "Proveedor",
            "type": "boolean",
            "icon": "i-cart",
            "options": [{"value": "si", "label": "Sí"}, {"value": "no", "label": "No"}],
        },
        {
            "key": "fecha_ingreso",
            "label": "Fecha de ingreso",
            "type": "daterange",
            "icon": "i-calendar",
            "params": ["fecha_ingreso_desde", "fecha_ingreso_hasta"],
        },
        {
            "key": "dni_cuit",
            "label": "DNI/CUIT",
            "type": "text",
            "icon": "i-idcard",
        },
        {
            "key": "direccion",
            "label": "Dirección",
            "type": "text",
            "icon": "i-map",
        },
    ]


def _parsear_fecha(valor):
    """Convierte "YYYY-MM-DD" (lo que manda un <input type="date">) a
    date, o None si viene vacío/mal formado — un filtro de fecha inválido
    o incompleto se ignora en vez de romper la consulta."""
    if not valor:
        return None
    try:
        return datetime.date.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def buscar_asociados(q="", filtros=None):
    """Listado filtrable de asociados (HU de búsqueda y filtros avanzados
    del listado): a diferencia de get_asociados_list(), que sigue
    devolviendo SIEMPRE todos los asociados sin filtrar —la usan
    asociados_search (buscador del topbar) y los tests de
    AssociateDataTests, que no deben cambiar de comportamiento—, acá el
    buscador general y cada filtro avanzado se resuelven como condiciones
    sobre el QuerySet de Asociado (Q() combinados con OR para el buscador
    general, .filter() encadenado —AND— para cada filtro activo) antes de
    tocar un solo registro en Python; recién con el QuerySet ya filtrado se
    arma la lista de diccionarios que consume el template, igual que hacía
    get_asociados_list().

    `filtros` es un dict {key: valor} con solo los filtros ACTIVOS (ver
    views.asociados_list, que arma este dict a partir de la querystring) —
    "es_proveedor" espera "si"/"no", "fecha_ingreso" espera
    {"desde": ..., "hasta": ...} (ambas claves opcionales), el resto espera
    el string tal cual viene del <select>/<input>.

    Ninguno de estos filtros cruza relaciones (SuscripcionAcciones,
    Suministro) — son todos campos propios de Asociado — así que no hace
    falta select_related/prefetch_related ni .distinct() para evitar filas
    duplicadas. Si en algún momento se agrega un filtro que sí cruce una
    relación (por ejemplo, por datos de Suministro), hay que revisar esto:
    un .filter() sobre una relación "a muchos" puede multiplicar filas."""
    filtros = filtros or {}
    queryset = Asociado.objects.all()

    q = (q or "").strip()
    if q:
        queryset = queryset.filter(
            Q(nombre_apellido__icontains=q)
            | Q(razon_social__icontains=q)
            | Q(numero_asociado__icontains=q)
            | Q(numero_usuario__icontains=q)
            | Q(numero_documento__icontains=q)
            | Q(cuit__icontains=q)
            | Q(domicilio__icontains=q)
            | Q(localidad__icontains=q)
            | Q(telefono_fijo__icontains=q)
            | Q(celular__icontains=q)
            | Q(email__icontains=q)
            | Q(email_alternativo__icontains=q)
        )

    estado = filtros.get("estado")
    if estado:
        queryset = queryset.filter(estado_societario=estado)

    localidad = filtros.get("localidad")
    if localidad:
        queryset = queryset.filter(localidad=localidad)

    tipo_persona = filtros.get("tipo_persona")
    if tipo_persona:
        queryset = queryset.filter(tipo_persona=tipo_persona)

    condicion_iva = filtros.get("condicion_iva")
    if condicion_iva:
        queryset = queryset.filter(condicion_iva=condicion_iva)

    categoria = filtros.get("categoria")
    if categoria:
        queryset = queryset.filter(categoria=categoria)

    es_proveedor = filtros.get("es_proveedor")
    if es_proveedor in ("si", "no"):
        queryset = queryset.filter(es_proveedor=(es_proveedor == "si"))

    fecha_ingreso = filtros.get("fecha_ingreso")
    if fecha_ingreso:
        desde = _parsear_fecha(fecha_ingreso.get("desde"))
        hasta = _parsear_fecha(fecha_ingreso.get("hasta"))
        if desde:
            queryset = queryset.filter(fecha_ingreso__gte=desde)
        if hasta:
            queryset = queryset.filter(fecha_ingreso__lte=hasta)

    dni_cuit = filtros.get("dni_cuit")
    if dni_cuit:
        queryset = queryset.filter(
            Q(numero_documento__icontains=dni_cuit) | Q(cuit__icontains=dni_cuit)
        )

    direccion = filtros.get("direccion")
    if direccion:
        queryset = queryset.filter(domicilio__icontains=direccion)

    return [_asociado_a_dict_listado(a) for a in queryset]


def get_associate(numero_asociado=None):
    """Ficha completa de un asociado real, o None si no existe ningún
    asociado con ese numero_asociado — antes (con datos de muestra) un
    numero_asociado no encontrado mostraba el primero de la lista por
    error; ahora se corrige: ver views.asociado_ficha, que convierte este
    None en un 404."""
    try:
        asociado = Asociado.objects.get(numero_asociado=numero_asociado)
    except Asociado.DoesNotExist:
        return None

    nombre_completo = asociado.nombre_o_razon_social
    estado_display = asociado.get_estado_societario_display()
    es_real = asociado.tipo_persona == Asociado.TIPO_PERSONA_REAL

    if es_real:
        personal = [
            {"label": "Nombre y apellido", "value": asociado.nombre_apellido or "—"},
            {"label": "DNI", "value": _formato_dni(asociado.numero_documento)},
            {"label": "CUIT/CUIL", "value": _formato_cuit(asociado.cuit) if asociado.cuit else "—"},
            {"label": "Fecha de nacimiento", "value": _formato_fecha(asociado.fecha_nacimiento_constitucion)},
            {"label": "Género", "value": asociado.get_sexo_display() if asociado.sexo else "—"},
        ]
    else:
        personal = [
            {"label": "Razón social", "value": asociado.razon_social or "—"},
            {"label": "Tipo de organismo", "value": asociado.tipo_organismo or "—"},
            {"label": "CUIT", "value": _formato_cuit(asociado.numero_documento)},
            {"label": "Fecha de constitución", "value": _formato_fecha(asociado.fecha_nacimiento_constitucion)},
        ]

    return {
        "nombre_completo": nombre_completo,
        "iniciales": _iniciales(nombre_completo),
        "numero_asociado": asociado.numero_asociado,
        "numero_usuario": asociado.numero_usuario,
        "estado": estado_display,
        "localidad": asociado.localidad or "—",
        "direccion": asociado.domicilio,
        "activo": asociado.estado_societario == "activo",
        "es_asociado": "Asociado" in _roles_de(asociado),
        "es_usuario": "Usuario" in _roles_de(asociado),
        "es_proveedor": asociado.es_proveedor,
        # suministros/deuda_total/reclamos_abiertos: de ejemplo visual, esos
        # módulos todavía no existen — conectar cuando existan.
        "resumen": [
            {"id": "estado", "label": "Estado", "value": estado_display, "kind": "status"},
            {"id": "suministros", "label": "Suministros", "value": "1 activo"},
            {"id": "deuda", "label": "Deuda total", "value": "$0", "chevron": True},
            {"id": "reclamos", "label": "Reclamos abiertos", "value": "0", "chevron": True},
        ],
        "personal": personal,
        "contacto": [
            {"label": "Teléfono fijo", "value": asociado.telefono_fijo or "—"},
            {"label": "Celular", "value": asociado.celular or "—"},
            {"label": "Email", "value": asociado.email or "—"},
            {"label": "Email alternativo", "value": asociado.email_alternativo or "—"},
        ],
        "domicilio_general": [
            {"label": "Domicilio fiscal", "value": asociado.domicilio},
            {"label": "Ruta / subruta", "value": asociado.ruta_subruta or "—"},
            {"label": "Localidad", "value": asociado.localidad or "—"},
            {"label": "Código postal", "value": asociado.codigo_postal or "—"},
            {"label": "Provincia", "value": asociado.provincia or "—"},
        ],
        "administrativa": [
            {"label": "N° usuario", "value": asociado.numero_usuario},
            {"label": "Fecha de ingreso", "value": _formato_fecha(asociado.fecha_ingreso)},
            {"label": "Estado societario", "value": estado_display},
            {"label": "Categoría", "value": asociado.categoria or "—"},
            {"label": "Observaciones", "value": asociado.observaciones or "—"},
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
    """Solapas de la ficha: General, Societario, Suscripción, Aportes,
    Suministros, Reclamos y OT, Familiares*, Proveedor*.

    Societario y Suscripción ya muestran datos reales del asociado (ver
    _asociado_real_de). Aportes/Suministros/Reclamos/Familiares siguen
    siendo de ejemplo visual: son módulos propios que todavía no existen
    (no tienen modelo ni Historia de Usuario confirmada) — no hay que
    inventar esa lógica acá, solo dejarlo documentado.

    "Proveedor*" solo se incluye si el asociado tiene el rol de proveedor
    activo (ver associate["es_proveedor"]) — si no, se oculta directamente
    de la lista de solapas, sin inventar más lógica que ese chequeo."""
    asociado = None
    if associate is not None:
        asociado = Asociado.objects.filter(numero_asociado=associate["numero_asociado"]).first()

    if asociado is not None:
        societario_fields = [
            {"label": "Fecha de ingreso", "value": _formato_fecha(asociado.fecha_ingreso)},
            {"label": "Estado societario", "value": asociado.get_estado_societario_display()},
        ]
        suscripcion = asociado.suscripciones.order_by("-fecha_suscripcion", "-numero_titulo").first()
    else:
        societario_fields = [
            {"label": "Fecha de ingreso", "value": "—"},
            {"label": "Estado societario", "value": "—"},
        ]
        suscripcion = None

    if suscripcion is not None:
        suscripcion_fields = [
            {"label": "N° de título", "value": suscripcion.numero_titulo},
            {"label": "Acciones suscriptas", "value": str(suscripcion.cantidad_acciones)},
            {"label": "Capital suscripto", "value": f"${suscripcion.capital_suscripto}"},
            {"label": "Fecha de suscripción", "value": _formato_fecha(suscripcion.fecha_suscripcion)},
        ]
    else:
        # HU-ASO-02, Escenario 6: puede no haber suscripción registrada
        # (faltaba el valor nominal vigente al momento del alta).
        suscripcion_fields = [
            {"label": "Acciones suscriptas", "value": "—"},
            {"label": "Capital suscripto", "value": "—"},
        ]

    direccion_suministro = (associate or {}).get("direccion", "—")
    localidad_suministro = (associate or {}).get("localidad", "—")
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
            "fields": societario_fields,
        },
        {
            "id": "suscripcion",
            "label": "Suscripción",
            "kind": "fields_button",
            "fields": suscripcion_fields,
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
                 "direccion": f"{direccion_suministro}, {localidad_suministro}", "activo": True},
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
