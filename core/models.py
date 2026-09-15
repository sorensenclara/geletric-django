"""
Modelo real de Asociado (HU-ASO-01 — Alta de asociado).

Primer modelo con persistencia real del sistema: hasta acá todo el módulo
Asociados (listado, ficha) funciona sobre datos de muestra fijos en
associate_data.py. Ese archivo sigue así — no se toca acá — hasta que su
propia Historia de Usuario quede cerrada; este modelo es la base real
exclusivamente para el alta.

Simplificaciones documentadas, pendientes de una decisión posterior:

- numero_asociado / numero_usuario: correlativo simple (máximo existente +
  1), sin reutilizar números de asociados dados de baja. PREG-ASO-01 (la
  pregunta bloqueante de HU-ASO-01) todavía no está respondida; cuando se
  resuelva, ajustar nada más que siguiente_numero_asociado/usuario acá.
- domicilio: un solo campo de texto libre. PREG-ASO-02 (diferida) todavía
  no define la estructura del domicilio fiscal.
"""
from django.db import models


class Asociado(models.Model):
    TIPO_PERSONA_REAL = "real"
    TIPO_PERSONA_IDEAL = "ideal"
    TIPO_PERSONA_CHOICES = [
        (TIPO_PERSONA_REAL, "De existencia real"),
        (TIPO_PERSONA_IDEAL, "De existencia ideal"),
    ]

    SEXO_CHOICES = [
        ("F", "Femenino"),
        ("M", "Masculino"),
        ("X", "No binario"),
    ]

    # Solo las tres condiciones que HU-ASO-01 nombra explícitamente — sumar
    # otras (Exento, No alcanzado, etc.) cuando el DEV las confirme.
    CONDICION_IVA_CHOICES = [
        ("consumidor_final", "Consumidor Final"),
        ("monotributista", "Monotributista"),
        ("responsable_inscripto", "Responsable Inscripto"),
    ]

    ESTADO_SOCIETARIO_CHOICES = [
        ("activo", "Activo"),
        ("inactivo", "Inactivo"),
    ]

    numero_asociado = models.CharField(max_length=10, unique=True, editable=False)
    numero_usuario = models.CharField(max_length=10, unique=True, editable=False)

    tipo_persona = models.CharField(max_length=10, choices=TIPO_PERSONA_CHOICES)

    # Existencia real
    nombre_apellido = models.CharField("Nombre y apellido", max_length=200, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True)

    # Existencia ideal
    razon_social = models.CharField("Razón social", max_length=200, blank=True)
    tipo_organismo = models.CharField("Tipo de organismo", max_length=100, blank=True)

    # Campo de fecha compartido — la etiqueta ("Fecha de nacimiento" /
    # "Fecha de constitución") depende de tipo_persona (Escenario 3).
    fecha_nacimiento_constitucion = models.DateField(
        "Fecha de nacimiento / constitución", null=True, blank=True,
    )

    # Identificación tributaria. Para existencia real, numero_documento es
    # el DNI y `cuit` es un campo aparte, exigido según condición de IVA.
    # Para existencia ideal, numero_documento ES el CUIT (no hay DNI ni
    # `cuit` separado) — ver validators.py y forms.py.
    numero_documento = models.CharField("N° de documento", max_length=11)
    cuit = models.CharField("CUIT", max_length=11, blank=True)
    condicion_iva = models.CharField(
        "Condición de IVA", max_length=30, choices=CONDICION_IVA_CHOICES,
    )

    domicilio = models.CharField(max_length=255)

    # Campos de contacto/domicilio/administrativos que la ficha del
    # asociado ya mostraba con datos de ejemplo (ver associate_data.py)
    # pero que hasta ahora no existían en el modelo real, porque ninguna
    # HU los había pedido. Se agregaron el 14/09/2026 a pedido de Clara,
    # para que el listado y la ficha dejen de depender de datos de
    # muestra — mismo patrón que seed_demo.py en San Cayetano. Todos
    # opcionales: el alta (HU-ASO-01) no los pide, así que un asociado
    # real puede no tenerlos cargados todavía.
    telefono_fijo = models.CharField("Teléfono fijo", max_length=30, blank=True)
    celular = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    email_alternativo = models.EmailField("Email alternativo", blank=True)
    ruta_subruta = models.CharField("Ruta / subruta", max_length=100, blank=True)
    localidad = models.CharField(max_length=100, blank=True)
    codigo_postal = models.CharField("Código postal", max_length=20, blank=True)
    provincia = models.CharField(max_length=100, blank=True, default="Buenos Aires")
    categoria = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)
    es_proveedor = models.BooleanField("Es proveedor", default=False)

    estado_societario = models.CharField(
        max_length=10, choices=ESTADO_SOCIETARIO_CHOICES, default="activo",
    )
    fecha_ingreso = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ["numero_asociado"]

    def __str__(self):
        return f"{self.numero_asociado} — {self.nombre_o_razon_social}"

    @property
    def nombre_o_razon_social(self):
        if self.tipo_persona == self.TIPO_PERSONA_IDEAL:
            return self.razon_social
        return self.nombre_apellido

    @classmethod
    def _siguiente_numero(cls, campo):
        valores = cls.objects.values_list(campo, flat=True)
        maximo = max((int(v) for v in valores if v), default=0)
        return str(maximo + 1).zfill(5)

    @classmethod
    def siguiente_numero_asociado(cls):
        return cls._siguiente_numero("numero_asociado")

    @classmethod
    def siguiente_numero_usuario(cls):
        return cls._siguiente_numero("numero_usuario")


