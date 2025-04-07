document.addEventListener("DOMContentLoaded", () => {
    const csrftoken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
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