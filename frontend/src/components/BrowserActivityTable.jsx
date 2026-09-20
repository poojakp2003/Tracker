import React, { useState } from "react";
import { ExternalLink, Globe, Search } from "lucide-react";

export const BrowserActivityTable = ({ items = [], loading = false }) => {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredItems = items.filter((item) => {
    const term = searchTerm.toLowerCase();
    return (
      item.url.toLowerCase().includes(term) ||
      (item.title && item.title.toLowerCase().includes(term)) ||
      (item.domain && item.domain.toLowerCase().includes(term))
    );
  });

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
              background: "rgba(16, 185, 129, 0.15)",
              color: "#34D399",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
            }}
          >
            <Globe size={18} />
          </div>
          <div style={{ minWidth: 0 }}>
            <h2 style={{ fontSize: "1.15rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              Browser Activity
            </h2>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              Recent visited web pages and timestamps
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
            placeholder="Search URLs..."
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
                <th style={{ padding: "8px 12px", fontWeight: 600 }}>URL</th>
                <th style={{ padding: "8px 12px", fontWeight: 600, width: "100px", textAlign: "right" }}>Time</th>
              </tr>
            </thead>
            <tbody>
              {filteredItems.slice(0, 10).map((item, idx) => {
                const displayUrl = item.domain || item.url.replace(/^https?:\/\//, "");
                return (
                  <tr
                    key={item.id || idx}
                    style={{
                      background: "rgba(255, 255, 255, 0.025)",
                      borderRadius: "var(--radius-sm)",
                      transition: "background 0.2s ease",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(255, 255, 255, 0.05)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "rgba(255, 255, 255, 0.025)")}
                  >
                    <td style={{ padding: "10px 12px", borderTopLeftRadius: "8px", borderBottomLeftRadius: "8px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: "2px", minWidth: 0 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                            <span
                              style={{
                                fontWeight: 500,
                                color: "var(--text-primary)",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                maxWidth: "280px",
                              }}
                              title={item.url}
                            >
                              {displayUrl}
                            </span>
                            <a
                              href={item.url.startsWith("http") ? item.url : `https://${item.url}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ color: "var(--text-muted)", display: "flex", alignItems: "center" }}
                              title="Open URL"
                            >
                              <ExternalLink size={13} />
                            </a>
                          </div>
                          {item.title && (
                            <span
                              style={{
                                color: "var(--text-muted)",
                                fontSize: "0.75rem",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                maxWidth: "300px",
                              }}
                            >
                              {item.title}
                            </span>
                          )}
                        </div>
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
                      <span
                        className="badge badge-emerald"
                        style={{
                          fontSize: "0.8rem",
                          fontWeight: 600,
                          fontFamily: "monospace",
                          letterSpacing: "0.5px",
                        }}
                      >
                        {item.time_formatted || "—"}
                      </span>
                    </td>
                  </tr>
                );
              })}
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
              Showing 10 of {filteredItems.length} visited pages
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
          {searchTerm ? "No matching browser visits found" : "No browser activity recorded yet"}
        </div>
      )}
    </div>
  );
};
