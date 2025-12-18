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
  })
);

const colorDots = document.querySelectorAll(".dot-ring");
const imgSwipers = document.querySelectorAll(".main-swiper");
const thumbs = document.querySelectorAll(".thumbs-swiper");

colorDots?.forEach((dot) => {
  dot.addEventListener("click", () => {
    colorDots.forEach((dot) => {
      dot.classList.remove("selected");
    });
    dot.classList.add("selected");

    btnCartStockManagement(addToCart);
    updateStockMsg(dot.dataset.hex);

    imgSwipers.forEach((img) => img.classList.add("hide"));
    thumbs.forEach((thum) => thum.classList.add("hide"));
    const index = dot.dataset.index;
    document
      .querySelector(`.main-swiper[data-index="${index}"]`)
      .classList.remove("hide");
    document
      .querySelector(`.thumbs-swiper[data-index="${index}"]`)
      .classList.remove("hide");
  });
});

const addToCart = document.querySelector(".product-add-cart");
const totalCarro = document.getElementById("carritoTotal");
addToCart.addEventListener("click", async () => {
  const prodId = addToCart.getAttribute("data-productoId");
  const colorId = document
    .querySelector(".dot-ring.selected")
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

document.addEventListener("DOMContentLoaded", () => {
  btnCartStockManagement(addToCart);
});

function btnCartStockManagement(button) {
  const stockDict = button.querySelector("script[type='application/json']");

  if (stockDict) {
    const stockValue = JSON.parse(stockDict.textContent.trim());

    const box = button.closest(".product-view");
    const colorsBox = box.querySelector(".product-colors");
    const colorDot = colorsBox.querySelector(".dot-ring.selected");
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

const inputFront = document.querySelector("input[name='stock-front']");
function updateStockMsg(hexColor) {
  if (!inputFront) return;
  const stockStatus = document.querySelectorAll(".stock-status");
  stockStatus.forEach((status) => {
    if (status.dataset.hex === hexColor) {
      status.classList.remove("hide");
    } else {
      status.classList.add("hide");
    }
  });
}
