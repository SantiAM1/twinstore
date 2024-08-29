const box_prod_display = document.querySelector(".box-productos-display");

document.addEventListener("DOMContentLoaded", () => {
    const botonProductos = document.getElementById("boton-productos");
    const boxProdDisplay = document.getElementById("box-productos-display");
    const resultProdDisplay = document.getElementById("result-productos-display");

    botonProductos.addEventListener("click", (event) => {
        event.stopPropagation();
        boxProdDisplay.classList.toggle("display_none");

        document.addEventListener("click", (event) => {
            if (!boxProdDisplay.contains(event.target) && event.target !== botonProductos) {
                boxProdDisplay.classList.add("display_none");
            }
        }, { once: true });
    });

    const navItems = document.querySelectorAll(".nav-productos-items");

    navItems.forEach(item => {
        item.addEventListener("mouseenter", () => {
            navItems.forEach(navItem => navItem.classList.remove("categoria-selec"));

            item.classList.add("categoria-selec");

            // Cambiar el contenido del result-productos-display
            resultProdDisplay.innerHTML = categorias[item.id] || '<div class="result-productos-column flex">No hay contenido disponible</div>';
        });
    });
});