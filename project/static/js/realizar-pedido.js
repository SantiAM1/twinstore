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
                ciudad: document.getElementById('id_ciudad').value,
                codigo_postal: document.getElementById('id_codigo_postal').value,
                recibir_mail: document.getElementById('id_recibir_estado_pedido').checked,
            };
            document.querySelectorAll('.error').forEach(div => div.innerText = '');

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
                window.scrollTo({ top: 0, behavior: "smooth" });
                document.querySelectorAll('input[name="forma_pago"]').forEach(radio => {
                    radio.checked = false;
                });
                const errors = error.response?.data;
                if (errors) {
                    Object.keys(errors).forEach(key => {
                        const errorDiv = document.getElementById(`${key}_error`);
                        if (errorDiv) {
                            errorDiv.innerText = errors[key][0];
                            errorDiv.classList.remove('display-none');
                        }
                    });
                } else {
                    alert('Ocurrió un error al calcular el pedido.');
                }
            } finally {
                
                toggleDisableItems(false);
            }
        });
    });
});