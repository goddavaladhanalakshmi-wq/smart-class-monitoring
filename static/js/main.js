document.addEventListener("DOMContentLoaded", function () {
    // 1. Sidebar Toggle
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const sidebar = document.getElementById("sidebar");

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", function () {
            sidebar.classList.toggle("collapsed");
        });
    }

    // 2. Real-Time Topbar Server Clock (Ticks every second)
    const clockTimeEl = document.getElementById("live-server-clock");
    const clockDateEl = document.getElementById("live-server-date");

    function updateLiveClock() {
        const now = new Date();

        // Format: HH:MM:SS AM/PM
        let hours = now.getHours();
        const minutes = String(now.getMinutes()).padStart(2, "0");
        const seconds = String(now.getSeconds()).padStart(2, "0");
        const ampm = hours >= 12 ? "PM" : "AM";
        hours = hours % 12;
        hours = hours ? hours : 12; // 0 becomes 12
        const strHours = String(hours).padStart(2, "0");

        if (clockTimeEl) {
            clockTimeEl.textContent = `${strHours}:${minutes}:${seconds} ${ampm}`;
        }

        // Format Date: YYYY-MM-DD
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, "0");
        const day = String(now.getDate()).padStart(2, "0");
        if (clockDateEl) {
            clockDateEl.textContent = `${year}-${month}-${day}`;
        }
    }

    updateLiveClock();
    setInterval(updateLiveClock, 1000);
});
