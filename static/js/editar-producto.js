const coloresBox = document.querySelector(".colores-box");
const agregarColorBtn = document.getElementById("agregar-color");
const agregarColoresSubmit = document.getElementById("agregar-colores");

const agregarImagenesBtn = document.getElementById("agregar-img");
const imagenesBox = document.querySelector(".imagenes-box");
const agregarImagenesSubmit = document.getElementById("agregar-imgs");

agregarImagenesBtn.addEventListener("click", function () {
  agregarImagenesSubmit.classList.remove("hide");
  const nuevoInputImagen = `
    <div class="generic-input">
        <input type="file" name="imagenes_producto[]" accept="image/*">
    </div>
  `;
  imagenesBox.insertAdjacentHTML("beforeend", nuevoInputImagen);
});

agregarColorBtn.addEventListener("click", function () {
  agregarColoresSubmit.classList.remove("hide");
  const nuevoColor = `
  <div class="generic-row-50">
    <div class="generic-input">
        <input type="text" name="nombre_color[]" placeholder="Nombre del color">
    </div>
    <div class="generic-input">
        <input type="color" name="codigo_color[]">
    </div>
  </div>
  `;
  coloresBox.insertAdjacentHTML("beforeend", nuevoColor);
});
