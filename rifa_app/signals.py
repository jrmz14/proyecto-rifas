# rifa_app/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction 
from .models import Rifa, Numero 

@receiver(post_save, sender=Rifa)
def generar_numeros_rifa_automatica(sender, instance, created, **kwargs):
    """
    Programa la creación de números DESPUÉS de que la Rifa se haya guardado
    correctamente en la base de datos (usando on_commit).
    """
    
    if created:
        
        # 1. Definimos la función de creación DENTRO de la señal
        def crear_numeros_en_base_datos():
            """Lógica que crea todos los números para la instancia actual."""
            
            # Usamos 'instance' que es visible dentro de esta función anidada
            cantidad = instance.cantidad_numeros
            formato = instance.get_formato_numero()
            
            numeros_a_crear = []
            for i in range(cantidad):
                numero_str = str(i).zfill(formato) 
                
                numeros_a_crear.append(
                    Numero(
                        rifa=instance, 
                        numero=numero_str,
                        estado='disponible'
                    )
                )
            
            # Inserción eficiente en la base de datos
            Numero.objects.bulk_create(numeros_a_crear)

      
        transaction.on_commit(crear_numeros_en_base_datos)