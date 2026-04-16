// > --------- Shipping ---------
const cotizadorForm = document.getElementById("cotizador");
const cotizadorBtn = document.getElementById("btn-cotizar");
const cotizadorResult = document.getElementById("cotizador-result");
const shippingResetBtns = document.querySelectorAll(".shipping-reset");
const shippingOptionsForm = document.getElementById("shipping-options");
const shippingOptionsBtn = document.getElementById("btn-shipping-opt");
const optionResult = document.getElementById("options-result");
const shippingStandarDelivery = document.getElementById("shipping-domicilio");
const optionStandarDelivery = document.getElementById(
  "standard_delivery-result",
);
const standarDeliveryBtn = document.getElementById("btn-shipping-domicilio");
const userReciver = document.getElementById("shipping-reciver");
const userReciverBtn = document.getElementById("btn-user-reciver");
const userReciverResultA = document.getElementById("user-reciver-result-1");
const sucursalesForm = document.getElementById("shipping-sucursales");
const sucursalesResult = document.getElementById("sucursal-result");
const sucursalesBtn = document.getElementById("btn-shipping-sucursal");
const formMetodoEnvio = document.querySelector(".shipping-labels");

function resultData(box, msg) {
  box.classList.remove("hide");
  const span = box.querySelector("span");
  span.textContent = msg;
}

// * Paso 1, seleccionar modalidad de envio
function asignEventShipping() {
  const envioInputs = document.querySelectorAll("input[name=retiro_envio]");
  if (!envioInputs) return;
  envioInputs.forEach((input) => {
    input.addEventListener("click", () => {
      if (input.id == "local") {
        shippingReset(1);
        toggleCotizador(false);
        nextBtnActive(true);
      } else {
        nextBtnActive(false);
        toggleCotizador(true);
      }
    });
  });
}

// * Paso 2, Cotizar envio
function toggleCotizador(flag) {
  cotizadorForm.classList.remove("expand");
  if (flag) {
    cotizadorForm.classList.add("expand");
  }
}

cotizadorBtn.addEventListener("click", async () => {
  if (!checkInputs(cotizadorForm)) return;

  const data = new FormData(cotizadorForm);
  const values = Object.fromEntries(data.entries());
  cotizadorBtn.classList.add("loading");

  try {
    const response = await axios.post("/shipping/api/cotizar/", values);
    const box = shippingOptionsForm.querySelector(".inner-item");
    box.innerHTML = response.data.html;
  } catch (error) {
    console.error("Error al cotizar el envío:", error);
    alert("Hubo un error al cotizar el envío. Por favor, intenta nuevamente.");
    return;
  } finally {
    cotizadorBtn.classList.remove("loading");
  }

  cotizadorForm.classList.remove("expand");
  msg = `CP: ${values.codigo_postal_cotiza}, ${values.provincia_cotiza}, ${values.localidad_cotiza}`;
  resultData(cotizadorResult, msg);
  shippingOptionsForm.classList.add("expand");
});

// * Paso 3, Eligir la opcion de envio (A domicilio | sucursal)
shippingOptionsBtn.addEventListener("click", async () => {
  if (!checkOptions(shippingOptionsForm)) return;

  const selectedInput = shippingOptionsForm.querySelector(
    'input[name="metodo_envio"]:checked',
  );

  const infoEnvio = selectedInput.dataset;
  const msg = `${infoEnvio.name}: ${infoEnvio.price}\n${infoEnvio.service_name}: ${infoEnvio.date}`;

  if (infoEnvio.service_code == "standard_delivery") {
    shippingStandarDelivery.classList.add("expand");
  } else if (infoEnvio.service_code == "pickup_point") {
    shippingOptionsBtn.classList.add("loading");
    try {
      const payload = {
        service_code: infoEnvio.service_code,
        carrier_name: infoEnvio.name,
      };
      console.log("Payload para obtener sucursales:", payload);
      const response = await axios.post(
        "/shipping/api/obtener-sucursales/",
        payload,
      );
      const box = sucursalesForm.querySelector(".inner-item");
      box.innerHTML = response.data.html;
      sucursalesForm.classList.add("expand");
    } catch (error) {
      console.error("Error al cargar las sucursales:", error);
      alert(
        "Hubo un error al cargar las sucursales. Por favor, intenta nuevamente.",
      );
      return;
    } finally {
      shippingOptionsBtn.classList.remove("loading");
    }
  }
  resultData(optionResult, msg);
  shippingOptionsForm.classList.remove("expand");
});

// * Paso 4b, elegir sucursal
sucursalesBtn.addEventListener("click", () => {
  if (!checkOptions(sucursalesForm)) return;

  const selectedInput = sucursalesForm.querySelector(
    'input[name="sucursales"]:checked',
  );

  const infoSucursal = selectedInput.dataset;
  const msg = `${infoSucursal.name}\n${infoSucursal.direccion}`;
  resultData(sucursalesResult, msg);
  userReciver.classList.add("expand");
  sucursalesForm.classList.remove("expand");
});

// * Paso 4a, Envio a domicilio
standarDeliveryBtn.addEventListener("click", () => {
  if (!checkInputs(shippingStandarDelivery)) return;

  const data = new FormData(shippingStandarDelivery);
  const values = Object.fromEntries(data.entries());

  shippingStandarDelivery.classList.remove("expand");
  const msg = `${values.calle_domicilio} ${values.altura_domicilio}\n${values?.referencias_domicilio}`;
  resultData(optionStandarDelivery, msg);
  userReciver.classList.add("expand");
});

// * Paso 5 Quien recibe/retira
userReciverBtn.addEventListener("click", () => {
  if (!checkInputs(userReciver)) return;

  const data = new FormData(userReciver);
  const values = Object.fromEntries(data.entries());

  msg = `${values.nombre_reciver}\n${values.dni_reciver}\n${values.email_reciver}\n${values.phone_reciver}`;
  resultData(userReciverResultA, msg);
  userReciver.classList.remove("expand");
  nextBtnActive(true);
});

// * Shipping reset
shippingResetBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    shippingReset(btn.dataset.value);
  });
});

function shippingReset(step) {
  nextBtnActive(false);
  if (step == 1) {
    cotizadorResult.classList.add("hide");
    cotizadorForm.classList.add("expand");
    shippingOptionsForm.classList.remove("expand");
    optionResult.classList.add("hide");
    optionStandarDelivery.classList.add("hide");
    shippingStandarDelivery.classList.remove("expand");
    userReciverResultA.classList.add("hide");
    userReciver.classList.remove("expand");
    sucursalesForm.classList.remove("expand");
    sucursalesResult.classList.add("hide");
  } else if (step == 2) {
    shippingOptionsForm.classList.add("expand");
    optionResult.classList.add("hide");
    optionStandarDelivery.classList.add("hide");
    userReciverResultA.classList.add("hide");
    userReciver.classList.remove("expand");
    sucursalesForm.classList.remove("expand");
    sucursalesResult.classList.add("hide");
    shippingStandarDelivery.remove("expand");
  } else if (step == "3a") {
    optionStandarDelivery.classList.add("hide");
    shippingStandarDelivery.classList.add("expand");
    userReciverResultA.classList.add("hide");
    userReciver.classList.remove("expand");
  } else if (step == "3b") {
    sucursalesForm.classList.add("expand");
    sucursalesResult.classList.add("hide");
    userReciverResultA.classList.add("hide");
    userReciver.classList.remove("expand");
  } else if (step == "4") {
    userReciverResultA.classList.add("hide");
    userReciver.classList.add("expand");
  }
}
asignEventShipping();
