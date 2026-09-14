"""
Siembra de asociados de ejemplo (ficticios pero realistas), para que el
listado y la ficha —hasta el 14/09/2026 alimentados por datos de muestra
fijos en associate_data.py, ahora por el modelo real Asociado— tengan algo
para mostrar sin depender de un padrón real todavía no provisto por
Clara. Mismo patrón que seed_demo.py en el proyecto de San Cayetano.

Idempotente: cada asociado se identifica por numero_documento y no se
crea de nuevo si ya existe uno con ese documento — correr este comando
más de una vez no duplica nada (podés correrlo de nuevo tranquilamente
después de una demo o de un deploy).

Además de los 12 asociados, este comando también se asegura de que exista
al menos un ValorNominalAccion y el ParametroSuscripcion (creándolos con
un valor de referencia si hace falta) para que cada asociado sembrado
quede con su suscripción de acciones real (HU-ASO-02) y no solo el alta
—si ya existen (por ejemplo, porque Técnico ya los cargó desde /admin/),
se respetan los que ya están y no se tocan.

Localidades, DNI/CUIT (con dígito verificador real, calculado — no
inventado a mano) y domicilios son ficticios; no representan personas ni
domicilios reales. Localidades: San Manuel (el pueblo) y los parajes
rurales de su zona en el partido de Tandil — Gardey, Fulton, María
Ignacia (Vela) —, las mismas que ya usaba associate_data.py con datos de
muestra. El código postal (7000) es el de Tandil ciudad, usado acá como
aproximación para toda la zona — no hay un CP oficial distinto confirmado
para cada paraje.
"""
import datetime

from django.core.management.base import BaseCommand

from core.models import Asociado, ParametroSuscripcion, SuscripcionAcciones, ValorNominalAccion
from core.validators import cuit_digito_verificador


def _cuit(prefijo, ocho_digitos):
    """Arma un CUIT de 11 dígitos válido (prefijo de 2 + 8 dígitos +
    dígito verificador módulo 11 calculado de verdad, ver validators.py) a
    partir de un prefijo y los 8 dígitos centrales (que, como en un CUIT
    real, coinciden con el DNI cuando la persona es de existencia real).

    Algunas combinaciones de prefijo+8 dígitos no tienen dígito
    verificador módulo 11 válido (cuit_digito_verificador devuelve None) —
    falla fuerte acá en vez de generar un CUIT inválido en silencio, para
    que un futuro dato de siembra con ese problema se note al tirar el
    comando, no recién cuando alguien lo mire en la ficha."""
    diez = f"{prefijo}{ocho_digitos}"
    verificador = cuit_digito_verificador(diez)
    if verificador is None:
        raise ValueError(
            f"'{prefijo}{ocho_digitos}' no tiene un dígito verificador de "
            f"CUIT válido — elegir otros 8 dígitos para este asociado de ejemplo."
        )
    return f"{diez}{verificador}"


