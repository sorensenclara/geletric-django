from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from . import associate_data as ad
from . import sample_data as sd
from .forms import AsociadoAltaForm, GeletricLoginForm
from .models import Asociado
from .modules_data import get_module


def _with_module_style(item):
    """Adjunta icon_tile/color/module_name del módulo referenciado en item['module'].
    Centraliza el join acá (en la vista) en vez de en el template."""
    module = get_module(item["module"])
    return {
        **item,
        "icon_tile": module["icon_tile"],
        "color": module["color"],
        "module_name": module["name"],
    }


def home(request):
    today = timezone.localdate()

    stats = [_with_module_style(s) for s in sd.get_stats()]
    tasks = [_with_module_style(t) for t in sd.get_tasks()]
    news = [_with_module_style(n) for n in sd.get_news()]
    quick_access = [get_module(slug) for slug in sd.QUICK_ACCESS_SLUGS]

    network = sd.get_network_status()
    network_total = sum(n["value"] for n in network)
    network_pct = round(network[0]["value"] / network_total * 100)

    context = {
        "active_slug": "home",
        "today_label": sd.format_today_long(today),
        "last_update_label": timezone.localtime().strftime("%H:%M"),
        "stats": stats,
        "tasks": tasks,
        "news": news,
        "quick_access": quick_access,
        "chart_series": sd.get_consumo_series(today),
        "network": network,
        "network_total": network_total,
        "network_pct": network_pct,
    }
    return render(request, "core/home.html", context)


def module_detail(request, slug):
    module = get_module(slug)
    if module is None:
        raise Http404("Módulo no encontrado")

    # Asociados y servicios ya tiene pantalla propia: una grilla de tarjetas
    # que linkean a cada funcionalidad interna (ver core:asociado_sub), en
    # vez del placeholder de texto plano. El resto de los módulos sigue
    # mostrando la lista genérica hasta que se confirme su propia Historia
    # de Usuario.
    if slug == "asociados":
        return render(request, "core/asociados_menu.html", {
            "active_slug": slug,
            "module": module,
            "cards": ad.get_asociados_cards(),
        })

    items = [{"label": label, "href": None} for label in module["items"]]
    return render(request, "core/module.html", {"active_slug": slug, "module": module, "items": items})


def asociados_list(request):
    """Listado de asociados: paso previo a la ficha. Buscador general +
    filtros avanzados agregables ("+ Agregar filtro"), a pedido de Clara —
    ver associate_data.buscar_asociados() y get_filtros_disponibles() para
    el detalle. A diferencia de la versión anterior, acá el filtrado se
    resuelve en el QuerySet de Asociado, no sobre la lista ya materializada
    de get_asociados_list() (esa función sigue existiendo tal cual, la usan
    asociados_search y los tests de AssociateDataTests).

    filtros_disponibles viaja al template con cada filtro ya resuelto
    contra la querystring, con DOS claves distintas que no hay que
    confundir:
      - "active"  — tiene un valor real cargado, lo que lo vuelve parte
                     del QuerySet (ver filtros_valores más abajo) y cuenta
                     para hay_filtros_activos / "Limpiar filtros".
      - "visible" — el usuario lo agregó a la interfaz con
                     "+ Agregar filtro", tenga o no un valor todavía. Se
                     reconstruye a partir de "campos_visibles" (un único
                     parámetro con las keys separadas por coma que
                     dashboard.js mantiene sincronizado con los filtros
                     agregados — ver initDynamicFilterBuilder) en vez de
                     inferirlo del valor, precisamente para poder tener en
                     pantalla un filtro agregado pero todavía vacío (p.ej.
                     agregaste Categoría y Estado pero solo completaste
                     Localidad, y presionaste "Filtrar" así): si "visible"
                     dependiera de "active" como antes, esos dos
                     desaparecerían al recargar por estar vacíos.
    El template dibuja cada filtro agregado según "visible" (no "active"),
    y el JS sabe cuáles faltan ofrecer en "+ Agregar filtro" también según
    "visible"."""
    q = request.GET.get("q", "").strip()

    campos_visibles_set = {
        c.strip() for c in request.GET.get("campos_visibles", "").split(",") if c.strip()
    }

    filtros_disponibles = ad.get_filtros_disponibles()
    filtros_valores = {}

    for filtro in filtros_disponibles:
        if filtro["type"] == "daterange":
            desde_param, hasta_param = filtro["params"]
            desde = request.GET.get(desde_param, "").strip()
            hasta = request.GET.get(hasta_param, "").strip()
            filtro["desde"] = desde
            filtro["hasta"] = hasta
            filtro["active"] = bool(desde or hasta)
            if filtro["active"]:
                filtros_valores[filtro["key"]] = {"desde": desde, "hasta": hasta}
        else:
            valor = request.GET.get(filtro["key"], "").strip()
            filtro["value"] = valor
            filtro["active"] = bool(valor)
            if filtro["active"]:
                filtros_valores[filtro["key"]] = valor
        filtro["visible"] = filtro["active"] or filtro["key"] in campos_visibles_set

    asociados = ad.buscar_asociados(q=q, filtros=filtros_valores)
    hay_filtros_activos = bool(q) or any(f["active"] for f in filtros_disponibles)
    campos_visibles_actual = ",".join(f["key"] for f in filtros_disponibles if f["visible"])

    return render(request, "core/asociados_list.html", {
        "active_slug": "asociados",
        "module": get_module("asociados"),
        "asociados": asociados,
        "total_asociados": Asociado.objects.count(),
        "q": q,
        "filtros_disponibles": filtros_disponibles,
        "hay_filtros_activos": hay_filtros_activos,
        "campos_visibles_actual": campos_visibles_actual,
    })


