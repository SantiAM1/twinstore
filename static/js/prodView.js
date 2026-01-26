const specsMore = document.querySelector(".specs-more");
const specsList = document.querySelector(".specs-list.generic-expand");
const payMethodBtn = document.querySelectorAll(".payment-method-btn");
const payMethodInfo = document.querySelectorAll(".payment-info");
const payMethodSelect = document.querySelector(".payment-select");
const payMethodTitle = document.querySelector(".generic-select-title");
specsMore?.addEventListener("click", () => {
  specsList.classList.toggle("expand");
  specsMore.textContent = specsList.classList.contains("expand")
    ? "Ver menos"
    : "Ver más";
});

document.querySelector(".prod-payment-btn").addEventListener("click", () => {
  payMethodSelect.classList.toggle("hide");
});

payMethodBtn.forEach((btn) =>
  btn.addEventListener("click", () => {
    payMethodInfo.forEach((method) => method.classList.add("hide"));
    document
      .querySelector(`.payment-info[data-method="${btn.dataset.method}"]`)
      .classList.remove("hide");
    payMethodSelect.classList.add("hide");
    payMethodTitle.textContent = btn.textContent;
  }),
);

// > Sin stock / Ultimas unidades / Stock Disponible
const inputFront = document.querySelector("input[name='stock-front']");
function updateStockMsg(sku) {
  if (!inputFront) return;
  const stockStatus = document.querySelectorAll(".stock-status");
  stockStatus.forEach((status) => {
    if (status.dataset.sku === sku) {
      status.classList.remove("hide");
    } else {
      status.classList.add("hide");
    }
  });
}

// > Agregar al carrito
const addToCart = document.querySelector(".product-add-cart");
const totalCarro = document.getElementById("carritoTotal");
addToCart.addEventListener("click", async () => {
  const prodId = addToCart.getAttribute("data-productoId");
  const sku = addToCart.getAttribute("data-sku");

  try {
    const response = await axios.post("/carro/api/agregar_al_carrito/", {
      producto_id: prodId,
      sku: sku || null,
    });

    if (response.data.totalProds > 0) {
      totalCarro.classList.add("active");
      totalCarro.textContent = response.data.totalProds;
    }
  } catch (err) {
    console.warn(err);
  }
});

// > Nuevo sistema de variantes
const container = document.getElementById("product-variants-container");
const allOptions = container?.querySelectorAll(".variant-option");
const prodSKU = document.querySelector(".producto-sku");
const imgSwipers = document.querySelectorAll(".main-swiper");
const thumbs = document.querySelectorAll(".thumbs-swiper");
document.addEventListener("DOMContentLoaded", function () {
  if (!container) {
    btnCartStockManagement(addToCart);
    return;
  }

  function parseSkus(skuString) {
    if (!skuString) return [];
    try {
      return JSON.parse(skuString.replace(/'/g, '"'));
    } catch (e) {
      return [];
    }
  }

  function updateState() {
    const groups = Array.from(container.querySelectorAll(".variant-group"));

    // * Grupo 1 valido
    let validSkusFromAbove = null;

    groups.forEach((group, index) => {
      const options = Array.from(group.querySelectorAll(".variant-option"));
      let selectedOption = group.querySelector(".variant-option.selected");

      options.forEach((opt) => {
        const optSkus = parseSkus(opt.dataset.skus);

        let isVisible = true;
        if (validSkusFromAbove !== null) {
          const hasIntersection = optSkus.some((sku) =>
            validSkusFromAbove.includes(sku),
          );
          if (!hasIntersection) isVisible = false;
        }

        if (isVisible) {
          opt.classList.remove("disabled");
          opt.disabled = false;
        } else {
          opt.classList.add("disabled");
          opt.disabled = true;
        }
      });

      // * Buscamos la primera opcion valida
      if (selectedOption && selectedOption.classList.contains("disabled")) {
        selectedOption.classList.remove("selected");
        selectedOption = null;
      }

      // * Fallback
      if (!selectedOption) {
        const firstAvailable = group.querySelector(
          ".variant-option:not(.disabled)",
        );
        if (firstAvailable) {
          firstAvailable.classList.add("selected");
          selectedOption = firstAvailable;
        }
      }

      if (selectedOption) {
        const selectedSkus = parseSkus(selectedOption.dataset.skus);

        if (validSkusFromAbove === null) {
          validSkusFromAbove = selectedSkus;
        } else {
          validSkusFromAbove = validSkusFromAbove.filter((sku) =>
            selectedSkus.includes(sku),
          );
        }
      } else {
        validSkusFromAbove = [];
      }
    });

    detectarSkuFinal(validSkusFromAbove);
  }

  function detectarSkuFinal(finalSkus) {
    if (finalSkus && finalSkus.length > 0) {
      if (finalSkus && finalSkus.length > 0) {
        const skuGanador = finalSkus[0];
        updateStockMsg(skuGanador);
        btnCartStockManagement(addToCart, skuGanador);
        prodSKU.textContent = `SKU: ${skuGanador}`;
        addToCart.dataset.sku = skuGanador;
      } else {
        addToCart.disabled = true;
        addToCart.classList.add("disabled");
        addToCart.dataset.sku = "";
        prodSKU.textContent = `SKU: Error`;
      }
    }
  }

  allOptions.forEach((opt) => {
    opt.addEventListener("click", (e) => {
      if (opt.classList.contains("disabled")) return;

      updateSwiper(opt);
      const group = opt.closest(".variant-group");
      group
        .querySelectorAll(".variant-option")
        .forEach((el) => el.classList.remove("selected"));
      opt.classList.add("selected");

      updateState();
    });
  });

  updateState();

  // > Colores e imagenes
  function updateSwiper(opt) {
    if (opt.dataset.type != "Color") return;
    imgSwipers.forEach((img) => img.classList.add("hide"));
    thumbs.forEach((thum) => thum.classList.add("hide"));
    const index = opt.dataset.index;
    document
      .querySelector(`.main-swiper[data-index="${index}"]`)
      .classList.remove("hide");
    document
      .querySelector(`.thumbs-swiper[data-index="${index}"]`)
      .classList.remove("hide");
    console.log(index);
  }

  // > Activar btn
  function btnEnableItem(button) {
    console.log("activando", button);
    button.disabled = false;
    button.classList.remove("disabled");
    button.setAttribute("aria-disabled", "false");
    button.removeAttribute("title");
  }

  // > Desactivar btn
  function btnDisableItem(button) {
    console.log("desactivando", button);
    button.disabled = true;
    button.classList.add("disabled");
    button.setAttribute("aria-disabled", "true");
    button.setAttribute("title", "Producto sin stock");
  }

  // > Manager add to cart
  function btnCartStockManagement(button, sku = null) {
    const stockDict = button.querySelector("script[type='application/json']");

    if (stockDict) {
      const stockValue = JSON.parse(stockDict.textContent.trim());
      console.log(stockValue);

      if (sku) {
        const stockDisponible = stockValue[sku];
        if (stockDisponible > 0) {
          btnEnableItem(button);
        } else {
          btnDisableItem(button);
        }
      } else {
        if (stockValue.total == 0) {
          btnDisableItem(button);
        }
      }
    }
  }
});
