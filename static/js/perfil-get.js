async function obtenerPerfil() {
  try {
    const response = await axios.get("/usuario/api/micuenta/");
    const data = response.data;

    for (const key in data) {
      const input = document.querySelector(`[name="${key}"]`);
      if (!input) continue;

      if (
        input.tagName === "SELECT" ||
        input.tagName === "INPUT" ||
        input.tagName === "TEXTAREA"
      ) {
        input.value = data[key] ?? "";
      }

      actualizarDecoracionInputs();
    }
  } catch (error) {
    console.error("Error al obtener perfil:", error);
  }
}

function actualizarDecoracionInputs() {
  document
    .querySelectorAll(
      ".generic-input input, .generic-input select, .generic-input textarea"
    )
    .forEach((el) => {
      const box = el.closest(".generic-input");
      if (!box) return;

      const value = el.tagName === "SELECT" ? el.value : el.value.trim();
      box.classList.toggle("active", !!value);
    });
}
