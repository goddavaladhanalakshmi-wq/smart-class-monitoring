const { useState, useEffect, useCallback, useMemo, useRef } = React;

// ==========================================
// TOAST NOTIFICATION COMPONENT
// ==========================================
function Toast({ toast, onClose }) {
    if (!toast) return null;
    const isError = toast.type === 'error';
    const isSuccess = toast.type === 'success';

    return (
        <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 px-5 py-3.5 rounded-xl shadow-2xl border text-sm font-medium transition-all duration-300 transform translate-y-0 ${
            isError ? 'bg-rose-950/90 border-rose-800/60 text-rose-200' :
            isSuccess ? 'bg-emerald-950/90 border-emerald-800/60 text-emerald-200' :
            'bg-slate-900/90 border-slate-700 text-slate-200'
        }`}>
            <i className={`fa-solid ${isError ? 'fa-triangle-exclamation text-rose-400' : isSuccess ? 'fa-circle-check text-emerald-400' : 'fa-circle-info text-indigo-400'}`}></i>
            <span>{toast.message}</span>
            <button onClick={onClose} className="ml-3 text-slate-400 hover:text-white transition-colors">
                <i className="fa-solid fa-xmark"></i>
            </button>
        </div>
    );
}

// ==========================================
// ADMIN LOGIN GATE (RESTRICTED ACCESS ONLY)
// ==========================================
function AdminLogin({ onLoginSuccess }) {
    const [username, setUsername] = useState('admin');
    const [password, setPassword] = useState('admin123');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                onLoginSuccess(data.admin);
            } else {
                setError(data.message || 'Access Denied: Invalid administrator credentials.');
            }
        } catch (err) {
            setError('Could not connect to backend server. Please verify Flask is running.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-[#0b0f19] bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(99,102,241,0.15),rgba(255,255,255,0))]">
            <div className="w-full max-w-md">
                {/* Security Gate Header Badge */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center h-20 w-20 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 mb-4 shadow-xl shadow-indigo-500/10">
                        <i className="fa-solid fa-shield-halved text-3xl"></i>
                    </div>
                    <h1 className="text-2xl font-bold tracking-tight text-white mb-2">SmartClass AI Portal</h1>
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider bg-rose-500/10 border border-rose-500/30 text-rose-400">
                        <i className="fa-solid fa-lock text-[10px]"></i>
                        Restricted Admin Access Only
                    </div>
                    <p className="text-sm text-slate-400 mt-2">Sign in to join live classroom sessions and monitor students.</p>
                </div>

                {/* Login Card */}
                <div className="bg-[#121826]/90 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-8 shadow-2xl">
                    {error && (
                        <div className="mb-6 flex items-start gap-3 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm">
                            <i className="fa-solid fa-circle-exclamation mt-0.5 text-rose-400"></i>
                            <div className="flex-1">{error}</div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                                Admin Username
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                                    <i className="fa-solid fa-user-shield"></i>
                                </div>
                                <input
                                    type="text"
                                    required
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder="Enter admin username"
                                    className="w-full pl-10 pr-4 py-2.5 bg-[#0b0f19] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm font-medium transition"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-2">
                                Admin Password
                            </label>
                            <div className="relative">
                                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                                    <i className="fa-solid fa-key"></i>
                                </div>
                                <input
                                    type="password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className="w-full pl-10 pr-4 py-2.5 bg-[#0b0f19] border border-slate-700/80 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm font-medium transition"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl text-sm transition shadow-lg shadow-indigo-600/25 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
                        >
                            {loading ? (
                                <>
                                    <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    <span>Verifying Credentials...</span>
                                </>
                            ) : (
                                <>
                                    <i className="fa-solid fa-arrow-right-to-bracket"></i>
                                    <span>Authenticate as Admin</span>
                                </>
                            )}
                        </button>
                    </form>

                    {/* Default Credentials Helper */}
                    <div className="mt-6 pt-5 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                        <span>Default Demo Credentials:</span>
                        <code className="px-2 py-1 bg-slate-800 rounded font-mono text-indigo-300">admin / admin123</code>
                    </div>
                </div>

                <div className="text-center mt-6 text-xs text-slate-500">
                    Smart Classroom Monitoring • OpenCV + MediaPipe + MySQL Vision Pipeline
                </div>
            </div>
        </div>
    );
}

// ==========================================
// TOP NAVIGATION & TIMESTAMP BAR
// ==========================================
function Navbar({ admin, activeTab, setActiveTab, onLogout, activeSession, dbStats, serverTime }) {
    return (
        <header className="sticky top-0 z-40 bg-[#121826]/90 backdrop-blur-xl border-b border-slate-800/80 px-4 lg:px-8 py-3">
            <div className="flex flex-wrap items-center justify-between gap-4">
                {/* Brand Logo & Class State */}
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20 font-bold">
                        <i className="fa-solid fa-graduation-cap text-lg"></i>
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <span className="font-bold text-white tracking-tight text-base">SmartClass</span>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-semibold">REACT AI</span>
                        </div>
                        <span className="text-xs text-slate-400 flex items-center gap-1.5">
                            <i className="fa-solid fa-shield-halved text-[10px] text-emerald-400"></i>
                            Admin Vision Portal
                        </span>
                    </div>
                </div>

                {/* Microsecond Server Timestamp & Active Session Indicator */}
                <div className="flex items-center gap-3">
                    {/* Active Session Badge */}
                    {activeSession ? (
                        <div className="hidden md:flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-indigo-950/60 border border-indigo-800/50 text-xs text-indigo-200">
                            <span className="h-2 w-2 rounded-full bg-indigo-400 animate-ping"></span>
                            <span className="font-semibold">{activeSession.title}</span>
                            <span className="text-indigo-400 font-mono">({activeSession.elapsed_formatted || 'Active'})</span>
                        </div>
                    ) : (
                        <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-xl bg-slate-800/40 border border-slate-700/50 text-xs text-slate-400">
                            <span className="h-2 w-2 rounded-full bg-slate-500"></span>
                            <span>No Active Class Session</span>
                        </div>
                    )}

                    {/* Server Digital Clock */}
                    <div className="flex items-center gap-2.5 px-3.5 py-1.5 rounded-xl bg-[#0b0f19] border border-slate-700/70 text-slate-200 font-mono text-xs shadow-inner">
                        <span className="h-2 w-2 rounded-full bg-emerald-400 pulse-slow"></span>
                        <i className="fa-regular fa-clock text-indigo-400 text-xs"></i>
                        <span className="font-semibold text-emerald-400 tracking-wider">
                            {serverTime || new Date().toLocaleTimeString()}
                        </span>
                    </div>

                    {/* Database Mode Badge */}
                    <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border"
                        style={{
                            borderColor: dbStats?.active_db === 'mysql' ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)',
                            backgroundColor: dbStats?.active_db === 'mysql' ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                            color: dbStats?.active_db === 'mysql' ? '#34d399' : '#fbbf24'
                        }}>
                        <i className="fa-solid fa-database text-[10px]"></i>
                        <span className="uppercase">{dbStats?.active_db || 'SQLite'}</span>
                    </div>
                </div>

                {/* Navigation Tabs & Admin Profile */}
                <div className="flex items-center gap-2">
                    {/* Admin User Chip */}
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs text-slate-200">
                        <div className="h-6 w-6 rounded-full bg-indigo-500/20 text-indigo-300 flex items-center justify-center font-bold">
                            {admin?.name ? admin.name[0].toUpperCase() : 'A'}
                        </div>
                        <span className="font-medium hidden sm:inline">{admin?.name || 'Administrator'}</span>
                    </div>

                    {/* Logout Button */}
                    <button
                        onClick={onLogout}
                        title="Sign Out"
                        className="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-300 text-xs font-semibold transition flex items-center gap-1.5 cursor-pointer"
                    >
                        <i className="fa-solid fa-arrow-right-from-bracket"></i>
                        <span className="hidden sm:inline">Logout</span>
                    </button>
                </div>
            </div>

            {/* Navigation Tabs Bar */}
            <div className="flex items-center gap-1 overflow-x-auto mt-3 pt-2 border-t border-slate-800/60 no-scrollbar">
                {[
                    { id: 'monitor', label: 'Live Classroom', icon: 'fa-video' },
                    { id: 'attendance', label: 'Join & Exit Timings', icon: 'fa-clock' },
                    { id: 'sessions', label: 'Class Sessions', icon: 'fa-graduation-cap' },
                    { id: 'students', label: 'Student Roster', icon: 'fa-users' },
                    { id: 'analytics', label: 'Analytics', icon: 'fa-chart-pie' },
                    { id: 'settings', label: 'MySQL & Settings', icon: 'fa-sliders' },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                            activeTab === tab.id
                                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/25'
                                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                        }`}
                    >
                        <i className={`fa-solid ${tab.icon} text-xs`}></i>
                        <span>{tab.label}</span>
                    </button>
                ))}
            </div>
        </header>
    );
}

