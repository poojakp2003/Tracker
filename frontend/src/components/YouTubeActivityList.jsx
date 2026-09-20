import React, { useState } from "react";
import { ExternalLink, Play, Search, Video } from "lucide-react";

export const YouTubeActivityList = ({ items = [], loading = false, totalWatchedFormatted = "0 mins" }) => {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredItems = items.filter((item) =>
    item.video_title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="glass-card" style={{ padding: "24px", display: "flex", flexDirection: "column" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: "12px",
          marginBottom: "18px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
          <div
            style={{
              width: "34px",
              height: "34px",
              borderRadius: "8px",
              background: "rgba(244, 63, 94, 0.15)",
              color: "#FB7185",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Video size={18} />
          </div>
          <div style={{ minWidth: 0 }}>
            <h2 style={{ fontSize: "1.15rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              YouTube Learning Activity
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              Watched tutorials, guides, and courses • Total: {totalWatchedFormatted}
            </p>
          </div>
        </div>

        {/* Search input */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "rgba(15, 23, 42, 0.6)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "var(--radius-sm)",
            padding: "6px 12px",
            flexShrink: 0,
          }}
        >
          <Search size={14} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search tutorials..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: "var(--text-primary)",
              fontSize: "0.85rem",
              width: "140px",
            }}
          />
        </div>
      </div>

      {/* YouTube List Content */}
      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div className="skeleton" style={{ height: "48px" }} />
          <div className="skeleton" style={{ height: "48px" }} />
          <div className="skeleton" style={{ height: "48px" }} />
        </div>
      ) : filteredItems.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          {filteredItems.map((yt, idx) => (
            <div
              key={yt.video_id || idx}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 16px",
                background: "rgba(255, 255, 255, 0.025)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-md)",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)";
                e.currentTarget.style.borderColor = "rgba(244, 63, 94, 0.3)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.025)";
                e.currentTarget.style.borderColor = "var(--border-subtle)";
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px", minWidth: 0 }}>
                <div
                  style={{
                    width: "28px",
                    height: "28px",
                    borderRadius: "6px",
                    background: "rgba(244, 63, 94, 0.12)",
                    color: "#F43F5E",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <Play size={14} fill="#F43F5E" />
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span
                      style={{
                        fontWeight: 600,
                        fontSize: "0.95rem",
                        color: "var(--text-primary)",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        maxWidth: "400px",
                      }}
                      title={yt.video_title}
                    >
                      {yt.video_title}
                    </span>
                    <a
                      href={yt.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: "var(--text-muted)", display: "flex", alignItems: "center" }}
                      title="Open YouTube video"
                    >
                      <ExternalLink size={13} />
                    </a>
                  </div>
                  <span style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                    {yt.watch_count} {yt.watch_count === 1 ? "session" : "sessions"}
                  </span>
                </div>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: "10px", flexShrink: 0 }}>
                <span
                  style={{
                    color: "#FB7185",
                    fontWeight: 600,
                    fontSize: "0.85rem",
                    padding: "4px 10px",
                    background: "rgba(244, 63, 94, 0.1)",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid rgba(244, 63, 94, 0.2)",
                  }}
                >
                  {yt.watched_formatted}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "160px",
            textAlign: "center",
            padding: "32px 12px",
            color: "var(--text-muted)",
            fontSize: "0.9rem",
          }}
        >
          {searchTerm ? "No matching YouTube videos found" : "No YouTube learning sessions recorded yet"}
        </div>
      )}
    </div>
  );
};
