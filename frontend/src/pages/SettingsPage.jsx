import React, { useEffect, useState } from "react";
import { Check, Shield, ToggleLeft, ToggleRight } from "lucide-react";
import { getPermissions, updatePermissions } from "../api/permissions";
import { Navbar } from "../components/Navbar";

export const SettingsPage = () => {
  const [permissions, setPermissions] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingField, setUpdatingField] = useState(null);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const loadPermissions = async () => {
    try {
      const data = await getPermissions();
      setPermissions(data);
    } catch (err) {
      console.error(err);
      setErrorMsg("Failed to load user permissions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPermissions();
  }, []);

  const handleToggle = async (field) => {
    if (!permissions) return;
    setUpdatingField(field);
    setSuccessMsg("");
    setErrorMsg("");

    const newValue = !permissions[field];
    try {
      const updated = await updatePermissions({ [field]: newValue });
      setPermissions(updated);
      setSuccessMsg(`Updated ${field.replace("_", " ")} successfully.`);
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (err) {
      console.error(err);
      setErrorMsg("Failed to update setting. Please try again.");
    } finally {
      setUpdatingField(null);
    }
  };

  const featureItems = [
    {
      field: "app_tracking",
      title: "Desktop Application Tracking",
      description: "Allows the desktop agent to track active application sessions (e.g. VS Code, Slack, Chrome).",
    },
    {
      field: "browser_tracking",
      title: "Browser Navigation Tracking",
      description: "Allows the Chrome extension to record visited URLs and domain analytics.",
    },
    {
      field: "youtube_tracking",
      title: "YouTube Video Tracking",
      description: "Tracks detailed video titles, video IDs, and watched duration on YouTube.",
    },
  ];

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-main)" }}>
      <Navbar />

      <main className="container animate-fade-in" style={{ maxWidth: "800px" }}>
        <div style={{ marginBottom: "28px" }}>
          <h1 style={{ fontSize: "2rem", marginBottom: "4px" }}>Tracking Permissions & Settings</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            Control which automated activity streams are captured and logged to your private dashboard.
          </p>
        </div>

        {successMsg && (
          <div style={{
            padding: "12px 16px",
            background: "rgba(16, 185, 129, 0.15)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "var(--radius-md)",
            color: "#34D399",
            fontSize: "0.85rem",
            marginBottom: "20px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}>
            <Check size={16} />
            <span>{successMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div style={{
            padding: "12px 16px",
            background: "rgba(244, 63, 94, 0.15)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: "var(--radius-md)",
            color: "#FB7185",
            fontSize: "0.85rem",
            marginBottom: "20px",
          }}>
            {errorMsg}
          </div>
        )}

        <div className="glass-card" style={{ padding: "28px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "24px", paddingBottom: "16px", borderBottom: "1px solid var(--border-subtle)" }}>
            <Shield size={22} color="var(--primary)" />
            <div>
              <h2 style={{ fontSize: "1.2rem" }}>Privacy & Agent Control</h2>
              <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                When a tracking feature is OFF, incoming data from extensions or agents is rejected by the backend.
              </p>
            </div>
          </div>

          {loading ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div className="skeleton" style={{ height: "64px" }} />
              <div className="skeleton" style={{ height: "64px" }} />
              <div className="skeleton" style={{ height: "64px" }} />
            </div>
          ) : permissions ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {featureItems.map((item) => {
                const isEnabled = permissions[item.field];
                const isUpdating = updatingField === item.field;

                return (
                  <div
                    key={item.field}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "16px 20px",
                      background: "rgba(255, 255, 255, 0.03)",
                      border: "1px solid var(--border-subtle)",
                      borderRadius: "var(--radius-md)",
                    }}
                  >
                    <div style={{ maxWidth: "80%" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                        <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>{item.title}</span>
                        <span className={`badge ${isEnabled ? "badge-emerald" : "badge-purple"}`} style={{ fontSize: "0.65rem" }}>
                          {isEnabled ? "ACTIVE" : "DISABLED"}
                        </span>
                      </div>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                        {item.description}
                      </p>
                    </div>

                    <button
                      onClick={() => handleToggle(item.field)}
                      disabled={isUpdating}
                      style={{
                        background: "transparent",
                        border: "none",
                        cursor: isUpdating ? "not-allowed" : "pointer",
                        color: isEnabled ? "var(--accent-emerald)" : "var(--text-muted)",
                        padding: "6px",
                        display: "flex",
                        alignItems: "center",
                        transition: "color 0.2s",
                      }}
                      title={isEnabled ? "Click to disable" : "Click to enable"}
                    >
                      {isEnabled ? (
                        <ToggleRight size={38} />
                      ) : (
                        <ToggleLeft size={38} />
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
};
