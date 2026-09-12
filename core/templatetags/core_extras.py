"""
Filtros/tags propios de GELETRIC.

inline_icon resuelve un problema puntual: los íconos "white" de cada módulo
(core/images/SVG/icon white -*.svg) son archivos reales de diseño con
fill="#fff" fijo. Como <img>, ese blanco no se puede recolorear con CSS —
por eso el ícono de "Inicio" (que usa el sprite de <symbol> en base.html,
con stroke="currentColor") sí se pintaba de verde al estar activo, pero los
íconos de módulo no. Este tag lee el SVG, cambia ese fill fijo por
currentColor e inserta el markup inline, así el CSS del <a class="nav-item">
(activo / hover / inactivo) controla el color exactamente igual que hace con
los íconos del sprite.
"""
import functools
import re

from django import template
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe

register = template.Library()

_XML_PROLOG_RE = re.compile(r"<\?xml[^>]*\?>\s*")
_ID_ATTR_RE = re.compile(r'\s(?:id|data-name)="[^"]*"')
_WHITE_FILL_RE = re.compile(r'fill="#fff(?:fff)?"', re.IGNORECASE)


@functools.lru_cache(maxsize=64)
def _load_svg(static_path):
    abspath = finders.find(static_path)
    if not abspath:
        return ""
    with open(abspath, encoding="utf-8") as f:
        content = f.read()
    content = _XML_PROLOG_RE.sub("", content)
    content = _ID_ATTR_RE.sub("", content)  # evita ids duplicados: el ícono se repite en cada página
    content = _WHITE_FILL_RE.sub('fill="currentColor"', content)
    return content.strip()


@register.simple_tag
def inline_icon(static_path, css_class=""):
    svg = _load_svg(static_path)
    if not svg:
        return ""
    if css_class:
        svg = svg.replace("<svg ", f'<svg class="{css_class}" ', 1)
    return mark_safe(svg)
