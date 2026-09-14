"""
Validaciones de identificación fiscal (HU-ASO-01 — Alta de asociado).

Funciones puras, sin dependencia de modelos ni formularios, para que se
puedan testear de forma aislada. Las reglas vienen de las "Decisiones
tomadas con el usuario" de HU-ASO-01:

- Normalización: se descarta todo lo que no sea dígito (Escenario 7).
- CUIT: dígito verificador por módulo 11 (Escenarios 4, 10, 13) y prefijo
  coherente con el tipo de persona (Escenario 14) — 20/23/24/27 para
  existencia real, 30/33/34 para existencia ideal.
- Duplicados por equivalencia DNI-CUIT (Escenario 12): los 8 dígitos
  centrales del CUIT son el DNI, rellenado con ceros a la izquierda.
"""
import re

CUIT_MULTIPLICADORES = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

PREFIJOS_CUIT_REAL = {"20", "23", "24", "27"}
PREFIJOS_CUIT_IDEAL = {"30", "33", "34"}


def normalizar_numero(valor):
    """Descarta todo lo que no sea dígito: '12.345.678' o '20-12345678-9'
    quedan en '12345678' / '20123456789' (Escenario 7)."""
    return re.sub(r"\D", "", valor or "")


def cuit_digito_verificador(diez_digitos):
    """Dígito verificador (módulo 11) a partir de los primeros 10 dígitos
    del CUIT. Devuelve None cuando el cálculo da 10 — ese CUIT no tiene
    dígito verificador válido posible."""
    total = sum(int(d) * m for d, m in zip(diez_digitos, CUIT_MULTIPLICADORES))
    verificador = 11 - (total % 11)
    if verificador == 11:
        return 0
    if verificador == 10:
        return None
    return verificador


def cuit_valido(cuit):
    """True si `cuit` (11 dígitos, ya normalizado) tiene un dígito
    verificador módulo 11 correcto. No valida el prefijo acá — son dos
    chequeos independientes (Escenarios 13 y 14)."""
    if len(cuit) != 11 or not cuit.isdigit():
        return False
    esperado = cuit_digito_verificador(cuit[:10])
    if esperado is None:
        return False
    return int(cuit[10]) == esperado


def prefijo_cuit_coherente(cuit, tipo_persona):
    """El prefijo (primeros 2 dígitos) del CUIT tiene que corresponder al
    tipo de persona (Escenario 14)."""
    prefijo = cuit[:2]
    if tipo_persona == "real":
        return prefijo in PREFIJOS_CUIT_REAL
    return prefijo in PREFIJOS_CUIT_IDEAL


def cuit_contiene_dni(cuit, dni):
    """Escenario 12: los 8 dígitos centrales del CUIT (posiciones 3 a 10)
    son el DNI, rellenado con ceros a la izquierda hasta 8 dígitos."""
    if len(cuit) != 11 or not dni:
        return False
    return cuit[2:10] == dni.zfill(8)
