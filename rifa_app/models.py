from django.db import models


# =======================================================
# 1. MODELO RIFA (INFORMACIÓN PRINCIPAL DEL EVENTO)
# =======================================================
class Rifa(models.Model):
    # Campos que definen la rifa
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Rifa")
    descripcion_corta = models.TextField(verbose_name="Descripción Breve")
    premio_principal = models.CharField(max_length=255, verbose_name="Premio Principal")
    
    # Campo para la imagen
    imagen_principal = models.ImageField(upload_to='rifas/', verbose_name="Imagen del Premio")
    
    # Precios y Cantidad
    precio = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Costo del Boleto ($)")
    cantidad_numeros = models.IntegerField(
        verbose_name="Cantidad Total de Números",
        default=10000, 
        help_text="Número total de boletos disponibles (ej: 100 para 00-99, 1000 para 000-999)"
    )
    
    # Fechas
    fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
    fecha_sorteo = models.DateTimeField(verbose_name="Fecha y Hora del Sorteo")

    # Estado
    activa = models.BooleanField(default=True, verbose_name="Rifa Activa")


    def get_formato_numero(self):
        """Retorna el número de dígitos (2, 3 o 4) para el formateo de números."""
        if self.cantidad_numeros <= 100:
            return 2 
        elif self.cantidad_numeros <= 1000:
            return 3 
        else:
            return 4 

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Rifa"
        verbose_name_plural = "Rifas"


# =======================================================
# 2. MODELO NUMERO (BOLETO Y DATOS DEL COMPRADOR)
# =======================================================
class Numero(models.Model):
    # Vínculo con la Rifa (CLAVE: null=True por la lógica de signals)
    rifa = models.ForeignKey(
        Rifa, 
        on_delete=models.CASCADE, 
        related_name='numeros',
        null=True,  
        blank=True  
    )
    
    # Campos del Boleto
    numero = models.CharField(max_length=4) # max_length 4 es suficiente para 0000-9999
    estado = models.CharField(
        max_length=20,
        default='disponible',
        choices=[
            ('disponible', 'Disponible'), 
            ('reservado', 'Reservado'), 
            ('vendido', 'Vendido')
        ]
    )
    
    # Datos del comprador
    cedula = models.CharField(max_length=20, blank=True, null=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    
    # Datos de la Transacción
    banco = models.CharField(max_length=100, blank=True, null=True)
    referencia = models.CharField(max_length=20, blank=True, null=True)
    imagen_transferencia = models.ImageField(upload_to='transferencias/', blank=True, null=True)
    fecha_compra = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        # Manejamos el caso de que 'rifa' sea None temporalmente (por la señal)
        rifa_nombre = self.rifa.nombre if self.rifa else "SIN RIFA"
        return f"[{rifa_nombre}] - {self.numero} ({self.estado.upper()})"

    class Meta:
        # 1. Asegura que no se repitan números dentro de la misma rifa
        unique_together = ('rifa', 'numero')
        # 2. Nombres para el administrador
        verbose_name = "Número de Boleto"
        verbose_name_plural = "Números de Boletos"