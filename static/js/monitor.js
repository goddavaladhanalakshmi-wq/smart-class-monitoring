document.addEventListener("DOMContentLoaded", function () {
    const kpiInFrame = document.getElementById("kpi-in-frame");
    const kpiPresentToday = document.getElementById("kpi-present-today");
    const kpiRateSub = document.getElementById("kpi-rate-sub");
    const kpiAvgAtt = document.getElementById("kpi-avg-attentiveness");
    const kpiDrowsy = document.getElementById("kpi-drowsy-count");

    const hudFps = document.getElementById("hud-fps-val");
    const hudTimestamp = document.getElementById("hud-timestamp-val");
    const activeBadge = document.getElementById("active-students-badge");
    const activeList = document.getElementById("active-students-list");
    const activityTicker = document.getElementById("activity-ticker");

    const btnToggleCam = document.getElementById("btn-toggle-cam");
    const camToggleIcon = document.getElementById("cam-toggle-icon");
    const camToggleText = document.getElementById("cam-toggle-text");
    const videoStream = document.getElementById("video-stream");
    const streamPausedOverlay = document.getElementById("stream-paused-overlay");
    const btnFullscreen = document.getElementById("btn-fullscreen");
    const videoWrapper = document.getElementById("video-wrapper");

    let isStreaming = true;
    const loggedEvents = new Set();

    // 1. Live Telemetry Polling Loop
    async function fetchLiveStats() {
        if (!isStreaming) return;

        try {
            const resp = await fetch("/api/live_stats");
            if (!resp.ok) return;
            const data = await resp.json();

            const t = data.telemetry || {};
            const d = data.db_stats || {};

            // Update Top KPIs
            if (kpiInFrame) kpiInFrame.textContent = t.face_count || 0;
            if (kpiPresentToday) kpiPresentToday.textContent = `${d.present_today || 0} / ${d.total_students || 0}`;
            if (kpiRateSub) kpiRateSub.innerHTML = `<i class="fa-solid fa-chart-pie"></i> ${d.attendance_rate || 0}% Enrolled Present`;
            if (kpiAvgAtt) kpiAvgAtt.textContent = `${d.avg_attentiveness || 100}%`;
            if (kpiDrowsy) kpiDrowsy.textContent = d.drowsy_count || 0;

            // Update Video HUD
            if (hudFps) hudFps.textContent = t.fps || "0.0";
            if (hudTimestamp) hudTimestamp.textContent = t.timestamp || data.server_time || "";

            // Update In-Camera Students Roster
            const activeStudents = t.active_students || [];
            if (activeBadge) activeBadge.textContent = `${activeStudents.length} Active`;

            if (activeList) {
                if (activeStudents.length === 0) {
                    activeList.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-user-astronaut"></i>
                            <p>No students detected in camera frame.</p>
                            <span class="empty-sub">Registered students will be identified and logged automatically with timestamps upon detection.</span>
                        </div>
                    `;
                } else {
                    let html = "";
                    activeStudents.forEach(stu => {
                        let stateClass = "";
                        let badgeClass = "badge-attentive";
                        if (stu.is_drowsy) {
                            stateClass = "state-drowsy";
                            badgeClass = "badge-drowsy";
                        } else if (stu.attention === "LOOKING AWAY") {
                            stateClass = "state-distracted";
                            badgeClass = "badge-distracted";
                        }

                        html += `
                            <div class="active-student-card ${stateClass}">
                                <div class="stu-left">
                                    <div class="stu-avatar-box">
                                        <i class="fa-solid fa-user"></i>
                                    </div>
                                    <div>
                                        <span class="stu-name">${stu.name}</span>
                                        <span class="stu-time"><i class="fa-regular fa-clock"></i> ${stu.check_in_time}</span>
                                    </div>
                                </div>
                                <div class="stu-right">
                                    <span class="stu-att-badge ${badgeClass}">${stu.attention}</span>
                                    <span class="stu-sim">Match: ${stu.similarity}%</span>
                                </div>
                            </div>
                        `;

                        // Add to event ticker if new
                        const eventKey = `${stu.name}-${data.server_time_display}`;
                        if (!loggedEvents.has(eventKey) && activityTicker) {
                            loggedEvents.add(eventKey);
                            const item = document.createElement("div");
                            item.className = "ticker-item";
                            item.innerHTML = `
                                <span class="ticker-time">${data.server_time_display}</span>
                                <span class="ticker-msg"><strong>${stu.name}</strong> marked Present [${stu.attention} - ${stu.similarity}%]</span>
                            `;
                            activityTicker.prepend(item);
                            // Keep max 15 events
                            if (activityTicker.children.length > 15) {
                                activityTicker.removeChild(activityTicker.lastChild);
                            }
                        }
                    });
                    activeList.innerHTML = html;
                }
            }
        } catch (err) {
            console.error("Telemetry error:", err);
        }
    }

    setInterval(fetchLiveStats, 1500);
    fetchLiveStats();

    // 2. Stream Toggle (Pause / Resume)
    if (btnToggleCam) {
        btnToggleCam.addEventListener("click", async function () {
            try {
                const resp = await fetch("/api/camera/toggle", { method: "POST" });
                const res = await resp.json();
                if (res.status === "stopped") {
                    isStreaming = false;
                    videoStream.src = "";
                    streamPausedOverlay.classList.remove("hidden");
                    camToggleIcon.className = "fa-solid fa-play";
                    camToggleText.textContent = "Resume Stream";
                } else {
                    isStreaming = true;
                    videoStream.src = "/video_feed?" + new Date().getTime();
                    streamPausedOverlay.classList.add("hidden");
                    camToggleIcon.className = "fa-solid fa-pause";
                    camToggleText.textContent = "Pause Stream";
                }
            } catch (e) {
                console.error("Toggle cam error:", e);
            }
        });
    }

    // 3. Fullscreen Stream
    if (btnFullscreen && videoWrapper) {
        btnFullscreen.addEventListener("click", function () {
            if (!document.fullscreenElement) {
                videoWrapper.requestFullscreen().catch(err => {
                    alert(`Error attempting to enable fullscreen: ${err.message}`);
                });
            } else {
                document.exitFullscreen();
            }
        });
    }
});
