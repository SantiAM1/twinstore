document.addEventListener("DOMContentLoaded", () => {

    document.addEventListener('change', function (e) {
        if (e.target && e.target.id === 'ordenby') {
            const orden = e.target.value;
    
            // 🔁 Tomamos los filtros actuales de la URL
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.set('ordenby', orden); // actualizamos el ordenamiento
    
            // 🔄 Convertimos a objeto y enviamos a la función
            const filtrosActualizados = Object.fromEntries(urlParams.entries());
    
            aplicarFiltrosDinamicos(filtrosActualizados);
        }
    });
    
    document.addEventListener('click', async function (e) {
        const link = e.target.closest('.filter-link ,.filter-active-link, .filter-link-mobile');
        if (link) {
            e.preventDefault();
            toggleDisableItems(true);
    
            const newParams = new URL(link.href).searchParams;
            const parametros = {};
            newParams.forEach((value, key) => parametros[key] = value);
    
            aplicarFiltrosDinamicos(parametros).finally(() => toggleDisableItems(false));
        }
    });
    
    document.querySelectorAll('.ordenar-opcion').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
    
            const ordenSeleccionado = this.dataset.orden;
            const urlParams = new URLSearchParams(window.location.search);
    
            urlParams.set('ordenby', ordenSeleccionado); // Sobrescribe el orden actual
    
            const filtrosActualizados = Object.fromEntries(urlParams.entries());
    
            aplicarFiltrosDinamicos(filtrosActualizados);
        });
    });    

    async function aplicarFiltrosDinamicos(parametros = {}) {
        try {
            const url = new URL(window.location.href);

            url.search = '';

            for (const [key, value] of Object.entries(parametros)) {
                url.searchParams.set(key, value);
            }

            const response = await axios.get(window.filters.apiUrl, {
                params: Object.fromEntries(url.searchParams.entries())
            });

            // * GRID COMPARTIDO
            const gridBox = document.querySelector('.grid-container');
            if (gridBox) {
                gridBox.innerHTML = response.data.html
            }
            // * COMPUTADORA
            const filterBox = document.querySelector('.filter-box');
            if (filterBox) {
                filterBox.innerHTML = response.data.filtros;
            }
            const linksProds = document.querySelector('.product-links-box');
            if (linksProds) {
                linksProds.innerHTML = response.data.navlinks;
            }
            const orderResult = document.getElementById('orden-result')
            if (orderResult) {
                orderResult.innerHTML = response.data.orden;
            }
            const paginacion = document.querySelector('.paginacion');
            if (paginacion) {
                paginacion.innerHTML = response.data.paginacion;
            }
            // * MOBILE
            const filterActiveBox = document.getElementById('filter-active-mobile');
            if (filterActiveBox) {
                filterActiveBox.innerHTML = response.data.activos
            }

            const filterMobileBox = document.getElementById('filters-box-mobile');
            if (filterMobileBox) {
                filterMobileBox.innerHTML = response.data.filtros;
            
                if (!filterMobileBox.dataset.listenerSet) {
                    filterMobileBox.addEventListener("click", function (event) {
                        const item = event.target.closest(".filter-item");

                        if (item && filterMobileBox.contains(item)) {
                            event.stopPropagation(); // evita conflicto con clic global

                            // Cerramos todos los filtros excepto el actual
                            document.querySelectorAll(".filter-expanded").forEach(box => {
                                if (box !== item.nextElementSibling) {
                                    box.classList.remove("show");
                                    box.previousElementSibling?.classList.remove("active");
                                }
                            });

                            const expanded = item.nextElementSibling;
                            if (expanded && expanded.classList.contains("filter-expanded")) {
                                expanded.classList.toggle("show");
                                item.classList.toggle("active");
                            }
                        }
                    });

                    filterMobileBox.dataset.listenerSet = "true"; // solo se ejecuta una vez
                }
            }
            window.history.replaceState(null, '', `?${url.searchParams.toString()}`);
        } catch (err) {
            console.error("Error cargando filtros dinámicos:", err);
        }
    }
});