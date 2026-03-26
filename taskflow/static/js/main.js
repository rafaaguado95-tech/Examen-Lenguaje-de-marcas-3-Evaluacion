// ============================================================
// main.js - JavaScript básico de TaskFlow
// ============================================================

// Auto-ocultar los mensajes flash después de 4 segundos
document.addEventListener('DOMContentLoaded', function () {
    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (el) {
        setTimeout(function () {
            el.style.transition = 'opacity 0.5s';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        }, 4000);
    });
});
