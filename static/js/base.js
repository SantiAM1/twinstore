const btnMenu = document.getElementById("menu-toggle");
const navbarButtom = document.querySelector(".navbar-buttom");
const navbarTop = document.querySelector(".navbar-top");
const searchButtom = document.getElementById("search-toggle");
const navbatSearch = document.querySelector(".navbar-search");
btnMenu.addEventListener("click", () => {
  navbarButtom.classList.toggle("show");
});
searchButtom.addEventListener("click", () => {
  navbatSearch.classList.toggle("show");
  searchButtom.classList.toggle("active");
  const input = navbatSearch.querySelector("input");
  input.focus();
});

let lastScrollTop = 0;

window.addEventListener("scroll", () => {
  const scrollTop = window.scrollY || document.documentElement.scrollTop;

  if (scrollTop > lastScrollTop) {
    navbarButtom.classList.add("scroll");
    navbarTop.classList.add("scroll");
  } else {
    navbarButtom.classList.remove("scroll");
    navbarTop.classList.remove("scroll");
  }

  lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
});

document.querySelectorAll(".password-toggle").forEach((btn) => {
  btn.addEventListener("click", () => {
    const input = btn.parentElement.querySelector(".api-required");
    btn.querySelectorAll("svg").forEach((svg) => {
      svg.classList.toggle("hide");
    });
    if (input.type === "password") {
      input.type = "text";
    } else {
      input.type = "password";
    }
  });
});

const modalUsers = document.querySelector(".generic-modal[data-modalId=users]");

modalUsers?.querySelectorAll(".generic-box").forEach((form) => {
  genericApiPost(form, {
    onSuccess: (response, form, btnSubmit) => {
      if (response.data.verificar)
        return userVerificar(form, response.data.modal);
    },
    onError: (err, form, btnSubmit) => {
      if (err.response?.data?.verificar) {
        userVerificar(form, err.response?.data?.modal, err);
      } else {
        usersError(form, btnSubmit, err);
      }
    },
  });
});

const pedidoView = document.querySelector(
  ".generic-modal[data-modalId=pedidos]",
);

genericApiPost(pedidoView.querySelector(".generic-box"), {
  onSuccess: (response, form, btnSubmit) => {
    if (response.data.redirect)
      return (window.location.href = response.data.redirect);
  },
  onError: (err, form, btnSubmit) => {
    usersError(form, btnSubmit, err);
  },
});

function genericApiPost(form, { onSuccess, onError, onProcess } = {}) {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btnSubmit = form.querySelector("button[type=submit]");
    btnSubmit.classList.add("loading");

    const url = form.getAttribute("data-api");
    const data = new FormData(form);

    if (onProcess) onProcess(form, btnSubmit);

    try {
      const response = await axios.post(url, data);

      if (response.data.redirect)
        return (window.location.href = decodeURIComponent(
          response.data.redirect,
        ));
      if (response.data.reload) return window.location.reload();

      if (onSuccess) onSuccess(response, form, btnSubmit);
    } catch (err) {
      if (onError) onError(err, form, btnSubmit);
    }
  });
}

function userVerificar(form, modal = null, err = null) {
  form.classList.add("hide");
  const box = modalUsers.querySelector(`.generic-box[data-modal=${modal}]`);
  box.classList.remove("hide");
  if (err) usersError(box, null, err);
}

function usersError(form, btn, err) {
  const errorData = err.response?.data;
  const errorMsg = form.querySelector(".msg-required-2");
  btn?.classList.remove("loading");

  form
    .querySelectorAll(".generic-input-2")
    .forEach((input) => input.classList.add("error"));

  let messages = [];

  if (typeof errorData === "object" && errorData !== null) {
    for (const [field, value] of Object.entries(errorData)) {
      if (field === "modal") continue;
      if (Array.isArray(value)) {
        messages.push(...value);
      } else if (typeof value === "string") {
        messages.push(value);
      }
    }
  } else {
    messages.push("Error de conexión.");
  }

  errorMsg.classList.add("show");
  errorMsg.innerHTML = messages.map((m) => `• ${m}`).join("<br>");
}

