const btnsNext = document.querySelectorAll(".billing-next");
const clientScreen = document.getElementById("step1");
const paymentScreen = document.getElementById("step2");
const finishScreen = document.getElementById("step3");
const titleScreen = document.getElementById("generic-title");
const btnBack = document.getElementById("generic-header-back");
const defaultDetail = document.getElementById("pagoEmpty");
const inputsClient = document.querySelectorAll(".api-required");
const importeMixto = document.getElementById("btn-importe-mixto");
const boxDetails = document.querySelector(".generic-item.details");
const inputPagos = document.querySelectorAll('input[name="forma_de_pago"]');
const msgDetails = document.querySelectorAll(".details-msg");
const btnFinish = document.querySelector(".btn-finish");
const pagoMixtoBox = document.getElementById("montomixto");
const inputMixto = pagoMixtoBox.querySelector("input");
const adicionalRow = document.querySelector(".adicional-row");
const totalRow = document.querySelector(".total-row");
const cuponRow = document.querySelector(".cupon-row");
const cuponSubmit = document.getElementById("submitCupon");
const cuponInput = document.getElementById("id_cupon");
const mixtoInput = document.getElementById("id_montomixto");
const mixtoSubmit = document.getElementById("submitMixto");
const montoMixtoBox = document.querySelector(".mixto-info");
const step3Check = document.querySelector("input[name='step3-check']");
const mixtoBox = mixtoInput.closest(".generic-input");
const msgMixto = mixtoBox.querySelector(".msg-required");
const montoMixto = montoMixtoBox.querySelector("#montoMixto");
const inputComprobante = document.getElementById("id_comprobante");
const fileNameDisplay = document.getElementById("file_name");
const labelComprobante = inputComprobante.nextElementSibling;
const submitComprobante = document.getElementById("submitComprobante");
const importeTransferencia = document.querySelector(".importe-transferencia");

submitComprobante.addEventListener("click", async (e) => {
  e.preventDefault();
  submitComprobante.classList.add("loading");
  btnFinish.click();
});

inputComprobante.addEventListener("change", () => {
  const file = inputComprobante.files[0];
  if (!file) return;

  const allowedTypes = ["pdf", "jpg", "jpeg", "png"];
  const fileExtension = file.name.split(".").pop().toLowerCase();
  if (!allowedTypes.includes(fileExtension)) {
    alert("Tipo de archivo no permitido. Solo se aceptan PDF, JPG o PNG.");
    reiniciarInputComprobante();
    return;
  }

  const maxSizeMB = 5;
  if (file.size > maxSizeMB * 1024 * 1024) {
    alert(`El archivo no puede superar ${maxSizeMB} MB`);
    reiniciarInputComprobante();
    return;
  }

  const fileName =
    inputComprobante.files[0]?.name || "Ningún archivo seleccionado";
  fileNameDisplay.textContent = fileName;
  labelComprobante.classList.add("active");

  submitComprobante.classList.remove("not-ready");
  step3Check.value = "done";
});

obtenerPerfil();

mixtoSubmit.addEventListener("click", async (e) => {
  mixtoBox.classList.remove("error");
  msgMixto.textContent = "";

  const monto = mixtoInput.value.trim();
  if (!monto) return;
  mixtoSubmit.classList.add("loading");
  try {
    const response = await axios.post(mixtoSubmit.dataset.api, {
      monto: monto,
    });

    if (response.data.mercadopago) {
      mixtoBox.classList.add("success");
      msgMixto.textContent = "Monto mixto aplicado correctamente.";
      montoMixtoBox.classList.remove(CL_HIDE);
      montoMixto.textContent = response.data.mercadopago;
      importeTransferencia.textContent = response.data.transferencia;
    }
    adicional(response);
    totalRow.querySelector("th").textContent = response.data.total;
    btnFinish.classList.remove("not-ready");
  } catch (error) {
    console.error("Error al aplicar el monto mixto:", error);
    montoMixtoBox.classList.add(CL_HIDE);
    mixtoBox.classList.add("error");
    msgMixto.textContent =
      error.response.data.error || "Error al aplicar el monto mixto.";
  } finally {
    mixtoSubmit.classList.remove("loading");
  }
});

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

    cuponRow.classList.remove(CL_HIDE);
    cuponRow.querySelector("th").textContent = response.data.cupon;
    totalRow.querySelector("th").textContent = response.data.total;
  } catch (error) {
    cuponBox.classList.add("error");
    msgCupon.textContent =
      error.response.data.error || "Error al aplicar el cupón.";
  } finally {
    cuponSubmit.classList.remove("loading");
  }
});

