"""
Tests de HU-ASO-01 (Alta de asociado): uno por escenario de aceptación
donde tiene sentido, más las funciones de validators.py por separado.

CUIT de prueba usados acá (verificados a mano con el algoritmo de
módulo 11 antes de escribir los tests, no inventados sobre la marcha):
- 20111111112 → real, DNI 11111111 (el "CUIT de prueba" más usado en
  sistemas argentinos, por eso se eligió como caso de referencia).
- 30712121218 → ideal, identificación 71212121.
"""
import datetime

from django.core.management import call_command
from django.test import TestCase

from . import associate_data as ad
from .forms import AsociadoAltaForm
from .models import Asociado, ParametroSuscripcion, SuscripcionAcciones, ValorNominalAccion
from .validators import (
    cuit_contiene_dni,
    cuit_valido,
    normalizar_numero,
    prefijo_cuit_coherente,
)


class ValidatorsTests(TestCase):
    def test_normalizar_numero_descarta_no_digitos(self):
        self.assertEqual(normalizar_numero("12.345.678"), "12345678")
        self.assertEqual(normalizar_numero("20-12345678-9"), "20123456789")
        self.assertEqual(normalizar_numero(""), "")
        self.assertEqual(normalizar_numero(None), "")

    def test_cuit_valido(self):
        self.assertTrue(cuit_valido("20111111112"))
        self.assertTrue(cuit_valido("30712121218"))
        self.assertFalse(cuit_valido("20111111113"))  # dígito verificador incorrecto
        self.assertFalse(cuit_valido("2011111111"))  # longitud incorrecta
        self.assertFalse(cuit_valido("2011111111a"))  # no numérico

    def test_prefijo_cuit_coherente(self):
        self.assertTrue(prefijo_cuit_coherente("20111111112", Asociado.TIPO_PERSONA_REAL))
        self.assertFalse(prefijo_cuit_coherente("30712121218", Asociado.TIPO_PERSONA_REAL))
        self.assertTrue(prefijo_cuit_coherente("30712121218", Asociado.TIPO_PERSONA_IDEAL))
        self.assertFalse(prefijo_cuit_coherente("20111111112", Asociado.TIPO_PERSONA_IDEAL))

    def test_cuit_contiene_dni(self):
        self.assertTrue(cuit_contiene_dni("20111111112", "11111111"))
        self.assertFalse(cuit_contiene_dni("20111111112", "99999999"))
        self.assertTrue(cuit_contiene_dni("20000123425", "12342"))  # dni corto, rellenado con ceros


def _datos_real(**overrides):
    datos = {
        "tipo_persona": Asociado.TIPO_PERSONA_REAL,
        "nombre_apellido": "Juan Pérez",
        "numero_documento": "30111222",
        "sexo": "M",
        "condicion_iva": "consumidor_final",
        "domicilio": "San Martín 350",
    }
    datos.update(overrides)
    return datos


def _datos_ideal(**overrides):
    datos = {
        "tipo_persona": Asociado.TIPO_PERSONA_IDEAL,
        "razon_social": "Cooperativa Ejemplo SRL",
        "numero_documento": "30712121218",
        "tipo_organismo": "SRL",
        "condicion_iva": "responsable_inscripto",
        "domicilio": "Belgrano 128",
    }
    datos.update(overrides)
    return datos


def _crear(datos):
    """Helper de test: valida y guarda, fallando fuerte si el form no es
    válido (evita que un typo en los datos de prueba se confunda con un
    bug real de validación)."""
    form = AsociadoAltaForm(data=datos)
    assert form.is_valid(), form.errors
    return form.save()


