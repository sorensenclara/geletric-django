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
