"use client";

import React from "react";
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { ChartConfig } from "@/lib/api";

// ── Colour palette for multi-series ─────────────────────────────────
const COLORS = [
  "#6366f1", // indigo-500
  "#22d3ee", // cyan-400
  "#f59e0b", // amber-500
  "#ec4899", // pink-500
  "#10b981", // emerald-500
  "#8b5cf6", // violet-500
  "#f97316", // orange-500
  "#14b8a6", // teal-500
];

interface ChartRendererProps {
  data: Record<string, unknown>[];
  config: ChartConfig;
}

export default function ChartRenderer({ data, config }: ChartRendererProps) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty">
        <p>No data to display.</p>
      </div>
    );
  }

  const { type, xAxis, yAxis, title } = config;

  // ── Metric card (single KPI) ──────────────────────────────────────
  if (type === "metric") {
    const key = yAxis[0];
    const value = data[0]?.[key];
    return (
      <div className="chart-card chart-card--metric">
        <p className="chart-card__label">{title}</p>
        <p className="chart-card__value">
          {typeof value === "number" ? value.toLocaleString() : String(value)}
        </p>
      </div>
    );
  }

  // ── Data table fallback ───────────────────────────────────────────
  if (type === "table") {
    const cols = Object.keys(data[0]);
    return (
      <div className="chart-card chart-card--table">
        <p className="chart-card__title">{title}</p>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                {cols.map((c) => (
                  <th key={c}>{c.replace(/_/g, " ")}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.slice(0, 100).map((row, i) => (
                <tr key={i}>
                  {cols.map((c) => (
                    <td key={c}>{String(row[c] ?? "")}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // ── Recharts visualisations ───────────────────────────────────────

  const customTooltip = {
    contentStyle: {
      background: "rgba(15, 23, 42, 0.92)",
      border: "1px solid rgba(99,102,241,0.3)",
      borderRadius: "10px",
      color: "#e2e8f0",
      fontSize: "13px",
      backdropFilter: "blur(12px)",
    },
    itemStyle: { color: "#e2e8f0" },
  };

  // ── Bar chart ─────────────────────────────────────────────────────
  if (type === "bar") {
    return (
      <div className="chart-card">
        <p className="chart-card__title">{title}</p>
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
            <XAxis dataKey={xAxis!} tick={{ fill: "#94a3b8", fontSize: 12 }} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
            <Tooltip {...customTooltip} />
            <Legend wrapperStyle={{ color: "#cbd5e1", fontSize: 13 }} />
            {yAxis.map((key, i) => (
              <Bar
                key={key}
                dataKey={key}
                fill={COLORS[i % COLORS.length]}
                radius={[6, 6, 0, 0]}
                animationDuration={800}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // ── Line chart ────────────────────────────────────────────────────
  if (type === "line") {
    return (
      <div className="chart-card">
        <p className="chart-card__title">{title}</p>
        <ResponsiveContainer width="100%" height={340}>
          <LineChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.1)" />
            <XAxis dataKey={xAxis!} tick={{ fill: "#94a3b8", fontSize: 12 }} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
            <Tooltip {...customTooltip} />
            <Legend wrapperStyle={{ color: "#cbd5e1", fontSize: 13 }} />
            {yAxis.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={COLORS[i % COLORS.length]}
                strokeWidth={2.5}
                dot={{ r: 4, fill: COLORS[i % COLORS.length] }}
                activeDot={{ r: 6, strokeWidth: 0 }}
                animationDuration={1000}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // ── Pie chart ─────────────────────────────────────────────────────
  if (type === "pie") {
    return (
      <div className="chart-card">
        <p className="chart-card__title">{title}</p>
        <ResponsiveContainer width="100%" height={340}>
          <PieChart>
            <Pie
              data={data}
              dataKey={yAxis[0]}
              nameKey={xAxis!}
              cx="50%"
              cy="50%"
              outerRadius={120}
              innerRadius={60}
              paddingAngle={3}
              animationDuration={900}
              label={({ name, percent }: { name?: string; percent?: number }) =>
                `${name ?? ""} ${((percent ?? 0) * 100).toFixed(0)}%`
              }
              labelLine={{ stroke: "#64748b" }}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip {...customTooltip} />
            <Legend wrapperStyle={{ color: "#cbd5e1", fontSize: 13 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // ── Ultimate fallback ─────────────────────────────────────────────
  return (
    <div className="chart-card">
      <p className="chart-card__title">{title}</p>
      <p className="text-slate-400 text-sm">Unsupported chart type: {type}</p>
    </div>
  );
}