class AsociadoAltaFormTests(TestCase):
    def test_escenario_1_alta_real_camino_feliz(self):
        form = AsociadoAltaForm(data=_datos_real())
        self.assertTrue(form.is_valid(), form.errors)
        asociado = form.save()
        self.assertEqual(asociado.numero_asociado, "00001")
        self.assertEqual(asociado.numero_usuario, "00001")
        self.assertEqual(asociado.estado_societario, "activo")
        self.assertIsNotNone(asociado.fecha_ingreso)

    def test_escenario_2_alta_ideal_camino_feliz(self):
        form = AsociadoAltaForm(data=_datos_ideal())
        self.assertTrue(form.is_valid(), form.errors)
        asociado = form.save()
        self.assertEqual(asociado.razon_social, "Cooperativa Ejemplo SRL")
        self.assertEqual(asociado.tipo_organismo, "SRL")
        self.assertEqual(asociado.sexo, "")

    def test_escenario_3_campos_condicionados(self):
        # Real sin sexo: inválido.
        form = AsociadoAltaForm(data=_datos_real(sexo=""))
        self.assertFalse(form.is_valid())
        self.assertIn("sexo", form.errors)

        # Ideal sin tipo_organismo: inválido.
        form = AsociadoAltaForm(data=_datos_ideal(tipo_organismo=""))
        self.assertFalse(form.is_valid())
        self.assertIn("tipo_organismo", form.errors)

    def test_escenario_4_cuit_exigido_por_condicion_iva(self):
        form = AsociadoAltaForm(data=_datos_real(
            condicion_iva="monotributista", cuit="20111111112",
        ))
        self.assertTrue(form.is_valid(), form.errors)
        asociado = form.save()
        self.assertEqual(asociado.numero_documento, "30111222")
        self.assertEqual(asociado.cuit, "20111111112")

    def test_escenario_5_sin_cuit_consumidor_final(self):
        form = AsociadoAltaForm(data=_datos_real(condicion_iva="consumidor_final"))
        self.assertTrue(form.is_valid(), form.errors)

    def test_escenario_6_sin_fecha_nacimiento(self):
        form = AsociadoAltaForm(data=_datos_real(fecha_nacimiento_constitucion=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_escenario_7_normalizacion_numero_identificacion(self):
        form = AsociadoAltaForm(data=_datos_real(numero_documento="30.111.222"))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["numero_documento"], "30111222")

    def test_escenario_8_falta_obligatorio_real(self):
        form = AsociadoAltaForm(data=_datos_real(nombre_apellido=""))
        self.assertFalse(form.is_valid())
        self.assertIn("nombre_apellido", form.errors)
        self.assertEqual(Asociado.objects.count(), 0)

    def test_escenario_9_falta_obligatorio_ideal(self):
        form = AsociadoAltaForm(data=_datos_ideal(razon_social=""))
        self.assertFalse(form.is_valid())
        self.assertIn("razon_social", form.errors)
        self.assertEqual(Asociado.objects.count(), 0)

    def test_escenario_10_cuit_faltante_exigido(self):
        form = AsociadoAltaForm(data=_datos_real(condicion_iva="monotributista", cuit=""))
        self.assertFalse(form.is_valid())
        self.assertIn("cuit", form.errors)
        self.assertEqual(Asociado.objects.count(), 0)

    def test_escenario_11_identificacion_ya_existente(self):
        _crear(_datos_real(numero_documento="30111222"))
        form = AsociadoAltaForm(data=_datos_real(numero_documento="30111222", nombre_apellido="Otra Persona"))
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())
        self.assertIn("00001", form.non_field_errors()[0])
        self.assertEqual(Asociado.objects.count(), 1)

    def test_escenario_12_duplicado_por_equivalencia_dni_cuit(self):
        # Existe un DNI 11111111; alguien intenta entrar con el CUIT que lo contiene.
        _crear(_datos_real(numero_documento="11111111"))
        form = AsociadoAltaForm(data=_datos_real(
            numero_documento="99999999",
            condicion_iva="monotributista",
            cuit="20111111112",
        ))
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())
        self.assertEqual(Asociado.objects.count(), 1)

        # Caso inverso: existe el CUIT, se ingresa el DNI contenido en él.
        Asociado.objects.all().delete()
        _crear(_datos_real(
            numero_documento="88888888",
            condicion_iva="monotributista",
            cuit="20111111112",
        ))
        form = AsociadoAltaForm(data=_datos_real(numero_documento="11111111", nombre_apellido="Otra Persona"))
        self.assertFalse(form.is_valid())
        self.assertEqual(Asociado.objects.count(), 1)

    def test_escenario_13_cuit_digito_verificador_incorrecto(self):
        form = AsociadoAltaForm(data=_datos_real(condicion_iva="monotributista", cuit="20111111113"))
        self.assertFalse(form.is_valid())
        self.assertIn("cuit", form.errors)

    def test_escenario_14_prefijo_cuit_incoherente(self):
        # Real con prefijo de ideal (30xxxxxxxxY no está en 20/23/24/27).
        form = AsociadoAltaForm(data=_datos_real(condicion_iva="monotributista", cuit="30712121218"))
        self.assertFalse(form.is_valid())
        self.assertIn("cuit", form.errors)

        # Ideal con prefijo de real.
        form = AsociadoAltaForm(data=_datos_ideal(numero_documento="20111111112"))
        self.assertFalse(form.is_valid())
        self.assertIn("numero_documento", form.errors)

    def test_correlativo_no_reutiliza_pero_avanza(self):
        _crear(_datos_real(numero_documento="11111111"))
        _crear(_datos_real(numero_documento="22222222"))
        segundo = Asociado.objects.get(numero_documento="22222222")
        self.assertEqual(segundo.numero_asociado, "00002")
        self.assertEqual(segundo.numero_usuario, "00002")


