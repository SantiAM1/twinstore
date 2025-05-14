document.addEventListener("DOMContentLoaded", () => {
    const consultarDisponibilidad = document.getElementById('consultar-disponibilidad');
    if (consultarDisponibilidad) {
        consultarDisponibilidad.addEventListener('click', function() {
            const nombre = consultarDisponibilidad.dataset.name
            let mensaje = `Hola Twistore! Me gustaría conocer si cuentan con la disponibilidad de ${nombre}`
        
            const url = `https://wa.me/5493412765167?text=${encodeURIComponent(mensaje)}`;
            window.open(url, '_blank');
        });
    }
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

    function mostrarFeedbackCarrito(productoNombre, totalPrecio, imagenUrl,cantidadPedido,subTotal) {
        const feedback = document.getElementById('carrito-feedback');
    
        if (!feedback) return;
    
        const htmlNoPurificado = `
            <div class="flex items-center gap-1rem carrito-feedback-imgbox">
                <img src="${imagenUrl}" alt="${productoNombre} loading="lazy"">
                <div class="flex flex-column carrito-feedback-info">
                    <p class="font-roboto">${productoNombre}</p>
                    <p class="font-roboto">${cantidadPedido} x ${subTotal}</p>
                </div>
            </div>
            <div class="flex justify-between carrito-feedback-divider">
                <p class="font-bold font-roboto">Subtotal</p>
                <p class="font-bold font-roboto">${totalPrecio}</p>
            </div>
            <div class="flex flex-column carrito-feedback-links">
                <a href="${window.api.verCarrito}" class="font-roboto decoration-none font-bold">VER CARRITO</a>
                <a href="${window.api.finalizarCompra}" class="font-roboto decoration-none font-bold">FINALIZAR COMPRA</a>
            </div>
            `
        feedback.innerHTML = DOMPurify.sanitize(htmlNoPurificado)
        feedback.classList.remove('oculto');
    
        setTimeout(() => {
            feedback.classList.add('oculto');
        }, 5000);
    }

    const prodBtnQuantity = document.querySelectorAll('.btn-cantidad-view');

    prodBtnQuantity.forEach((btn) => {
        btn.addEventListener('click', () => {
            const action = btn.dataset.action
            if (action === "decrement")  {
                decreaseQuantity()
            } else {
                increaseQuantity()
            }
        });
    });

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
