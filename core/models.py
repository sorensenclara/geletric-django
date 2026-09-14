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
