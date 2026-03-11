"use client";

import React, { useState } from "react";
import PromptBox from "@/components/PromptBox";
import DashboardGrid from "@/components/DashboardGrid";
import { submitQuery, uploadCsv } from "@/lib/api";
import type { QueryResult } from "@/lib/api";

export default function Home() {
  const [results, setResults] = useState<QueryResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: "success" | "error" } | null>(null);

  const showToast = (message: string, type: "success" | "error" = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  // ── Submit a natural-language query ───────────────────────────────
  const handleQuery = async (prompt: string) => {
    setIsLoading(true);
    try {
      const result = await submitQuery(prompt);
      // Newest result at the top of the dashboard
      setResults((prev) => [result, ...prev]);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong";
      showToast(message, "error");
    } finally {
      setIsLoading(false);
    }
  };

  // ── Upload a CSV file ─────────────────────────────────────────────
  const handleUpload = async (file: File) => {
    setIsLoading(true);
    try {
      const res = await uploadCsv(file);
      showToast(`${res.message} (${res.rows_loaded} rows, ${res.columns_detected.length} columns)`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Upload failed";
      showToast(message, "error");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-shell">
      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className="app-header">
        <div className="app-header__logo">
          <span className="app-header__icon">⚡</span>
          <h1>BI Dashboard</h1>
        </div>
        <p className="app-header__tagline">
          Ask questions in plain English — get instant charts
        </p>
      </header>

      {/* ── Prompt input ───────────────────────────────────────────── */}
      <PromptBox
        onSubmit={handleQuery}
        onFileUpload={handleUpload}
        isLoading={isLoading}
      />

      {/* ── Dashboard grid ─────────────────────────────────────────── */}
      <main className="app-main">
        <DashboardGrid results={results} />
      </main>

      {/* ── Toast notifications ────────────────────────────────────── */}
      {toast && (
        <div className={`toast toast--${toast.type} animate-slide-up`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
