const modal = document.getElementById("imageModal");
const modalImg = document.getElementById("img01");
const span = document.getElementsByClassName("close-img")[0];

// Hacemos openModal global (aunque el DOMContentLoaded no es necesario aquí, es mejor para la compatibilidad)
window.openModal = function(imgSrc) {
    modal.style.display = "block";
    modalImg.src = imgSrc;
}

if (span) {
    span.onclick = function() { 
        modal.style.display = "none";
    }
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}


// =======================================================
// LÓGICA DE CONFIRMACIÓN DE VENTA (Segura con CSRF)
// =======================================================

// 🎯 Esta es la función que llama el botón onclick
async function confirmarVentaForm(buttonElement) {
    
    const form = buttonElement.closest('form');
    // Obtenemos los datos del botón (del HTML)
    const url = form.action;
    const nombre = buttonElement.dataset.nombre; 
    const numero = buttonElement.dataset.numeroValor;
    const telefono = buttonElement.dataset.whatsappTelefono;
    
    // El CSRF Token lo tomamos del formulario (input oculto)
    const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]').value;
    
    // 1. Preguntar confirmación
    if (!confirm(`⚠️ ¿Estás seguro de CONFIRMAR la venta del número ${numero} a ${nombre}? Esto es irreversible.`)) {
        return;
    }

    try {
        // 2. Enviar la solicitud POST (Confirmar la venta)
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken, // Enviamos el token del formulario
            },
            // Como la vista de Django espera un POST sin JSON, esto es más simple
        });
        
        const data = await response.json();

        if (data.status === 'success') { // Tu vista de Django debe devolver 'success'
            
            // 3. Abrir WhatsApp en una nueva pestaña (Usamos la URL que Django devuelve)
            if (data.whatsapp_url) {
                window.open(data.whatsapp_url, '_blank');
            }
            
            // 4. Recargar la página para actualizar el estado de la tabla
            alert(`✅ ¡Venta de ${numero} confirmada! Abrirá WhatsApp para notificar a ${nombre}.`);
            window.location.reload(); 
            
        } else {
            alert(`Error al confirmar venta: ${data.message}`);
        }

    } catch (error) {
        console.error('Error en la confirmación:', error);
        alert('Hubo un error de conexión al confirmar la venta.');
    }
}

