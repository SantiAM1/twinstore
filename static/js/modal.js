document.querySelectorAll(".generic-modal-close-2").forEach((btn) => {
  btn.addEventListener("click", () => {
    const formTarget = btn.closest(".generic-box");
    if (formTarget.classList.contains("hide")) {
      formTarget.classList.add("hide");
    }
    document
      .querySelector(`.generic-modal[data-modalId="${btn.dataset.modalid}"]`)
      .classList.remove("open");
  });
});

document.querySelectorAll(".generic-modal-navegator").forEach((nav) => {
  nav.addEventListener("click", (e) => {
    e.preventDefault();
    const formTarget = nav.closest(".generic-box");
    formTarget.classList.add("hide");
    document
      .querySelector(`form[data-modal=${nav.dataset.nav}]`)
      .classList.remove("hide");
  });
});

const modalLogin = document.querySelector("form[data-modal=signin]");
const modalUser = document.querySelector("section[data-modalId=users]");
const loginInput = document.getElementById("id_login_email");

document.querySelectorAll(".generic-modal-open").forEach((btn) => {
  btn.addEventListener("click", (e) => {
    e.preventDefault();

    const modal = document.querySelector(
      `.generic-modal[data-modalId="${btn.dataset.modalid}"]`
    );
    if (!modal) return;

    modal.classList.add("open");

    const focus = btn.getAttribute("data-focus");
    const input = document.getElementById(focus);

    if (input) {
      setTimeout(() => input.focus(), 250);
    }
  });
});
