from django.contrib import admin

from .models import Asociado, ParametroSuscripcion, SuscripcionAcciones, ValorNominalAccion


@admin.register(Asociado)
class AsociadoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_asociado", "numero_usuario", "nombre_o_razon_social",
        "tipo_persona", "condicion_iva", "estado_societario", "fecha_ingreso",
    )
    list_filter = ("tipo_persona", "condicion_iva", "estado_societario")
    search_fields = ("numero_asociado", "numero_usuario", "nombre_apellido", "razon_social", "numero_documento", "cuit")
    readonly_fields = ("numero_asociado", "numero_usuario", "fecha_ingreso")


@admin.register(ParametroSuscripcion)
class ParametroSuscripcionAdmin(admin.ModelAdmin):
    """Fila única (HU-ASO-02) — se edita acá hasta que exista la pantalla
    Técnico → Parámetros generales. No se permite agregar una segunda."""
    list_display = ("cantidad_acciones_inicial",)

    def has_add_permission(self, request):
        return not ParametroSuscripcion.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ValorNominalAccion)
class ValorNominalAccionAdmin(admin.ModelAdmin):
    list_display = ("vigente_desde", "valor")
    ordering = ("-vigente_desde",)


@admin.register(SuscripcionAcciones)
class SuscripcionAccionesAdmin(admin.ModelAdmin):
    list_display = (
        "numero_titulo", "asociado", "cantidad_acciones",
        "valor_nominal", "capital_suscripto", "fecha_suscripcion",
    )
    search_fields = ("numero_titulo", "asociado__numero_asociado", "asociado__nombre_apellido", "asociado__razon_social")
    readonly_fields = ("numero_titulo",)
