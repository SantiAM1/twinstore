// > Facturacion
const facturacionForm = document.getElementById("facturacion");

function checkForm() {
  const isValid = checkInputs(facturacionForm);
  nextBtnActive(isValid);
  return isValid;
}

facturacionForm.addEventListener("input", () => {
  checkForm();
});

(async () => {
  try {
    await obtenerPerfil();
    checkForm();
  } catch (error) {
    console.error("Error al obtener el perfil:", error);
  }
})();
