document.addEventListener("DOMContentLoaded", () => {
    
    const termCondiciones = document.getElementById('id_aceptar');
    termCondiciones.addEventListener('change',function() {
        resetRadio()
    })

    const btnAplicar = document.querySelector(".btn-aplicar");
    const inputCupon = document.getElementById("codigo-descuento");
    const msgError = document.querySelector(".cupon-error");
    const msgSuccess = document.querySelector(".cupon-success");
    const cuponTr = document.getElementById("cupon-tr")
    const cuponDivider = document.getElementById("cupon-divider")
    btnAplicar.addEventListener("click", async () => {
        msgError.textContent = ""
        msgSuccess.textContent = ""
        inputCupon.classList.remove("success")
        inputCupon.classList.remove("errors")

        resetRadio()

        const codigo = inputCupon.value.trim();
        if (!codigo) {
            msgError.textContent = "Ingresá un código"
            inputCupon.classList.add("errors")
            return
        }

        toggleDisableItems(true);

        try {
            const response = await axios.post("/carro/api/validar-cupon/", {
                codigo:codigo
            })

            const data = response.data

            msgSuccess.textContent = "Cupón validado correctamente!"
            inputCupon.classList.add("success")
            btnAplicar.classList.add("btn-success")
            setTimeout(() => btnAplicar.classList.remove("btn-success"), 2000)
            
            cuponTr.children[0].textContent = `Cupón %${data.porcentaje}`
            cuponTr.children[1].textContent = `-${data.descuento}`
            cuponTr.classList.add("cart-finsh-prods")

            cuponDivider.innerHTML = `<th colspan="2" class="border-1px"></th>`

            document.getElementById('total-value').textContent = data.nuevo_total

        } catch (error) {
            const mensaje = error.response?.data?.error || "Ocurrió un error inesperado";
            msgError.textContent = mensaje
            inputCupon.classList.add("errors")
            btnAplicar.classList.add("btn-error")
            cuponTr.innerHTML = `<th></th><td></td>`
            cuponTr.classList.remove("cart-finsh-prods")
            cuponDivider.innerHTML = ""
            setTimeout(() => btnAplicar.classList.remove("btn-error"), 2000)
        } finally {
            toggleDisableItems(false);
        }
    })

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
                condicion_iva: document.getElementById('id_condicion_iva').value || 'B',
                calle: document.getElementById('id_calle').value,
                ciudad: document.getElementById('id_ciudad').value,
                codigo_postal: document.getElementById('id_codigo_postal').value,
                recibir_mail: document.getElementById('id_recibir_estado_pedido').checked,
                telefono: document.getElementById('id_telefono').value,
                razon_social: document.getElementById('id_razon_social').value,
            };
            document.querySelectorAll('.error').forEach(div => div.innerText = '');

            try {
                const response = await axios.post(window.api.calcularPedido, datos);
                const { total, adicional, init_point,metodoPagoSeleccionado } = response.data;
                document.getElementById('adicionales-value').textContent = adicional
                document.getElementById('total-value').textContent = total

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
                resetRadio()
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

function resetRadio() {
    document.querySelectorAll('input[name="forma_pago"]').forEach(radio => {
        radio.checked = false;
    });
}