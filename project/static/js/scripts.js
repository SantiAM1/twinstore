document.addEventListener("DOMContentLoaded", () => {
    // ----- Tipo de factura ----- //
    const tipoFactura = document.getElementById('id_tipo_factura');
    const dniCuitContainer = document.getElementById('dni_cuit_container');
    const razonSocialContainer = document.getElementById('razon_social_container');
    const dniCuitInput = document.getElementById('id_dni_cuit');
    const dniCuitLabel = document.getElementById('dni_cuit_label');
    const razonSocialInput = document.getElementById('id_razon_social');
    
    if (tipoFactura) {
        function actualizarCamposFactura() {
            const value = tipoFactura.value;

            if (value === 'B') {
                dniCuitLabel.textContent = 'DNI *';
                dniCuitInput.required = true;
                dniCuitContainer.style.display = 'block';

                razonSocialContainer.style.display = 'none';
                razonSocialInput.required = false;
            } else if (value === 'A' || value === 'C') {
                dniCuitLabel.textContent = 'CUIT *';
                dniCuitInput.required = true;
                dniCuitContainer.style.display = 'block';

                razonSocialContainer.style.display = 'block';
                razonSocialInput.required = true;
            } else {
                dniCuitContainer.style.display = 'none';
                razonSocialContainer.style.display = 'none';
                dniCuitInput.required = false;
                razonSocialInput.required = false;
            }
        }
        tipoFactura.addEventListener('change', actualizarCamposFactura);
        window.addEventListener('DOMContentLoaded', actualizarCamposFactura);
    }
    // ----- Header ------ //
    let lastScrollTop = 0;
    const header = document.querySelector('.header-tag');
    const lowerHeader = document.querySelectorAll('.header-item')[1];

    window.addEventListener('scroll', function() {
        let currentScroll = window.scrollY || document.documentElement.scrollTop;
        if (currentScroll > lastScrollTop && currentScroll > 50) {
            // Scroll hacia abajo: animamos
            lowerHeader.classList.add('hide-on-scroll');
            header.classList.add('shrink');
            // Luego de la transición, aplicamos display none
            setTimeout(() => {
                if (lowerHeader.classList.contains('hide-on-scroll')) {
                    lowerHeader.classList.add('hidden');
                }
            }, 400); // mismo tiempo que la transición
        } else {
            // Volver a mostrar
            lowerHeader.classList.remove('hidden'); // quitamos display none
            setTimeout(() => {
                lowerHeader.classList.remove('hide-on-scroll');
            }, 10); // pequeño delay para que el navegador registre el cambio
            header.classList.remove('shrink');
        }
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    });
    // --- scripts.js ---
    const botonProductos = document.getElementById("boton-productos");
    const boxProdDisplay = document.getElementById("box-productos-display");
    const resultProdDisplay = document.getElementById("result-productos-display");

    botonProductos.addEventListener("click", (event) => {
        event.stopPropagation();
        boxProdDisplay.classList.toggle("display_none");

        document.addEventListener("click", (event) => {
            if (!boxProdDisplay.contains(event.target) && event.target !== botonProductos) {
                boxProdDisplay.classList.add("display_none");
            }
        }, { once: true });
    });

    const navItems = document.querySelectorAll(".nav-productos-items");

    navItems.forEach(item => {
        item.addEventListener("mouseenter", () => {
            navItems.forEach(navItem => navItem.classList.remove("categoria-selec"));
            item.classList.add("categoria-selec");
            resultProdDisplay.innerHTML = categorias[item.id] || '<div class="result-productos-column flex">No hay contenido disponible</div>';
        });
    });

    const userMenu = document.querySelector(".user-menu");
    const dropdown = document.getElementById("userDropdown");

    userMenu.addEventListener("click", function(event) {
        event.stopPropagation();
        dropdown.classList.toggle("show");
    });

    document.addEventListener("click", function(event) {
        if (!userMenu.contains(event.target)) {
            dropdown.classList.remove("show");
        }
    });

    const toggles = document.querySelectorAll(".toggle");
    toggles.forEach(toggle => {
        toggle.addEventListener("click", function() {
            toggle.querySelector("i").classList.toggle("rotated");
            let submenu = this.nextElementSibling;
            if (submenu) {
                submenu.style.display = submenu.style.display === "block" ? "none" : "block";
            }
        });
    });

    const menu = document.querySelector(".menu");
    const closeBtn = document.querySelector(".menu-title i");
    const openBtn = document.getElementById("open-menu");

    openBtn.addEventListener("click", function () {
        menu.classList.add("active");
    });

    closeBtn.addEventListener("click", function () {
        menu.classList.remove("active");
    });

    // --- mobile.js ---
    const filterButton = document.querySelector(".filter-button");
    const filterBox = document.querySelector(".filter-box-mobile");
    const filterItems = document.querySelectorAll(".filter-item");

    const ordenarButtons = document.querySelectorAll(".ordenar-button");
    const ordenarBoxes = document.querySelectorAll(".ordenar-box-mobile");

    function closeAllMenus(except = null) {
        if (except !== filterBox) {
            filterBox.classList.remove("show");
        }
        if (except !== ordenarBoxes) {
            ordenarBoxes.forEach(box => box.classList.remove("show"));
        }
    }

    if (filterButton) {
        filterButton.addEventListener("click", function (event) {
            event.stopPropagation();
            closeAllMenus(filterBox);
            filterBox.classList.toggle("show");
        });
    }

    ordenarButtons.forEach((button, index) => {
        button.addEventListener("click", function (event) {
            event.stopPropagation();
            closeAllMenus(ordenarBoxes);
            ordenarBoxes[index].classList.toggle("show");
        });
    });

    filterItems.forEach(item => {
        item.addEventListener("click", function (event) {
            event.stopPropagation();
            const expanded = this.nextElementSibling;
            const icon = this.querySelector("i");
            if (expanded && expanded.classList.contains("filter-expanded")) {
                expanded.classList.toggle("show");
                this.classList.toggle("active");
            }
        });
    });

    document.addEventListener("click", function (event) {
        closeAllMenus();
    });    
});