inputMixto.addEventListener("input", () => {
  if (inputMixto.value) {
    pagoMixtoBox.classList.add("prefix");
  } else {
    pagoMixtoBox.classList.remove("prefix");
  }
});

boxDetails.addEventListener("animationend", () => {
  boxDetails.classList.remove("splash");
});

inputPagos.forEach((input) => {
  input.addEventListener("click", async () => {
    montoMixtoBox.classList.add(CL_HIDE);
    mixtoBox.classList.remove("success", "error");
    msgMixto.textContent = "";
    mixtoInput.value = "";
    msgDetails.forEach((msg) => msg.classList.add("hide"));
    defaultDetail.classList.add(CL_HIDE);
    document.getElementById(input.dataset.info).classList.remove("hide");
    boxDetails.classList.add("splash");

    btnFinish.querySelector("code").textContent = input.dataset.finish;
    btnFinish.classList.add("loading");
    btnFinish.classList.add("not-ready");

    console.log("Forma de pago seleccionada:", input.value);

    if (
      input.value == "mixto" ||
      input.value == "transferencia" ||
      input.value == "tarjeta"
    ) {
      step3Check.value = "true";
    } else {
      step3Check.value = "false";
    }

    try {
      const response = await axios.post("/carro/api/checkout/adicionales/", {
        forma_de_pago: input.value,
      });

      if (input.value != "mixto") {
        btnFinish.classList.remove("not-ready");
      }
      if (response.data.total) {
        totalRow.querySelector("th").textContent = response.data.total;
        if (input.value == "transferencia") {
          importeTransferencia.textContent = response.data.total;
        }
      }

      adicional(response);
    } catch (error) {
      btnFinish.classList.add("not-ready");
    } finally {
      btnFinish.classList.remove("loading");
    }
  });
});

btnFinish?.addEventListener("click", async (e) => {
  e.preventDefault();
  if (btnFinish.classList.contains("not-ready")) return;
  if (step3Check.value === "true") return;

  const formCheckout = document.getElementById("form-checkout");
  const url = formCheckout.dataset.api;
  const btnSubmit = btnFinish;
  btnSubmit.classList.add("loading");

  try {
    const formData = new FormData(formCheckout);

    const response = await axios.post(url, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    if (response.data.init_point) {
      window.location.href = response.data.init_point;
      return;
    }

    if (response.data.success) {
      const modal = document.querySelector(
        `.generic-modal[data-modalid="compra-finalizada"]`
      );
      modal.classList.add("open");
      modal.querySelector("#merchant_order_id").textContent =
        "#" + response.data.order_id;
    }

    btnSubmit.classList.remove("loading");
  } catch (err) {
    console.error(err);
    btnSubmit.classList.remove("loading");
    reiniciarInputComprobante();
  }
});

btnBack.addEventListener("click", (e) => {
  e.preventDefault();
  reiniciarInputComprobante();
  if (busy) return;
  if (
    clientScreen.classList.contains(CL_HIDE) &&
    finishScreen.classList.contains(CL_HIDE)
  ) {
    animateElement(paymentScreen, clientScreen, titleScreen, "Facturación");
  }

  if (
    clientScreen.classList.contains(CL_HIDE) &&
    paymentScreen.classList.contains(CL_HIDE)
  ) {
    animateElement(
      finishScreen,
      paymentScreen,
      titleScreen,
      "Tu forma de pago"
    );
  }
});

btnsNext.forEach((btnNext) => {
  btnNext.addEventListener("click", async (e) => {
    e.preventDefault();
    if (busy) return;

    const formaPago = document.querySelector(
      'input[name="forma_de_pago"]:checked'
    )?.value;

    if (!clientScreen.classList.contains(CL_HIDE)) {
      const form = document.getElementById("form-checkout");
      const formData = new FormData(form);
      const url = form.dataset.validate;

      clientScreen.querySelectorAll(".generic-input").forEach((box) => {
        box.classList.remove("error");
        const msg = box.querySelector(".msg-required");
        if (msg) msg.textContent = "";
      });

      try {
        const response = await axios.post(url, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });

        await scrollToTop("smooth");
        animateElement(
          clientScreen,
          paymentScreen,
          titleScreen,
          "Tu forma de pago"
        );
      } catch (err) {
        const errors = err.response.data;
        for (const field in errors) {
          const input = form.querySelector(`[name="${field}"]`);
          const box = input?.closest(".generic-input");
          box.classList.add("error");
          box.querySelector(".msg-required").textContent = errors[field];
        }
        await scrollToTop("smooth");
      }
    } else if (
      !paymentScreen.classList.contains(CL_HIDE) &&
      (formaPago == "mixto" || formaPago == "transferencia")
    ) {
      console.log("Forma de pago seleccionada:", formaPago);
      const msgFinish = formaPago == "mixto" ? "Pago Mixto" : "Transferencia";
      await scrollToTop("smooth");
      animateElement(paymentScreen, finishScreen, titleScreen, msgFinish);
    }
  });
});

