from django.contrib import admin

from .models import Asociado


@admin.register(Asociado)
class AsociadoAdmin(admin.ModelAdmin):
    list_display = (
        "numero_asociado", "numero_usuario", "nombre_o_razon_social",
        "tipo_persona", "condicion_iva", "estado_societario", "fecha_ingreso",
    )
    list_filter = ("tipo_persona", "condicion_iva", "estado_societario")
    search_fields = ("numero_asociado", "numero_usuario", "nombre_apellido", "razon_social", "numero_documento", "cuit")
    readonly_fields = ("numero_asociado", "numero_usuario", "fecha_ingreso")
