from django.urls import path, include 
from . import views
from django.conf.urls.static import static
from django.conf import settings # <-- NECESARIO




urlpatterns = [

    path('', views.index, name='index'), 
    path('rifa/', views.lista_numeros, name='lista_numeros'),
    path('comprar/', views.comprar_numeros, name='comprar_numeros'),
    path('buscar/', views.buscar_dinamico, name='buscar_dinamico'),

      
    # Rutas del Administrador
    path('admin-panel/', views.panel_admin, name='panel_admin'), # <-- Nueva ruta
    path('admin-panel/confirmar/<int:numero_id>/', views.confirmar_venta, name='confirmar_venta'), # <-- Nueva ruta
    path('admin-panel/cancelar/<int:numero_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('', include('django.contrib.auth.urls')),
    path('api/status/', views.get_numeros_status, name='get_numeros_status'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)