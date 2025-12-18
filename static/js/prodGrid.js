const categoryBtn = document.querySelectorAll(".product-category-item");
const orderBtn = document.getElementById("product-order-toggle");
const orderList = document.querySelector(".generic-list");
const productTitle = document.querySelectorAll(".product-title");
const subCategory = document.querySelectorAll(".product-subcategory");
const btnsFilter = document.querySelectorAll(".prodGrid-filters");
const orderSpan = document.querySelector(".producto-order-span");
const prodGrid = document.querySelector(".product-grid");
const orderBox = document.querySelector(".product-filters");
const activeFiltersBox = document.querySelector(".product-filters-active");
const prodOrderLinks = document.querySelector(".prodOrderLinks");
const title = document.getElementById("generic-title");

document.body.addEventListener("click", async (e) => {
  const link = e.target.closest("a.prodGrid-filters");
  if (!link) return;

  orderList.classList.add("hide");

  e.preventDefault();
  const url = link.getAttribute("href");
  const currentPath = window.location.pathname;
  const fullUrl = `${currentPath}${url}${
    url.includes("?") ? "&" : "?"
  }type=json`;

  try {
    const response = await axios.get(fullUrl);
    const data = response.data;

    orderSpan.textContent = data.filtro;

    if (prodGrid && data.prodGrid) prodGrid.innerHTML = data.prodGrid;

    if (orderBox && data.filtersNav) orderBox.innerHTML = data.filtersNav;

    if (activeFiltersBox) activeFiltersBox.innerHTML = data.activeFilters;

    if (prodOrderLinks) prodOrderLinks.innerHTML = data.orderLinks;

    if (data.title) title.textContent = data.title;

    window.history.pushState({}, "", `${currentPath}${url}`);
  } catch (error) {
    console.error("Error al actualizar los filtros:", error);
  } finally {
    toggleDisableItems(false);
  }
});

orderBtn?.addEventListener("click", () => {
  orderList.classList.toggle("hide");
});

productTitle.forEach((title) => {
  title.addEventListener("click", () => {
    let flag = !title.classList.contains("flip");
    const expand = title.nextElementSibling;
    resetTitle();
    if (flag) {
      title.classList.toggle("flip");
      expand.classList.add("expand");
    }
  });
});

categoryBtn.forEach((btn) => {
  btn.addEventListener("click", () => {
    const subCategory = btn.querySelector(".product-subcategory");
    const titleCategory = btn.querySelector(".product-category");
    let flag = !subCategory.classList.contains("expand");
    resetSubCategory();
    titleCategory.classList.toggle("flip");
    if (flag) {
      subCategory.classList.add("expand");
    }
  });
});

document.querySelectorAll(".btn-card").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
  });
});

const totalCarro = document.getElementById("carritoTotal");
document.querySelectorAll(".card-product__cart").forEach((btn) => {
  btn.addEventListener("click", async (e) => {
    const card = btn.closest(".card-product");

    const prodId = btn.getAttribute("data-productId");
    const colorId = card
      .querySelector(".card-color-dot.selected")
      ?.getAttribute("data-colorId");

    try {
      const response = await axios.post("/carro/api/agregar_al_carrito/", {
        producto_id: prodId,
        color_id: colorId || null,
      });
      if (response.data.totalProds > 0) {
        totalCarro.classList.add("active");
        totalCarro.textContent = response.data.totalProds;
      }
    } catch (err) {
      console.warn(err);
    }
  });
});

document.querySelectorAll(".card-color-dot").forEach((dot) => {
  dot.addEventListener("click", (e) => {
    const selectedColor = e.target.getAttribute("data-hex");
    const card = e.target.closest(".card-product");
    const images = card.querySelectorAll("header.card-product__media img");
    const btn = card.querySelector(".card-product__cart");

    dot.classList.add("selected");
    card.querySelectorAll(".card-color-dot").forEach((d) => {
      if (d !== dot) d.classList.remove("selected");
    });

    btnCartStockManagement(btn);

    images.forEach((img) => {
      if (img.dataset.hex === selectedColor) {
        img.classList.remove("hide");
      } else {
        img.classList.add("hide");
      }
    });
  });
});

function resetSubCategory() {
  subCategory.forEach((btn) => {
    btn.classList.remove("expand");
  });
}

function resetTitle() {
  productTitle.forEach((title) => {
    title.classList.remove("flip");
    title.nextElementSibling.classList.remove("expand");
  });
}

const eventoTimer = document.getElementById("evento_timer");
if (eventoTimer) {
  const fechaFin = new Date(eventoTimer.value.replace(" ", "T")).getTime();
  console.log(fechaFin);
  const diasValue = document.getElementById("dias_value");
  const horasValue = document.getElementById("horas_value");
  const minValue = document.getElementById("min_value");

  function actualizarContador() {
    const ahora = new Date().getTime();
    const diff = fechaFin - ahora;

    if (diff <= 0) {
      document.getElementById("countdown").innerHTML = "¡Finalizado!";
      return;
    }

    const dias = Math.floor(diff / (1000 * 60 * 60 * 24));
    const horas = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    diasValue.textContent = dias;
    horasValue.textContent = horas;
    minValue.textContent = mins;
  }

  actualizarContador();
  setInterval(actualizarContador, 1000);
}

document.addEventListener("DOMContentLoaded", () => {
  const stockButtons = document.querySelectorAll(".btn-card");
  stockButtons.forEach((button) => {
    btnCartStockManagement(button);
  });
});

function btnCartStockManagement(button) {
  const stockDict = button.querySelector("script[type='application/json']");

  if (stockDict) {
    const stockValue = JSON.parse(stockDict.textContent.trim());

    const card = button.closest(".card-product");
    const colorsBox = card.querySelector(".card-product-colors");
    const colorDot = colorsBox.querySelector(".card-color-dot.selected");

    if (colorsBox && colorDot) {
      const colorHex = colorDot.getAttribute("data-hex");
      const stockDisponible = stockValue[colorHex];
      console.log(
        "Stock disponible para color " + colorHex + ": " + stockDisponible
      );
      if (stockDisponible > 0) {
        btnEnableItem(button);
      } else {
        btnDisableItem(button);
      }
      return;
    }

    if (stockValue.total == 0) {
      btnDisableItem(button);
    }
  }
}

function btnEnableItem(button) {
  button.disabled = false;
  button.classList.remove("disabled");
  button.setAttribute("aria-disabled", "false");
  button.removeAttribute("title");
}

function btnDisableItem(button) {
  button.disabled = true;
  button.classList.add("disabled");
  button.setAttribute("aria-disabled", "true");
  button.setAttribute("title", "Producto sin stock");
}