// ==========================================
// VIEW 1: LIVE CLASSROOM MONITOR (ADMIN JOINS & MONITORS)
// ==========================================
function MonitorView({ activeSession, telemetry, dbStats, serverTime, onStartSession, onEndSession, onMarkExit, showToast }) {
    const [cameraActive, setCameraActive] = useState(true);
    const [isStartingSession, setIsStartingSession] = useState(false);
    const [sessionTitleInput, setSessionTitleInput] = useState('Computer Science - AI & Machine Learning');

    const toggleCamera = async () => {
        try {
            const res = await fetch('/api/camera/toggle', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                setCameraActive(data.status === 'started');
                showToast({ type: 'info', message: `Camera stream ${data.status}.` });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Failed to toggle camera stream.' });
        }
    };

    const handleStartSessionSubmit = (e) => {
        e.preventDefault();
        onStartSession(sessionTitleInput);
        setIsStartingSession(false);
    };

    const activeStudents = telemetry?.active_students || [];

    return (
        <div className="space-y-6">
            {/* Top Command & Status Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl">
                <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
                        <i className="fa-solid fa-desktop text-indigo-400"></i>
                        Live Classroom Surveillance & Attention HUD
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                        Admin real-time video feed with OpenCV YuNet face detection, SFace biometric matching, and MediaPipe gaze/drowsiness analysis.
                    </p>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                    {activeSession ? (
                        <button
                            onClick={onEndSession}
                            className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs transition shadow-lg shadow-rose-600/20 flex items-center gap-2 cursor-pointer"
                        >
                            <i className="fa-solid fa-stop"></i>
                            <span>End Class Session</span>
                        </button>
                    ) : (
                        <button
                            onClick={() => setIsStartingSession(true)}
                            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition shadow-lg shadow-indigo-600/20 flex items-center gap-2 cursor-pointer"
                        >
                            <i className="fa-solid fa-play"></i>
                            <span>Join / Start Class Session</span>
                        </button>
                    )}

                    <button
                        onClick={toggleCamera}
                        className={`px-3.5 py-2 rounded-xl border text-xs font-semibold transition flex items-center gap-2 cursor-pointer ${
                            cameraActive
                                ? 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                                : 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300 hover:bg-emerald-900/50'
                        }`}
                    >
                        <i className={`fa-solid ${cameraActive ? 'fa-video-slash' : 'fa-video'}`}></i>
                        <span>{cameraActive ? 'Pause Stream' : 'Resume Stream'}</span>
                    </button>
                </div>
            </div>

            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="p-4 rounded-xl bg-[#121826] border border-slate-800/80">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">Students in View</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-black text-white">{telemetry?.face_count || 0}</span>
                        <span className="text-xs text-indigo-400 font-medium">Detected</span>
                    </div>
                </div>

                <div className="p-4 rounded-xl bg-[#121826] border border-slate-800/80">
                    <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block mb-1">Attentive</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-black text-emerald-400">{telemetry?.attentive_count || 0}</span>
                        <span className="text-xs text-slate-400">Focused</span>
                    </div>
                </div>

                <div className="p-4 rounded-xl bg-[#121826] border border-slate-800/80">
                    <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider block mb-1">Distracted</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-black text-amber-400">
                            {Math.max(0, (telemetry?.face_count || 0) - (telemetry?.attentive_count || 0) - (telemetry?.drowsy_count || 0))}
                        </span>
                        <span className="text-xs text-slate-400">Looking Away</span>
                    </div>
                </div>

                <div className="p-4 rounded-xl bg-[#121826] border border-slate-800/80">
                    <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block mb-1">Drowsy / Inactive</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-black text-rose-400">{telemetry?.drowsy_count || 0}</span>
                        <span className="text-xs text-slate-400">Sleepy</span>
                    </div>
                </div>

                <div className="p-4 rounded-xl bg-[#121826] border border-slate-800/80">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">Avg Attention</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-black text-indigo-400">{dbStats?.avg_attentiveness || 100}%</span>
                        <span className="text-xs text-slate-400">Today</span>
                    </div>
                </div>

                <div className="p-4 rounded-xl bg-[#121826] border border-slate-800/80">
                    <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">Stream Performance</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-2xl font-black text-cyan-400">{telemetry?.fps || 25}</span>
                        <span className="text-xs text-slate-400">FPS</span>
                    </div>
                </div>
            </div>

            {/* Main Video Stream & Active Students Panel */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left (2 Columns): Video Monitor Feed */}
                <div className="lg:col-span-2 space-y-3">
                    <div className="relative rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-2xl group">
                        {/* Live Feed Image */}
                        {cameraActive ? (
                            <img
                                src="/video_feed"
                                alt="Live Classroom Stream"
                                className="w-full h-auto min-h-[380px] max-h-[540px] object-cover object-center bg-[#0d1117]"
                                onError={(e) => {
                                    e.target.style.display = 'none';
                                    const fallback = document.getElementById('camera-fallback-msg');
                                    if (fallback) fallback.style.display = 'flex';
                                }}
                            />
                        ) : (
                            <div className="flex flex-col items-center justify-center min-h-[420px] bg-slate-950 text-slate-400 p-8 text-center">
                                <i className="fa-solid fa-video-slash text-4xl mb-3 text-slate-600"></i>
                                <span className="text-base font-semibold text-white">Camera Stream Paused</span>
                                <span className="text-xs text-slate-500 mt-1">Click "Resume Stream" above to reactivate camera monitoring.</span>
                            </div>
                        )}

                        {/* Stream Error Fallback */}
                        <div id="camera-fallback-msg" className="hidden flex-col items-center justify-center min-h-[420px] bg-slate-950 text-slate-400 p-8 text-center">
                            <i className="fa-solid fa-triangle-exclamation text-4xl text-amber-500 mb-3"></i>
                            <span className="text-base font-semibold text-white">Video Feed Reconnecting</span>
                            <span className="text-xs text-slate-400 mt-1">Waiting for OpenCV video frames from the Python backend...</span>
                        </div>

                        {/* Live Watermark Overlay (Bottom-Right) */}
                        <div className="absolute bottom-3 right-3 px-2.5 py-1 rounded-md bg-black/70 backdrop-blur-sm border border-white/10 text-[11px] font-mono text-cyan-300">
                            TIME: {serverTime || telemetry?.timestamp}
                        </div>
                    </div>

                    <div className="flex items-center justify-between text-xs text-slate-400 px-1">
                        <span className="flex items-center gap-1.5">
                            <i className="fa-solid fa-microchip text-indigo-400"></i>
                            YuNet Detection + SFace Biometrics + MediaPipe 468 Landmarks
                        </span>
                        <span className="text-slate-500 font-mono">Camera: DirectShow / Device #0</span>
                    </div>
                </div>

                {/* Right (1 Column): Active Students Detected Shelf */}
                <div className="space-y-4">
                    <div className="p-4 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <i className="fa-solid fa-user-check text-indigo-400"></i>
                                <h3 className="font-bold text-white text-sm">Active Students in Frame</h3>
                            </div>
                            <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold">
                                {activeStudents.length} Active
                            </span>
                        </div>

                        {activeStudents.length === 0 ? (
                            <div className="p-8 text-center rounded-xl bg-slate-900/40 border border-slate-800/60 text-slate-400">
                                <i className="fa-regular fa-face-smile text-3xl mb-2 text-slate-600"></i>
                                <p className="text-xs font-medium">No registered students recognized currently in frame.</p>
                                <span className="text-[11px] text-slate-500 mt-1 block">Students will appear here with join timestamps when detected.</span>
                            </div>
                        ) : (
                            <div className="space-y-3 max-h-[460px] overflow-y-auto pr-1">
                                {activeStudents.map((stu, idx) => (
                                    <div key={idx} className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition">
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="flex items-center gap-3">
                                                <div className="h-10 w-10 rounded-full bg-indigo-900/50 border border-indigo-500/40 text-indigo-300 flex items-center justify-center font-bold text-sm">
                                                    {stu.name ? stu.name[0].toUpperCase() : 'S'}
                                                </div>
                                                <div>
                                                    <span className="font-bold text-white text-sm block">{stu.name}</span>
                                                    <span className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                                                        <i className="fa-regular fa-clock text-[10px] text-indigo-400"></i>
                                                        Join: {stu.check_in_time || 'Just now'}
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Status Pill */}
                                            <span className={`text-[11px] px-2 py-0.5 rounded-full font-semibold border ${
                                                stu.is_drowsy ? 'bg-rose-500/20 text-rose-300 border-rose-500/40' :
                                                stu.attention === 'ATTENTIVE' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' :
                                                'bg-amber-500/20 text-amber-300 border-amber-500/40'
                                            }`}>
                                                {stu.attention || 'Present'}
                                            </span>
                                        </div>

                                        <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-800/80 text-[11px]">
                                            <span className="text-slate-400">
                                                Attention: <strong className="text-slate-200">{stu.score}%</strong>
                                            </span>
                                            <button
                                                onClick={() => onMarkExit(stu.name)}
                                                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-rose-950/60 hover:text-rose-300 text-slate-300 text-[10px] font-semibold transition flex items-center gap-1 cursor-pointer"
                                                title="Record Student Exit"
                                            >
                                                <i className="fa-solid fa-arrow-right-from-bracket"></i>
                                                <span>Mark Exit</span>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Start Session Modal */}
            {isStartingSession && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
                    <div className="w-full max-w-md bg-[#121826] border border-slate-800 rounded-2xl p-6 shadow-2xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-white text-base flex items-center gap-2">
                                <i className="fa-solid fa-graduation-cap text-indigo-400"></i>
                                Start New Classroom Session
                            </h3>
                            <button onClick={() => setIsStartingSession(false)} className="text-slate-400 hover:text-white">
                                <i className="fa-solid fa-xmark"></i>
                            </button>
                        </div>
                        <form onSubmit={handleStartSessionSubmit} className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                                    Session Topic / Subject Name
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={sessionTitleInput}
                                    onChange={(e) => setSessionTitleInput(e.target.value)}
                                    placeholder="e.g. Artificial Intelligence Lecture 4"
                                    className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500 font-medium"
                                />
                            </div>
                            <p className="text-xs text-slate-400">
                                When the session starts, the AI engine will log each student's exact Join Timestamp and track attentiveness until the session concludes.
                            </p>
                            <div className="flex justify-end gap-2.5 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsStartingSession(false)}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/25 cursor-pointer"
                                >
                                    Start Monitoring
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

// ==========================================
// VIEW 2: JOIN & EXIT TIMINGS ATTENDANCE LOG
// ==========================================
function AttendanceView({ onMarkExit, showToast }) {
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [dateFilter, setDateFilter] = useState('');
    const [statusFilter, setStatusFilter] = useState('All');
    const [searchQuery, setSearchQuery] = useState('');
    const [isManualModalOpen, setIsManualModalOpen] = useState(false);
    const [manualStudentId, setManualStudentId] = useState('');
    const [manualStatus, setManualStatus] = useState('Present');
    const [manualRemarks, setManualRemarks] = useState('Manual Entry by Admin');

    const fetchRecords = useCallback(async () => {
        setLoading(true);
        try {
            const params = new URLSearchParams();
            if (dateFilter) params.append('date', dateFilter);
            if (statusFilter && statusFilter !== 'All') params.append('status', statusFilter);
            if (searchQuery) params.append('q', searchQuery);

            const res = await fetch(`/api/attendance/list?${params.toString()}`);
            const data = await res.json();
            setRecords(data.records || []);
        } catch (err) {
            showToast({ type: 'error', message: 'Could not fetch attendance timings.' });
        } finally {
            setLoading(false);
        }
    }, [dateFilter, statusFilter, searchQuery]);

    useEffect(() => {
        fetchRecords();
    }, [fetchRecords]);

    const handleExportCSV = () => {
        const url = `/api/attendance/export_csv${dateFilter ? `?date=${dateFilter}` : ''}`;
        window.location.href = url;
        showToast({ type: 'success', message: 'Downloading timestamped CSV export...' });
    };

    const handleManualSubmit = async (e) => {
        e.preventDefault();
        try {
            const res = await fetch('/api/attendance/mark_manual', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student_id: manualStudentId,
                    status: manualStatus,
                    remarks: manualRemarks
                })
            });
            const data = await res.json();
            if (data.success) {
                showToast({ type: 'success', message: data.message });
                setIsManualModalOpen(false);
                fetchRecords();
            } else {
                showToast({ type: 'error', message: data.message });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Failed to record manual attendance.' });
        }
    };

    return (
        <div className="space-y-6">
            {/* Header & Actions */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl">
                <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
                        <i className="fa-solid fa-clock-rotate-left text-indigo-400"></i>
                        Student Join & Exit Timings Log
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                        Exact microsecond/second attendance check-in, last seen, and exit timestamps stored in database.
                    </p>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                    <button
                        onClick={handleExportCSV}
                        className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition flex items-center gap-2 shadow-lg shadow-emerald-600/20 cursor-pointer"
                    >
                        <i className="fa-solid fa-file-csv"></i>
                        <span>Export CSV</span>
                    </button>
                    <button
                        onClick={() => setIsManualModalOpen(true)}
                        className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition flex items-center gap-2 border border-slate-700 cursor-pointer"
                    >
                        <i className="fa-solid fa-plus"></i>
                        <span>Manual Entry</span>
                    </button>
                    <button
                        onClick={fetchRecords}
                        className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition cursor-pointer"
                        title="Refresh Table"
                    >
                        <i className="fa-solid fa-arrows-rotate"></i>
                    </button>
                </div>
            </div>

            {/* Filter Bar */}
            <div className="p-4 rounded-xl bg-[#121826] border border-slate-800/80 flex flex-wrap items-center gap-4">
                {/* Search query */}
                <div className="relative flex-1 min-w-[200px]">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                        <i className="fa-solid fa-magnifying-glass text-xs"></i>
                    </div>
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search student name or ID..."
                        className="w-full pl-9 pr-3.5 py-2 bg-[#0b0f19] border border-slate-700/80 rounded-xl text-white text-xs placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    />
                </div>

                {/* Date Filter */}
                <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 font-medium">Date:</span>
                    <input
                        type="date"
                        value={dateFilter}
                        onChange={(e) => setDateFilter(e.target.value)}
                        className="px-3 py-2 bg-[#0b0f19] border border-slate-700/80 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                    />
                    {dateFilter && (
                        <button onClick={() => setDateFilter('')} className="text-xs text-slate-400 hover:text-white" title="Clear Date">
                            <i className="fa-solid fa-xmark"></i>
                        </button>
                    )}
                </div>

                {/* Status Filter */}
                <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400 font-medium">Status:</span>
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="px-3 py-2 bg-[#0b0f19] border border-slate-700/80 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                    >
                        <option value="All">All Statuses</option>
                        <option value="Present">Present</option>
                        <option value="Late">Late</option>
                        <option value="Left Early">Left Early</option>
                        <option value="Drowsy">Drowsy</option>
                    </select>
                </div>
            </div>

            {/* Timings Table */}
            <div className="rounded-2xl bg-[#121826] border border-slate-800/80 overflow-hidden shadow-xl">
                {loading ? (
                    <div className="p-12 text-center text-slate-400">
                        <div className="h-8 w-8 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin mx-auto mb-3"></div>
                        <span className="text-xs font-medium">Loading join and exit records...</span>
                    </div>
                ) : records.length === 0 ? (
                    <div className="p-12 text-center text-slate-400">
                        <i className="fa-solid fa-clipboard-list text-3xl mb-3 text-slate-600"></i>
                        <p className="text-sm font-semibold text-white">No attendance records found.</p>
                        <p className="text-xs text-slate-500 mt-1">Start a classroom session or turn on the camera to detect students.</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                                <tr>
                                    <th className="py-3.5 px-4">Student</th>
                                    <th className="py-3.5 px-4">Student ID</th>
                                    <th className="py-3.5 px-4">Date</th>
                                    <th className="py-3.5 px-4 text-emerald-400">Join Time</th>
                                    <th className="py-3.5 px-4 text-cyan-400">Last Seen</th>
                                    <th className="py-3.5 px-4 text-rose-400">Exit Time</th>
                                    <th className="py-3.5 px-4">Duration</th>
                                    <th className="py-3.5 px-4">Status</th>
                                    <th className="py-3.5 px-4">Attention</th>
                                    <th className="py-3.5 px-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60 font-medium">
                                {records.map((r, idx) => (
                                    <tr key={idx} className="hover:bg-slate-800/30 transition">
                                        <td className="py-3 px-4 font-bold text-white flex items-center gap-2.5">
                                            <div className="h-7 w-7 rounded-full bg-indigo-900/60 text-indigo-300 flex items-center justify-center text-xs">
                                                {r.student_name ? r.student_name[0].toUpperCase() : 'S'}
                                            </div>
                                            <span>{r.student_name}</span>
                                        </td>
                                        <td className="py-3 px-4 font-mono text-slate-400">{r.student_id}</td>
                                        <td className="py-3 px-4 text-slate-300">{r.log_date}</td>
                                        {/* Exact Join Time */}
                                        <td className="py-3 px-4 font-mono text-emerald-300 font-semibold">
                                            {r.join_time || r.check_in_time || '--:--:--'}
                                        </td>
                                        {/* Last Seen Time */}
                                        <td className="py-3 px-4 font-mono text-cyan-300">
                                            {r.last_seen_time || '--:--:--'}
                                        </td>
                                        {/* Exact Exit Time */}
                                        <td className="py-3 px-4 font-mono text-rose-300 font-semibold">
                                            {r.exit_time || '--:--:--'}
                                        </td>
                                        {/* Duration */}
                                        <td className="py-3 px-4 font-mono text-slate-300">
                                            {r.duration_formatted || `${r.duration_seconds || 0}s`}
                                        </td>
                                        {/* Attendance Status Badge */}
                                        <td className="py-3 px-4">
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                                                r.attendance_status === 'Present' || r.status === 'Present' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                                                r.attendance_status === 'Late' || r.status === 'Late' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
                                                r.attendance_status === 'Left Early' ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' :
                                                'bg-slate-700/50 text-slate-300 border-slate-600'
                                            }`}>
                                                {r.attendance_status || r.status || 'Present'}
                                            </span>
                                        </td>
                                        {/* Attention Score */}
                                        <td className="py-3 px-4">
                                            <div className="flex items-center gap-2">
                                                <span className="text-slate-200 font-semibold">{r.attentiveness_avg || 100}%</span>
                                                {r.drowsiness_detected ? (
                                                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold" title="Drowsiness Detected">
                                                        SLEEPY
                                                    </span>
                                                ) : null}
                                            </div>
                                        </td>
                                        {/* Actions */}
                                        <td className="py-3 px-4 text-right">
                                            <button
                                                onClick={async () => {
                                                    await onMarkExit(r.student_id);
                                                    fetchRecords();
                                                }}
                                                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-rose-950/60 hover:text-rose-300 text-slate-300 text-[11px] font-semibold transition inline-flex items-center gap-1 cursor-pointer"
                                                title="Record Student Exit Timestamp"
                                            >
                                                <i className="fa-solid fa-right-from-bracket text-[10px]"></i>
                                                <span>Exit</span>
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Manual Attendance Modal */}
            {isManualModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
                    <div className="w-full max-w-md bg-[#121826] border border-slate-800 rounded-2xl p-6 shadow-2xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-white text-base">Manual Attendance Entry</h3>
                            <button onClick={() => setIsManualModalOpen(false)} className="text-slate-400 hover:text-white">
                                <i className="fa-solid fa-xmark"></i>
                            </button>
                        </div>
                        <form onSubmit={handleManualSubmit} className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                                    Student ID / Roll No
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={manualStudentId}
                                    onChange={(e) => setManualStudentId(e.target.value)}
                                    placeholder="e.g. STU-ESAS-001"
                                    className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                                    Status
                                </label>
                                <select
                                    value={manualStatus}
                                    onChange={(e) => setManualStatus(e.target.value)}
                                    className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                                >
                                    <option value="Present">Present</option>
                                    <option value="Late">Late</option>
                                    <option value="Excused">Excused</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                                    Remarks
                                </label>
                                <input
                                    type="text"
                                    value={manualRemarks}
                                    onChange={(e) => setManualRemarks(e.target.value)}
                                    placeholder="e.g. Verified by Admin"
                                    className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                            <div className="flex justify-end gap-2.5 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsManualModalOpen(false)}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/25 cursor-pointer"
                                >
                                    Save Record
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

// ==========================================
// VIEW 3: CLASS SESSIONS
// ==========================================
function SessionsView({ activeSession, onStartSession, onEndSession, showToast }) {
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [newTitle, setNewTitle] = useState('Machine Learning Lecture');

    const fetchSessions = useCallback(async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/session/list');
            const data = await res.json();
            setSessions(data.sessions || []);
        } catch (err) {
            showToast({ type: 'error', message: 'Failed to fetch sessions.' });
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSessions();
    }, [fetchSessions]);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl">
                <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
                        <i className="fa-solid fa-chalkboard-user text-indigo-400"></i>
                        Classroom Monitoring Sessions
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                        Track live and historical class sessions, session codes, duration, and attendance logs.
                    </p>
                </div>
                <div className="flex items-center gap-2.5">
                    {!activeSession && (
                        <button
                            onClick={() => setIsCreateModalOpen(true)}
                            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition shadow-lg shadow-indigo-600/20 flex items-center gap-2 cursor-pointer"
                        >
                            <i className="fa-solid fa-plus"></i>
                            <span>Start New Session</span>
                        </button>
                    )}
                    <button
                        onClick={fetchSessions}
                        className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition cursor-pointer"
                        title="Refresh"
                    >
                        <i className="fa-solid fa-arrows-rotate"></i>
                    </button>
                </div>
            </div>

            {/* Active Session Highlight Card */}
            {activeSession && (
                <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-950/60 to-purple-950/40 border border-indigo-800/60 shadow-2xl">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                        <div>
                            <div className="flex items-center gap-2 mb-2">
                                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
                                <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">Session Active</span>
                                <span className="text-xs text-indigo-300 font-mono px-2 py-0.5 rounded bg-indigo-900/60">
                                    {activeSession.session_code}
                                </span>
                            </div>
                            <h3 className="text-xl font-black text-white">{activeSession.title}</h3>
                            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 mt-2 font-mono">
                                <span>Start: {activeSession.start_time}</span>
                                <span>•</span>
                                <span className="text-cyan-300 font-bold">Elapsed: {activeSession.elapsed_formatted || '00:00'}</span>
                            </div>
                        </div>

                        <button
                            onClick={onEndSession}
                            className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white font-semibold text-xs transition shadow-lg shadow-rose-600/20 flex items-center gap-2 cursor-pointer"
                        >
                            <i className="fa-solid fa-flag-checkered"></i>
                            <span>End Session & Seal Timings</span>
                        </button>
                    </div>
                </div>
            )}

            {/* Past Sessions List */}
            <div className="rounded-2xl bg-[#121826] border border-slate-800/80 overflow-hidden shadow-xl">
                <div className="p-4 border-b border-slate-800 font-bold text-sm text-white flex items-center gap-2">
                    <i className="fa-solid fa-clock-rotate-left text-slate-400"></i>
                    Past Classroom Sessions History
                </div>

                {loading ? (
                    <div className="p-8 text-center text-xs text-slate-400">Loading sessions...</div>
                ) : sessions.length === 0 ? (
                    <div className="p-8 text-center text-xs text-slate-400">No sessions recorded yet.</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                                <tr>
                                    <th className="py-3 px-4">Session Code</th>
                                    <th className="py-3 px-4">Topic / Title</th>
                                    <th className="py-3 px-4">Start Time</th>
                                    <th className="py-3 px-4">End Time</th>
                                    <th className="py-3 px-4">Duration</th>
                                    <th className="py-3 px-4">Status</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60 font-medium">
                                {sessions.map((s, idx) => (
                                    <tr key={idx} className="hover:bg-slate-800/30 transition">
                                        <td className="py-3 px-4 font-mono font-bold text-indigo-300">{s.session_code}</td>
                                        <td className="py-3 px-4 font-semibold text-white">{s.title}</td>
                                        <td className="py-3 px-4 font-mono text-slate-300">{s.start_time}</td>
                                        <td className="py-3 px-4 font-mono text-slate-300">{s.end_time || 'In Progress'}</td>
                                        <td className="py-3 px-4 font-mono text-slate-300">{s.duration_minutes || 0} mins</td>
                                        <td className="py-3 px-4">
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                                                s.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                                                'bg-slate-700/50 text-slate-400 border-slate-600'
                                            }`}>
                                                {s.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Start Session Modal */}
            {isCreateModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
                    <div className="w-full max-w-md bg-[#121826] border border-slate-800 rounded-2xl p-6 shadow-2xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-white text-base">Start New Class Session</h3>
                            <button onClick={() => setIsCreateModalOpen(false)} className="text-slate-400 hover:text-white">
                                <i className="fa-solid fa-xmark"></i>
                            </button>
                        </div>
                        <form onSubmit={(e) => {
                            e.preventDefault();
                            onStartSession(newTitle);
                            setIsCreateModalOpen(false);
                        }} className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                                    Session Title
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={newTitle}
                                    onChange={(e) => setNewTitle(e.target.value)}
                                    placeholder="Enter class lecture title"
                                    className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                            <div className="flex justify-end gap-2.5 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsCreateModalOpen(false)}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/25 cursor-pointer"
                                >
                                    Start Session
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

// ==========================================
// VIEW 4: STUDENT ROSTER & WEBCAM ENROLLMENT
// ==========================================
function StudentsView({ showToast }) {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isEnrollModalOpen, setIsEnrollModalOpen] = useState(false);
    const [enrollName, setEnrollName] = useState('');
    const [enrollId, setEnrollId] = useState('');
    const [enrollDept, setEnrollDept] = useState('Computer Science');
    const [enrollEmail, setEnrollEmail] = useState('');
    const [enrolling, setEnrolling] = useState(false);

    const fetchStudents = useCallback(async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/students');
            const data = await res.json();
            setStudents(data.students || []);
        } catch (err) {
            showToast({ type: 'error', message: 'Failed to load students roster.' });
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchStudents();
    }, [fetchStudents]);

    const handleEnrollSubmit = async (e) => {
        e.preventDefault();
        setEnrolling(true);
        try {
            const res = await fetch('/api/students/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: enrollName,
                    student_id: enrollId,
                    department: enrollDept,
                    email: enrollEmail
                })
            });
            const data = await res.json();
            if (data.success) {
                showToast({ type: 'success', message: data.message });
                setIsEnrollModalOpen(false);
                setEnrollName('');
                setEnrollId('');
                setEnrollEmail('');
                fetchStudents();
            } else {
                showToast({ type: 'error', message: data.message });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Error capturing student face.' });
        } finally {
            setEnrolling(false);
        }
    };

    const handleDeleteStudent = async (stuId, stuName) => {
        if (!confirm(`Are you sure you want to remove ${stuName}?`)) return;
        try {
            const res = await fetch(`/api/students/${stuId}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                showToast({ type: 'success', message: data.message });
                fetchStudents();
            } else {
                showToast({ type: 'error', message: data.message });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Could not delete student.' });
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4 p-5 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl">
                <div>
                    <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
                        <i className="fa-solid fa-users text-indigo-400"></i>
                        Enrolled Students Directory
                    </h2>
                    <p className="text-xs text-slate-400 mt-1">
                        Biometric facial profiles registered with 128-dimensional SFace embeddings for instant AI recognition.
                    </p>
                </div>
                <div className="flex items-center gap-2.5">
                    <button
                        onClick={() => setIsEnrollModalOpen(true)}
                        className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition shadow-lg shadow-indigo-600/20 flex items-center gap-2 cursor-pointer"
                    >
                        <i className="fa-solid fa-camera"></i>
                        <span>Register Face via Webcam</span>
                    </button>
                    <button
                        onClick={fetchStudents}
                        className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition cursor-pointer"
                        title="Refresh"
                    >
                        <i className="fa-solid fa-arrows-rotate"></i>
                    </button>
                </div>
            </div>

            {/* Students Grid */}
            {loading ? (
                <div className="p-12 text-center text-xs text-slate-400">Loading student directory...</div>
            ) : students.length === 0 ? (
                <div className="p-12 text-center text-slate-400 rounded-2xl bg-[#121826] border border-slate-800">
                    <i className="fa-solid fa-user-xmark text-3xl mb-3 text-slate-600"></i>
                    <p className="text-sm font-semibold text-white">No students currently registered.</p>
                    <p className="text-xs text-slate-500 mt-1">Use the "Register Face via Webcam" button to enroll new students.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {students.map((stu) => (
                        <div key={stu.id} className="p-5 rounded-2xl bg-[#121826] border border-slate-800/80 hover:border-slate-700 transition shadow-lg flex flex-col justify-between">
                            <div>
                                <div className="flex items-start justify-between gap-3 mb-4">
                                    <div className="h-14 w-14 rounded-2xl bg-indigo-950/60 border border-indigo-500/30 overflow-hidden flex items-center justify-center text-indigo-300 font-bold text-xl">
                                        {stu.photo_path ? (
                                            <img
                                                src={`/data/photos/${stu.photo_path}`}
                                                alt={stu.name}
                                                className="h-full w-full object-cover"
                                                onError={(e) => { e.target.style.display = 'none'; }}
                                            />
                                        ) : (
                                            stu.name[0].toUpperCase()
                                        )}
                                    </div>
                                    <button
                                        onClick={() => handleDeleteStudent(stu.id, stu.name)}
                                        className="text-slate-500 hover:text-rose-400 p-1 transition"
                                        title="Remove Student"
                                    >
                                        <i className="fa-solid fa-trash text-xs"></i>
                                    </button>
                                </div>
                                <h3 className="font-bold text-white text-base leading-snug">{stu.name}</h3>
                                <p className="text-xs font-mono text-indigo-400 mt-0.5">{stu.student_id}</p>
                                <p className="text-xs text-slate-400 mt-2">{stu.department || 'Computer Science'}</p>
                                <p className="text-[11px] text-slate-500 truncate">{stu.email || 'No email provided'}</p>
                            </div>

                            <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-400">
                                <span className="flex items-center gap-1 text-emerald-400">
                                    <i className="fa-solid fa-circle-check text-[10px]"></i>
                                    Biometric .npy
                                </span>
                                <span className="font-mono text-slate-500">Active</span>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Webcam Face Enrollment Modal */}
            {isEnrollModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
                    <div className="w-full max-w-md bg-[#121826] border border-slate-800 rounded-2xl p-6 shadow-2xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-white text-base flex items-center gap-2">
                                <i className="fa-solid fa-camera text-indigo-400"></i>
                                Webcam Student Biometric Enrollment
                            </h3>
                            <button onClick={() => setIsEnrollModalOpen(false)} className="text-slate-400 hover:text-white">
                                <i className="fa-solid fa-xmark"></i>
                            </button>
                        </div>
                        <form onSubmit={handleEnrollSubmit} className="space-y-4">
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                                    Student Full Name
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={enrollName}
                                    onChange={(e) => setEnrollName(e.target.value)}
                                    placeholder="e.g. Alex Johnson"
                                    className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                                    Student ID / Roll Number
                                </label>
                                <input
                                    type="text"
                                    required
                                    value={enrollId}
                                    onChange={(e) => setEnrollId(e.target.value)}
                                    placeholder="e.g. STU-CS-2026-042"
                                    className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                                    Department
                                </label>
                                <input
                                    type="text"
                                    value={enrollDept}
                                    onChange={(e) => setEnrollDept(e.target.value)}
                                    placeholder="e.g. Computer Science"
                                    className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                                    Email Address
                                </label>
                                <input
                                    type="email"
                                    value={enrollEmail}
                                    onChange={(e) => setEnrollEmail(e.target.value)}
                                    placeholder="alex@smartclass.edu"
                                    className="w-full px-3.5 py-2.5 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-sm focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-800/40 text-xs text-indigo-300 flex items-start gap-2">
                                <i className="fa-solid fa-lightbulb mt-0.5 text-indigo-400"></i>
                                <span>Ensure the student is facing the webcam directly with good room lighting when clicking capture.</span>
                            </div>

                            <div className="flex justify-end gap-2.5 pt-2">
                                <button
                                    type="button"
                                    onClick={() => setIsEnrollModalOpen(false)}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={enrolling}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/25 flex items-center gap-2 cursor-pointer disabled:opacity-50"
                                >
                                    {enrolling ? (
                                        <>
                                            <div className="h-3.5 w-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                            <span>Extracting Biometrics...</span>
                                        </>
                                    ) : (
                                        <>
                                            <i className="fa-solid fa-camera"></i>
                                            <span>Capture & Enroll Face</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

// ==========================================
// VIEW 5: ANALYTICS & REPORTS
// ==========================================
function AnalyticsView({ dbStats, showToast }) {
    const [analytics, setAnalytics] = useState(null);
    const [summary, setSummary] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchAnalytics = async () => {
            setLoading(true);
            try {
                const [r1, r2] = await Promise.all([
                    fetch('/api/reports/analytics').then(r => r.json()),
                    fetch('/api/reports/summary').then(r => r.json())
                ]);
                setAnalytics(r1);
                setSummary(r2);
            } catch (err) {
                showToast({ type: 'error', message: 'Failed to load analytics.' });
            } finally {
                setLoading(false);
            }
        };
        fetchAnalytics();
    }, []);

    return (
        <div className="space-y-6">
            <div className="p-5 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl">
                <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
                    <i className="fa-solid fa-chart-line text-indigo-400"></i>
                    Classroom Engagement & Turnout Analytics
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                    Turnout percentages, attentiveness metrics, drowsiness alerts, and student performance rankings.
                </p>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-5 rounded-2xl bg-[#121826] border border-slate-800/80">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Today's Turnout</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-black text-white">{Math.min(100, Math.max(0, dbStats?.attendance_rate || 0))}%</span>
                        <span className="text-xs text-emerald-400">({dbStats?.present_today || 0} / {dbStats?.total_students || 0})</span>
                    </div>
                </div>

                <div className="p-5 rounded-2xl bg-[#121826] border border-slate-800/80">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Average Attentiveness</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-black text-indigo-400">{Math.min(100, Math.max(0, dbStats?.avg_attentiveness || 100))}%</span>
                        <span className="text-xs text-slate-400">Overall</span>
                    </div>
                </div>

                <div className="p-5 rounded-2xl bg-[#121826] border border-slate-800/80">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Drowsiness Incidents</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-black text-rose-400">{dbStats?.drowsy_count || 0}</span>
                        <span className="text-xs text-rose-300">Flagged</span>
                    </div>
                </div>

                <div className="p-5 rounded-2xl bg-[#121826] border border-slate-800/80">
                    <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">Total Class Sessions</span>
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-black text-cyan-400">{dbStats?.total_sessions || 0}</span>
                        <span className="text-xs text-slate-400">Conducted</span>
                    </div>
                </div>
            </div>

            {/* Student Performance Ranking Table */}
            <div className="rounded-2xl bg-[#121826] border border-slate-800/80 overflow-hidden shadow-xl">
                <div className="p-4 border-b border-slate-800 font-bold text-sm text-white flex items-center gap-2">
                    <i className="fa-solid fa-trophy text-amber-400"></i>
                    Student Performance & Attendance Summary
                </div>

                {loading ? (
                    <div className="p-8 text-center text-xs text-slate-400">Loading student summaries...</div>
                ) : !summary?.students_summary || summary.students_summary.length === 0 ? (
                    <div className="p-8 text-center text-xs text-slate-400">No records to analyze yet.</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                            <thead className="bg-slate-900/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                                <tr>
                                    <th className="py-3 px-4">Student</th>
                                    <th className="py-3 px-4">Roll ID</th>
                                    <th className="py-3 px-4">Classes Attended</th>
                                    <th className="py-3 px-4">Attendance %</th>
                                    <th className="py-3 px-4">Total Time In Class</th>
                                    <th className="py-3 px-4">Avg Attention</th>
                                    <th className="py-3 px-4">Performance Grade</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/60 font-medium">
                                {summary.students_summary.map((s, idx) => (
                                    <tr key={idx} className="hover:bg-slate-800/30 transition">
                                        <td className="py-3 px-4 font-bold text-white">{s.name}</td>
                                        <td className="py-3 px-4 font-mono text-slate-400">{s.student_id}</td>
                                        <td className="py-3 px-4 text-slate-300">{s.attended_classes} of {s.total_classes}</td>
                                        <td className="py-3 px-4 font-bold text-emerald-400">{Math.min(100, Math.max(0, s.attendance_percentage || 0))}%</td>
                                        <td className="py-3 px-4 font-mono text-slate-300">{s.total_duration_formatted || '0s'}</td>
                                        <td className="py-3 px-4 font-bold text-indigo-400">{Math.min(100, Math.max(0, s.avg_attentiveness || 100))}%</td>
                                        <td className="py-3 px-4">
                                            <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                                                s.grade === 'Excellent' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                                                s.grade === 'Good' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' :
                                                'bg-amber-500/10 text-amber-400 border-amber-500/30'
                                            }`}>
                                                {s.grade}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

// ==========================================
// VIEW 6: MYSQL DATABASE & SETTINGS
// ==========================================
function SettingsView({ dbStats, showToast }) {
    // MySQL form state
    const [host, setHost] = useState('localhost');
    const [port, setPort] = useState(3306);
    const [user, setUser] = useState('root');
    const [password, setPassword] = useState('');
    const [database, setDatabase] = useState('smart_class_db');
    const [testingMysql, setTestingMysql] = useState(false);
    const [savingMysql, setSavingMysql] = useState(false);

    // Thresholds state
    const [cosineThreshold, setCosineThreshold] = useState(0.363);
    const [detectionConfidence, setDetectionConfidence] = useState(0.60);
    const [savingThresholds, setSavingThresholds] = useState(false);

    // Admin profile state
    const [adminName, setAdminName] = useState('Administrator');
    const [adminEmail, setAdminEmail] = useState('admin@smartclass.edu');
    const [adminNewPassword, setAdminNewPassword] = useState('');
    const [savingProfile, setSavingProfile] = useState(false);

    const handleTestMysql = async () => {
        setTestingMysql(true);
        try {
            const res = await fetch('/api/settings/mysql_test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, port, user, password, database })
            });
            const data = await res.json();
            if (data.success) {
                showToast({ type: 'success', message: 'MySQL connection successful! Database verified.' });
            } else {
                showToast({ type: 'error', message: data.message || 'MySQL connection failed.' });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Error communicating with server.' });
        } finally {
            setTestingMysql(false);
        }
    };

    const handleSaveMysql = async (e) => {
        e.preventDefault();
        setSavingMysql(true);
        try {
            const res = await fetch('/api/settings/update_mysql', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ host, port, user, password, database })
            });
            const data = await res.json();
            if (data.success) {
                showToast({ type: 'success', message: data.message });
            } else {
                showToast({ type: 'error', message: data.message });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Could not save MySQL configuration.' });
        } finally {
            setSavingMysql(false);
        }
    };

    const handleSaveThresholds = async (e) => {
        e.preventDefault();
        setSavingThresholds(true);
        try {
            const res = await fetch('/api/settings/update_thresholds', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    cosine_threshold: cosineThreshold,
                    detection_confidence: detectionConfidence
                })
            });
            const data = await res.json();
            if (data.success) {
                showToast({ type: 'success', message: data.message });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Failed to update vision sensitivity.' });
        } finally {
            setSavingThresholds(false);
        }
    };

    const handleSaveProfile = async (e) => {
        e.preventDefault();
        setSavingProfile(true);
        try {
            const res = await fetch('/api/settings/update_admin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    full_name: adminName,
                    email: adminEmail,
                    new_password: adminNewPassword
                })
            });
            const data = await res.json();
            if (data.success) {
                showToast({ type: 'success', message: data.message });
                setAdminNewPassword('');
            } else {
                showToast({ type: 'error', message: data.message });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Could not update profile.' });
        } finally {
            setSavingProfile(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="p-5 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl">
                <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
                    <i className="fa-solid fa-sliders text-indigo-400"></i>
                    System Configuration & Database
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                    Manage MySQL database credentials, vision recognition thresholds, and administrator credentials.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* MySQL Database Configuration */}
                <div className="p-6 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="font-bold text-white text-sm flex items-center gap-2">
                            <i className="fa-solid fa-database text-indigo-400"></i>
                            MySQL Server Connection
                        </h3>
                        <span className={`text-[10px] px-2.5 py-1 rounded-full font-bold uppercase tracking-wider border ${
                            dbStats?.active_db === 'mysql'
                                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                        }`}>
                            {dbStats?.active_db === 'mysql' ? 'MySQL Active' : 'SQLite Fallback'}
                        </span>
                    </div>

                    <p className="text-xs text-slate-400">
                        Primary storage for student biometrics, class sessions, and timestamped attendance logs.
                    </p>

                    <form onSubmit={handleSaveMysql} className="space-y-3.5">
                        <div className="grid grid-cols-3 gap-3">
                            <div className="col-span-2">
                                <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">Host</label>
                                <input
                                    type="text"
                                    value={host}
                                    onChange={(e) => setHost(e.target.value)}
                                    className="w-full px-3 py-2 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">Port</label>
                                <input
                                    type="number"
                                    value={port}
                                    onChange={(e) => setPort(e.target.value)}
                                    className="w-full px-3 py-2 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">Username</label>
                                <input
                                    type="text"
                                    value={user}
                                    onChange={(e) => setUser(e.target.value)}
                                    className="w-full px-3 py-2 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                            <div>
                                <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">Password</label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    className="w-full px-3 py-2 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">Database Name</label>
                            <input
                                type="text"
                                value={database}
                                onChange={(e) => setDatabase(e.target.value)}
                                className="w-full px-3 py-2 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                            />
                        </div>

                        <div className="flex items-center justify-end gap-2.5 pt-2">
                            <button
                                type="button"
                                onClick={handleTestMysql}
                                disabled={testingMysql}
                                className="px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold transition border border-slate-700 cursor-pointer disabled:opacity-50"
                            >
                                {testingMysql ? 'Testing...' : 'Test Connection'}
                            </button>
                            <button
                                type="submit"
                                disabled={savingMysql}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 cursor-pointer disabled:opacity-50"
                            >
                                {savingMysql ? 'Saving...' : 'Save & Connect'}
                            </button>
                        </div>
                    </form>
                </div>

                {/* Vision AI Sensitivity Thresholds */}
                <div className="p-6 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl space-y-4">
                    <h3 className="font-bold text-white text-sm flex items-center gap-2">
                        <i className="fa-solid fa-eye text-indigo-400"></i>
                        Vision & Recognition Sensitivity
                    </h3>
                    <p className="text-xs text-slate-400">
                        Calibrate OpenCV SFace cosine similarity matching threshold and YuNet face detection confidence.
                    </p>

                    <form onSubmit={handleSaveThresholds} className="space-y-4 pt-1">
                        <div>
                            <div className="flex justify-between text-xs mb-1">
                                <span className="font-semibold text-slate-300">SFace Cosine Similarity Threshold</span>
                                <span className="font-mono text-indigo-400 font-bold">{cosineThreshold}</span>
                            </div>
                            <input
                                type="range"
                                min="0.20"
                                max="0.60"
                                step="0.005"
                                value={cosineThreshold}
                                onChange={(e) => setCosineThreshold(parseFloat(e.target.value))}
                                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                            />
                            <span className="text-[11px] text-slate-500 block mt-1">Recommended: 0.363 for high-precision facial biometric verification.</span>
                        </div>

                        <div>
                            <div className="flex justify-between text-xs mb-1">
                                <span className="font-semibold text-slate-300">YuNet Detection Confidence</span>
                                <span className="font-mono text-indigo-400 font-bold">{detectionConfidence}</span>
                            </div>
                            <input
                                type="range"
                                min="0.30"
                                max="0.90"
                                step="0.05"
                                value={detectionConfidence}
                                onChange={(e) => setDetectionConfidence(parseFloat(e.target.value))}
                                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                            />
                            <span className="text-[11px] text-slate-500 block mt-1">Higher values prevent false positive face detections in complex room lighting.</span>
                        </div>

                        <div className="flex justify-end pt-3">
                            <button
                                type="submit"
                                disabled={savingThresholds}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 cursor-pointer disabled:opacity-50"
                            >
                                {savingThresholds ? 'Updating...' : 'Update Thresholds'}
                            </button>
                        </div>
                    </form>
                </div>

                {/* Admin Profile & Password Management */}
                <div className="lg:col-span-2 p-6 rounded-2xl bg-[#121826] border border-slate-800/80 shadow-xl space-y-4">
                    <h3 className="font-bold text-white text-sm flex items-center gap-2">
                        <i className="fa-solid fa-lock text-indigo-400"></i>
                        Administrator Account & Security
                    </h3>

                    <form onSubmit={handleSaveProfile} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">Full Name</label>
                            <input
                                type="text"
                                value={adminName}
                                onChange={(e) => setAdminName(e.target.value)}
                                className="w-full px-3 py-2 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                        <div>
                            <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">Email</label>
                            <input
                                type="email"
                                value={adminEmail}
                                onChange={(e) => setAdminEmail(e.target.value)}
                                className="w-full px-3 py-2 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                        <div>
                            <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">New Password (Optional)</label>
                            <input
                                type="password"
                                value={adminNewPassword}
                                onChange={(e) => setAdminNewPassword(e.target.value)}
                                placeholder="Leave blank to keep current"
                                className="w-full px-3 py-2 bg-[#0b0f19] border border-slate-700 rounded-xl text-white text-xs focus:outline-none focus:border-indigo-500"
                            />
                        </div>

                        <div className="sm:col-span-3 flex justify-end pt-2">
                            <button
                                type="submit"
                                disabled={savingProfile}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-lg shadow-indigo-600/20 cursor-pointer disabled:opacity-50"
                            >
                                {savingProfile ? 'Saving...' : 'Update Admin Credentials'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}

// ==========================================
// MAIN ROOT APP COMPONENT
// ==========================================
function App() {
    const [admin, setAdmin] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [checkingAuth, setCheckingAuth] = useState(true);
    const [activeTab, setActiveTab] = useState('monitor');
    const [activeSession, setActiveSession] = useState(null);
    const [telemetry, setTelemetry] = useState(null);
    const [dbStats, setDbStats] = useState(null);
    const [serverTime, setServerTime] = useState('');
    const [toast, setToast] = useState(null);

    const showToast = useCallback((toastObj) => {
        setToast(toastObj);
        setTimeout(() => setToast(null), 4000);
    }, []);

    // 1. Check current admin session on mount
    useEffect(() => {
        const checkAuth = async () => {
            try {
                const res = await fetch('/api/auth/check');
                const data = await res.json();
                if (data.authenticated) {
                    setIsAuthenticated(true);
                    setAdmin(data.admin);
                }
            } catch (err) {
                console.error("Auth check failed:", err);
            } finally {
                setCheckingAuth(false);
            }
        };
        checkAuth();
    }, []);

    // 2. Poll live telemetry, active session, and server time
    useEffect(() => {
        if (!isAuthenticated) return;

        const pollStats = async () => {
            try {
                const res = await fetch('/api/live_stats');
                if (res.ok) {
                    const data = await res.json();
                    setTelemetry(data.telemetry);
                    setDbStats(data.db_stats);
                    setServerTime(data.server_time);
                    if (data.db_stats?.active_session) {
                        setActiveSession(data.db_stats.active_session);
                    } else {
                        setActiveSession(null);
                    }
                }
            } catch (err) {
                // Ignore network blips in background polling
            }
        };

        pollStats();
        const interval = setInterval(pollStats, 1500);
        return () => clearInterval(interval);
    }, [isAuthenticated]);

    // Handle Admin Session Start
    const handleStartSession = async (title) => {
        try {
            const res = await fetch('/api/session/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title })
            });
            const data = await res.json();
            if (data.success) {
                setActiveSession(data.session);
                showToast({ type: 'success', message: data.message });
            } else {
                showToast({ type: 'error', message: data.message });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Failed to start class session.' });
        }
    };

    // Handle Admin Session End
    const handleEndSession = async () => {
        if (!confirm("Are you sure you want to end this class session? All students' exit timings and total attendance duration will be permanently sealed.")) {
            return;
        }

        try {
            const res = await fetch('/api/session/end', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: activeSession?.id })
            });
            const data = await res.json();
            if (data.success) {
                setActiveSession(null);
                showToast({ type: 'success', message: data.message });
            } else {
                showToast({ type: 'error', message: data.message });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Error ending session.' });
        }
    };

    // Handle Student Exit Timestamp Recording
    const handleMarkExit = async (studentId) => {
        try {
            const res = await fetch('/api/attendance/mark_exit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    student_id: studentId,
                    session_id: activeSession?.id
                })
            });
            const data = await res.json();
            if (data.success) {
                showToast({ type: 'success', message: data.message });
            } else {
                showToast({ type: 'error', message: data.message });
            }
        } catch (err) {
            showToast({ type: 'error', message: 'Failed to record student exit timing.' });
        }
    };

    // Handle Logout
    const handleLogout = async () => {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
        } finally {
            setIsAuthenticated(false);
            setAdmin(null);
            showToast({ type: 'info', message: 'Signed out successfully.' });
        }
    };

    if (checkingAuth) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-[#0b0f19] text-center p-6">
                <div className="h-10 w-10 border-2 border-indigo-500/20 border-t-indigo-500 rounded-full animate-spin"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return (
            <>
                <AdminLogin onLoginSuccess={(adminUser) => {
                    setIsAuthenticated(true);
                    setAdmin(adminUser);
                    showToast({ type: 'success', message: `Welcome back, ${adminUser.name || 'Admin'}!` });
                }} />
                <Toast toast={toast} onClose={() => setToast(null)} />
            </>
        );
    }

    return (
        <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col">
            {/* Top Navbar */}
            <Navbar
                admin={admin}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                onLogout={handleLogout}
                activeSession={activeSession}
                dbStats={dbStats}
                serverTime={serverTime}
            />

            {/* Main Tab Content */}
            <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">
                {activeTab === 'monitor' && (
                    <MonitorView
                        activeSession={activeSession}
                        telemetry={telemetry}
                        dbStats={dbStats}
                        serverTime={serverTime}
                        onStartSession={handleStartSession}
                        onEndSession={handleEndSession}
                        onMarkExit={handleMarkExit}
                        showToast={showToast}
                    />
                )}

                {activeTab === 'attendance' && (
                    <AttendanceView
                        onMarkExit={handleMarkExit}
                        showToast={showToast}
                    />
                )}

                {activeTab === 'sessions' && (
                    <SessionsView
                        activeSession={activeSession}
                        onStartSession={handleStartSession}
                        onEndSession={handleEndSession}
                        showToast={showToast}
                    />
                )}

                {activeTab === 'students' && (
                    <StudentsView
                        showToast={showToast}
                    />
                )}

                {activeTab === 'analytics' && (
                    <AnalyticsView
                        dbStats={dbStats}
                        showToast={showToast}
                    />
                )}

                {activeTab === 'settings' && (
                    <SettingsView
                        dbStats={dbStats}
                        showToast={showToast}
                    />
                )}
            </main>

            {/* Toast Alerts */}
            <Toast toast={toast} onClose={() => setToast(null)} />
        </div>
    );
}

// Render React App to DOM
const rootElement = document.getElementById('root');
if (rootElement) {
    const root = ReactDOM.createRoot(rootElement);
    root.render(<App />);
}