function scrollToImage(index) {
    const slider = document.querySelector('.product-slider');
    const imageWidth = slider.querySelector('img').clientWidth;
    const scrollPosition = index * imageWidth;

    slider.scrollTo({
        left: scrollPosition,
        behavior: 'smooth'
    });
}

let quantity = 1;
function increaseQuantity() {
    if (quantity < 5) {
        quantity++;
        document.getElementById("quantity").value = quantity;
    }
}
function decreaseQuantity() {
    if (quantity > 1) {
        quantity--;
        document.getElementById("quantity").value = quantity;
    }
}

// --- Lógica Axios --- //
document.addEventListener("DOMContentLoaded", () => {
    const csrftoken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
    axios.defaults.headers.common['X-CSRFToken'] = csrftoken;
    
    function toggleDisableItems(disabled = true) {
        const formElements = document.querySelectorAll('.bloqueable');
        formElements.forEach(element => {
            if (disabled) {
                element.setAttribute('disabled', 'disabled');
            } else {
                element.removeAttribute('disabled');
            }
        });

        const overlay = document.getElementById('loading-overlay');
        if (overlay) overlay.style.display = disabled ? 'flex' : 'none';
    }

    document.addEventListener('change', function (e) {
        if (e.target && e.target.id === 'ordenby') {
            const orden = e.target.value;
    
            // 🔁 Tomamos los filtros actuales de la URL
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.set('ordenby', orden); // actualizamos el ordenamiento
    
            // 🔄 Convertimos a objeto y enviamos a la función
            const filtrosActualizados = Object.fromEntries(urlParams.entries());
    
            aplicarFiltrosDinamicos(filtrosActualizados);
        }
    });
    
    
    document.addEventListener('click', async function (e) {
        const link = e.target.closest('.filter-link ,.filter-active-link, .filter-link-mobile');
        if (link) {
            e.preventDefault();
            toggleDisableItems(true);
    
            const newParams = new URL(link.href).searchParams;
            const parametros = {};
            newParams.forEach((value, key) => parametros[key] = value);
    
            aplicarFiltrosDinamicos(parametros).finally(() => toggleDisableItems(false));
        }
    });
    
    document.querySelectorAll('.ordenar-opcion').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
    
            const ordenSeleccionado = this.dataset.orden;
            const urlParams = new URLSearchParams(window.location.search);
    
            urlParams.set('ordenby', ordenSeleccionado); // Sobrescribe el orden actual
    
            const filtrosActualizados = Object.fromEntries(urlParams.entries());
    
            aplicarFiltrosDinamicos(filtrosActualizados);
        });
    });    

    document.querySelectorAll('.btn-cantidad').forEach(btn => {
        btn.addEventListener('click', async function() {
            const container = this.closest('.quantity-container');
            const pedidoId = container.dataset.pedidoId;
            const action = this.dataset.action

            toggleDisableItems(true);

            try {
                const response = await axios.post(window.api.actualizarPedido,{
                    pedido_id:pedidoId,
                    action:action,
                });

                const { total_productos, total_precio, cantidad } = response.data;

                container.querySelector('.input-value-cart').value = cantidad
                const fila = container.closest('tr');
                const precioSubtotal = fila?.querySelector('.cart-total-precio');
                const precio = parseFloat(container.dataset.precio);

                if (precioSubtotal && !isNaN(precio)) {
                    precioSubtotal.innerHTML = `$${(precio * cantidad).toFixed(2)}`;

                    // Animación suave
                    precioSubtotal.classList.remove('animate-flash'); // reset
                    void precioSubtotal.offsetWidth; // reflow trick
                    precioSubtotal.classList.add('animate-flash');
                }

                actualizarCarrito(total_precio,total_productos)
                
                if (parseInt(total_productos) === 0) {
                    mostrarCarritoVacio()
                }

                if (parseInt(cantidad) === 0) {
                    const fila = this.closest('tr');
                    fila?.nextElementSibling?.remove();
                    fila?.remove();
                }

                actualizarPreciosCarrito(total_precio)

            } catch (error) {
                console.error("Error al eliminar el producto:", error);
            } finally {
                toggleDisableItems(false);
            }
        });
    });

    document.querySelectorAll('.cart-prod-delete').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const pedidoId = this.dataset.pedidoId;
    
            toggleDisableItems(true);

            try {
                const response = await axios.post(window.api.eliminarPedido, {
                    pedido_id: parseInt(pedidoId)
                });

                const { total_productos, total_precio } = response.data;

                actualizarCarrito(total_precio,total_productos)
                
                if (parseInt(total_productos) === 0) {
                    mostrarCarritoVacio()
                } else  {
                    const fila = this.closest('tr');
                    fila?.nextElementSibling?.remove();
                    fila?.remove();
                }

                actualizarPreciosCarrito(total_precio)

            } catch (error) {
                console.error("Error al eliminar el producto:", error);
            } finally {
                toggleDisableItems(false);
            }
        });
    });    

    const addToCartForm = document.getElementById('add-to-cart-form');
    if (addToCartForm) {
        addToCartForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const producto_id = document.getElementById('producto-id').value;
            const cantidad = document.getElementById('quantity').value;

            try {
                const response = await axios.post(window.api.agregarAlCarrito, {
                    producto_id: parseInt(producto_id),
                    cantidad: parseInt(cantidad),
                });

                const { total_productos, total_precio, productoNombre,imagen_url,cantidad_pedido,subtotal } = response.data;

                actualizarCarrito(total_precio,total_productos)
                
                mostrarFeedbackCarrito(productoNombre, total_precio,imagen_url,cantidad_pedido,subtotal);

            } catch (error) {
                console.error('Error al agregar producto:', error);
                alert('Hubo un error al agregar el producto');
            }
        });
    }

    document.querySelectorAll('input[name="forma_pago"]').forEach((radio) => {
        radio.addEventListener('change', async (e) => {
            const form = document.querySelector('.users-perfil');
            if (!form.checkValidity()) {
                form.reportValidity();
                e.target.checked = false;
                return;
            }

            toggleDisableItems(true);

            const datos = {
                metodo_pago: e.target.id === 'mercadopago' ? 'mercado_pago' : 'otro',
                nombre: document.getElementById('id_nombre').value,
                apellido: document.getElementById('id_apellido').value,
                email: document.getElementById('id_email').value,
                dni_cuit: document.getElementById('id_dni_cuit').value || '00000000',
                tipo_factura: document.getElementById('id_tipo_factura').value || 'B',
                calle: document.getElementById('id_calle').value,
                cuidad: document.getElementById('id_cuidad').value,
                codigo_postal: document.getElementById('id_codigo_postal').value,
            };

            try {
                const response = await axios.post(window.api.calcularPedido, datos);
                const { total, adicional, init_point,metodoPagoSeleccionado } = response.data;

                document.getElementById('adicionales-value').innerText = `$${adicional}`;
                document.getElementById('total-value').innerText = `$${total}`;

                const boxCheckout = document.getElementById('box-checkout-pro');

                if (init_point && metodoPagoSeleccionado === 'mercado_pago') {
                    boxCheckout.innerHTML = `
                        <a href="${init_point}" rel="noopener noreferrer" class="boton-checkout-pro">
                            <img src="${window.api.imgMP}" alt="Pagar con Mercado Pago" />  Pagar con Mercado Pago
                        </a>
                    `;
                } else {
                    boxCheckout.innerHTML = "";
                }

            } catch (error) {
                console.error('Error al calcular el pedido', error);
                alert('Ocurrió un error al calcular el pedido.');
            } finally {
                
                toggleDisableItems(false);
            }
        });
    });
});

