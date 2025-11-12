const cartTotal = document.querySelector(".cart-total");
const cartSubTotal = document.querySelector(".cart-subtotal");
const cartDescuento = document.querySelector(".cart-descuento");
const cartTotalProds = document.querySelector(".cart-totalProds");
const totalCarro = document.getElementById("carritoTotal");
const genericBox = document.querySelector(".generic-data");

const navBox = document.querySelectorAll(".cart-navbox");
navBox.forEach((nav) => {
  nav.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const pedidoId = nav.getAttribute("data-pedidoId");
      const url = btn.getAttribute("data-api");
      const action = btn.getAttribute("data-action");

      const itemBox = nav.closest(".cart-item");
      const itemPriceNow = itemBox.querySelector(".cart-item-price-now");
      const itemPriceOld = itemBox.querySelector(".cart-item-price-old");

      const data = { pedido_id: pedidoId };
      if (action) data["action"] = action;

      try {
        const response = await axios.post(url, data);

        const {
          totalPrecio,
          subTotal,
          totalProductos,
          descuento,
          cantidad,
          precio,
          precioAnterior,
        } = response.data;

        if (response.data.totalProductos === 0) {
          resetCart();
          return;
        }

        if (cantidad !== undefined) {
          if (cantidad == 0) {
            itemBox.remove();
            refreshCart(totalPrecio, subTotal, totalProductos, descuento);
            return;
          } else {
            nav.querySelector(".cart-item-cantidad").textContent = cantidad;
          }
        }

        if (precio) itemPriceNow.textContent = precio;
        if (precioAnterior) itemPriceOld.textContent = precioAnterior;

        refreshCart(totalPrecio, subTotal, totalProductos, descuento);
      } catch (err) {
        console.warn(err);
      }
    });
  });
});

function refreshCart(totalPrecio, subTotal, totalProductos, descuento) {
  cartTotal.textContent = totalPrecio;
  cartSubTotal.textContent = subTotal;
  cartTotalProds.textContent = `${totalProductos} producto(s)`;
  cartDescuento.textContent = `-${descuento}`;
  totalCarro.textContent = totalProductos;
}

function resetCart() {
  totalCarro.classList.remove("active");
  totalCarro.textContent = "";
  genericBox.textContent = "";
  genericBox.innerHTML = `
    <div class="generic-item cart-empty">
      <h3>Tu carrito esta vacío<svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="2"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-shopping-cart-x"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M4 19a2 2 0 1 0 4 0a2 2 0 0 0 -4 0" /><path d="M13 17h-7v-14h-2" /><path d="M6 5l14 1l-1 7h-13" /><path d="M22 22l-5 -5" /><path d="M17 22l5 -5" /></svg></h3>
      <a href="/productos/" class="generic-button btn-1">Volver a la tienda</a>
    </div>
  `;
}

const iniciarCompraBtn = document.querySelector(".check-auth");
iniciarCompraBtn?.addEventListener("click", (e) => {
  e.preventDefault();
  const apiUrl = iniciarCompraBtn.getAttribute("data-api");

  axios
    .get(apiUrl)
    .then((response) => {
      if (response.data.is_authenticated) {
        window.location.href = iniciarCompraBtn.href;
      } else {
        modalUsers.classList.add("open");
        modalUsers.querySelector(".next-login").value = iniciarCompraBtn.href;
        modalUsers.querySelector(".next-login-validar").value =
          iniciarCompraBtn.href;
        modalUsers.querySelector("#id_login_email").focus();
      }
    })
    .catch((error) => {
      console.error("Error checking authentication:", error);
    });
});
