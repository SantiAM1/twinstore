document.addEventListener("DOMContentLoaded", () => {

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

                const { total_productos, total_precio, cantidad,sub_total } = response.data;

                container.querySelector('.input-value-cart').value = cantidad
                const fila = container.closest('tr');
                const precioSubtotal = fila?.querySelector('.cart-total-precio');
                // const precio = parseFloat(container.dataset.precio);

                if (precioSubtotal) {
                    precioSubtotal.textContent = `${sub_total}`;

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

    function actualizarPreciosCarrito(total_precio) {
        const subTotal = document.getElementById('cart-subtotal');
        const total = document.getElementById('cart-total');
        if (subTotal && total) {
            subTotal.textContent = `${total_precio}`;
            total.textContent = `${total_precio}`
        }
    }

    document.querySelectorAll('.cart-prod-delete').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.preventDefault();
            const pedidoId = this.dataset.pedidoId;
    
            toggleDisableItems(true);

            try {
                const response = await axios.post(window.api.eliminarPedido, {
                    pedido_id: pedidoId
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

    const cotizarEnvio = document.getElementById('cotizar-envio');
    if (cotizarEnvio) {
        cotizarEnvio.addEventListener('click', () => {
            enviarWhatsApp()
        })
    }
    function enviarWhatsApp() {
        axios.get(window.api.enviarWtap)
        .then(response => {
            const {productos,direccion,codigo_postal} = response.data;
    
            if (productos.length === 0) {
                alert("Tu carrito está vacío.");
                return;
            }
    
            let mensaje = "Hola Twistore! Me gustaría cotizar un envío de:\n";
            productos.forEach(p => {
                mensaje += `- ${p.nombre} (x${p.cantidad})\n`;
            });
    
            mensaje += `\nCódigo Postal:${codigo_postal}\nDirección:${direccion}`;

            const url = `https://wa.me/5493412765167?text=${encodeURIComponent(mensaje)}`;
            window.open(url, '_blank');
        })
        .catch(error => {
            console.error("Error al obtener productos del carrito:", error);
            alert("Hubo un problema al generar el mensaje de WhatsApp.");
        });
    }
    function mostrarCarritoVacio() {
        const carritoBox = document.getElementById('carrito-box');
        if (carritoBox) {
            carritoBox.innerHTML = `
            <p class="cart-empty-msg font-roboto">Tu carrito esta vacío</p>
            <a href="/" class="decoration-none cart-volver-tienda font-roboto color-fff font-bold text-center padding1rem">Volver a la tienda</a>
            `
        }
    }
    function actualizarCarrito(total_precio,total_productos) {
        const cantidadCarrito = document.getElementById('carrito-cantidad');
        if (cantidadCarrito) {
            cantidadCarrito.textContent = total_productos;
            }
                    
        const precioCarrito = document.querySelector('.carrito-total-precio');
        if (precioCarrito) {
            precioCarrito.textContent = `Carrito / ${total_precio}`;
        }
    }
})