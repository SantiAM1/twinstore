document.querySelectorAll(".orders-info-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const order = btn.closest(".orders");
    const infoBox = order.querySelector(".generic-expand.orders-info");
    infoBox.classList.toggle("expand");
    btn.classList.toggle("active");
  });
});

const navUserAnchor = document.querySelectorAll(".users-navbar-a");

let actualId = null;
let nuevoId = null;

navUserAnchor.forEach((anch) => {
  anch.addEventListener("click", (e) => {
    e.preventDefault();

    navUserAnchor.forEach((a) => {
      if (a.classList.contains("active")) {
        actualId = a.dataset.section;
      }
      a.classList.remove("active");
    });

    anch.classList.add("active");
    nuevoId = anch.dataset.section;

    const fromEl = document.getElementById(actualId);
    const toEl = document.getElementById(nuevoId);
    animateElement(fromEl, toEl);
  });
});

obtenerPerfil();

const formUser = document.getElementById("userdata");
genericApiPost(formUser, {
  onSuccess: (response, form, btnSubmit) => {
    btnSubmit.classList.remove("loading");
  },
  onError: (err, form, btnSubmit) => {
    for (const key in err.response.data) {
      const genericInput = document
        .querySelector(`[name="${key}"]`)
        .closest(".generic-input");
      genericInput.classList.add("error");
      genericInput.querySelector(".msg-required").textContent =
        err.response.data[key];
    }
    btnSubmit.classList.remove("loading");
  },
  onProcess: (form, btnSubmit) => {
    form.querySelectorAll(".generic-input").forEach((input) => {
      input.classList.remove("error");
    });
  },
});

const submitComprobante = document.getElementById("submitComprobante");
const inputComprobante = document.getElementById("id_comprobante");
const fileNameDisplay = document.getElementById("file_name");
const labelComprobante = inputComprobante.nextElementSibling;
const formComprobante = document.getElementById("comprobante-form");
const btnTransferencia = document.querySelectorAll("button.comprobante");
const importeTransferencia = document.querySelector(".importe-transferencia");
const historialIdInput = formComprobante.querySelector(
  'input[name="historial_id"]'
);
const btnMercadoPago = document.querySelectorAll("button.mercadopago");
const btnArrepentimiento = document.querySelectorAll("button.arrepentimiento");
const arrepentimientoModal = document.querySelector(".arrepentimiento-modal");
const formArrepentimiento = document.getElementById("arrepentido_form");
const cerrarModalArrepentimiento = document.querySelector(".btn-2.warning");

cerrarModalArrepentimiento.addEventListener("click", () => {
  arrepentimientoModal.classList.remove("open");
});

btnArrepentimiento.forEach((btn) => {
  btn.addEventListener("click", () => {
    const pedidoId = btn.dataset.pedidoid;
    const inputHidden = arrepentimientoModal.querySelector(
      'input[name="numero_firmado"]'
    );
    inputHidden.value = pedidoId;
    arrepentimientoModal.classList.add("open");
  });
});

genericApiPost(formArrepentimiento, {
  onSuccess: (response, form, btnSubmit) => {
    alert("Solicitud de arrepentimiento enviada con éxito.");
    btnSubmit.classList.remove("loading");
    document
      .querySelector(".generic-modal.arrepentimiento-modal")
      .classList.remove("open");
  },
  onError: (err, form, btnSubmit) => {
    alert("Error al enviar la solicitud. Intente nuevamente.");
    btnSubmit.classList.remove("loading");
  },
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
});

genericApiPost(formComprobante, {
  onSuccess: (response, form, btnSubmit) => {
    alert("Comprobante subido con éxito.");
  },
  onError: (err, form, btnSubmit) => {
    alert("Error al subir el comprobante. Intente nuevamente.");
    btnSubmit.classList.remove("loading");
  },
  onProcess: (form, btnSubmit) => {
    submitComprobante.classList.add("loading");
  },
});

btnTransferencia.forEach((btn) => {
  btn.addEventListener("click", async () => {
    const pedidoId = btn.dataset.pedidoid;

    try {
      const response = await axios.post("/payment/api/datos-comprobante/", {
        numero_firmado: pedidoId,
      });
      const datos = response.data;
      importeTransferencia.textContent = datos.monto;
      historialIdInput.value = datos.id_firmado;
      document
        .querySelector(".generic-modal.comprobante-modal")
        .classList.add("open");
    } catch (error) {
      console.error("Error al obtener datos del comprobante:", error);
    }
  });
});

btnMercadoPago.forEach((btn) => {
  btn.addEventListener("click", async () => {
    const ticketId = btn.getAttribute("data-ticketId");
    const textBtn = btn.querySelector("code");
    textBtn.textContent = "Generando...";

    try {
      const response = await axios.post("/payment/api/init-point-mp/", {
        numero_firmado: ticketId,
      });
      const initPoint = response.data.init_point;
      window.location.href = initPoint;
    } catch (error) {
      console.error("Error al crear preferencia de pago:", error);
      textBtn.textContent = "Generar link de pago";
    }
  });
});

function reiniciarInputComprobante() {
  inputComprobante.value = "";
  fileNameDisplay.textContent = "Ningún archivo seleccionado";
  labelComprobante.classList.remove("active");
  submitComprobante.classList.remove("loading");
  submitComprobante.classList.add("not-ready");
}

if (params.get("section") === "orders") {
  document.querySelector(`.users-navbar-a[data-section="orders"]`).click();
}

function getModalByCompraStatus(status) {
  const modal = document.querySelector(
    `section[data-modalId="compra-${status}"]`
  );
  const compraId = params.get("idcompra");
  const textOrderId = modal.querySelector(".merchant_order_id");

  textOrderId.textContent = `#${compraId}`;

  if (status === "fallida") {
    const btnWhatsapp = modal.querySelector(".whatsapp-support");
    const phone = "5493413491911"; // tu número
    const message = `Hola! Necesito ayuda con mi pedido #${compraId}`;
    const wppUrl = `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
    btnWhatsapp.href = wppUrl;
  }

  return modal;
}

const paramCompra = params.get("compra");
if (paramCompra === "exitosa" || paramCompra === "fallida") {
  const modal = getModalByCompraStatus(paramCompra);
  modal.classList.add("open");
}
