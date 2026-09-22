import React, { useState } from "react";
import { ExternalLink, Play, Search, Video } from "lucide-react";

export const YouTubeActivityList = ({ items = [], loading = false, totalWatchedFormatted = "0 mins" }) => {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredItems = items
    .filter((item) =>
      item.video_title.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => new Date(b.last_watched) - new Date(a.last_watched));

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

      {/* Table Content */}
      {loading ? (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
          <div className="skeleton" style={{ height: "40px" }} />
          <div className="skeleton" style={{ height: "40px" }} />
          <div className="skeleton" style={{ height: "40px" }} />
        </div>
      ) : filteredItems.length > 0 ? (
        <div style={{ overflowX: "auto" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "separate",
              borderSpacing: "0 6px",
              fontSize: "0.9rem",
            }}
          >
            <thead>
              <tr style={{ color: "var(--text-secondary)", textAlign: "left", fontSize: "0.8rem" }}>
                <th style={{ padding: "8px 12px", fontWeight: 600 }}>Watched Video</th>
                <th style={{ padding: "8px 12px", fontWeight: 600, width: "140px", textAlign: "right" }}>Sessions</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.slice(0, 10).map((yt, idx) => (
                <tr
                  key={yt.video_id || idx}
                  style={{
                    background: "rgba(255, 255, 255, 0.025)",
                    borderRadius: "var(--radius-sm)",
                    transition: "background 0.2s ease",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255, 255, 255, 0.025)")}
                >
                  <td style={{ padding: "10px 12px", borderTopLeftRadius: "8px", borderBottomLeftRadius: "8px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
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
                      <span
                        style={{
                          fontWeight: 500,
                          color: "var(--text-primary)",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          maxWidth: "300px",
                        }}
                        title={yt.video_title}
                      >
                        {yt.video_title}
                      </span>
                      <a
                        href={yt.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        style={{ color: "var(--text-muted)", display: "flex", alignItems: "center", flexShrink: 0 }}
                        title="Open YouTube video"
                      >
                        <ExternalLink size={13} />
                      </a>
                    </div>
                  </td>
                  <td
                    style={{
                      padding: "10px 12px",
                      textAlign: "right",
                      borderTopRightRadius: "8px",
                      borderBottomRightRadius: "8px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "14px" }}>
                      <span style={{ color: "var(--text-muted)", fontSize: "0.85rem", minWidth: "18px", textAlign: "center" }}>
                        {yt.watch_count}
                      </span>
                      <span
                        style={{
                          color: "#FB7185",
                          fontWeight: 600,
                          fontSize: "0.8rem",
                          fontFamily: "monospace",
                          letterSpacing: "0.5px",
                          padding: "4px 10px",
                          background: "rgba(244, 63, 94, 0.1)",
                          borderRadius: "var(--radius-sm)",
                          border: "1px solid rgba(244, 63, 94, 0.2)",
                          minWidth: "60px",
                          textAlign: "center",
                        }}
                      >
                        {yt.watched_formatted}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filteredItems.length > 10 && (
            <div
              style={{
                textAlign: "center",
                paddingTop: "10px",
                color: "var(--text-muted)",
                fontSize: "0.8rem",
              }}
            >
              Showing 10 of {filteredItems.length} watched videos
            </div>
          )}
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