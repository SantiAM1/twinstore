// > --------- Genericos ---------
const nextBtn = document.querySelector(".btn-next");
const backBtn = document.querySelector(".btn-back");
function nextBtnActive(active) {
  nextBtn.classList.add("not-ready");
  if (active) {
    nextBtn.classList.remove("not-ready");
  }
}

function backBtnActive(active) {
  backBtn.classList.add("not-ready");
  if (active) {
    backBtn.classList.remove("not-ready");
  }
}

function checkInputs(form) {
  const inputs = form.querySelectorAll(".api-required");
  let isFormValid = true;

  inputs.forEach((input) => {
    const errorMsg = input.parentElement.querySelector(".msg-required");
    if (!input.value.trim()) {
      input.parentElement.classList.add("error");
      if (errorMsg) errorMsg.textContent = "Este campo es obligatorio";
      isFormValid = false;
    } else {
      input.parentElement.classList.remove("error");
      if (errorMsg) errorMsg.textContent = "";
    }
  });
  return isFormValid;
}

function checkOptions(form) {
  let isFormValid = form.checkValidity();
  const msg = form.querySelector(".msg-required");
  if (!isFormValid) {
    msg.classList.add("show");
    msg.textContent = "Seleccioná una opción para continuar";
  } else {
    msg.classList.remove("show");
    msg.textContent = "";
  }
  return isFormValid;
}

function checkInputsNoError(form) {
  const inputs = form.querySelectorAll(".api-required");
  let isFormValid = true;

  inputs.forEach((input) => {
    if (!input.value.trim()) {
      isFormValid = false;
    }
  });
  return isFormValid;
}

function checkOptionsNoError(form) {
  let isFormValid = form.checkValidity();
  return isFormValid;
}

nextBtnActive(false);