class SuscripcionAccionesTests(TestCase):
    """Tests de HU-ASO-02 (Suscripción de acciones al alta del asociado):
    uno por escenario de aceptación. El alta en sí (Asociado) se prueba en
    AsociadoAltaFormTests — acá el foco es la suscripción que se crea
    automáticamente en form.save() (ver forms.AsociadoAltaForm.save)."""

    def test_escenario_1_suscripcion_inicial_al_dar_de_alta(self):
        ValorNominalAccion.objects.create(valor="10.00", vigente_desde="2026-01-01")
        ParametroSuscripcion.objects.create(pk=1, cantidad_acciones_inicial=50)
        asociado = _crear(_datos_real())
        self.assertEqual(SuscripcionAcciones.objects.count(), 1)
        suscripcion = SuscripcionAcciones.objects.get(asociado=asociado)
        self.assertEqual(suscripcion.numero_titulo, "00001")
        self.assertEqual(suscripcion.cantidad_acciones, 50)
        self.assertEqual(suscripcion.fecha_suscripcion, datetime.date.today())

    def test_escenario_2_calculo_del_capital_suscripto(self):
        ValorNominalAccion.objects.create(valor="12.50", vigente_desde="2026-01-01")
        ParametroSuscripcion.objects.create(pk=1, cantidad_acciones_inicial=50)
        asociado = _crear(_datos_real())
        suscripcion = SuscripcionAcciones.objects.get(asociado=asociado)
        self.assertEqual(suscripcion.capital_suscripto, 50 * 12.50)

    def test_escenario_3_consulta_desde_la_ficha(self):
        # Este escenario pide mostrar cantidad de acciones, N° de título,
        # capital suscripto y fecha en la solapa Suscripción de la ficha.
        # La ficha todavía usa datos de muestra (ver associate_data.py) y
        # el modelo Asociado no tiene los campos que esa pantalla necesita
        # (teléfono, categoría, etc.), así que verificamos acá que el
        # registro guardado tiene todos los datos que esa consulta
        # necesitaría mostrar, en vez de una prueba de la vista de ficha —
        # ver la nota en views.asociado_alta y el mensaje a Clara.
        ValorNominalAccion.objects.create(valor="10.00", vigente_desde="2026-01-01")
        ParametroSuscripcion.objects.create(pk=1, cantidad_acciones_inicial=50)
        asociado = _crear(_datos_real())
        suscripcion = SuscripcionAcciones.objects.get(asociado=asociado)
        self.assertTrue(suscripcion.cantidad_acciones)
        self.assertTrue(suscripcion.numero_titulo)
        self.assertTrue(suscripcion.capital_suscripto)
        self.assertTrue(suscripcion.fecha_suscripcion)

    def test_escenario_4_cambio_del_parametro_de_suscripcion_inicial(self):
        ValorNominalAccion.objects.create(valor="10.00", vigente_desde="2026-01-01")
        ParametroSuscripcion.objects.create(pk=1, cantidad_acciones_inicial=5)
        primero = _crear(_datos_real(numero_documento="11111111"))

        parametro = ParametroSuscripcion.obtener()
        parametro.cantidad_acciones_inicial = 50
        parametro.save()
        segundo = _crear(_datos_real(numero_documento="22222222"))

        self.assertEqual(SuscripcionAcciones.objects.get(asociado=primero).cantidad_acciones, 5)
        self.assertEqual(SuscripcionAcciones.objects.get(asociado=segundo).cantidad_acciones, 50)

    def test_escenario_5_suscripciones_bajo_distintos_valores_nominales(self):
        ValorNominalAccion.objects.create(valor="10.00", vigente_desde="2026-01-01")
        ParametroSuscripcion.objects.create(pk=1, cantidad_acciones_inicial=50)
        asociado = _crear(_datos_real())
        suscripcion_original = SuscripcionAcciones.objects.get(asociado=asociado)
        self.assertEqual(suscripcion_original.capital_suscripto, 500)

        # Se carga un valor nominal nuevo con vigencia futura: no debe
        # alterar el capital ya calculado de la suscripción existente.
        ValorNominalAccion.objects.create(valor="99.00", vigente_desde="2099-01-01")
        suscripcion_original.refresh_from_db()
        self.assertEqual(suscripcion_original.capital_suscripto, 500)
        self.assertEqual(suscripcion_original.valor_nominal, 10)

    def test_escenario_6_suscripcion_sin_valor_nominal_vigente(self):
        # No se crea ningún ValorNominalAccion.
        ParametroSuscripcion.objects.create(pk=1, cantidad_acciones_inicial=50)
        asociado = _crear(_datos_real())
        # El asociado se crea igual; la suscripción no.
        self.assertEqual(Asociado.objects.count(), 1)
        self.assertEqual(SuscripcionAcciones.objects.count(), 0)

        form = AsociadoAltaForm(data=_datos_real(numero_documento="99999999"))
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertIsNone(form.suscripcion)
        self.assertIn("valor nominal", form.suscripcion_error)
        self.assertEqual(SuscripcionAcciones.objects.count(), 0)

    def test_numero_titulo_correlativo_independiente(self):
        ValorNominalAccion.objects.create(valor="10.00", vigente_desde="2026-01-01")
        ParametroSuscripcion.objects.create(pk=1, cantidad_acciones_inicial=50)
        _crear(_datos_real(numero_documento="11111111"))
        _crear(_datos_ideal(numero_documento="30712121218"))
        titulos = list(SuscripcionAcciones.objects.order_by("numero_titulo").values_list("numero_titulo", flat=True))
        self.assertEqual(titulos, ["00001", "00002"])


