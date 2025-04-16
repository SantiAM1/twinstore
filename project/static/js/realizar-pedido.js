document.addEventListener("DOMContentLoaded", () => {
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
                recibir_mail: document.getElementById('id_recibir_estado_pedido').checked,
            };

            try {
                const response = await axios.post(window.api.calcularPedido, datos);
                const { total, adicional, init_point,metodoPagoSeleccionado } = response.data;

                document.getElementById('adicionales-value').innerText = `$${parseFloat(adicional).toLocaleString("es-AR", { minimumFractionDigits: 2, 
                    maximumFractionDigits: 2, 
                    useGrouping: false})}`
                document.getElementById('total-value').innerText = `$${parseFloat(total).toLocaleString("es-AR", { minimumFractionDigits: 2, 
                    maximumFractionDigits: 2, 
                    useGrouping: false})}`

                const boxCheckout = document.getElementById('box-checkout-pro');
                boxCheckout.innerHTML = "";
                    
                if (init_point && metodoPagoSeleccionado === 'mercado_pago') {
                    const a = document.createElement("a");
                    a.href = init_point;
                    a.rel = "noopener noreferrer";
                    a.className = "boton-checkout-pro flex font-roboto items-center decoration-none font-bold gap-05rem";
                    
                    const img = document.createElement("img");
                    img.src = window.api.imgMP;
                    img.alt = "Pagar con Mercado Pago";
                    img.loading = "lazy";
                    
                    a.appendChild(img);
                    a.appendChild(document.createTextNode(" Pagar con Mercado Pago"));
                    
                    boxCheckout.appendChild(a);
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