// > Bar Track
const barTitle = document.getElementById("bar-title");
const barFill = document.querySelector(".bar-fill");
const stepsBox = document.querySelector(".step-progress");
const stepsItems = stepsBox.querySelectorAll("span");
function setTrack(index) {
  stepsItems.forEach((item) => {
    item.classList.remove("selected");
  });
  stepsItems[index].classList.add("selected");
  barTitle.textContent = `Paso ${index + 1} de ${stepsItems.length}: ${stepsItems[index].textContent}`;
  barFill.style.width = `${((index + 1) / stepsItems.length) * 100}%`;
}
