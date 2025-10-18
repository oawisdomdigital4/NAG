// Convert any Font Awesome classes to Bootstrap Icons dynamically
document.addEventListener("DOMContentLoaded", function () {
    const iconMap = {
        "fa-users": "bi-people",
        "fa-user": "bi-person",
        "fa-book": "bi-journal-bookmark",
        "fa-bell": "bi-bell",
        "fa-credit-card": "bi-credit-card",
        "fa-globe": "bi-globe",
        "fa-money-bill-wave": "bi-cash-stack",
        "fa-history": "bi-clock-history",
    };

    document.querySelectorAll("i[class*='fa-']").forEach(icon => {
        for (const [fa, bi] of Object.entries(iconMap)) {
            if (icon.classList.contains(fa)) {
                icon.className = `bi ${bi}`;
                break;
            }
        }
    });
});