function mostrarFeedbackCarrito(productoNombre, totalPrecio, imagenUrl,cantidadPedido,subTotal) {
    const feedback = document.getElementById('carrito-feedback');

    if (!feedback) return;

    const precioFormateado = parseFloat(totalPrecio).toFixed(2);
    const subTotalFormateado = parseFloat(subTotal).toFixed(2);
    feedback.innerHTML = `
        <div class="carrito-feedback-imgbox">
            <img src="${imagenUrl}" alt="${productoNombre}">
            <div class="carrito-feedback-info">
                <p>${productoNombre}</p>
                <p>${cantidadPedido} x $${subTotalFormateado}</p>
            </div>
        </div>
        <div class="carrito-feedback-divider">
            <p>Subtotal</p>
            <p>$${precioFormateado}</p>
        </div>
        <div class="carrito-feedback-links">
            <a href="${window.api.verCarrito}">VER CARRITO</a>
            <a href="${window.api.finalizarCompra}">FINALIZAR COMPRA</a>
        </div>
    `;
    feedback.classList.remove('oculto');

    setTimeout(() => {
        feedback.classList.add('oculto');
    }, 5000);
}

function mostrarCarritoVacio() {
    const carritoBox = document.getElementById('carrito-box');
    if (carritoBox) {
        carritoBox.innerHTML = `
        <p class="cart-empty-msg">Tu carrito esta vacio</p>
        <a href="/" class="decoration-none cart-volver-tienda">Volver a la tienda</a>
        `
    }
}