class AssociateDataTests(TestCase):
    """Tests de associate_data.py después de reemplazar los datos de
    muestra (_ASOCIADOS_MUESTRA) por consultas reales al modelo Asociado —
    a pedido de Clara, mismo patrón que seed_demo.py en San Cayetano. El
    contrato de diccionario que consumen los templates (asociados_list.html,
    asociado_ficha.html) no cambió: estos tests verifican ese contrato
    contra datos reales, no contra la muestra fija."""

    def test_listado_vacio_sin_asociados(self):
        self.assertEqual(ad.get_asociados_list(), [])
        self.assertEqual(ad.get_localidades(), [])

    def test_listado_refleja_asociados_reales(self):
        real = _crear(_datos_real(
            numero_documento="11111111", nombre_apellido="Ana Ríos",
        ))
        real.localidad = "San Manuel"
        real.domicilio = "Rivadavia 100"
        real.save()

        listado = ad.get_asociados_list()
        self.assertEqual(len(listado), 1)
        fila = listado[0]
        self.assertEqual(fila["numero_asociado"], real.numero_asociado)
        self.assertEqual(fila["numero_usuario"], real.numero_usuario)
        self.assertEqual(fila["nombre_completo"], "Ana Ríos")
        self.assertEqual(fila["estado"], "Activo")
        self.assertEqual(fila["localidad"], "San Manuel")
        self.assertEqual(fila["direccion"], "Rivadavia 100")
        self.assertEqual(fila["roles"], ["Asociado", "Usuario"])

        self.assertEqual(ad.get_localidades(), ["San Manuel"])

    def test_roles_incluye_proveedor_solo_si_esta_activo(self):
        real = _crear(_datos_real(numero_documento="22222222"))
        real.es_proveedor = True
        real.save()
        fila = ad.get_asociados_list()[0]
        self.assertEqual(fila["roles"], ["Asociado", "Usuario", "Proveedor"])

    def test_get_associate_numero_inexistente_devuelve_none(self):
        """Antes (con datos de muestra) un numero_asociado no encontrado
        mostraba por error el primer asociado de la lista. Ahora tiene que
        devolver None — ver views.asociado_ficha, que lo convierte en 404."""
        _crear(_datos_real(numero_documento="11111111"))
        self.assertIsNone(ad.get_associate("00999"))
        self.assertIsNone(ad.get_associate(None))

    def test_get_associate_persona_real(self):
        real = _crear(_datos_real(
            numero_documento="11111111", nombre_apellido="Ana Ríos", sexo="F",
            fecha_nacimiento_constitucion="1990-01-15",
        ))
        real.cuit = ""
        real.telefono_fijo = "0249 442-1180"
        real.categoria = "Residencial"
        real.save()

        ficha = ad.get_associate(real.numero_asociado)
        self.assertEqual(ficha["nombre_completo"], "Ana Ríos")
        self.assertEqual(ficha["iniciales"], "AR")
        self.assertTrue(ficha["activo"])
        self.assertTrue(ficha["es_asociado"])
        self.assertTrue(ficha["es_usuario"])
        self.assertFalse(ficha["es_proveedor"])

        personal = {f["label"]: f["value"] for f in ficha["personal"]}
        self.assertEqual(personal["Nombre y apellido"], "Ana Ríos")
        self.assertEqual(personal["DNI"], "11.111.111")
        self.assertEqual(personal["CUIT/CUIL"], "—")
        self.assertEqual(personal["Fecha de nacimiento"], "15/01/1990")
        self.assertEqual(personal["Género"], "Femenino")

        contacto = {f["label"]: f["value"] for f in ficha["contacto"]}
        self.assertEqual(contacto["Teléfono fijo"], "0249 442-1180")
        self.assertEqual(contacto["Email"], "—")

        administrativa = {f["label"]: f["value"] for f in ficha["administrativa"]}
        self.assertEqual(administrativa["Categoría"], "Residencial")

    def test_get_associate_persona_ideal(self):
        ideal = _crear(_datos_ideal(numero_documento="30712121218"))
        ficha = ad.get_associate(ideal.numero_asociado)
        self.assertEqual(ficha["nombre_completo"], "Cooperativa Ejemplo SRL")
        personal = {f["label"]: f["value"] for f in ficha["personal"]}
        self.assertEqual(personal["Razón social"], "Cooperativa Ejemplo SRL")
        self.assertEqual(personal["Tipo de organismo"], "SRL")
        self.assertEqual(personal["CUIT"], "30-71212121-8")
        self.assertNotIn("DNI", personal)

    def test_tabs_suscripcion_y_societario_con_datos_reales(self):
        ValorNominalAccion.objects.create(valor="10.00", vigente_desde="2026-01-01")
        ParametroSuscripcion.objects.create(pk=1, cantidad_acciones_inicial=50)
        real = _crear(_datos_real(numero_documento="11111111"))

        associate = ad.get_associate(real.numero_asociado)
        tabs = ad.get_associate_tabs(associate)
        soc = next(t for t in tabs if t["id"] == "societario")
        self.assertEqual(
            {f["label"]: f["value"] for f in soc["fields"]}["Estado societario"],
            "Activo",
        )
        susc = next(t for t in tabs if t["id"] == "suscripcion")
        susc_fields = {f["label"]: f["value"] for f in susc["fields"]}
        titulo = SuscripcionAcciones.objects.get(asociado=real)
        self.assertEqual(susc_fields["N° de título"], titulo.numero_titulo)
        self.assertEqual(susc_fields["Acciones suscriptas"], "50")
        self.assertEqual(susc_fields["Capital suscripto"], f"${titulo.capital_suscripto}")

    def test_tab_suscripcion_sin_valor_nominal_vigente(self):
        # Escenario 6 de HU-ASO-02: alta sin valor nominal configurado — la
        # ficha no debe romper, tiene que mostrar "—" en vez de reventar.
        real = _crear(_datos_real(numero_documento="11111111"))
        self.assertIsNone(SuscripcionAcciones.objects.filter(asociado=real).first())

        associate = ad.get_associate(real.numero_asociado)
        tabs = ad.get_associate_tabs(associate)
        susc = next(t for t in tabs if t["id"] == "suscripcion")
        susc_fields = {f["label"]: f["value"] for f in susc["fields"]}
        self.assertEqual(susc_fields["Acciones suscriptas"], "—")

    def test_tab_proveedor_oculta_si_no_corresponde(self):
        real = _crear(_datos_real(numero_documento="11111111"))
        associate = ad.get_associate(real.numero_asociado)
        tabs = ad.get_associate_tabs(associate)
        self.assertNotIn("proveedor", [t["id"] for t in tabs])

        real.es_proveedor = True
        real.save()
        associate = ad.get_associate(real.numero_asociado)
        tabs = ad.get_associate_tabs(associate)
        self.assertIn("proveedor", [t["id"] for t in tabs])


