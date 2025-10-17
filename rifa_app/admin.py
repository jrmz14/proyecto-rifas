from django.contrib import admin
from .models import Rifa, Numero


class RifaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'premio_principal', 'precio', 'activa', 'fecha_sorteo')
    list_filter = ('activa', 'fecha_sorteo')
    search_fields = ('nombre', 'premio_principal')


class NumeroAdmin(admin.ModelAdmin):
    # Muestra campos clave en la lista
    list_display = ('rifa', 'numero', 'estado', 'nombre', 'apellido', 'telefono')
    # Permite filtrar por rifa y estado
    list_filter = ('rifa', 'estado')
    # Habilita la búsqueda por número o datos del comprador
    search_fields = ('numero', 'nombre', 'apellido', 'cedula', 'telefono')
    # Hace que el campo 'rifa' sea un enlace de solo lectura para evitar cambios accidentales
    readonly_fields = ('rifa',)

admin.site.register(Rifa, RifaAdmin)
admin.site.register(Numero, NumeroAdmin)