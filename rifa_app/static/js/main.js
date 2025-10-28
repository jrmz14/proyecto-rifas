// =======================================================
// MÓDULO PRINCIPAL: GESTIÓN DE RIFAS Y SELECCIÓN (main.js)
// =======================================================

document.addEventListener('DOMContentLoaded', () => {

    // ----------------------------------------------------
    // 1. INICIALIZACIÓN CRÍTICA (FUERA DE CUALQUIER RETURN)
    // ----------------------------------------------------
    const gridNumeros = document.getElementById('grid-numeros');
    
    // Si no estamos en la página de la rifa, salimos.
    if (!gridNumeros) return; 

    // Referencias y variables de estado
    const botonComprar = document.getElementById('boton-comprar');
    const cantidadSeleccionadaSpan = document.getElementById('cantidad-seleccionada');
    const modal = document.getElementById('modal-formulario');
    const closeButton = document.querySelector('.close-button');
    const resumenNumerosDiv = document.getElementById('resumen-numeros');
    const inputNumerosSeleccionados = document.getElementById('id_numeros_seleccionados');
    const buscadorInput = document.getElementById('buscador-input');
    const paginacionDiv = document.querySelector('.paginacion');
    const rifaActualId = gridNumeros.dataset.rifaId;
    const rifaGuardadaId = localStorage.getItem('rifaIdSeleccionada'); 
    let debounceTimeout;

    // 🎯 CARGA DE LA VARIABLE CLAVE (CRÍTICO)
    let numerosSeleccionados = JSON.parse(localStorage.getItem('numerosSeleccionados')) || [];
    // Asegura que todos los elementos son STRING para que la selección funcione
    numerosSeleccionados = numerosSeleccionados.map(String); 


    // ----------------------------------------------------
    // 2. LÓGICA DE LIMPIEZA INICIAL
    // ----------------------------------------------------
    
    // FIX DE LOCALSTORAGE: Limpieza de Rifas Anteriores
    if (rifaActualId !== rifaGuardadaId) {
        localStorage.removeItem('numerosSeleccionados');
        numerosSeleccionados = []; 
        if (rifaActualId) {
            localStorage.setItem('rifaIdSeleccionada', rifaActualId);
        }
    }
    
    // FIX POST-COMPRA: Limpieza de Éxito
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('compra_exitosa') === 'true') {
        localStorage.removeItem('numerosSeleccionados');
        numerosSeleccionados = []; 
        alert('¡Felicidades! Tu(s) número(s) ha(n) sido reservado(s) pendiente de verificación de pago.');
        // Limpiamos la URL sin detener la ejecución del script
        window.history.replaceState({}, document.title, window.location.pathname); 
    }


    // ----------------------------------------------------
    // 3. FUNCIONES DE LÓGICA DE INTERFAZ (UI)
    // ----------------------------------------------------
    
    // ... (Tu función dibujarResumenModal va aquí) ...
    const dibujarResumenModal = () => {
        resumenNumerosDiv.innerHTML = '';
        inputNumerosSeleccionados.value = JSON.stringify(numerosSeleccionados);

        if (numerosSeleccionados.length === 0) {
            resumenNumerosDiv.innerHTML = '<p>No hay números seleccionados.</p>';
            return;
        }

        const titulo = document.createElement('p');
        titulo.innerHTML = '<strong>Haz clic en un número para eliminarlo:</strong>';
        resumenNumerosDiv.appendChild(titulo);
        
        numerosSeleccionados.forEach(num => {
            const span = document.createElement('span');
            span.className = 'numero-resumen';
            span.dataset.numero = num; 
            span.textContent = `${num} ❌`;
            resumenNumerosDiv.appendChild(span);
        });
    };
    
    // ... (Tu función actualizarUI va aquí) ...
    const actualizarUI = () => {
        cantidadSeleccionadaSpan.textContent = numerosSeleccionados.length;
        botonComprar.disabled = numerosSeleccionados.length === 0;

        document.querySelectorAll('.numero').forEach(numeroDiv => {
            const num = numeroDiv.dataset.numero;
            const esDisponible = numeroDiv.classList.contains('disponible');
            const estaSeleccionado = numerosSeleccionados.includes(num); 
            
            if (estaSeleccionado && esDisponible) {
                numeroDiv.classList.add('seleccionado');
            } else {
                numeroDiv.classList.remove('seleccionado');
            }
        });
    };


    // ----------------------------------------------------
    // 4. LÓGICA DE BÚSQUEDA OPTIMIZADA (AJAX/Fetch)
    // ----------------------------------------------------
    
    // ... (Tu función buscarNumeros va aquí) ...
    const buscarNumeros = (busqueda) => {
        if (!busqueda || busqueda.length < 2) {
            window.location.href = window.location.pathname; 
            return;
        }

        fetch(window.location.origin + `/buscar/?q=${busqueda}`)
            .then(response => response.json())
            .then(data => {
                gridNumeros.innerHTML = '';
                if (paginacionDiv) paginacionDiv.style.display = 'none';

                if (data.numeros.length === 0) {
                    gridNumeros.innerHTML = '<p style="text-align:center; padding: 20px;">No se encontraron números.</p>';
                    return;
                }

                data.numeros.forEach(numero => {
                    const numDiv = document.createElement('div');
                    const isSelected = numerosSeleccionados.includes(numero.numero) ? 'seleccionado' : '';
                    
                    numDiv.className = `numero ${numero.estado} ${isSelected}`;
                    numDiv.dataset.numero = numero.numero;
                    numDiv.textContent = numero.numero;
                    gridNumeros.appendChild(numDiv);
                });
                actualizarUI(); 
            })
            .catch(error => console.error('Error al buscar números:', error));
    };


    // ----------------------------------------------------
    // 5. LÓGICA DE POLLING (Sincronización de Estados)
    // ----------------------------------------------------

    function actualizarNumerosPorPolling() {
        // REFUERZO: Usamos la URL absoluta. El 200 OK en Network indica que la ruta funciona.
        fetch(window.location.origin + '/api/status/') 
            .then(response => {
                if (!response.ok) {
                    console.error(`Error de conexión HTTP: ${response.status}`);
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Aquí el Polling es correcto. El fallo debe ser la aplicación de cambios.
                if (data.status === 'ok') {
                    data.numeros.forEach(num => {
                        const numeroDiv = gridNumeros.querySelector(`[data-numero="${num.numero}"]`);
                        
                        if (numeroDiv) {
                            const estadoActual = numeroDiv.className.split(' ').find(cls => 
                                cls === 'reservado' || cls === 'vendido' || cls === 'disponible'
                            );

                            if (estadoActual !== num.estado) {
                                
                                // A. ACTUALIZACIÓN DEL DOM
                                numeroDiv.classList.remove('reservado', 'vendido', 'disponible', 'seleccionado');
                                numeroDiv.classList.add(num.estado);
                                
                                // B. LÓGICA CRÍTICA: LIMPIEZA DEL CARRITO DEL CLIENTE
                                if (num.estado === 'vendido' || num.estado === 'reservado') {
                                    const numValue = num.numero; 
                                    const index = numerosSeleccionados.indexOf(numValue);
                                    
                                    if (index > -1) {
                                        numerosSeleccionados.splice(index, 1);
                                        localStorage.setItem('numerosSeleccionados', JSON.stringify(numerosSeleccionados));
                                        
                                        actualizarUI(); 
                                        if (modal.style.display === 'block') { dibujarResumenModal(); }
                                    }
                                }
                            }
                        }
                    });
                }
            })
            .catch(error => { console.error("Error grave en el Polling o el formato de respuesta:", error); });
    }


    // ----------------------------------------------------
    // 6. ASIGNACIÓN DE EVENT LISTENERS
    // ----------------------------------------------------

    // A. Lógica de SELECCIÓN/DESELECCIÓN en la CUADRÍCULA (Esta es la que NO funciona)
    gridNumeros.addEventListener('click', (event) => {
        const numeroDiv = event.target;
        // Solo interactuamos con números disponibles y con el elemento 'numero'
        if (!numeroDiv.classList.contains('numero') || !numeroDiv.classList.contains('disponible')) {
            return; 
        }
        
        const num = numeroDiv.dataset.numero; 
        const index = numerosSeleccionados.indexOf(num);

        if (index > -1) {
            numerosSeleccionados.splice(index, 1);
        } else {
            numerosSeleccionados.push(num);
        }

        localStorage.setItem('numerosSeleccionados', JSON.stringify(numerosSeleccionados));
        actualizarUI();
    });


    // B. Lógica de ELIMINACIÓN en el MODAL (Resumen)
    resumenNumerosDiv.addEventListener('click', (event) => {
        if (event.target.classList.contains('numero-resumen')) {
            const numAEliminar = event.target.dataset.numero;

            const index = numerosSeleccionados.indexOf(numAEliminar); 
            
            if (index > -1) {
                numerosSeleccionados.splice(index, 1); 
            }

            localStorage.setItem('numerosSeleccionados', JSON.stringify(numerosSeleccionados));
            actualizarUI();
            dibujarResumenModal(); 
        }
    });


    // C. Lógica del BUSCADOR DINÁMICO (Debounce)
    buscadorInput.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        const busqueda = buscadorInput.value.trim();

        debounceTimeout = setTimeout(() => {
            if (busqueda.length > 1) {
                buscarNumeros(busqueda);
            } else if (busqueda.length === 0) {
                window.location.href = window.location.pathname; 
            }
        }, 300);
    });

    // D. Apertura y cierre del MODAL
    botonComprar.addEventListener('click', () => {
        dibujarResumenModal(); 
        modal.style.display = 'block';
    });
    
    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // E. INICIO AL CARGAR LA PÁGINA
    actualizarUI();

    // 🎯 INICIAR EL POLLING
    actualizarNumerosPorPolling();
    setInterval(actualizarNumerosPorPolling, 10000); 

   
});


$(document).ready(function() { 
    // Aseguramos que Slick y jQuery estén definidos y que el elemento exista
    if (typeof $.fn.slick !== 'undefined' && $('.finished-events-carousel').length) {
        $('.finished-events-carousel').slick({
            infinite: true,
            slidesToShow: 3, 
            slidesToScroll: 1,
            autoplay: true,
            autoplaySpeed: 3000,
            dots: true, 
            arrows: true, 
            responsive: [
                {
                    breakpoint: 1024,
                    settings: { slidesToShow: 2, slidesToScroll: 2 }
                },
                {
                    breakpoint: 600,
                    settings: { slidesToShow: 1, slidesToScroll: 1 }
                }
            ]
        });
    }
});