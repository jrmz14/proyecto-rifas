from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.utils.http import urlencode
from urllib.parse import quote
import json
from .models import Numero, Rifa
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

# =======================================================
# FUNCIÓN AUXILIAR
# =======================================================

def get_rifa_activa():
    """Busca la rifa marcada como activa o devuelve None si no hay."""
    try:
        # Usamos .get() para asegurarnos de que solo hay una
        return Rifa.objects.get(activa=True)
    except (Rifa.DoesNotExist, Rifa.MultipleObjectsReturned):
        # Maneja ambos casos de forma limpia
        return None

# =======================================================
# VISTAS PRINCIPALES (Optimizadas)
# =======================================================

def index(request):
    # Usamos la función auxiliar
    rifa_activa = get_rifa_activa()
    
    rifas_finalizadas = Rifa.objects.filter(activa=False).order_by('-fecha_sorteo')[:5]

    context = {
        'rifa_activa': rifa_activa,
        'rifas_finalizadas': rifas_finalizadas,
    }
    return render(request, 'rifa_app/index.html', context)

def lista_numeros(request, rifa_id):
    rifa = get_object_or_404(Rifa, id=rifa_id)
    
    # --- 1. Definición de Rangos (Asume números de 0 a 999) ---
    rangos = []
    # Genera rangos de 100 en 100
    for i in range(0, 1000, 100):
        inicio = str(i).zfill(3)       # 000, 100, 200, etc.
        fin = str(i + 99).zfill(3)     # 099, 199, 299, etc.
        rangos.append((inicio, fin))

    # --- 2. Obtener el Rango Solicitado ---
    rango_param = request.GET.get('rango')
    rango_actual = None
    
    if rango_param and '-' in rango_param:
        try:
            inicio_rango, fin_rango = rango_param.split('-')
            inicio_rango = int(inicio_rango)
            fin_rango = int(fin_rango)
            rango_actual = rango_param # Para resaltar el botón activo en el HTML
        except ValueError:
            # Si el rango es inválido, volvemos al inicio
            inicio_rango = 0
            fin_rango = 99
            rango_actual = '000-099'
    else:
        # Rango por defecto (el primero)
        inicio_rango = 0
        fin_rango = 99
        rango_actual = '000-099'

   
    
    # Filtrar por un campo de texto requiere que los valores de inicio y fin sean strings con padding
    start_str = str(inicio_rango).zfill(3)
    end_str = str(fin_rango).zfill(3)

    numeros_del_rango = rifa.numero_set.filter(
        numero__gte=start_str,
        numero__lte=end_str
    ).order_by('numero')

    
    # Ya no usamos Paginator, el resultado es la lista filtrada.
    
    context = {
        'rifa': rifa,
        'page_obj': numeros_del_rango,         # Cambiamos 'page_obj' por la lista filtrada
        'rangos_disponibles': rangos,          # Para el menú de navegación
        'rango_actual': rango_actual,          # Para el botón activo
    }
    
    return render(request, 'rifa_app/lista_numeros.html', context)


def comprar_numeros(request):
    rifa_activa = get_rifa_activa()
    
    if rifa_activa is None:
        return HttpResponse("No hay rifa activa para procesar la compra.", status=400)

    if request.method == 'POST':
        # ... (Data retrieval) ...
        numeros_seleccionados_json = request.POST.get('numeros_seleccionados')
        numeros_a_vender = json.loads(numeros_seleccionados_json)
        
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        telefono = request.POST.get('telefono')
        banco = request.POST.get('banco')
        referencia = request.POST.get('referencia')
        imagen_transferencia = request.FILES.get('imagen_transferencia')
        
        try:
            with transaction.atomic():
                for num_str in numeros_a_vender:
                    numero_obj = Numero.objects.get(
                        rifa=rifa_activa, # CLAVE: Solo busca en la rifa activa
                        numero=num_str
                    )
                    
                    if numero_obj.estado != 'disponible':
                        return HttpResponse(f"El número {num_str} no está disponible (estado: {numero_obj.estado}).", status=400)
                    
                    numero_obj.estado = 'reservado'
                    numero_obj.cedula = cedula
                    numero_obj.nombre = nombre
                    numero_obj.apellido = apellido
                    numero_obj.telefono = telefono
                    numero_obj.banco = banco
                    numero_obj.referencia = referencia
                    numero_obj.imagen_transferencia = imagen_transferencia
                    numero_obj.save()
            
            return redirect('/rifa/?compra_exitosa=true') 
            
        except Numero.DoesNotExist:
            return HttpResponse("Uno de los números no existe en la rifa activa.", status=404)
        except Exception as e:
            return HttpResponse(f"Hubo un error en la compra: {e}", status=500)
    
    return HttpResponse("Método no permitido.", status=405)


