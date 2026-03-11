"use client";

import React from "react";
import ChartRenderer from "./ChartRenderer";
import type { QueryResult } from "@/lib/api";

interface DashboardGridProps {
  results: QueryResult[];
}

export default function DashboardGrid({ results }: DashboardGridProps) {
  if (results.length === 0) {
    return (
      <div className="dashboard-empty">
        <div className="dashboard-empty__icon">
          <svg width="56" height="56" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z" />
          </svg>
        </div>
        <h3 className="dashboard-empty__title">Your dashboard is empty</h3>
        <p className="dashboard-empty__subtitle">
          Upload a CSV file and ask a question to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="dashboard-grid">
      {results.map((result, idx) => (
        <div key={idx} className="dashboard-grid__item animate-fade-in">
          {/* Chart */}
          <ChartRenderer data={result.data} config={result.chart_config} />

          {/* AI insight */}
          <div className="dashboard-grid__insight">
            <span className="dashboard-grid__insight-badge">AI Insight</span>
            <p>{result.summary}</p>
          </div>

          {/* SQL preview */}
          <details className="dashboard-grid__sql">
            <summary>View SQL</summary>
            <pre><code>{result.sql}</code></pre>
          </details>
        </div>
      ))}
    </div>
  );
}
