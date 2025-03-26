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

function scrollToImage(index) {
    const slider = document.querySelector('.product-slider');
    const imageWidth = slider.querySelector('img').clientWidth;
    const scrollPosition = index * imageWidth;

    console.log("Índice:", index, "Posición de desplazamiento:", scrollPosition);

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

document.addEventListener("DOMContentLoaded", function() {
    const userMenu = document.querySelector(".user-menu");
    const dropdown = document.getElementById("userDropdown");

    userMenu.addEventListener("click", function(event) {
        event.stopPropagation(); // Evita que el clic en el menú lo cierre inmediatamente
        dropdown.classList.toggle("show");
    });

    document.addEventListener("click", function(event) {
        if (!userMenu.contains(event.target)) {
            dropdown.classList.remove("show"); // Cierra el menú si se hace clic fuera
        }
    });
});

document.addEventListener("DOMContentLoaded", function() {
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
});

document.addEventListener("DOMContentLoaded", function () {
    const menu = document.querySelector(".menu");
    const closeBtn = document.querySelector(".menu-title i");
    const openBtn = document.getElementById("open-menu");

    // Abrir el menú
    openBtn.addEventListener("click", function () {
        menu.classList.add("active");
    });

    // Cerrar el menú
    closeBtn.addEventListener("click", function () {
        menu.classList.remove("active");
    });
});