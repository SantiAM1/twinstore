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
            // link.classList.add("disabled");

            const numero_firmado = anchor.dataset.pedidoId;
            try {
                const response = await axios.post('/carro/api/initpagomixto/', {
                    numero_firmado: numero_firmado
                });
        
                window.location.href = response.data.init_point
        
            } catch (error) {
                console.error("No se pudo crear el pago de Mercado Pago.");
            }
        });
    })

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
    function asignarListenersNotificaciones() {
        document.addEventListener('click', async function (e) {
            const btn = e.target.closest('.button-notification');
        
            if (btn) {
                const token = btn.dataset.token;
                toggleDisableItems(true);
                try {
                    const response = await axios.post(window.api.recibirMail, {
                        token: token
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