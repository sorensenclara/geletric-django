"""
Tests de HU-ASO-01 (Alta de asociado): uno por escenario de aceptación
donde tiene sentido, más las funciones de validators.py por separado.

CUIT de prueba usados acá (verificados a mano con el algoritmo de
módulo 11 antes de escribir los tests, no inventados sobre la marcha):
- 20111111112 → real, DNI 11111111 (el "CUIT de prueba" más usado en
  sistemas argentinos, por eso se eligió como caso de referencia).
- 30712121218 → ideal, identificación 71212121.
"""
from django.test import TestCase

from .forms import AsociadoAltaForm
from .models import Asociado
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