const params = new URLSearchParams(window.location.search);
if (params.get("login") === "required") {
  const modal = document.querySelector('.generic-modal[data-modalId="users"]');
  if (modal) {
    modal.classList.add("open");
    modal
      .querySelectorAll(".generic-box")
      .forEach((box) => box.classList.add("hide"));
    modal.querySelector('[data-modal="signin"]')?.classList.remove("hide");
    modal.querySelector("#id_login_email")?.focus();
  }
}

const inputSearch = document.querySelector("#search");
const resultSearch = document.querySelector("#search-results-list");
const resultBox = document.querySelector(".navbar-search-results");

let cancelToken;

function debounce(func, delay) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), delay);
  };
}

function formatoPesos(value) {
  if (value == null || isNaN(value)) return value;

  const valor = parseFloat(value);
  const entero = Math.floor(valor);
  const decimales = Math.round((valor - entero) * 100) / 100;

  if (decimales === 0) {
    return `$${entero.toLocaleString("es-AR")}`;
  } else {
    return `$${valor.toLocaleString("es-AR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
}

function resetResultBox() {
  resultSearch.innerHTML = "";
  resultBox.classList.remove("active");
}

async function buscarProductos(query) {
  if (query.length < 2) {
    resetResultBox();
    return;
  }

  if (cancelToken) cancelToken.cancel("Nueva búsqueda iniciada");
  cancelToken = axios.CancelToken.source();

  try {
    const res = await axios.get(`/api/busqueda_predictiva/`, {
      params: { q: query },
      cancelToken: cancelToken.token,
    });

    const data = res.data;
    if (!data.length) {
      resetResultBox();
      return;
    }

    resultBox.classList.add("active");
    resultSearch.innerHTML = data
      .map(
        (p) => `
          <li>
              <a href="/productos/${p.slug}/">
                  <header>
                      <img src="${
                        p.imagenes_producto__imagen_200 ||
                        "/static/img/prod_default.webp"
                      }" alt="${p.nombre}">
                  </header>
                <p>${p.nombre}</p>
                  <div class="search-results-prices">
                      <span>${formatoPesos(p.precio_final)}</span>
                  </div>
              </a>
          </li>
        `,
      )
      .join("");
  } catch (error) {
    if (!axios.isCancel(error)) console.error("Error:", error);
    resetResultBox();
  }
}

const buscarDebounce = debounce(buscarProductos, 1000);

inputSearch.addEventListener("input", (e) => {
  const query = e.target.value.trim();
  buscarDebounce(query);
});

const backBtn = document.getElementById("generic-header-back");
if (backBtn && window.location.pathname !== "/carro/finalizar-compra/") {
  backBtn.addEventListener("click", () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = "/";
    }
  });
}

const themeToggleBtn = document.getElementById("theme-toggle");
const body = document.body;
const lightTheme = document.querySelector(".theme-light");
const darkTheme = document.querySelector(".theme-dark");

const savedTheme = localStorage.getItem("theme") || "light";
setTheme(savedTheme);

function setTheme(theme) {
  if (theme === "dark") {
    body.setAttribute("data-theme", "dark");
    darkTheme.classList.add("hide");
    lightTheme.classList.remove("hide");
  } else {
    body.setAttribute("data-theme", "light");
    darkTheme.classList.remove("hide");
    lightTheme.classList.add("hide");
  }
}

if (themeToggleBtn) {
  themeToggleBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const currentTheme = body.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    setTheme(newTheme);
    localStorage.setItem("theme", newTheme);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".navbar-cart-user");

  if (!container) return;

  const updateScrollMask = () => {
    const isAtStart = container.scrollLeft <= 1;
    const isAtEnd =
      Math.abs(
        container.scrollWidth - container.clientWidth - container.scrollLeft,
      ) <= 1;
    const hasOverflow = container.scrollWidth > container.clientWidth;

    container.classList.remove("mask-left", "mask-right", "mask-both");

    if (!hasOverflow) return;

    if (!isAtStart && !isAtEnd) {
      container.classList.add("mask-both");
    } else if (isAtStart) {
      container.classList.add("mask-right");
    } else if (isAtEnd) {
      container.classList.add("mask-left");
    }
  };

  container.addEventListener("scroll", updateScrollMask);
  window.addEventListener("resize", updateScrollMask);

  updateScrollMask();
});
