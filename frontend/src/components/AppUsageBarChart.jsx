import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import { Clock, Layers } from "lucide-react";

const BAR_COLORS = [
  "#06B6D4", // Cyan
  "#8B5CF6", // Purple
  "#3B82F6", // Blue
  "#10B981", // Emerald
  "#F59E0B", // Amber
  "#EC4899", // Pink
];

// Custom Tooltip component for Dark Glassmorphism aesthetic
const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div
        style={{
          background: "rgba(15, 23, 42, 0.95)",
          border: "1px solid rgba(255, 255, 255, 0.15)",
          backdropFilter: "blur(12px)",
          padding: "12px 16px",
          borderRadius: "10px",
          boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
          color: "#F9FAFB",
          minWidth: "160px",
        }}
      >
        <div style={{ fontWeight: 600, fontSize: "0.95rem", marginBottom: "4px" }}>
          {data.app_name}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "#22D3EE", fontSize: "0.85rem", marginBottom: "2px" }}>
          <Clock size={14} />
          <span>{data.duration_formatted} ({data.hours} hrs)</span>
        </div>
        <div style={{ color: "#94A3B8", fontSize: "0.8rem" }}>
          {data.session_count} {data.session_count === 1 ? "session" : "sessions"} • {data.percentage}%
        </div>
      </div>
    );
  }
  return null;
};

export const AppUsageBarChart = ({ items = [], totalDurationFormatted = "0 mins" }) => {
  if (!items || items.length === 0) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "280px",
          color: "var(--text-muted)",
          fontSize: "0.9rem",
          background: "rgba(255, 255, 255, 0.02)",
          borderRadius: "var(--radius-md)",
          border: "1px dashed var(--border-subtle)",
        }}
      >
        <Layers size={32} style={{ marginBottom: "8px", opacity: 0.5 }} />
        <span>No application usage data recorded for this period</span>
      </div>
    );
  }

  // Format data for Recharts: calculate hours as decimal for the bar length
  const chartData = items.slice(0, 8).map((item) => ({
    ...item,
    hours: Number((item.duration_seconds / 3600).toFixed(2)),
  }));

  return (
    <div>
      <div style={{ height: 280, width: "100%", marginTop: "10px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              horizontal={false}
              stroke="rgba(255, 255, 255, 0.06)"
            />
            <XAxis
              type="number"
              unit="h"
              stroke="#64748B"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
            />
            <YAxis
              dataKey="app_name"
              type="category"
              stroke="#94A3B8"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
              width={90}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255, 255, 255, 0.03)" }} />
            <Bar
              dataKey="hours"
              radius={[0, 6, 6, 0]}
              barSize={20}
              animationDuration={800}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={BAR_COLORS[index % BAR_COLORS.length]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Quick summary below bar chart */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          paddingTop: "14px",
          marginTop: "12px",
          borderTop: "1px solid var(--border-subtle)",
          fontSize: "0.85rem",
          color: "var(--text-secondary)",
        }}
      >
        <span>Top App: <strong style={{ color: "var(--text-primary)" }}>{items[0]?.app_name || "N/A"}</strong></span>
        <span>Total: <strong style={{ color: "var(--primary)" }}>{totalDurationFormatted}</strong></span>
      </div>
    </div>
  );
};
