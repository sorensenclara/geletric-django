"""
Formularios propios de GELETRIC.

GeletricLoginForm es un AuthenticationForm estándar de Django (misma
validación de usuario/contraseña de siempre): lo único que cambia son los
widgets, para que el <input> ya salga con la clase que usa el CSS del login
(ver .auth-input en dashboard.css) en vez del render por defecto de Django.

AsociadoAltaForm implementa HU-ASO-01 (Alta de asociado) — ver
core/models.py y core/validators.py para las simplificaciones y las
reglas de CUIT documentadas ahí.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q

from .models import Asociado, Suministro, SuscripcionAcciones
from .validators import cuit_contiene_dni, cuit_valido, normalizar_numero, prefijo_cuit_coherente


class GeletricLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(attrs={
            "class": "auth-input",
            "placeholder": "usuario@geletric.com.ar",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "auth-input",
            "placeholder": "••••••••",
        }),
    )


class AsociadoAltaForm(forms.Form):
    """Alta de asociado (HU-ASO-01). Form simple (no ModelForm): la
    obligatoriedad de sexo/tipo_organismo/CUIT depende de tipo_persona y
    condición de IVA (Escenarios 3, 4, 5, 10), así que se valida a mano en
    clean() en vez de con el required fijo por campo de un ModelForm.

    "Tipo de documento" (Escenarios 8, 9) no es un campo propio acá: es
    DNI para existencia real y CUIT para existencia ideal, siempre — no
    hay otro tipo de documento confirmado todavía."""

    tipo_persona = forms.ChoiceField(
        label="Tipo de persona",
        choices=Asociado.TIPO_PERSONA_CHOICES,
        widget=forms.Select(attrs={"class": "list-select", "id": "id_tipo_persona"}),
    )
    nombre_apellido = forms.CharField(
        label="Nombre y apellido", max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "auth-input"}),
    )
    razon_social = forms.CharField(
        label="Razón social", max_length=200, required=False,
        widget=forms.TextInput(attrs={"class": "auth-input"}),
    )
    numero_documento = forms.CharField(
        label="N° de documento", max_length=20, required=True,
        widget=forms.TextInput(attrs={
            "class": "auth-input",
            "placeholder": "Se aceptan puntos, guiones y espacios",
        }),
    )
    cuit = forms.CharField(
        label="CUIT", max_length=20, required=False,
        widget=forms.TextInput(attrs={"class": "auth-input", "placeholder": "20-12345678-9"}),
    )
    sexo = forms.ChoiceField(
        label="Sexo", choices=[("", "—")] + Asociado.SEXO_CHOICES, required=False,
        widget=forms.Select(attrs={"class": "list-select"}),
    )
    tipo_organismo = forms.CharField(
        label="Tipo de organismo", max_length=100, required=False,
        widget=forms.TextInput(attrs={"class": "auth-input"}),
    )
    fecha_nacimiento_constitucion = forms.DateField(
        label="Fecha de nacimiento", required=False,
        widget=forms.DateInput(attrs={"class": "auth-input", "type": "date"}),
    )
    condicion_iva = forms.ChoiceField(
        label="Condición de IVA",
        choices=Asociado.CONDICION_IVA_CHOICES,
        widget=forms.Select(attrs={"class": "list-select"}),
    )
    domicilio = forms.CharField(
        label="Domicilio", max_length=255,
        widget=forms.TextInput(attrs={"class": "auth-input"}),
    )

    def clean_numero_documento(self):
        return normalizar_numero(self.cleaned_data["numero_documento"])

    def clean_cuit(self):
        return normalizar_numero(self.cleaned_data.get("cuit", ""))

    def clean(self):
        cleaned = super().clean()
        tipo_persona = cleaned.get("tipo_persona")
        condicion_iva = cleaned.get("condicion_iva")
        numero_documento = cleaned.get("numero_documento", "")
        cuit = cleaned.get("cuit", "")

        if tipo_persona == Asociado.TIPO_PERSONA_REAL:
            if not cleaned.get("nombre_apellido"):
                self.add_error("nombre_apellido", "Este campo es obligatorio.")
            if not cleaned.get("sexo"):
                self.add_error("sexo", "Este campo es obligatorio.")

            # CUIT (campo aparte del DNI) exigido según condición de IVA
            # (Escenarios 4, 5, 10) y, si se completa, siempre validado
            # (Escenarios 13, 14) sin importar si era obligatorio o no.
            cuit_exigido = condicion_iva in ("monotributista", "responsable_inscripto")
            if cuit_exigido and not cuit:
                self.add_error("cuit", "El CUIT es obligatorio para esta condición de IVA.")
            elif cuit:
                if len(cuit) != 11:
                    self.add_error("cuit", "El CUIT debe tener 11 dígitos.")
                elif not cuit_valido(cuit):
                    self.add_error("cuit", "El dígito verificador del CUIT no es válido.")
                elif not prefijo_cuit_coherente(cuit, Asociado.TIPO_PERSONA_REAL):
                    self.add_error("cuit", "El prefijo del CUIT no corresponde a una persona de existencia real.")

        elif tipo_persona == Asociado.TIPO_PERSONA_IDEAL:
            if not cleaned.get("razon_social"):
                self.add_error("razon_social", "Este campo es obligatorio.")
            if not cleaned.get("tipo_organismo"):
                self.add_error("tipo_organismo", "Este campo es obligatorio.")

            # Para existencia ideal, numero_documento ES el CUIT — misma
            # validación completa (Escenario 14: "aplica el mismo control").
            if numero_documento:
                if len(numero_documento) != 11:
                    self.add_error("numero_documento", "El número de identificación (CUIT) debe tener 11 dígitos.")
                elif not cuit_valido(numero_documento):
                    self.add_error("numero_documento", "El dígito verificador no es válido.")
                elif not prefijo_cuit_coherente(numero_documento, Asociado.TIPO_PERSONA_IDEAL):
                    self.add_error(
                        "numero_documento",
                        "El prefijo no corresponde a una persona de existencia ideal.",
                    )

        # Duplicados (Escenarios 11, 12) — solo si no hay otros errores de
        # formato todavía, para no encimar mensajes sobre el mismo campo.
        if not self.errors and numero_documento:
            duplicado = self._buscar_duplicado(tipo_persona, numero_documento, cuit)
            if duplicado:
                raise ValidationError(
                    f"Ya existe un contacto creado con esa identificación: "
                    f"N° {duplicado.numero_asociado} — {duplicado.nombre_o_razon_social}."
                )

        return cleaned

    def _buscar_duplicado(self, tipo_persona, numero_documento, cuit):
        """Escenario 11: coincidencia exacta de la identificación ingresada
        contra cualquier DNI o CUIT ya cargado. Escenario 12: además, para
        existencia real, equivalencia cruzada DNI-CUIT (los 8 dígitos
        centrales del CUIT son el DNI) — no aplica a existencia ideal,
        que no tiene DNI."""
        coincidencia = Asociado.objects.filter(
            Q(numero_documento=numero_documento) | Q(cuit=numero_documento)
        ).first()
        if coincidencia:
            return coincidencia

        if cuit:
            coincidencia = Asociado.objects.filter(
                Q(numero_documento=cuit) | Q(cuit=cuit)
            ).first()
            if coincidencia:
                return coincidencia

        if tipo_persona == Asociado.TIPO_PERSONA_REAL:
            reales = Asociado.objects.filter(tipo_persona=Asociado.TIPO_PERSONA_REAL)
            if cuit:
                for existente in reales.exclude(numero_documento=""):
                    if cuit_contiene_dni(cuit, existente.numero_documento):
                        return existente
            for existente in reales.exclude(cuit=""):
                if cuit_contiene_dni(existente.cuit, numero_documento):
                    return existente

        return None

    def save(self):
        """Además de crear el Asociado, registra su suscripción inicial de
        acciones (HU-ASO-02, Escenario 1) en la misma transacción. Si no
        hay valor nominal configurado para hoy (Escenario 6), el asociado
        se crea igual y self.suscripcion queda en None con el motivo en
        self.suscripcion_error — la vista decide qué mensaje mostrar."""
        cleaned = self.cleaned_data
        tipo_persona = cleaned["tipo_persona"]
        es_real = tipo_persona == Asociado.TIPO_PERSONA_REAL

        with transaction.atomic():
            asociado = Asociado.objects.create(
                numero_asociado=Asociado.siguiente_numero_asociado(),
                numero_usuario=Asociado.siguiente_numero_usuario(),
                tipo_persona=tipo_persona,
                nombre_apellido=cleaned.get("nombre_apellido", "") if es_real else "",
                sexo=cleaned.get("sexo", "") if es_real else "",
                razon_social=cleaned.get("razon_social", "") if not es_real else "",
                tipo_organismo=cleaned.get("tipo_organismo", "") if not es_real else "",
                fecha_nacimiento_constitucion=cleaned.get("fecha_nacimiento_constitucion"),
                numero_documento=cleaned["numero_documento"],
                cuit=cleaned.get("cuit", "") if es_real else "",
                condicion_iva=cleaned["condicion_iva"],
                domicilio=cleaned["domicilio"],
            )
            self.suscripcion, self.suscripcion_error = SuscripcionAcciones.registrar_para(asociado)
            return asociado


class SuministroAltaForm(forms.Form):
    """Vínculo societario del suministro (HU-ASO-03). No es un alta de
    suministro completa (ver la nota en models.Suministro) — valida
    exactamente lo que pide esta HU.

    Titular no es obligatorio para el operador: si no se indica uno
    distinto, el suministro queda con el mismo contacto como Socio y
    como Titular (Escenario 4) — el caso más común, según la propia HU.
    Escenario 3 (Titular distinto, ej. un inquilino) se cubre indicando
    un Titular distinto del Socio."""

    socio = forms.ModelChoiceField(
        queryset=Asociado.objects.all(),
        label="Socio",
        widget=forms.Select(attrs={"class": "list-select"}),
        error_messages={"required": "El Socio del suministro es obligatorio."},
    )
    titular = forms.ModelChoiceField(
        queryset=Asociado.objects.all(),
        label="Titular",
        required=False,
        widget=forms.Select(attrs={"class": "list-select"}),
    )

    def clean(self):
        cleaned = super().clean()
        socio = cleaned.get("socio")
        if socio and not cleaned.get("titular"):
            cleaned["titular"] = socio
        return cleaned

    def save(self):
        cleaned = self.cleaned_data
        return Suministro.objects.create(socio=cleaned["socio"], titular=cleaned["titular"])
