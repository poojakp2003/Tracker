import React, { useEffect, useState } from "react";
import {
  Activity,
  Calendar,
  Clock,
  Compass,
  ExternalLink,
  Flame,
  Globe,
  Layers,
  RefreshCw,
  Video,
} from "lucide-react";
import {
  getDashboardApps,
  getDashboardBrowser,
  getDashboardSummary,
  getDashboardYouTube,
} from "../api/dashboard";
import { Navbar } from "../components/Navbar";
import { RangeSelector } from "../components/RangeSelector";
import { StatCard } from "../components/StatCard";

export const DashboardPage = () => {
  const [range, setRange] = useState("7d");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState(null);
  const [appsData, setAppsData] = useState(null);
  const [browserData, setBrowserData] = useState(null);
  const [youtubeData, setYoutubeData] = useState(null);
  const [error, setError] = useState("");

  const fetchData = async (isManualRefresh = false) => {
    if (isManualRefresh) setRefreshing(true);
    setError("");

    try {
      const [summaryRes, appsRes, browserRes, ytRes] = await Promise.all([
        getDashboardSummary(),
        getDashboardApps(range),
        getDashboardBrowser(range),
        getDashboardYouTube(range),
      ]);

      setSummary(summaryRes);
      setAppsData(appsRes);
      setBrowserData(browserRes);
      setYoutubeData(ytRes);
    } catch (err) {
      console.error("Dashboard fetch failed:", err);
      setError("Failed to fetch dashboard data. Please ensure the backend is running.");
    } finally {
      setLoading(false);
      if (isManualRefresh) setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [range]);

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-main)" }}>
      <Navbar />

      <main className="container animate-fade-in">
        {/* Top bar: Title & Range Selector */}
        <div style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "16px",
          marginBottom: "28px",
        }}>
          <div>
            <h1 style={{ fontSize: "2rem", marginBottom: "4px" }}>Activity Dashboard</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
              Overview of your application focus, web navigation, and video learning
            </p>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <RangeSelector currentRange={range} onSelectRange={setRange} />
            <button
              onClick={() => fetchData(true)}
              disabled={refreshing}
              className="btn btn-secondary"
              style={{ padding: "8px 12px" }}
              title="Refresh metrics"
            >
              <RefreshCw size={15} style={{ animation: refreshing ? "spin 1s linear infinite" : "none" }} />
            </button>
          </div>
        </div>

        {error && (
          <div style={{
            padding: "14px 18px",
            background: "rgba(244, 63, 94, 0.15)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            borderRadius: "var(--radius-md)",
            color: "#FB7185",
            fontSize: "0.9rem",
            marginBottom: "24px",
          }}>
            {error}
          </div>
        )}

        {/* 1. Summary Metrics Cards */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "20px",
          marginBottom: "32px",
        }}>
          <StatCard
            title="Today"
            value={summary ? summary.today_formatted : "..."}
            subtitle="Active tracked duration"
            icon={Flame}
            color="#06B6D4"
          />
          <StatCard
            title="This Week (7d)"
            value={summary ? summary.week_formatted : "..."}
            subtitle="Aggregated time"
            icon={Calendar}
            color="#8B5CF6"
          />
          <StatCard
            title="This Month (30d)"
            value={summary ? summary.month_formatted : "..."}
            subtitle="Aggregated time"
            icon={Clock}
            color="#10B981"
          />
          <StatCard
            title="Total Sessions"
            value={summary ? `${summary.total_app_sessions} sessions` : "..."}
            subtitle={`${summary ? summary.total_browser_visits : 0} web visits`}
            icon={Activity}
            color="#F59E0B"
          />
        </div>

        {/* 2. Main Visual Grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(450px, 1fr))",
          gap: "24px",
        }}>
          {/* Apps Usage Card */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "8px",
                  background: "rgba(6, 182, 212, 0.15)",
                  color: "#22D3EE",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}>
                  <Layers size={18} />
                </div>
                <div>
                  <h2 style={{ fontSize: "1.15rem" }}>Application Usage</h2>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                    Total active time: {appsData ? appsData.total_duration_formatted : "0 mins"}
                  </p>
                </div>
              </div>
              <span className="badge badge-cyan">{range.toUpperCase()}</span>
            </div>

            {loading ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div className="skeleton" style={{ height: "42px" }} />
                <div className="skeleton" style={{ height: "42px" }} />
                <div className="skeleton" style={{ height: "42px" }} />
              </div>
            ) : appsData && appsData.items.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                {appsData.items.map((app, idx) => (
                  <div key={idx} style={{
                    padding: "12px 14px",
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                      <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>{app.app_name}</span>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>{app.duration_formatted}</span>
                        <span style={{ color: "var(--primary)", fontWeight: 600, fontSize: "0.85rem" }}>{app.percentage}%</span>
                      </div>
                    </div>
                    {/* Progress Bar */}
                    <div style={{
                      width: "100%",
                      height: "6px",
                      background: "rgba(255, 255, 255, 0.08)",
                      borderRadius: "9999px",
                      overflow: "hidden",
                    }}>
                      <div style={{
                        width: `${Math.min(Math.max(app.percentage, 2), 100)}%`,
                        height: "100%",
                        background: idx === 0 ? "var(--primary)" : idx === 1 ? "var(--accent-purple)" : "var(--accent-emerald)",
                        borderRadius: "9999px",
                        transition: "width 0.4s ease",
                      }} />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "36px 12px", color: "var(--text-muted)", fontSize: "0.9rem" }}>
                No application activity recorded for this time range.
              </div>
            )}
          </div>

          {/* Browser Activity Card */}
          <div className="glass-card" style={{ padding: "24px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "8px",
                  background: "rgba(16, 185, 129, 0.15)",
                  color: "#34D399",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}>
                  <Globe size={18} />
                </div>
                <div>
                  <h2 style={{ fontSize: "1.15rem" }}>Browser Domains</h2>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                    {browserData ? `${browserData.total_visits} total page visits` : "Web visits"}
                  </p>
                </div>
              </div>
              <span className="badge badge-emerald">{range.toUpperCase()}</span>
            </div>

            {loading ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div className="skeleton" style={{ height: "42px" }} />
                <div className="skeleton" style={{ height: "42px" }} />
                <div className="skeleton" style={{ height: "42px" }} />
              </div>
            ) : browserData && browserData.items.length > 0 ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                {browserData.items.map((b, idx) => (
                  <div key={idx} style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    padding: "10px 14px",
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                  }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <Compass size={16} color="var(--accent-emerald)" />
                      <span style={{ fontWeight: 500, fontSize: "0.9rem" }}>{b.domain}</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <span style={{ color: "var(--text-secondary)", fontSize: "0.85rem" }}>
                        {b.visit_count} {b.visit_count === 1 ? "visit" : "visits"}
                      </span>
                      <span className="badge badge-emerald" style={{ fontSize: "0.7rem" }}>
                        {b.percentage}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "36px 12px", color: "var(--text-muted)", fontSize: "0.9rem" }}>
                No browser domains logged in this period.
              </div>
            )}
          </div>

          {/* YouTube Activity Card */}
          <div className="glass-card" style={{ padding: "24px", gridColumn: "1 / -1" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <div style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "8px",
                  background: "rgba(244, 63, 94, 0.15)",
                  color: "#FB7185",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}>
                  <Video size={18} />
                </div>
                <div>
                  <h2 style={{ fontSize: "1.15rem" }}>YouTube Video Activity</h2>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                    Total watched: {youtubeData ? youtubeData.total_watched_formatted : "0 mins"}
                  </p>
                </div>
              </div>
              <span className="badge badge-purple">{range.toUpperCase()}</span>
            </div>

            {loading ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                <div className="skeleton" style={{ height: "48px" }} />
                <div className="skeleton" style={{ height: "48px" }} />
              </div>
            ) : youtubeData && youtubeData.items.length > 0 ? (
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
                gap: "14px",
              }}>
                {youtubeData.items.map((yt, idx) => (
                  <div key={idx} style={{
                    padding: "14px 16px",
                    background: "rgba(255, 255, 255, 0.03)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-md)",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    gap: "10px",
                  }}>
                    <div>
                      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "8px" }}>
                        <span style={{ fontWeight: 600, fontSize: "0.95rem" }}>{yt.video_title}</span>
                        <a href={yt.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--text-muted)" }}>
                          <ExternalLink size={15} />
                        </a>
                      </div>
                      <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>ID: {yt.video_id}</span>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: "8px", borderTop: "1px solid var(--border-subtle)" }}>
                      <span style={{ color: "#F43F5E", fontWeight: 600, fontSize: "0.85rem" }}>
                        {yt.watched_formatted}
                      </span>
                      <span style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                        {yt.watch_count} {yt.watch_count === 1 ? "session" : "sessions"}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "36px 12px", color: "var(--text-muted)", fontSize: "0.9rem" }}>
                No YouTube activity captured for this time period.
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};