function scrollToTop(behavior = "smooth") {
  return new Promise((resolve) => {
    const el = document.scrollingElement || document.documentElement;
    if (el.scrollTop === 0) return resolve();

    const done = () => {
      window.removeEventListener("scrollend", onScrollEnd);
      cancelAnimationFrame(rafId);
      resolve();
    };

    const onScrollEnd = () => done();
    window.addEventListener("scrollend", onScrollEnd, { once: true });

    let rafId;
    const tick = () => {
      if (el.scrollTop <= 0) return done();
      rafId = requestAnimationFrame(tick);
    };

    window.scrollTo({ top: 0, behavior });
    rafId = requestAnimationFrame(tick);
  });
}

function adicional(response) {
  if (response.data.adicional) {
    adicionalRow.classList.remove(CL_HIDE);
    adicionalRow.querySelector("th").textContent = response.data.adicional;
  } else {
    adicionalRow.classList.add(CL_HIDE);
  }
}

function reiniciarInputComprobante() {
  inputComprobante.value = "";
  fileNameDisplay.textContent = "Ningún archivo seleccionado";
  labelComprobante.classList.remove("active");
  submitComprobante.classList.remove("loading");
  submitComprobante.classList.add("not-ready");
}

const cardModal = document.querySelector(".generic-modal");
const closeModal = document.querySelector(".generic-modal-close");
const cardInputCVV = document.querySelector(".card-cvv-input");
const cardFront = document.querySelector(".front");
const cardBack = document.querySelector(".back");

closeModal.addEventListener("click", () => {
  if (cardModal.classList.contains("open")) cardModal.classList.remove("open");
});

function formatCardNumber(value) {
  return value
    .replace(/\D/g, "")
    .replace(/(.{4})/g, "$1 ")
    .trim();
}

function bindInputToDisplay(
  inputSelector,
  displaySelector,
  defaultText,
  formatter = null
) {
  const input = document.querySelector(inputSelector);
  const display = document.querySelector(displaySelector);
  if (input && display) {
    input.addEventListener("input", () => {
      const value = input.value.trim();
      display.textContent = value
        ? formatter
          ? formatter(value)
          : value
        : defaultText;
    });
  }
}

bindInputToDisplay(
  ".card-number-input",
  ".card-number-box",
  "#### #### #### ####",
  formatCardNumber
);
bindInputToDisplay(".card-holder-input", ".card-fullname", "FULL NAME");
bindInputToDisplay(".card-month-input", ".exp-month", "MM");
bindInputToDisplay(".card-year-input", ".exp-year", "YY");
bindInputToDisplay(".card-cvv-input", ".card-cvv-box", "");

cardInputCVV.addEventListener("focus", () => {
  cardFront.style.transform = "perspective(1000px) rotateY(-180deg)";
  cardBack.style.transform = "perspective(1000px) rotateY(0deg)";
});

cardInputCVV.addEventListener("blur", () => {
  cardFront.style.transform = "perspective(1000px) rotateY(0deg)";
  cardBack.style.transform = "perspective(1000px) rotateY(180deg)";
});
