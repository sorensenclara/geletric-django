from django.urls import reverse

from .nav_map import GROUPS, MODULES
from .templatetags.core_extras import module_icon


def module_href(module):
    """URL de entrada de un módulo: su pantalla real si la tiene
    (url_name, p. ej. Asociados → listado), si no /modulos/<slug>/."""
    url_name = (module.get("view") or {}).get("url_name")
    if url_name:
        return reverse(url_name)
    return reverse("core:module_detail", kwargs={"slug": module["slug"]})


def item_href(module, item):
    return reverse("core:nav_item", kwargs={"slug": module["slug"], "item_slug": item["slug"]})


def card_href(module, item, card):
    return reverse("core:nav_card", kwargs={
        "slug": module["slug"], "item_slug": item["slug"], "card_slug": card["slug"],
    })


def sidebar_modules(request):
    """{{ nav_groups }} en todos los templates: los bloques del sidebar ya
    con el href de cada módulo e ítem resuelto, para que base.html solo
    tenga que recorrerlos. {{ modules }} se mantiene por compatibilidad."""
    groups = []
    for g in GROUPS:
        mods = []
        for m in g["modules"]:
            mods.append({
                **m,
                "href": module_href(m),
                "items": [{**it, "href": item_href(m, it)} for it in m.get("sub", [])],
            })
        groups.append({**g, "modules": mods})
    return {"nav_groups": groups, "modules": MODULES}


def sidebar_search_index(request):
    """Índice para el buscador de la barra lateral (ver dashboard.js,
    initSidebarSearch): una entrada por módulo, por ítem de submenú y por
    tarjeta de cada página de tarjetas del mapa v3, para que el filtrado
    ocurra en el navegador sin ir al servidor en cada letra tipeada."""
    entries = [{
        "label": "Inicio", "sub": "", "href": reverse("core:home"),
        "icon_kind": "sprite", "icon_id": "i-home",
    }]

    for m in MODULES:
        icon_svg = str(module_icon(m, "white", "nav-icon-img"))
        entries.append({"label": m["name"], "sub": "", "href": module_href(m),
                        "icon_kind": "inline", "icon_svg": icon_svg})
        for it in m.get("sub", []):
            entries.append({"label": it["label"], "sub": m["name"], "href": item_href(m, it),
                            "icon_kind": "inline", "icon_svg": icon_svg})
            for cd in it["view"].get("cards", []):
                entries.append({"label": cd["label"], "sub": f'{m["name"]} › {it["label"]}',
                                "href": card_href(m, it, cd),
                                "icon_kind": "inline", "icon_svg": icon_svg})

    return {"sidebar_search_index": entries}
