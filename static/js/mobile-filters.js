document.addEventListener("DOMContentLoaded", () => {
    const filterButton = document.querySelector(".filter-button");
    const filterBox = document.querySelector(".filter-box-mobile");
    const filterItems = document.querySelectorAll(".filter-item");

    const ordenarButtons = document.querySelectorAll(".ordenar-button");
    const ordenarBoxes = document.querySelectorAll(".ordenar-box-mobile");

    function closeAllMenus(except = null) {
        if (except !== filterBox) {
            filterBox.classList.remove("show");
        }
        if (except !== ordenarBoxes) {
            ordenarBoxes.forEach(box => box.classList.remove("show"));
        }
    }

    if (filterButton) {
        filterButton.addEventListener("click", function (event) {
            event.stopPropagation();
            closeAllMenus(filterBox);
            filterBox.classList.toggle("show");
        });
    }

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
            const icon = this.querySelector("i");
            if (expanded && expanded.classList.contains("filter-expanded")) {
                expanded.classList.toggle("show");
                this.classList.toggle("active");
            }
        });
    });

    document.addEventListener("click", function (event) {
        closeAllMenus();
    });
});