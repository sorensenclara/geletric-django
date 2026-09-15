from django.urls import reverse

from .associate_data import get_asociados_cards
from .modules_data import MODULES
from .templatetags.core_extras import inline_icon


def sidebar_modules(request):
    """Disponible en todos los templates como {{ modules }}, para que la barra
    lateral se pueda armar desde base.html sin que cada vista la repita."""
    return {"modules": MODULES}


def sidebar_search_index(request):
    """Índice para el buscador de la barra lateral (ver dashboard.js,
    initSidebarSearch): una entrada por módulo de primer nivel más una por
    cada opción de menú/submenú, para que el filtrado ocurra en el
    navegador sin ir al servidor en cada letra tipeada.

    "Asociados y servicios" es, por ahora, el único módulo con pantalla
    propia por opción (ver associate_data.get_asociados_cards) — el resto
    linkea a la vista genérica del módulo (core:module_detail) hasta que su
    propia Historia de Usuario confirme una pantalla por ítem; buscar ahí
    igual sirve para llegar al módulo correcto."""
    entries = [{
        "label": "Inicio",
        "sub": "",
        "href": reverse("core:home"),
        "icon_kind": "sprite",
        "icon_id": "i-home",
    }]

    for module in MODULES:
        icon_svg = inline_icon(module["icon_white"], "nav-icon-img")
        module_href = reverse("core:module_detail", kwargs={"slug": module["slug"]})
        entries.append({
            "label": module["name"],
            "sub": "",
            "href": module_href,
            "icon_kind": "inline",
            "icon_svg": icon_svg,
        })

        if module["slug"] == "asociados":
            for card in get_asociados_cards():
                if card["slug"] == "ficha":
                    href = reverse("core:asociados_list")
                elif card["slug"] == "abm":
                    href = reverse("core:asociado_alta")
                else:
                    href = reverse("core:asociado_sub", kwargs={"subslug": card["slug"]})
                entries.append({
                    "label": card["label"],
                    "sub": module["name"],
                    "href": href,
                    "icon_kind": "inline",
                    "icon_svg": icon_svg,
                })
        else:
            for item_label in module["items"]:
                entries.append({
                    "label": item_label,
                    "sub": module["name"],
                    "href": module_href,
                    "icon_kind": "inline",
                    "icon_svg": icon_svg,
                })

    return {"sidebar_search_index": entries}
