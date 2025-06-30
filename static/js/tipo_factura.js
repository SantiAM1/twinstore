document.addEventListener("DOMContentLoaded", () => {
    const tipoFactura = document.getElementById('id_condicion_iva');
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
});