def asociados_search(request):
    """Buscador del topbar (ver dashboard.js, initTopbarSearch): devuelve en
    JSON los asociados que coinciden con lo tipeado, para el desplegable
    que aparece bajo la barra — sin recargar la página. El placeholder de
    esa barra menciona "asociado, suministro, factura, orden de trabajo",
    pero hoy solo Asociado tiene datos y pantalla real (ver
    associate_data.get_asociados_list); el resto se suma cuando tenga su
    propia Historia de Usuario.

    Requiere 2+ caracteres (evita devolver el padrón completo con la
    primera letra) y devuelve como mucho 8 resultados, coincidencias por
    nombre o N° de asociado — primero las que empiezan con lo tipeado."""
    q = request.GET.get("q", "").strip().lower()
    if len(q) < 2:
        return JsonResponse({"results": []})

    empieza_con = []
    contiene = []
    for a in ad.get_asociados_list():
        nombre = a["nombre_completo"].lower()
        numero = a["numero_asociado"].lower()
        if nombre.startswith(q) or numero.startswith(q):
            empieza_con.append(a)
        elif q in nombre or q in numero:
            contiene.append(a)

    resultados = [{
        "numero_asociado": a["numero_asociado"],
        "nombre_completo": a["nombre_completo"],
        "estado": a["estado"],
        "href": reverse("core:asociado_ficha", kwargs={"numero_asociado": a["numero_asociado"]}),
    } for a in (empieza_con + contiene)[:8]]

    return JsonResponse({"results": resultados})


def asociado_ficha(request, numero_asociado):
    """Ficha del asociado: ventana con encabezado, resumen y solapas,
    primera funcionalidad real del módulo Asociados y servicios. Se llega
    acá eligiendo un asociado del listado (core:asociados_list). Datos
    reales desde el 14/09/2026 — ver associate_data.py. Si numero_asociado
    no existe, 404 (antes, con datos de muestra, mostraba por error el
    primer asociado de la lista)."""
    associate = ad.get_associate(numero_asociado)
    if associate is None:
        raise Http404("Asociado no encontrado")
    return render(request, "core/asociado_ficha.html", {
        "active_slug": "asociados",
        "module": get_module("asociados"),
        "associate": associate,
        "tabs": ad.get_associate_tabs(associate),
    })


def asociado_alta(request):
    """Alta de asociado (HU-ASO-01) — primer formulario del sistema con
    persistencia real (ver core/models.py: Asociado). Desde el 14/09/2026
    el listado y la ficha (core:asociados_list, core:asociado_ficha)
    también son reales: un alta hecha acá ya aparece ahí de inmediato,
    igual que la suscripción de acciones que se registra acá (HU-ASO-02),
    visible en la solapa "Suscripción" de la ficha.

    PREG-ASO-01 (bloqueante en la HU) sigue sin resolverse: el número de
    asociado/usuario se asigna con un correlativo simple, sin reutilizar
    números dados de baja — ver Asociado.siguiente_numero_asociado."""
    if request.method == "POST":
        form = AsociadoAltaForm(request.POST)
        if form.is_valid():
            asociado = form.save()
            mensaje = (
                f"Asociado N° {asociado.numero_asociado} (Usuario N° {asociado.numero_usuario}) "
                f"creado correctamente."
            )
            if form.suscripcion:
                s = form.suscripcion
                mensaje += (
                    f" Suscripción registrada: Título N° {s.numero_titulo}, "
                    f"{s.cantidad_acciones} acciones, capital suscripto ${s.capital_suscripto}."
                )
                messages.success(request, mensaje)
            else:
                messages.success(request, mensaje)
                messages.warning(request, form.suscripcion_error)
            return redirect("core:asociado_alta")
    else:
        form = AsociadoAltaForm()

    return render(request, "core/asociado_alta.html", {
        "active_slug": "asociados",
        "module": get_module("asociados"),
        "form": form,
    })


class GeletricLoginView(LoginView):
    """Login real (django.contrib.auth): valida usuario/contraseña contra la
    base de usuarios de Django, sin lógica propia inventada. "Recordarme" sin
    tildar expira la sesión al cerrar el navegador; tildado, usa la duración
    default de Django (ver SESSION_COOKIE_AGE)."""
    template_name = "core/login.html"
    authentication_form = GeletricLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.POST.get("remember"):
            self.request.session.set_expiry(0)
        return response


def wizard_demo(request):
    """Demo del componente de wizard (pasos de un proceso largo). Todavía no
    hay ningún proceso multi-paso real confirmado en el sistema — esta
    pantalla existe solo para mostrar el componente funcionando, con datos de
    ejemplo. Cuando se confirme el primer proceso real (alta de asociado,
    etc.), este mismo componente se reutiliza ahí."""
    steps = [
        {"label": "Datos personales", "state": "done"},
        {"label": "Domicilio y contacto", "state": "active"},
        {"label": "Documentación", "state": "pending"},
        {"label": "Confirmación", "state": "pending"},
    ]
    return render(request, "core/component_demo.html", {"steps": steps})


def asociado_sub(request, subslug):
    """Funcionalidades de Asociados y servicios que todavía no tienen
    pantalla propia (ver ad.get_asociados_cards): vista "en construcción"
    genérica hasta que se confirme su Historia de Usuario. "ficha" no pasa
    por acá — tiene su propia vista real (asociado_ficha)."""
    card = next(
        (c for c in ad.get_asociados_cards() if c["slug"] == subslug and c["slug"] != "ficha"),
        None,
    )
    if card is None:
        raise Http404("Página no encontrada")
    return render(request, "core/asociado_sub.html", {
        "active_slug": "asociados",
        "module": get_module("asociados"),
        "card": card,
    })
