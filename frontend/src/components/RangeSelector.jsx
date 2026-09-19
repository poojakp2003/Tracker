import React from "react";

const RANGES = [
  { key: "today", label: "Today" },
  { key: "7d", label: "7 Days" },
  { key: "30d", label: "30 Days" },
  { key: "all", label: "All Time" },
];

export const RangeSelector = ({ currentRange, onSelectRange }) => {
  return (
    <div className="filter-bar">
      {RANGES.map((r) => (
        <button
          key={r.key}
          onClick={() => onSelectRange(r.key)}
          className={`filter-pill ${currentRange === r.key ? "active" : ""}`}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
};
