document.addEventListener("DOMContentLoaded", () => {
    // --- scripts.js ---
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
            resultProdDisplay.innerHTML = categorias[item.id] || '<div class="result-productos-column flex">No hay contenido disponible</div>';
        });
    });

    const userMenu = document.querySelector(".user-menu");
    const dropdown = document.getElementById("userDropdown");

    userMenu.addEventListener("click", function(event) {
        event.stopPropagation();
        dropdown.classList.toggle("show");
    });

    document.addEventListener("click", function(event) {
        if (!userMenu.contains(event.target)) {
            dropdown.classList.remove("show");
        }
    });

    const toggles = document.querySelectorAll(".toggle");
    toggles.forEach(toggle => {
        toggle.addEventListener("click", function() {
            toggle.querySelector("i").classList.toggle("rotated");
            let submenu = this.nextElementSibling;
            if (submenu) {
                submenu.style.display = submenu.style.display === "block" ? "none" : "block";
            }
        });
    });

    const menu = document.querySelector(".menu");
    const closeBtn = document.querySelector(".menu-title i");
    const openBtn = document.getElementById("open-menu");

    openBtn.addEventListener("click", function () {
        menu.classList.add("active");
    });

    closeBtn.addEventListener("click", function () {
        menu.classList.remove("active");
    });

    // --- mobile.js ---
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

    filterButton.addEventListener("click", function (event) {
        event.stopPropagation();
        closeAllMenus(filterBox);
        filterBox.classList.toggle("show");
    });

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

    document.addEventListener("click", function () {
        closeAllMenus();
    });
});

function scrollToImage(index) {
    const slider = document.querySelector('.product-slider');
    const imageWidth = slider.querySelector('img').clientWidth;
    const scrollPosition = index * imageWidth;

    slider.scrollTo({
        left: scrollPosition,
        behavior: 'smooth'
    });
}

let quantity = 1;
function increaseQuantity() {
    if (quantity < 10) {
        quantity++;
        document.getElementById("quantity").value = quantity;
    }
}
function decreaseQuantity() {
    if (quantity > 1) {
        quantity--;
        document.getElementById("quantity").value = quantity;
    }
}
