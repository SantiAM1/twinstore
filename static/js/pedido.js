document.addEventListener("DOMContentLoaded", () => {

    const linksMP = document.querySelectorAll(".link-subir-ticket.mercadopago");
    linksMP.forEach(link => {
        link.addEventListener("click", async (e) => {
            e.preventDefault();

            const anchor = e.currentTarget;
            const texto = anchor.querySelector(".texto-link ");
            const spinner = anchor.querySelector(".spinner");
            texto.textContent = "Generando...";
            spinner.classList.remove("hidden");
            link.classList.add("disabled");

            const numero_firmado = anchor.dataset.pedidoId;
            try {
                const response = await axios.post('/carro/api/initpointmp/', {
                    numero_firmado: numero_firmado
                });
        
                window.location.href = response.data.init_point
        
            } catch (error) {
                alert("No se pudo crear el pago de Mercado Pago.");
            }
        });
    })

    document.querySelectorAll(".gen-comprobante").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.preventDefault();
            const id = btn.dataset.pedidoId;
            try {
                const response = await axios.get("/payment/api/generarcomprobante/", {
                    params: { id: id }
                });
                
                const { modal } = response.data;

                const modalItem = document.getElementById("modal-comprobante");
                modalItem.innerHTML = modal;
                modalItem.style.display = 'block';

                activarModalComprobantes()

                const cerrarModal = document.getElementById("close-comprobante-modal");
                cerrarModal.addEventListener("click", () =>{
                    modalItem.style.display = 'none';
                    modalItem.innerHTML = "";
                });

            } catch (error) {
                console.log(error.response?.data || error.message);
            }
        });
    });

    const successModal = document.getElementById("success-modal")
    const params = new URLSearchParams(window.location.search);
    if (params.get("compra") === "exitosa") {
        setTimeout(() =>{successModal.style.display = 'block'},300)
        document.getElementById("close-success-modal").addEventListener("click", () => {
            successModal.style.display = 'none';
        })
    }

    const failModal = document.getElementById("fail-modal")
    if (params.get("compra") === "fallida") {
        setTimeout(() =>{failModal.style.display = 'block'},300)
        document.getElementById("close-fail-modal").addEventListener("click", () => {
            failModal.style.display = 'none';
        })
    }

    document.querySelectorAll('.btn-modal-open').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal-id');
            document.getElementById(modalId).style.display = 'block';
        });
    });
    
    document.querySelectorAll('.btn-modal-close').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal-id');
            document.getElementById(modalId).style.display = 'none';
        });
    });

    function activarModalComprobantes() {
        document.getElementById("id_file").addEventListener("change", function () {
            const archivo = this.files[0];
            const maxSizeMB = 2;
            const label = document.getElementById("label-file");
            const buttonSubir = document.getElementById('button-subir');
        
            if (archivo && archivo.size > maxSizeMB * 1024 * 1024) {
                alert(`❌ El archivo supera el límite de ${maxSizeMB} MB.`);
                this.value = "";
            }
            if (archivo) {
            label.textContent = `${archivo.name} (${(archivo.size / 1024).toFixed(1)} KB)`;
            buttonSubir.classList.add('ready');
            }
        });
    }

    function asignarListenersNotificaciones() {
        document.addEventListener('click', async function (e) {
            const btn = e.target.closest('.button-notification');
        
            if (btn) {
                const id = btn.dataset.id;
                toggleDisableItems(true);
                try {
                    const response = await axios.post(window.api.recibirMail, {
                        id: id
                    });
        
                    const { html } = response.data;
        
                    const notificationBox = btn.closest('.notification-box');
                    notificationBox.innerHTML = DOMPurify.sanitize(html);
        
                } catch (error) {
                    console.error("No se pudo actualizar el pedido:", error);
                } finally {
                    toggleDisableItems(false);
                }
            }
        });    
    }
    
    asignarListenersNotificaciones();
})