class ParametroSuscripcion(models.Model):
    """Parámetro configurable: cantidad de acciones de la suscripción
    inicial (HU-ASO-02, Escenarios 1 y 4). Fila única (singleton, pk=1) —
    se edita desde Técnico → Parámetros generales; hasta que exista una
    pantalla propia para eso, se edita desde /admin/.

    El valor con el que arranca esta fila es un placeholder: PREG-ASO-04
    (con qué valor cargarlo) sigue sin responder — CONSULTORIA hablaba de
    50 acciones y TECNICO de 5, y la HU no eligió entre ambas. Se puso 1
    por ser el valor menos arbitrario mientras tanto; cambiarlo desde el
    admin apenas se sepa el valor real no afecta a los asociados ya dados
    de alta, porque cada suscripción guarda su propia cantidad
    (Escenario 4 — ver SuscripcionAcciones.registrar_para)."""

    cantidad_acciones_inicial = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Parámetro de suscripción"
        verbose_name_plural = "Parámetros de suscripción"

    def __str__(self):
        return f"Suscripción inicial: {self.cantidad_acciones_inicial} acciones"

    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ValorNominalAccion(models.Model):
    """Historial de valores nominales de la acción, con vigencia desde una
    fecha (HU-ASO-02, decisión tomada con el usuario el 07/09/2026): cada
    suscripción usa el valor vigente en su propia fecha de suscripción y
    no se recalcula si después se carga un valor nuevo (Escenario 5) — se
    eligió esta variante, con historial, en vez de un valor único, porque
    los ítems 13 y 14 del checklist necesitan poder reconstruir el capital
    de un asociado a una fecha histórica.

    No hay "vigente_hasta": el valor vigente a una fecha es el de mayor
    vigente_desde que sea <= esa fecha (ver vigente_a_fecha). No se carga
    ningún valor por defecto acá — a diferencia de ParametroSuscripcion,
    no hay ninguna cifra de referencia en la HU para este campo, así que
    inventar una sería una decisión de negocio que no corresponde tomar
    acá: Técnico tiene que cargar al menos uno desde /admin/ antes de que
    la primera suscripción pueda registrarse (Escenario 6)."""

    valor = models.DecimalField(max_digits=12, decimal_places=2)
    vigente_desde = models.DateField()

    class Meta:
        ordering = ["-vigente_desde"]
        verbose_name = "Valor nominal de la acción"
        verbose_name_plural = "Valores nominales de la acción"

    def __str__(self):
        return f"${self.valor} desde {self.vigente_desde:%d/%m/%Y}"

    @classmethod
    def vigente_a_fecha(cls, fecha):
        """Valor nominal vigente a `fecha`, o None si no hay ninguno
        configurado con vigencia que la cubra (Escenario 6)."""
        return cls.objects.filter(vigente_desde__lte=fecha).order_by("-vigente_desde").first()