_ASOCIADOS_DEMO = [
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Juan Carlos Pérez",
        "sexo": "M",
        "fecha_nacimiento_constitucion": datetime.date(1980, 5, 14),
        "numero_documento": "28451902",
        "cuit": "",
        "condicion_iva": "consumidor_final",
        "domicilio": "San Martín 350",
        "telefono_fijo": "0249 442-1180",
        "celular": "+54 9 249 400-1180",
        "email": "juancperez@gmail.com",
        "localidad": "San Manuel",
        "codigo_postal": "7000",
        "categoria": "Residencial",
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "María Elena Gómez",
        "sexo": "F",
        "fecha_nacimiento_constitucion": datetime.date(1975, 11, 2),
        "numero_documento": "23987655",
        "cuit": _cuit("27", "23987655"),
        "condicion_iva": "monotributista",
        "domicilio": "Belgrano 128",
        "telefono_fijo": "0249 442-2201",
        "celular": "+54 9 249 400-2201",
        "email": "mariaelenagomez@gmail.com",
        "localidad": "San Manuel",
        "codigo_postal": "7000",
        "categoria": "Comercial",
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Roberto Daniel Fernández",
        "sexo": "M",
        "fecha_nacimiento_constitucion": datetime.date(1968, 2, 20),
        "numero_documento": "20655322",
        "cuit": _cuit("20", "20655322"),
        "condicion_iva": "monotributista",
        "domicilio": "Zona rural, Gardey",
        "ruta_subruta": "Ruta provincial 30",
        "celular": "+54 9 249 400-3302",
        "localidad": "Gardey",
        "codigo_postal": "7000",
        "categoria": "Rural",
        "estado_societario": "inactivo",
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Ana Lucía Benítez",
        "sexo": "F",
        "fecha_nacimiento_constitucion": datetime.date(1985, 7, 9),
        "numero_documento": "31220145",
        "cuit": _cuit("27", "31220145"),
        "condicion_iva": "monotributista",
        "domicilio": "Zona rural, Fulton",
        "ruta_subruta": "Ruta provincial 30",
        "celular": "+54 9 249 400-4403",
        "email": "analuciabenitez@gmail.com",
        "localidad": "Fulton",
        "codigo_postal": "7000",
        "categoria": "Rural",
        "es_proveedor": True,
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Carlos Alberto Duarte",
        "sexo": "M",
        "fecha_nacimiento_constitucion": datetime.date(1990, 3, 30),
        "numero_documento": "35441278",
        "cuit": "",
        "condicion_iva": "consumidor_final",
        "domicilio": "9 de Julio 640",
        "telefono_fijo": "0249 442-5504",
        "localidad": "San Manuel",
        "codigo_postal": "7000",
        "categoria": "Residencial",
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Silvia Beatriz Acosta",
        "sexo": "F",
        "fecha_nacimiento_constitucion": datetime.date(1963, 9, 17),
        "numero_documento": "16789432",
        "cuit": "",
        "condicion_iva": "consumidor_final",
        "domicilio": "Zona rural, Gardey",
        "ruta_subruta": "Ruta provincial 30",
        "localidad": "Gardey",
        "codigo_postal": "7000",
        "categoria": "Rural",
        "estado_societario": "inactivo",
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Miguel Ángel Rojas",
        "sexo": "M",
        "fecha_nacimiento_constitucion": datetime.date(1979, 12, 5),
        "numero_documento": "27334890",
        "cuit": _cuit("20", "27334890"),
        "condicion_iva": "monotributista",
        "domicilio": "Zona rural, María Ignacia (Vela)",
        "ruta_subruta": "Ruta provincial 30",
        "celular": "+54 9 249 400-6607",
        "email": "miguelrojas@gmail.com",
        "localidad": "María Ignacia (Vela)",
        "codigo_postal": "7000",
        "categoria": "Rural",
        "es_proveedor": True,
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Laura Patricia Ríos",
        "sexo": "F",
        "fecha_nacimiento_constitucion": datetime.date(1972, 6, 25),
        "numero_documento": "22109876",
        "cuit": _cuit("27", "22109876"),
        "condicion_iva": "responsable_inscripto",
        "domicilio": "Rivadavia 215",
        "telefono_fijo": "0249 442-7708",
        "celular": "+54 9 249 400-7708",
        "email": "laurarios@hotmail.com",
        "email_alternativo": "lauraprios@gmail.com",
        "localidad": "San Manuel",
        "codigo_postal": "7000",
        "categoria": "Comercial",
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Jorge Luis Cabrera",
        "sexo": "M",
        "fecha_nacimiento_constitucion": datetime.date(1988, 1, 11),
        "numero_documento": "33556789",
        "cuit": "",
        "condicion_iva": "consumidor_final",
        "domicilio": "Zona rural, Gardey",
        "ruta_subruta": "Ruta provincial 30",
        "celular": "+54 9 249 400-8809",
        "localidad": "Gardey",
        "codigo_postal": "7000",
        "categoria": "Rural",
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Verónica Soledad Torres",
        "sexo": "F",
        "fecha_nacimiento_constitucion": datetime.date(1995, 4, 3),
        "numero_documento": "38112456",
        "cuit": "",
        "condicion_iva": "consumidor_final",
        "domicilio": "Moreno 480",
        "celular": "+54 9 249 400-9910",
        "localidad": "San Manuel",
        "codigo_postal": "7000",
        "categoria": "Residencial",
        "estado_societario": "inactivo",
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_IDEAL,
        "razon_social": "Cooperativa de Trabajo El Amanecer Ltda.",
        "tipo_organismo": "Cooperativa de trabajo",
        "fecha_nacimiento_constitucion": datetime.date(2005, 8, 1),
        "numero_documento": _cuit("30", "71234567"),
        "cuit": "",
        "condicion_iva": "responsable_inscripto",
        "domicilio": "Av. Libertad 220",
        "telefono_fijo": "0249 443-1122",
        "email": "administracion@elamanecer.coop.ar",
        "localidad": "San Manuel",
        "codigo_postal": "7000",
        "categoria": "Comercial",
        "es_proveedor": True,
    },
    {
        "tipo_persona": Asociado.TIPO_PERSONA_IDEAL,
        "razon_social": "Electricidad del Sur S.R.L.",
        "tipo_organismo": "Sociedad de responsabilidad limitada",
        "fecha_nacimiento_constitucion": datetime.date(2011, 3, 15),
        "numero_documento": _cuit("30", "71987654"),
        "cuit": "",
        "condicion_iva": "responsable_inscripto",
        "domicilio": "Ruta provincial 30, zona industrial",
        "telefono_fijo": "0249 443-3344",
        "email": "contacto@electricidaddelsur.com.ar",
        "localidad": "San Manuel",
        "codigo_postal": "7000",
        "categoria": "Comercial",
        "es_proveedor": True,
    },
]