def buscar_dinamico(request):
    rifa_activa = get_rifa_activa()
    
    if rifa_activa is None:
        return JsonResponse({'numeros': []})
        
    query = request.GET.get('q')

    if not query or len(query) < 2:
        return JsonResponse({'numeros': []})

    resultados = Numero.objects.filter(
        rifa=rifa_activa, # CLAVE: Filtro por Rifa
        numero__startswith=query 
    ).values('numero', 'estado')[:50] 

    data = list(resultados)
    return JsonResponse({'numeros': data})

def get_numeros_status(request):
    """Devuelve el estado actual de todos los números de la rifa activa en formato JSON."""
    try:
        # Busca la rifa activa (Ajusta este filtro si usas otra lógica)
        rifa_activa = Rifa.objects.get(activa=True)
        
        # Consulta optimizada: solo obtiene el 'numero' y el 'estado'
        numeros_data = list(Numero.objects
                            .filter(rifa=rifa_activa)
                            .values('numero', 'estado'))
        
        return JsonResponse({'status': 'ok', 'numeros': numeros_data}, safe=False)
    
    except Rifa.DoesNotExist:
        # Si no hay rifa activa, devuelve un error 404
        return JsonResponse({'status': 'error', 'message': 'No hay rifa activa.'}, status=404)
    except Exception as e:
        # Si hay algún error en el servidor
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
# =======================================================
# VISTAS DE ADMINISTRACIÓN (Ligeramente modificadas)
# =======================================================
@login_required
def panel_admin(request):
    
    # 1. Obtenemos la rifa activa
    rifa_activa = get_rifa_activa()
    
    # 2. Manejo de Caso: Si NO hay rifa activa
    if rifa_activa is None:
        context = {
            'numeros': [],
            'rifa_activa': None,
            'mensaje_alerta': 'Actualmente no hay una Rifa marcada como activa para gestionar.'
        }
        # Renderizamos la plantilla con un mensaje de alerta
        return render(request, 'rifa_app/panel_admin.html', context)

    # 3. FILTRADO ROBUSTO: Solo números de la rifa activa
    numeros_gestion = Numero.objects.filter(
        rifa=rifa_activa, # <-- FILTRO CRÍTICO
        estado__in=['reservado', 'vendido'] # Solo gestionamos estos estados
    ).order_by('-fecha_compra')

    # 4. Lógica de WhatsApp (se mantiene correcta)
    for num in numeros_gestion:
        if num.estado == 'reservado' and num.telefono and num.nombre:
            mensaje = f"🎉 ¡Felicidades, {num.nombre}! El pago de tu número ({num.numero}) ha sido CONFIRMADO. ¡Ya es tuyo!"
            encoded_text = urlencode({'text': mensaje})
            num.whatsapp_link = f"https://wa.me/{num.telefono}?{encoded_text}"
        else:
            num.whatsapp_link = None
            
    # 5. Pasamos la rifa activa al contexto para mostrar su nombre
    context = {
        'numeros': numeros_gestion,
        'rifa_activa': rifa_activa, # Lo pasamos para mostrar el nombre del evento
    }
    return render(request, 'rifa_app/panel_admin.html', context)

# Nueva vista para confirmar una venta
@login_required
@login_required
def confirmar_venta(request, numero_id):
    if request.method == 'POST':
        try:
            numero_obj = get_object_or_404(Numero, id=numero_id)
            
            # 1. CAMBIO DE ESTADO (OK, esto funciona)
            numero_obj.estado = 'vendido'
            numero_obj.save()
            
           
            mensaje = (
                f"¡Hola {numero_obj.nombre}! Tu número *{numero_obj.numero}* "
                f"para la rifa ha sido confirmado y vendido con éxito. ¡Mucha suerte!"
            )
            
            if numero_obj.telefono:
                 whatsapp_url = (
                    f"https://wa.me/{numero_obj.telefono}" 
                    f"?text={quote(mensaje)}"
                 )
            else:
                 # Si no hay teléfono, debemos devolver una URL vacía o manejar el error
                 whatsapp_url = None 
                 
            # 3. DEVOLVER RESPUESTA JSON
            return JsonResponse({
                'status': 'success',
                'message': 'Venta confirmada en DB. Abriendo WhatsApp...',
                'whatsapp_url': whatsapp_url
            })
        
        except Exception as e:
           
            print(f"Error en la vista confirmar_venta: {e}") 
            return JsonResponse({'status': 'error', 'message': f'Fallo interno: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=400)
# Nueva vista para cancelar una reserva
@login_required
def cancelar_reserva(request, numero_id):
    if request.method == 'POST':
        numero_obj = get_object_or_404(Numero, id=numero_id)
        
        # Solo permite cancelar si el estado es 'reservado'
        if numero_obj.estado == 'reservado':
            numero_obj.estado = 'disponible'
            
            # Limpia los datos del comprador
            numero_obj.cedula = None
            numero_obj.nombre = None
            numero_obj.apellido = None
            numero_obj.banco = None
            numero_obj.referencia = None
            numero_obj.imagen_transferencia = None
            numero_obj.save()
            
        return redirect('panel_admin')