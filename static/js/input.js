document
  .querySelectorAll(".generic-input input, .generic-input select")
  .forEach((el) => {
    const box = el.closest(".generic-input");

    const toggleActive = () => {
      const value = el.tagName === "SELECT" ? el.value : el.value.trim();
      box.classList.toggle("active", !!value);
    };

    toggleActive();

    const eventType = el.tagName === "SELECT" ? "change" : "input";
    el.addEventListener(eventType, toggleActive);
  });

document.querySelectorAll('input[inputmode="numeric"]').forEach((input) => {
  input.addEventListener("input", function () {
    this.value = this.value.replace(/\D/g, "");
  });
});
