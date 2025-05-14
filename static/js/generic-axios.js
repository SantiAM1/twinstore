document.addEventListener("DOMContentLoaded", () => {
    const csrftoken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    axios.defaults.headers.common['X-CSRFToken'] = csrftoken;
});

function toggleDisableItems(disabled = true) {
    const formElements = document.querySelectorAll('.bloqueable');
    formElements.forEach(element => {
        if (disabled) {
            element.setAttribute('disabled', 'disabled');
        } else {
            element.removeAttribute('disabled');
        }
    });

    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = disabled ? 'flex' : 'none';
}