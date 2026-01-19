const brands = Array.from(document.querySelectorAll(".brand"));
const featuredNames = [
  "staticBento1",
  "staticBento2",
  "staticBento3",
  "staticBento4",
];
const longNames = [
  "staticBento5",
  "staticBento6",
  "staticBento5",
  "staticBento7",
];

const featuredEls = brands.filter((el) =>
  featuredNames.includes(el.dataset.name),
);
const longEls = brands.filter((el) => longNames.includes(el.dataset.name));

let activeIndex = 0;
let activeIndexLong = 0;

function highlightNextBrand() {
  brands.forEach((b) => {
    b.classList.remove("active");
    b.classList.remove("long");
    b.classList.remove("up");
  });

  if (featuredEls.length) {
    featuredEls[activeIndex].classList.add("active");
  }

  if (longEls.length) {
    longEls[activeIndexLong].classList.add("long");
  }

  activeIndex = (activeIndex + 1) % featuredEls.length;
  activeIndexLong = (activeIndexLong + 1) % longEls.length;
}

highlightNextBrand();
setInterval(highlightNextBrand, 5000);

document.querySelectorAll(".card-color-dot").forEach((dot) => {
  dot.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();

    const selectedColor = e.target.getAttribute("data-hex");
    const card = e.target.closest(".card-product");
    const images = card.querySelectorAll("header.card-product__media img");

    dot.classList.add("selected");
    card.querySelectorAll(".card-color-dot").forEach((d) => {
      if (d !== dot) d.classList.remove("selected");
    });

    images.forEach((img) => {
      if (img.dataset.hex === selectedColor) {
        img.classList.remove("hide");
      } else {
        img.classList.add("hide");
      }
    });
  });
});
