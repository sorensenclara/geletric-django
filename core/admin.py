from django.contrib import admin

from .models import Asociado, ParametroSuscripcion, Suministro, SuscripcionAcciones, ValorNominalAccion


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


@admin.register(Suministro)
class SuministroAdmin(admin.ModelAdmin):
    """HU-ASO-03: todavía no tiene alta propia (ver nota en
    models.Suministro), así que /admin/ es la única forma de cargar uno
    hasta que exista el wizard — acá el campo Socio ya sale marcado como
    obligatorio porque el modelo no admite blank/null (Escenario 1)."""
    list_display = ("socio", "titular", "fecha_alta")
    search_fields = (
        "socio__numero_asociado", "socio__nombre_apellido", "socio__razon_social",
        "titular__numero_asociado", "titular__nombre_apellido", "titular__razon_social",
    )
    readonly_fields = ("fecha_alta",)
