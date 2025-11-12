const CL_IN = "in-right";
const CL_OUT = "out-left";
const CL_HIDE = "hide";

let busy = false;

function animateOut(el) {
  if (!el) return;
  el.classList.remove(CL_IN);
  void el.offsetWidth;
  el.classList.add(CL_OUT);
}

function animateIn(el) {
  if (!el) return;
  el.classList.remove(CL_HIDE, CL_OUT);
  void el.offsetWidth;
  el.classList.add(CL_IN);
}

function resetAnimation(el, classes = []) {
  if (!el) return;
  el.classList.remove(...classes);
}

function animateElement(fromEl, toEl, titleEl = null, newTitle = null) {
  busy = true;
  animateOut(fromEl);
  if (titleEl) {
    animateOut(titleEl);
  }

  fromEl.addEventListener(
    "animationend",
    () => {
      if (titleEl) {
        titleEl.textContent = newTitle;
        resetAnimation(titleEl, [CL_OUT]);
        animateIn(titleEl);
      }

      fromEl.classList.add(CL_HIDE);
      resetAnimation(fromEl, [CL_OUT]);

      animateIn(toEl);
      busy = false;
    },
    { once: true }
  );
}
