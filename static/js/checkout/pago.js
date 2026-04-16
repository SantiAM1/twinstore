// > Formas de pago
const paymentLabels = document.querySelectorAll(".payment-method-label");
const paymentInfo = document.querySelectorAll(".payment-method-info");
const pagoMixtoBox = document.getElementById("montomixto");
const inputMixto = pagoMixtoBox.querySelector("input");

paymentLabels.forEach((label) => {
  label.addEventListener("click", () => {
    paymentInfo.forEach((info) => info.classList.add("hide"));
    const infoBox = document.getElementById(
      `pago${label.attributes.for.value}`,
    );
    infoBox.classList.remove("hide");
    if (label.attributes.for.value == "__mixto") {
      console.log(inputMixto.value.trim());
      if (!inputMixto.value.trim()) {
        nextBtnActive(false);
        console.log("No hay monto ingresado");
      } else {
        nextBtnActive(true);
      }
    } else {
      nextBtnActive(true);
    }
  });
});

const formatter = new Intl.NumberFormat("es-AR", {
  maximumFractionDigits: 0,
});

inputMixto.addEventListener("input", (e) => {
  let value = e.target.value.replace(/\D/g, "");

  if (!value) {
    e.target.value = "";
    pagoMixtoBox.classList.remove("prefix");
    nextBtnActive(false);
    return;
  }

  e.target.value = formatter.format(parseInt(value));

  pagoMixtoBox.classList.add("prefix");
  nextBtnActive(true);
});

const billingCupon = document.getElementById("billing-cupon");
const cuponInput = document.getElementById("id_cupon");
const cuponSubmit = document.getElementById("submitCupon");
cuponSubmit.addEventListener("click", async (e) => {
  const cuponBox = cuponInput.closest(".generic-input");
  const msgCupon = cuponBox.querySelector(".msg-required");
  cuponBox.classList.remove("error");
  msgCupon.textContent = "";

  const codigo = cuponInput.value.trim();
  if (!codigo) return;
  cuponSubmit.classList.add("loading");
  try {
    const response = await axios.post(cuponSubmit.dataset.api, {
      codigo: codigo,
    });

    billingCupon.classList.remove("hide");
    billingCupon.querySelector("p").textContent = response.data.descuento;
    billingTotal.querySelector("p").textContent = response.data.precio_total;
    cuponBox.classList.add("success");
  } catch (error) {
    billingCupon.classList.add("hide");
    cuponBox.classList.add("error");
    msgCupon.textContent =
      error.response.data.error || "Error al aplicar el cupón.";
  } finally {
    cuponSubmit.classList.remove("loading");
  }
});
