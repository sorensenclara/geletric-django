from .modules_data import MODULES


def sidebar_modules(request):
    """Disponible en todos los templates como {{ modules }}, para que la barra
    lateral se pueda armar desde base.html sin que cada vista la repita."""
    return {"modules": MODULES}
