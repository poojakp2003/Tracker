import React, { useEffect, useState } from "react";
import {
  AlertCircle,
  AppWindow,
  CheckCircle2,
  Globe,
  Loader2,
  RefreshCw,
  Youtube,
  Zap,
} from "lucide-react";
import { getPermissions, updatePermissions } from "../api/permissions";
import { Navbar } from "../components/Navbar";

export const SettingsPage = () => {
  const [permissions, setPermissions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingField, setUpdatingField] = useState(null);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadPermissions = async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) setIsRefreshing(true);
    setErrorMsg("");
    try {
      // React -> GET /permissions -> FastAPI -> Database
      const data = await getPermissions();
      setPermissions(data);
    } catch (err) {
      console.error("Failed to load permissions:", err);
      setErrorMsg("Failed to retrieve tracking permissions from server. Please retry.");
    } finally {
      setLoading(false);
      if (showRefreshIndicator) {
        setTimeout(() => setIsRefreshing(false), 400);
      }
    }
  };

  useEffect(() => {
    loadPermissions();
  }, []);

  const handleToggle = async (field, currentVal, label) => {
    if (updatingField) return;

    setUpdatingField(field);
    setSuccessMsg("");
    setErrorMsg("");

    const newValue = !currentVal;

    try {
      // React -> PUT /permissions -> FastAPI -> PostgreSQL
      const updated = await updatePermissions({ [field]: newValue });
      setPermissions(updated);
      setSuccessMsg(`${label} switched ${newValue ? "[ ON ]" : "[ OFF ]"} successfully.`);
      setTimeout(() => setSuccessMsg(""), 3500);
    } catch (err) {
      console.error(`Failed to update ${field}:`, err);
      setErrorMsg(`Failed to update ${label}. Please try again.`);
    } finally {
      setUpdatingField(null);
    }
  };

  const trackingOptions = [
    {
      id: "app_tracking",
      title: "App Tracking",
      description:
        "Monitors desktop applications in use and session durations (e.g. IDEs, terminal, productivity tools).",
      icon: AppWindow,
      color: "var(--primary)",
      colorBg: "rgba(6, 182, 212, 0.12)",
    },
    {
      id: "browser_tracking",
      title: "Browser Tracking",
      description:
        "Logs visited websites and active domain navigation via the browser extension watcher.",
      icon: Globe,
      color: "var(--accent-purple)",
      colorBg: "rgba(139, 92, 246, 0.12)",
    },
    {
      id: "youtube_tracking",
      title: "YouTube Tracking",
      description:
        "Analyzes YouTube video titles, video IDs, and playback time metrics for video consumption.",
      icon: Youtube,
      color: "var(--accent-rose)",
      colorBg: "rgba(244, 63, 94, 0.12)",
    },
  ];

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-main)" }}>
      <Navbar />

      <main className="container animate-fade-in" style={{ maxWidth: "860px", paddingBottom: "60px" }}>
        {/* Page Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
              <h1 style={{ fontSize: "2rem" }}>Settings</h1>
              <span className="badge badge-cyan" style={{ fontSize: "0.7rem" }}>
                Live Control
              </span>
            </div>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.92rem" }}>
              Manage automated data collection permissions and agent ingestion policies.
            </p>
          </div>

          <button
            onClick={() => loadPermissions(true)}
            disabled={loading || isRefreshing}
            className="btn btn-secondary"
            style={{ fontSize: "0.85rem", padding: "8px 14px", display: "flex", alignItems: "center", gap: "6px" }}
            title="Reload current permissions from database"
          >
            <RefreshCw size={14} className={isRefreshing ? "animate-spin" : ""} />
            <span>Sync</span>
          </button>
        </div>

        {/* Feedback Messages */}
        {successMsg && (
          <div className="toast-banner toast-success">
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <CheckCircle2 size={18} />
              <span>{successMsg}</span>
            </div>
            <span style={{ fontSize: "0.75rem", opacity: 0.8 }}>Saved to PostgreSQL</span>
          </div>
        )}

        {errorMsg && (
          <div className="toast-banner toast-error">
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <AlertCircle size={18} />
              <span>{errorMsg}</span>
            </div>
            <button
              onClick={() => loadPermissions()}
              style={{
                background: "transparent",
                border: "none",
                color: "#FB7185",
                fontWeight: 600,
                cursor: "pointer",
                textDecoration: "underline",
                fontSize: "0.8rem",
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* Tracking Settings Main Card */}
        <div className="glass-card" style={{ padding: "32px", marginBottom: "24px" }}>
          {/* Section Header */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "28px",
              paddingBottom: "18px",
              borderBottom: "1px solid var(--border-subtle)",
              flexWrap: "wrap",
              gap: "12px",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                <Zap size={20} color="var(--primary)" />
                <h2 style={{ fontSize: "1.35rem" }}>Tracking Settings</h2>
              </div>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.86rem" }}>
                Real-time switches for desktop agent, browser extension, and YouTube tracking.
              </p>
            </div>
          </div>

          {/* Settings Items */}
          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div className="skeleton" style={{ height: "80px" }} />
              <div className="skeleton" style={{ height: "80px" }} />
              <div className="skeleton" style={{ height: "80px" }} />
            </div>
          ) : permissions ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {trackingOptions.map((opt) => {
                const IconComponent = opt.icon;
                const isEnabled = Boolean(permissions[opt.id]);
                const isUpdating = updatingField === opt.id;

                return (
                  <div
                    key={opt.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "18px 22px",
                      background: "rgba(255, 255, 255, 0.025)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                      transition: "all 0.2s ease",
                      gap: "16px",
                    }}
                  >
                    {/* Left: Icon and Labels */}
                    <div style={{ display: "flex", alignItems: "flex-start", gap: "16px", maxWidth: "75%" }}>
                      <div
                        style={{
                          width: "42px",
                          height: "42px",
                          borderRadius: "10px",
                          backgroundColor: opt.colorBg,
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          flexShrink: 0,
                          marginTop: "2px",
                        }}
                      >
                        <IconComponent size={20} color={opt.color} />
                      </div>

                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                          <span style={{ fontWeight: 600, fontSize: "1.05rem", color: "var(--text-primary)" }}>
                            {opt.title}
                          </span>
                        </div>
                        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", lineHeight: "1.4" }}>
                          {opt.description}
                        </p>
                      </div>
                    </div>

                    {/* Right: Explicit [ ON ] / [ OFF ] Toggle Button */}
                    <button
                      onClick={() => handleToggle(opt.id, isEnabled, opt.title)}
                      disabled={isUpdating}
                      className={`tracking-switch-btn ${isEnabled ? "on" : "off"}`}
                      aria-label={`Toggle ${opt.title}`}
                      title={isEnabled ? `Click to switch ${opt.title} OFF` : `Click to switch ${opt.title} ON`}
                    >
                      {isUpdating ? (
                        <>
                          <Loader2 size={14} className="animate-spin" />
                          <span>SAVING...</span>
                        </>
                      ) : (
                        <>
                          <span className={`tracking-dot ${isEnabled ? "on" : "off"}`} />
                          <span>{isEnabled ? "[ ON ]" : "[ OFF ]"}</span>
                        </>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "30px", color: "var(--text-muted)" }}>
              No permission record found. Click Refresh to initialize.
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
export default SettingsPage;