class SuscripcionAcciones(models.Model):
    """Suscripción de acciones de un asociado (HU-ASO-02). Se crea
    automáticamente al dar de alta un asociado (ver
    forms.AsociadoAltaForm.save), tomando la cantidad del parámetro
    vigente en ese momento y el valor nominal vigente a la fecha de alta —
    ver registrar_para.

    FK a Asociado (no OneToOne) a propósito: un escenario de camino triste
    que impedía una segunda suscripción del mismo asociado se sacó del
    borrador de la HU por ser una inferencia propia sin respaldo en las
    fuentes: se reincorporará (con el bloqueo que corresponda) cuando el
    cliente responda PREG-ASO-06. Hasta entonces, nada impide acá una
    segunda fila para el mismo asociado."""

    asociado = models.ForeignKey(
        "Asociado", on_delete=models.CASCADE, related_name="suscripciones",
    )
    numero_titulo = models.CharField(max_length=10, unique=True, editable=False)
    cantidad_acciones = models.PositiveIntegerField()
    valor_nominal = models.DecimalField(max_digits=12, decimal_places=2)
    capital_suscripto = models.DecimalField(max_digits=14, decimal_places=2)
    fecha_suscripcion = models.DateField()

    class Meta:
        ordering = ["numero_titulo"]
        verbose_name = "Suscripción de acciones"
        verbose_name_plural = "Suscripciones de acciones"

    def __str__(self):
        return f"Título {self.numero_titulo} — {self.asociado.nombre_o_razon_social}"

    @classmethod
    def siguiente_numero_titulo(cls):
        valores = cls.objects.values_list("numero_titulo", flat=True)
        maximo = max((int(v) for v in valores if v), default=0)
        return str(maximo + 1).zfill(5)

    @classmethod
    def registrar_para(cls, asociado, fecha=None):
        """Escenario 1: crea la suscripción inicial de `asociado`. Devuelve
        (suscripcion, None) si se creó, o (None, mensaje) si no hay valor
        nominal vigente para la fecha (Escenario 6) — en ese caso no crea
        nada; no es responsabilidad de este método decidir si el alta del
        asociado en sí debe revertirse o no (ver views.asociado_alta)."""
        from django.utils import timezone

        fecha = fecha or timezone.localdate()
        valor_nominal_row = ValorNominalAccion.vigente_a_fecha(fecha)
        if valor_nominal_row is None:
            return None, (
                "No se pudo registrar la suscripción de acciones: falta "
                f"configurar el valor nominal vigente para el {fecha:%d/%m/%Y}."
            )

        cantidad = ParametroSuscripcion.obtener().cantidad_acciones_inicial
        capital = cantidad * valor_nominal_row.valor
        suscripcion = cls.objects.create(
            asociado=asociado,
            numero_titulo=cls.siguiente_numero_titulo(),
            cantidad_acciones=cantidad,
            valor_nominal=valor_nominal_row.valor,
            capital_suscripto=capital,
            fecha_suscripcion=fecha,
        )
        return suscripcion, None


class Suministro(models.Model):
    """Vínculo societario obligatorio del suministro (HU-ASO-03). Modela
    únicamente lo que esta HU exige — el vínculo con el asociado — no un
    alta de suministro completa: todavía no tiene pantalla propia (según
    TECNICO va a ser un wizard que arranca desde el alta del asociado) ni
    los campos operativos que un suministro real necesita (domicilio,
    NIS, tipo de servicio, tarifa, etc.) — esos quedan para cuando su
    propia Historia de Usuario los defina.

    Socio y Titular son dos vínculos separados a propósito (decisión
    tomada con el usuario el 09/09/2026, corrigiendo una primera versión
    que los trataba como sinónimos): el Socio sostiene la relación
    cooperativa (lo que hace del servicio un acto cooperativo exento de
    Ingresos Brutos); el Titular es quien de hecho consume el servicio y
    recibe la factura. Coinciden casi siempre, pero no cuando, por
    ejemplo, un asociado alquila el inmueble a un tercero.

    Escenario 1 (Socio obligatorio) lo garantiza el propio campo `socio`,
    que no admite blank/null. Escenario 2 (rechazar un Socio sin rol de
    asociado) no necesita código de validación propio: hoy Asociado es la
    única tabla de contactos del sistema y toda fila ahí ya tiene el rol
    "Asociado" por construcción (ver HU-ASO-01 y la nota de roles en
    associate_data.py) — el FK ya lo garantiza, no hace falta chequearlo
    a mano. El día que exista un contacto que sea Usuario/Titular sin ser
    Asociado (PREG-ASO-10, sobre el padrón migrado), ahí sí va a hacer
    falta un chequeo explícito acá; hasta entonces, escribir esa
    validación sería simular una distinción que el modelo de datos
    todavía no tiene. Titular no tiene ninguna restricción de rol
    (Escenarios 3, 4, 5): cualquier Asociado puede ser Titular."""

    socio = models.ForeignKey(
        "Asociado", on_delete=models.CASCADE, related_name="suministros_como_socio",
        verbose_name="Socio",
    )
    titular = models.ForeignKey(
        "Asociado", on_delete=models.CASCADE, related_name="suministros_como_titular",
        verbose_name="Titular",
    )
    fecha_alta = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Suministro"
        verbose_name_plural = "Suministros"

    def __str__(self):
        if self.titular_id == self.socio_id:
            return f"Suministro de {self.socio.nombre_o_razon_social}"
        return (
            f"Suministro de {self.titular.nombre_o_razon_social} "
            f"(socio: {self.socio.nombre_o_razon_social})"
        )
