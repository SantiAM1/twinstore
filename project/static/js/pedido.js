document.addEventListener("DOMContentLoaded", () => {
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
                    notificationBox.innerHTML = html;
        
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