class SeedAsociadosCommandTests(TestCase):
    """Tests del comando de siembra (core/management/commands/seed_asociados
    .py): idempotencia, cantidad de registros y validez de los datos
    generados (DNI/CUIT, localidades)."""

    def test_siembra_crea_doce_asociados_con_suscripcion(self):
        call_command("seed_asociados")
        self.assertEqual(Asociado.objects.count(), 12)
        self.assertTrue(ValorNominalAccion.objects.exists())
        self.assertTrue(ParametroSuscripcion.objects.exists())
        # Todos los sembrados quedan con su suscripción inicial registrada,
        # porque el comando se asegura de que exista un valor nominal antes.
        self.assertEqual(SuscripcionAcciones.objects.count(), 12)

    def test_siembra_es_idempotente(self):
        call_command("seed_asociados")
        primeros = set(Asociado.objects.values_list("numero_documento", flat=True))
        call_command("seed_asociados")
        self.assertEqual(Asociado.objects.count(), 12)
        self.assertEqual(
            set(Asociado.objects.values_list("numero_documento", flat=True)), primeros,
        )

    def test_siembra_respeta_valor_nominal_ya_cargado(self):
        ValorNominalAccion.objects.create(valor="999.00", vigente_desde="2020-01-01")
        call_command("seed_asociados")
        self.assertEqual(ValorNominalAccion.objects.count(), 1)
        self.assertEqual(ValorNominalAccion.objects.first().valor, 999)

    def test_todos_los_cuit_generados_son_validos(self):
        call_command("seed_asociados")
        for asociado in Asociado.objects.exclude(cuit=""):
            self.assertTrue(cuit_valido(asociado.cuit), f"CUIT inválido: {asociado.cuit}")
        for asociado in Asociado.objects.filter(tipo_persona=Asociado.TIPO_PERSONA_IDEAL):
            self.assertTrue(cuit_valido(asociado.numero_documento), f"CUIT inválido: {asociado.numero_documento}")

    def test_siembra_incluye_al_menos_un_proveedor_y_una_localidad_rural(self):
        call_command("seed_asociados")
        self.assertTrue(Asociado.objects.filter(es_proveedor=True).exists())
        self.assertIn("Gardey", ad.get_localidades())
