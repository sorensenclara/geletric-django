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
from django.utils.html import format_html
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


# ---------- {% cell %} / {% endcell %}: celda de tabla responsive ----------
# Las tablas con clase .table-responsive (dashboard.css) necesitan que cada
# <td> lleve un atributo data-th con el nombre de su columna, para que en
# mobile el CSS pueda mostrarlo como etiqueta arriba del valor (mismo
# comportamiento que las tablas de argentina.gob.ar: thead se oculta, cada
# celda se arma como data-th::before). Este tag genera ese <td data-th="…">
# a partir de la MISMA etiqueta que ya se escribe en el <th> de esa columna,
# sin tocar el contenido de la celda — adentro puede ir cualquier markup
# (badges, links, íconos) exactamente como en un <td> normal.
#
# Uso (una fila de ejemplo; el resto de las filas del listado sale igual
# por el {% for %} de Django, no hace falta repetir nada por fila):
#
#   <table class="ficha-table table-responsive">
#     <thead><tr><th>Nombre</th><th>Estado</th></tr></thead>
#     <tbody>
#       {% for a in asociados %}
#       <tr>
#         {% cell "Nombre" %}{{ a.nombre_completo }}{% endcell %}
#         {% cell "Estado" %}<span class="status-pill good">{{ a.estado }}</span>{% endcell %}
#       </tr>
#       {% endfor %}
#     </tbody>
#   </table>
class TableCellNode(template.Node):
    def __init__(self, label_expr, nodelist):
        self.label_expr = label_expr
        self.nodelist = nodelist

    def render(self, context):
        label = self.label_expr.resolve(context)
        content = self.nodelist.render(context)
        return format_html('<td data-th="{}">{}</td>', label, mark_safe(content))


@register.tag(name="cell")
def do_cell(parser, token):
    bits = token.split_contents()
    if len(bits) != 2:
        raise template.TemplateSyntaxError(
            "%r requiere exactamente un argumento: la etiqueta de la columna (ej. %% cell \"Estado\" %%)" % bits[0]
        )
    label_expr = parser.compile_filter(bits[1])
    nodelist = parser.parse(("endcell",))
    parser.delete_first_token()
    return TableCellNode(label_expr, nodelist)


@register.filter(name="zip")
def zip_lists(headers, row):
    """
    Empareja encabezados con valores de una misma fila (listas paralelas,
    como t.headers / cada item de t.rows en asociado_ficha.html) para poder
    armar {% cell %} con la etiqueta correcta en una tabla cuyas columnas
    son dinámicas, sin tener que escribir cada columna a mano:

        {% for h, valor in t.headers|zip:row %}
          {% cell h %}{{ valor }}{% endcell %}
        {% endfor %}
    """
    return zip(headers, row)
