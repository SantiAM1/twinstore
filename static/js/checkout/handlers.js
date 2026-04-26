// > SETUP
const confirmFacturacion = document.getElementById("confirm-facturacion");
const confirmEnvio = document.getElementById("confirm-envio");
const confirmPago = document.getElementById("confirm-pago");
const billingCostoEnvio = document.getElementById("billing-envio");
const billingTotal = document.getElementById("billing-total");
const billingAdicional = document.getElementById("billing-adicional");
const steps = ["facturacion", "envio", "pago", "confirmacion"];
let currentStepIndex = 0;

// > Editar desde confirmacion
document.querySelectorAll(".confirm-edit").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    const step = btn.dataset.step;
    const index = parseInt(btn.dataset.index);
    document.getElementById(steps[currentStepIndex]).classList.add("hide");
    currentStepIndex = index;
    document.getElementById(steps[currentStepIndex]).classList.remove("hide");
    setTrack(currentStepIndex);
    nextBtn.querySelector("code").innerHTML = "Continuar";
  });
});

// > Boton siguiente
nextBtn.addEventListener("click", async (e) => {
  e.preventDefault();
  backBtnActive(true);
  nextBtn.disabled = true;
  nextBtn.classList.add("loading");
  const currentStepId = steps[currentStepIndex];

  const isValid = await stepHandlers[currentStepId]();

  if (isValid) {
    if (currentStepIndex < steps.length - 1) {
      document.getElementById(steps[currentStepIndex]).classList.add("hide");

      currentStepIndex++;
      document.getElementById(steps[currentStepIndex]).classList.remove("hide");
      setTrack(currentStepIndex);

      if (currentStepIndex === steps.length - 1) {
        nextBtn.querySelector("code").innerHTML = "Finalizar Compra";
      } else {
        nextBtn.querySelector("code").innerHTML = "Continuar";
      }
    } else {
      window.location.href = "/checkout/exito/";
    }
  }

  nextBtn.disabled = false;
  nextBtn.classList.remove("loading");
});

// > Boton volver
backBtn.addEventListener("click", async (e) => {
  e.preventDefault();
  if (currentStepIndex == 1) {
    backBtnActive(false);
  }

  if (currentStepIndex == 3)
    nextBtn.querySelector("code").innerHTML = "Continuar";

  nextBtnActive(true);

  document.getElementById(steps[currentStepIndex]).classList.add("hide");
  currentStepIndex--;
  document.getElementById(steps[currentStepIndex]).classList.remove("hide");
  setTrack(currentStepIndex);
  const currentStepId = steps[currentStepIndex];
  backHandlers[currentStepId]?.();
});