class Command(BaseCommand):
    help = (
        "Siembra ~12 asociados de ejemplo (ficticios pero realistas, con "
        "DNI/CUIT válidos) con su suscripción de acciones inicial, para "
        "que el listado y la ficha tengan datos reales para mostrar. "
        "Idempotente: no duplica si ya existen (se identifica por "
        "numero_documento)."
    )

    def handle(self, *args, **options):
        self._asegurar_parametros_suscripcion()

        creados = 0
        ya_existian = 0
        sin_suscripcion = 0
        for datos in _ASOCIADOS_DEMO:
            asociado, fue_creado = self._crear_si_no_existe(datos)
            if not fue_creado:
                ya_existian += 1
                continue
            creados += 1
            _, error = SuscripcionAcciones.registrar_para(asociado)
            if error:
                sin_suscripcion += 1
                self.stdout.write(self.style.WARNING(
                    f"  {asociado.numero_asociado} — {asociado.nombre_o_razon_social}: {error}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Listo: {creados} asociados creados, {ya_existian} ya existían "
            f"(no se tocaron)."
            + (f" {sin_suscripcion} sin suscripción registrada (ver avisos arriba)." if sin_suscripcion else "")
        ))

    def _asegurar_parametros_suscripcion(self):
        """HU-ASO-02, Escenario 6: sin un ValorNominalAccion vigente no se
        puede registrar ninguna suscripción. Si Técnico todavía no cargó
        ninguno desde /admin/, se crea uno de referencia acá para que la
        siembra no quede a mitad de camino; si ya existe alguno (cargado a
        mano o por una siembra anterior), se respeta y no se toca."""
        if not ValorNominalAccion.objects.exists():
            ValorNominalAccion.objects.create(
                valor="500.00", vigente_desde=datetime.date(2020, 1, 1),
            )
            self.stdout.write(
                "No había ningún valor nominal de la acción cargado — se "
                "creó uno de referencia ($500 desde 01/01/2020)."
            )
        ParametroSuscripcion.obtener()  # crea la fila singleton (default) si no existe.

    def _crear_si_no_existe(self, datos):
        documento = datos["numero_documento"]
        existente = Asociado.objects.filter(numero_documento=documento).first()
        if existente is not None:
            return existente, False

        asociado = Asociado.objects.create(
            numero_asociado=Asociado.siguiente_numero_asociado(),
            numero_usuario=Asociado.siguiente_numero_usuario(),
            **datos,
        )
        return asociado, True
