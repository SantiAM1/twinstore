document.addEventListener("DOMContentLoaded", () => {
    const currentTheme = document.body.dataset.theme;
    const lastTheme = sessionStorage.getItem('ultimaTheme');

    if (lastTheme && lastTheme !== currentTheme) {
        if (currentTheme === 'black') {
            document.body.style.animation = 'cambiarfondooscuro 0.8s forwards';
        } else if (currentTheme === 'white') {
            document.body.style.animation = 'cambiarfondoclaro 0.8s forwards';
        }
    }

    // Guardar el tema actual para la próxima carga
    sessionStorage.setItem('ultimaTheme', currentTheme);
    document.body.addEventListener('animationend', () => {
        document.body.style.animation = '';
    });
    // ----- Menu desktop mobile ------ //
    const categorias = JSON.parse(document.getElementById('menu-json').textContent);
    const botonProductos = document.getElementById("boton-productos");
    const boxProdDisplay = document.getElementById("box-productos-display");
    const resultProdDisplay = document.getElementById("result-productos-display");

    if (!resultProdDisplay.innerHTML.trim()) {
        resultProdDisplay.innerHTML = DOMPurify.sanitize(categorias["componentes"].join(""));
    }

    botonProductos.addEventListener("click", (event) => {
        event.stopPropagation();
        boxProdDisplay.classList.toggle("display-none");

        document.addEventListener("click", (event) => {
            if (!boxProdDisplay.contains(event.target) && event.target !== botonProductos) {
                boxProdDisplay.classList.add("display-none");
            }
        }, { once: true });
    });

    const navItems = document.querySelectorAll(".nav-productos-items");

    navItems.forEach(item => {
        item.addEventListener("mouseenter", () => {
            navItems.forEach(navItem => navItem.classList.remove("categoria-selec"));
            item.classList.add("categoria-selec");
            let columna = categorias[item.id]
            if (columna) {
                columna = columna.join("")
            } else {
                columna = '<div class="result-productos-column flex">No hay contenido disponible</div>'
            }
            resultProdDisplay.innerHTML = DOMPurify.sanitize(columna);
        });
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

    // ----- Usuario toggle ------ //
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

    // ----- Header ------ //
    let lastScrollTop = 0;
    const header = document.querySelector('.header-tag');
    const lowerHeader = document.querySelectorAll('.header-item')[1];

    window.addEventListener('scroll', function() {
        let currentScroll = window.scrollY || document.documentElement.scrollTop;
        if (currentScroll > lastScrollTop && currentScroll > 50) {
            // Scroll hacia abajo: animamos
            lowerHeader.classList.add('hide-on-scroll');
            header.classList.add('shrink');
            // Luego de la transición, aplicamos display none
            setTimeout(() => {
                if (lowerHeader.classList.contains('hide-on-scroll')) {
                    lowerHeader.classList.add('hidden');
                }
            }, 400); // mismo tiempo que la transición
        } else {
            // Volver a mostrar
            lowerHeader.classList.remove('hidden'); // quitamos display none
            setTimeout(() => {
                lowerHeader.classList.remove('hide-on-scroll');
            }, 10); // pequeño delay para que el navegador registre el cambio
            header.classList.remove('shrink');
        }
        lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
    });

    // ----- Carousel ------ //
    const track = document.querySelector(".carousel-track");
    if (track) {
        const slides = Array.from(track.children);
        const totalSlides = slides.length;

        let index = 0;

        slides.forEach(slide => {
            const clone = slide.cloneNode(true);
            track.appendChild(clone);
        });

        const move = () => {
            index++;
            track.style.transition = "transform 0.5s ease-in-out";
            track.style.transform = `translateX(-${index * 100}vw)`;

            if (index >= totalSlides) {
                setTimeout(() => {
                    track.style.transition = "none";
                    track.style.transform = `translateX(0vw)`;
                    index = 0;
                }, 500);
            }
        };

        setInterval(move, 8000); // cada 8 segundos
    }
    
    // ----- Prediccion de busqueda ------ //
    function autocompletar(inputId, sugerenciasId) {
        const input = document.getElementById(inputId);
        const sugerenciasBox = document.getElementById(sugerenciasId);
        let timeout = null;
    
        input.addEventListener("input", () => {
            clearTimeout(timeout);
            const query = input.value.trim();
    
            if (query.length < 2) {
                sugerenciasBox.style.display = "none";
                return;
            }
    
            timeout = setTimeout(() => {
                fetch(`/api/buscar-productos/?q=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        sugerenciasBox.innerHTML = "";
                        if (data.length === 0) {
                            sugerenciasBox.style.display = "none";
                            return;
                        }
    
                        data.forEach(producto => {
                            const div = document.createElement("div");
                            div.textContent = producto.nombre;
                            div.className = "sugerencia-item";
                            div.addEventListener("click", () => {
                                window.location.href = `/productos/${producto.slug}/`;
                            });
                            sugerenciasBox.appendChild(div);
                        });
                        sugerenciasBox.style.display = "block";
                    });
            }, 300);
        });
    
        document.addEventListener("click", e => {
            if (!e.target.closest(`#${inputId}`) && !e.target.closest(`#${sugerenciasId}`)) {
                sugerenciasBox.style.display = "none";
            }
        });
    }
    autocompletar("busqueda-input-arriba", "sugerencias-arriba");
    autocompletar("busqueda-input-abajo", "sugerencias-abajo");
});