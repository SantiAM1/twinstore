document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll('.btn-arrepentimiento').forEach(btn => {
        btn.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal-id');
            document.getElementById(modalId).style.display = 'block';
        });
    });
    
    document.querySelectorAll('.cancelar-arrepentimiento').forEach(btn => {
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