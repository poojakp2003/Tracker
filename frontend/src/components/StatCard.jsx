import React from "react";

export const StatCard = ({ title, value, subtitle, icon: Icon, color = "var(--primary)" }) => {
  return (
    <div className="glass-card" style={{ padding: "20px 24px", position: "relative", overflow: "hidden" }}>
      <div style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        height: "2px",
        background: `linear-gradient(90deg, ${color}, transparent)`,
      }} />

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
        <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
          {title}
        </span>
        {Icon && (
          <div style={{
            width: "36px",
            height: "36px",
            borderRadius: "10px",
            background: `rgba(255, 255, 255, 0.05)`,
            border: "1px solid var(--border-subtle)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: color,
          }}>
            <Icon size={18} />
          </div>
        )}
      </div>

      <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.02em", marginBottom: "6px" }}>
        {value}
      </div>

      {subtitle && (
        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
          {subtitle}
        </div>
      )}
    </div>
  );
};