function actualizarPreciosCarrito(total_precio) {
    const totalFormateado = parseFloat(total_precio).toFixed(2)
    const subTotal = document.getElementById('cart-subtotal');
    const total = document.getElementById('cart-total');
    if (subTotal && total) {
        subTotal.innerHTML = `$${totalFormateado}`;
        total.innerHTML = `$${totalFormateado}`
    }
}

function actualizarCarrito(total_precio,total_productos) {
    const cantidadCarrito = document.getElementById('carrito-cantidad');
    if (cantidadCarrito) {
        cantidadCarrito.textContent = total_productos;
        }
                
    const precioCarrito = document.querySelector('.carrito-total-precio');
    if (precioCarrito) {
        const totalFormateado = parseFloat(total_precio).toFixed(2);
        precioCarrito.textContent = `Carrito / $${totalFormateado}`;
    }
}

async function aplicarFiltrosDinamicos(parametros = {}) {
    try {
        const url = new URL(window.location.href);

        url.search = '';

        for (const [key, value] of Object.entries(parametros)) {
            url.searchParams.set(key, value);
        }

        const response = await axios.get(window.filters.apiUrl, {
            params: Object.fromEntries(url.searchParams.entries())
        });

        // * GRID COMPARTIDO
        const gridBox = document.querySelector('.grid-container');
        if (gridBox) {
            gridBox.innerHTML = response.data.html
        }
        // * COMPUTADORA
        const filterBox = document.querySelector('.filter-box');
        if (filterBox) {
            filterBox.innerHTML = response.data.filtros;
        }
        const linksProds = document.querySelector('.product-links-box');
        if (linksProds) {
            linksProds.innerHTML = response.data.navlinks;
        }
        const orderResult = document.getElementById('orden-result')
        if (orderResult) {
            orderResult.innerHTML = response.data.orden;
        }
        // * MOBILE
        const filterActiveBox = document.getElementById('filter-active-mobile');
        if (filterActiveBox) {
            filterActiveBox.innerHTML = response.data.activos
        }

        const filterMobileBox = document.getElementById('filters-box-mobile');
        if (filterMobileBox) {
            filterMobileBox.innerHTML = response.data.filtros;
        
            if (!filterMobileBox.dataset.listenerSet) {
                filterMobileBox.addEventListener("click", function (event) {
                    const item = event.target.closest(".filter-item");

                    if (item && filterMobileBox.contains(item)) {
                        event.stopPropagation(); // evita conflicto con clic global

                        // Cerramos todos los filtros excepto el actual
                        document.querySelectorAll(".filter-expanded").forEach(box => {
                            if (box !== item.nextElementSibling) {
                                box.classList.remove("show");
                                box.previousElementSibling?.classList.remove("active");
                            }
                        });

                        const expanded = item.nextElementSibling;
                        if (expanded && expanded.classList.contains("filter-expanded")) {
                            expanded.classList.toggle("show");
                            item.classList.toggle("active");
                        }
                    }
                });

                filterMobileBox.dataset.listenerSet = "true"; // solo se ejecuta una vez
            }
            
        }
        

        window.history.replaceState(null, '', `?${url.searchParams.toString()}`);
    } catch (err) {
        console.error("Error cargando filtros dinámicos:", err);
    }
}

