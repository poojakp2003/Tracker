import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { Calendar, TrendingUp } from "lucide-react";

const CustomTooltip = ({ active, payload, label }) => {
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
          minWidth: "150px",
        }}
      >
        <div style={{ fontWeight: 600, fontSize: "0.95rem", marginBottom: "4px" }}>
          {data.day}
        </div>
        <div style={{ color: "#94A3B8", fontSize: "0.75rem", marginBottom: "6px" }}>
          {data.date}
        </div>
        <div style={{ color: "#06B6D4", fontSize: "0.9rem", fontWeight: 600 }}>
          {data.hours} hrs ({data.duration_formatted})
        </div>
        <div style={{ color: "#94A3B8", fontSize: "0.8rem", marginTop: "2px" }}>
          {data.session_count} {data.session_count === 1 ? "session" : "sessions"}
        </div>
      </div>
    );
  }
  return null;
};

export const UsageTimeLineChart = ({ items = [], totalHours = 0, range = "7d" }) => {
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
        <TrendingUp size={32} style={{ marginBottom: "8px", opacity: 0.5 }} />
        <span>No daily timeline activity recorded</span>
      </div>
    );
  }

  // Format short day for X-Axis (e.g. Mon, Tue or Mon 15)
  const chartData = items.map((point) => {
    const shortDay = point.day ? point.day.substring(0, 3) : point.date;
    return {
      ...point,
      displayLabel: shortDay,
    };
  });

  return (
    <div>
      <div style={{ height: 280, width: "100%", marginTop: "10px" }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 20, left: -10, bottom: 5 }}
          >
            <defs>
              <linearGradient id="usageGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#06B6D4" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255, 255, 255, 0.06)"
              vertical={false}
            />
            <XAxis
              dataKey="displayLabel"
              stroke="#94A3B8"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
            />
            <YAxis
              unit="h"
              stroke="#64748B"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="hours"
              stroke="#8B5CF6"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#usageGradient)"
              activeDot={{
                r: 6,
                fill: "#06B6D4",
                stroke: "#FFFFFF",
                strokeWidth: 2,
              }}
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Quick summary below line chart */}
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
        <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <Calendar size={14} color="var(--accent-purple)" />
          <span>Active Trend ({range.toUpperCase()})</span>
        </span>
        <span>Avg/Day: <strong style={{ color: "var(--accent-purple)" }}>
          {items.length > 0 ? (totalHours / items.length).toFixed(1) : 0} hrs
        </strong></span>
      </div>
    </div>
  );
};
