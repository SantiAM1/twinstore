const svgs = document.querySelectorAll(".icon-tabler-star");
const btnSubmit = document.querySelector("button[type='submit']");
const msgRequired = document.querySelector(".msg-required-2");
let rating = 0;

svgs.forEach((svg) => {
  svg.addEventListener("click", () => {
    rating = svg.getAttribute("data-index");
    svgs.forEach((s, index) => {
      if (index < rating) {
        s.classList.add("active");
      } else {
        s.classList.remove("active");
      }
    });
  });
});

btnSubmit.addEventListener("click", async (e) => {
  e.preventDefault();
  if (rating === 0) {
    msgRequired.textContent =
      "Por favor, selecciona una calificación antes de enviar tu reseña.";
    return;
  }
  const reviewText = document.querySelector("textarea").value;

  try {
    const token = btnSubmit.getAttribute("data-token");
    const response = await axios.post("/usuario/api/crear-reseña/", {
      rating: parseInt(rating),
      review: reviewText || "",
      token: token,
    });

    if (response.status === 201) {
      window.location.href = "/";
    }
  } catch (error) {
    alert("Hubo un error al enviar tu reseña. Por favor, intenta nuevamente.");
  }
});

if (params.get("stars")) {
  const stars = parseInt(params.get("stars"));
  svgs.forEach((s, index) => {
    if (index < stars) {
      s.classList.add("active");
    } else {
      s.classList.remove("active");
    }
  });
  rating = stars;
  document.querySelector(`.users-navbar-a[data-section="orders"]`).click();
}