const stepHandlers = {
  facturacion: async () => {
    const data = new FormData(facturacionForm);
    const values = Object.fromEntries(data.entries());
    const apiEndpoint = facturacionForm.dataset.api;
    try {
      const response = await axios.post(apiEndpoint, values);
      nextBtnActive(false);
      const data = response.data;
      confirmFacturacion.innerHTML = `
      <div>
          <strong>Nombre completo</strong>
          <span>${data.nombre_completo}</span>
      </div>
      <div>
          <strong>DNI/CUIT</strong>
          <span>${data.dni_cuit}</span>
      </div>
      <div>
          <strong>Condicion frente al IVA</strong>
          <span>${data.condicion_iva}</span>
      </div>
      <div>
          <strong>Dirección</strong>
          <span>${data.direccion}</span>
      </div>
      `;
      if (response.status === 200) {
        const envioInputs = document.querySelector(
          "input[name=retiro_envio]:checked",
        );

        if (envioInputs) {
          if (envioInputs.id == "local") {
            nextBtnActive(true);
          } else {
            const selectedInput = shippingOptionsForm.querySelector(
              'input[name="metodo_envio"]:checked',
            );

            if (!selectedInput) {
              nextBtnActive(false);
              return true;
            }

            const infoEnvio = selectedInput.dataset;
            if (infoEnvio.service_code == "standard_delivery") {
              isValid = checkInputsNoError(shippingStandarDelivery);
            } else if (infoEnvio.service_code == "pickup_point") {
              isValid = checkOptionsNoError(sucursalesForm);
            }
            const isValidReciver = checkInputsNoError(userReciver);
            if (isValid && isValidReciver) {
              nextBtnActive(true);
            }
          }
        }

        return true;
      }
    } catch (e) {
      console.error("Error al validar la facturación:", e.response?.data || e);
      alert(
        "Hubo un error al validar la información de facturación. Por favor, revisa los datos e intenta nuevamente.",
      );
    }
  },
  envio: async () => {
    const envioInputs = document.querySelector(
      "input[name=retiro_envio]:checked",
    );

    if (!envioInputs) {
      alert("Seleccioná una modalidad de envío para continuar.");
      return false;
    }

    nextBtnActive(false);

    if (envioInputs.id == "local") {
      confirmEnvio.innerHTML = `
      <div>
          <strong>Metodo de envio</strong>
          <span>Retiro en local</span>
      </div>
      `;
      try {
        const response = await axios.post("/shipping/api/retiro-local/");
        const data = response.data;
        confirmEnvio.innerHTML += `
        <div>
            <strong>Dirección del local</strong>
            <span>${data.direccion}</span>
        </div>
        <div>
            <strong>Horario de atención</strong>
            <span>${data.horario_atencion}</span>
        </div>
          `;
        if (validarPago()) {
          nextBtnActive(true);
        } else {
          nextBtnActive(false);
        }
        billingTotal.querySelector("p").textContent = data.precio_total;
        billingCostoEnvio.classList.add("hide");
        return true;
      } catch (e) {
        console.error("Error al obtener la información de retiro en local:", e);
        alert(
          "Hubo un error al obtener la información de retiro en local. Por favor, intenta nuevamente.",
        );
        return false;
      }
    }

    const selectedInput = shippingOptionsForm.querySelector(
      'input[name="metodo_envio"]:checked',
    );
    const infoEnvio = selectedInput.dataset;
    if (infoEnvio.service_code == "standard_delivery") {
      const data = new FormData(shippingStandarDelivery);
      values = Object.fromEntries(data.entries());
    } else if (infoEnvio.service_code == "pickup_point") {
      const data = new FormData(sucursalesForm);
      values = Object.fromEntries(data.entries());
    }
    const userReciverData = new FormData(userReciver);
    const userReciverValues = Object.fromEntries(userReciverData.entries());

    const payload = {
      metodo_envio: infoEnvio.service_code,
      calle_domicilio: values.calle_domicilio || "",
      altura_domicilio: values.altura_domicilio || "",
      referencias_domicilio: values.referencias_domicilio || "",
      point_id: values.sucursales || "",
      nombre_reciver: userReciverValues.nombre_reciver,
      dni_reciver: userReciverValues.dni_reciver,
      email_reciver: userReciverValues.email_reciver,
      phone_reciver: userReciverValues.phone_reciver,
      id: infoEnvio.id,
    };

    try {
      const response = await axios.post(
        "/shipping/api/validar-envio/",
        payload,
      );
      const data = response.data.data;

      confirmEnvio.innerHTML = `
      <div>
          <strong>Metodo de envio</strong>
          <span>${data.service_name}</span>
      </div>
      <div>
          <strong>Empresa de transporte</strong>
          <span>${data.carrier_name}</span>
      </div>
      <div>
          <strong>Sucursal o dirección de envio</strong>
          <span>${data.domicilio_entrega}</span>
      </div>
      <div>
          <strong>Fecha de entrega</strong>
          <span>${data.fecha_entrega}</span>
      </div>
        `;

      billingCostoEnvio.querySelector("p").textContent = data.costo_envio;
      billingCostoEnvio.classList.remove("hide");
      billingTotal.querySelector("p").textContent = data.pago_total;

      return response.status === 200;
    } catch (e) {
      nextBtnActive(false);
      const errorData = e.response?.data || {};
      console.error("Error al validar el envío:", errorData);
      errorData.non_field_errors?.forEach((msg) => alert(msg));
      Object.keys(errorData).forEach((key) => {
        const fieldErrors = errorData[key];
        fieldErrors.forEach((msg) => {
          const fieldItem = document.querySelector(`input[name="${key}"]`);
          if (fieldItem) {
            fieldItem?.closest("form.generic-expand").classList.add("expand");
            fieldItem?.closest(".generic-input").classList.add("error");
            fieldItem.nextElementSibling.textContent = msg;
          }
        });
      });
    }
  },
  pago: async () => {
    try {
      const inputPago = document.querySelector(
        'input[name="forma_pago"]:checked',
      );

      if (!inputPago) {
        alert("Seleccioná una forma de pago para continuar.");
        return false;
      }
      payload = {
        forma_de_pago: inputPago.value,
        monto_mixto:
          inputPago.value === "mixto"
            ? inputMixto.value.replace(/\./g, "").trim()
            : null,
      };

      const response = await axios.post("/pedidos/api/validar-pago/", payload);
      const data = response.data;
      console.log(data);
      if (data.mixto) {
        confirmPago.innerHTML = `
          <div style="grid-column: span 2">
              <strong>Metodo de pago</strong>
              <span>${data.title}</span>
          </div>
          <div>
              <strong>Monto a transferir</strong>
              <span>${data.monto_transferencia}</span>
          </div>
          <div>
              <strong>Monto a pagar en Mercado Pago</strong>
              <span>${data.monto_mercadopago}</span>
          </div>`;
      } else {
        confirmPago.innerHTML = `
          <div style="grid-column: span 2">
              <strong>Metodo de pago</strong>
              <span>${data.title}</span>
          </div>`;
      }

      if (data.adicional) {
        billingAdicional.querySelector("p").textContent = data.adicional;
        billingAdicional.classList.remove("hide");
      } else {
        billingAdicional.classList.add("hide");
      }

      billingTotal.querySelector("p").textContent = data.pago_total;

      const msgBilling = document.querySelectorAll(".msg-billing");
      const msgBillingBox = document.getElementById(
        "billing-resume-confirmacion",
      );
      msgBilling.forEach((elem) => elem.classList.add("hide"));

      if (data.forma_de_pago) {
        const msg = document.querySelector(`#msg-${data.forma_de_pago}`);
        if (msg) {
          msg.classList.remove("hide");
          msgBillingBox.classList.remove("hide");
        } else {
          msgBillingBox.classList.add("hide");
        }
      }

      return response.status === 200;
    } catch (e) {
      const errorData = e.response?.data || {};
      const MixtoGenericInput = pagoMixtoBox.closest(".generic-input");
      if (errorData.mixto) {
        MixtoGenericInput.classList.add("error");
        MixtoGenericInput.querySelector(".msg-required").textContent =
          errorData.error;
      } else {
        alert(
          errorData.error ||
            "Hubo un error al validar el pago. Por favor, intenta nuevamente.",
        );
      }
      return false;
    }
  },
  confirmacion: async () => {
    try {
      const response = await axios.post("/pedidos/api/finalizar-compra/");
      data = response.data;
      console.log(data);
      if (data.message) {
        apiMessage(data.message, data.type);
        return false;
      } else if (data.redirect) {
        apiRedirect(data.redirect);
        return false;
      } else if (data.init_point) {
        console.log("Redirigiendo a Mercado Pago...");
        window.location.href = data.init_point;
        return false;
      } else if (data.merchant_order_id) {
        return true;
      } else {
        alert(
          "Hubo un error al finalizar la compra. Por favor, intenta nuevamente.",
        );
        return false;
      }
    } catch (e) {
      console.error("Error al finalizar la compra:", e.response?.data || e);
      alert(
        "Hubo un error al finalizar la compra. Por favor, intenta nuevamente.",
      );
    }
    return false;
  },
};

function validarPago() {
  const inputPago = document.querySelector('input[name="forma_pago"]:checked');
  if (!inputPago) {
    return false;
  }
  if (inputPago.value === "mixto") {
    if (!inputMixto.value.trim()) {
      return false;
    }
  }
  return true;
}

const backHandlers = {
  facturacion: () => {
    console.log("Reseteando formulario de facturación");
  },
  envio: () => {
    console.log("Reseteando formulario de envío");
  },
};
