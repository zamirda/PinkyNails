from django.contrib import admin

from .models import Bloqueo, Cita, Foto


@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ("inicio", "nombre", "servicio", "telefono", "estado")
    list_filter = ("estado", "servicio")
    search_fields = ("nombre", "telefono")


@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ("fecha", "hora", "motivo")


@admin.register(Foto)
class FotoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "orden")
    list_editable = ("orden",)
