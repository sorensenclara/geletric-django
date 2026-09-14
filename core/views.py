from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone

from . import associate_data as ad
from . import sample_data as sd
from .forms import AsociadoAltaForm, GeletricLoginForm
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
    """Listado de asociados: paso previo a la ficha (buscador por nombre/N°
    de asociado + filtros de estado/rol/localidad). Datos de muestra por
    ahora — ver associate_data.get_asociados_list()."""
    q = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "")
    rol = request.GET.get("rol", "")
    localidad = request.GET.get("localidad", "")

    asociados = ad.get_asociados_list()

    if q:
        q_lower = q.lower()
        asociados = [
            a for a in asociados
            if q_lower in a["nombre_completo"].lower() or q_lower in a["numero_asociado"]
        ]
    if estado:
        asociados = [a for a in asociados if a["estado"] == estado]
    if rol:
        asociados = [a for a in asociados if rol in a["roles"]]
    if localidad:
        asociados = [a for a in asociados if a["localidad"] == localidad]

    return render(request, "core/asociados_list.html", {
        "active_slug": "asociados",
        "module": get_module("asociados"),
        "asociados": asociados,
        "total_asociados": len(ad.get_asociados_list()),
        "q": q,
        "estado_filter": estado,
        "rol_filter": rol,
        "localidad_filter": localidad,
        "localidades": ad.get_localidades(),
    })


def asociado_ficha(request, numero_asociado):
    """Ficha del asociado: ventana con encabezado, resumen y solapas,
    primera funcionalidad real del módulo Asociados y servicios. Se llega
    acá eligiendo un asociado del listado (core:asociados_list). Datos de
    muestra por ahora — ver associate_data.py."""
    associate = ad.get_associate(numero_asociado)
    return render(request, "core/asociado_ficha.html", {
        "active_slug": "asociados",
        "module": get_module("asociados"),
        "associate": associate,
        "tabs": ad.get_associate_tabs(associate),
    })


def asociado_alta(request):
    """Alta de asociado (HU-ASO-01) — primer formulario del sistema con
    persistencia real (ver core/models.py: Asociado). El listado y la
    ficha (core:asociados_list, core:asociado_ficha) siguen mostrando
    datos de muestra de associate_data.py hasta que su propia Historia de
    Usuario quede cerrada: un alta hecha acá todavía no aparece ahí.

    PREG-ASO-01 (bloqueante en la HU) sigue sin resolverse: el número de
    asociado/usuario se asigna con un correlativo simple, sin reutilizar
    números dados de baja — ver Asociado.siguiente_numero_asociado."""
    if request.method == "POST":
        form = AsociadoAltaForm(request.POST)
        if form.is_valid():
            asociado = form.save()
            messages.success(
                request,
                f"Asociado N° {asociado.numero_asociado} (Usuario N° {asociado.numero_usuario}) "
                f"creado correctamente.",
            )
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
