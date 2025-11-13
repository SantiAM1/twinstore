document.querySelectorAll(".orders-info-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const order = btn.closest(".orders");
    const infoBox = order.querySelector(".generic-expand.orders-info");
    infoBox.classList.toggle("expand");
    btn.classList.toggle("active");
  });
});
