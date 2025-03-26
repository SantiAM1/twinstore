document.addEventListener("DOMContentLoaded", function () {
    const filterButton = document.querySelector(".filter-button");
    const filterBox = document.querySelector(".filter-box-mobile");
    const filterItems = document.querySelectorAll(".filter-item");

    const ordenarButtons = document.querySelectorAll(".ordenar-button");
    const ordenarBoxes = document.querySelectorAll(".ordenar-box-mobile");

    // Función para cerrar todos los menús, excepto el que se está abriendo
    function closeAllMenus(except = null) {
        if (except !== filterBox) {
            filterBox.classList.remove("show");
        }
        if (except !== ordenarBoxes) {
            ordenarBoxes.forEach(box => box.classList.remove("show"));
        }
    }

    // Toggle para mostrar/ocultar el menú de filtros
    filterButton.addEventListener("click", function (event) {
        event.stopPropagation();
        closeAllMenus(filterBox);
        filterBox.classList.toggle("show");
    });

    // Toggle para mostrar/ocultar el menú de ordenar
    ordenarButtons.forEach((button, index) => {
        button.addEventListener("click", function (event) {
            event.stopPropagation();
            closeAllMenus(ordenarBoxes);
            ordenarBoxes[index].classList.toggle("show");
        });
    });

    filterItems.forEach(item => {
    item.addEventListener("click", function (event) {
        event.stopPropagation();

        const expanded = this.nextElementSibling;
        const icon = this.querySelector("i"); // Seleccionar la flecha dentro de filter-item

        if (expanded && expanded.classList.contains("filter-expanded")) {
            expanded.classList.toggle("show");
            this.classList.toggle("active"); // Agrega o quita la clase activa en el item
            }
        });
    });

    // Cerrar menús si se hace clic fuera de ellos
    document.addEventListener("click", function () {
        closeAllMenus();
    });
});