document.querySelectorAll('.form-admin-control').forEach((input) => {
    input.addEventListener('change', () => {
        const fileName = input.files.length ? input.files[0].name : 'Ningún archivo seleccionado';

        const span = input.nextElementSibling;
        if (span) {
            span.textContent = `Imagen seleccionada: ${fileName}`;
            span.classList.add('active');
        }
    });
});
