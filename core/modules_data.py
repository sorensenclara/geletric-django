"""
Compatibilidad: el listado de módulos ahora vive en core/nav_map.py (mapa
de sitio v3 — 12 módulos en 4 bloques, con submenús). Este archivo solo
re-exporta para no romper imports viejos; el código nuevo importa de
nav_map directamente. Se puede borrar cuando nada lo importe.
"""
from .nav_map import MODULES, get_module  # noqa: F401
