"use client";

import React, { useState, useRef } from "react";

interface PromptBoxProps {
  onSubmit: (prompt: string) => void;
  onFileUpload: (file: File) => void;
  isLoading: boolean;
}

export default function PromptBox({
  onSubmit,
  onFileUpload,
  isLoading,
}: PromptBoxProps) {
  const [prompt, setPrompt] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    onSubmit(prompt.trim());
    setPrompt("");
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileUpload(file);
      e.target.value = "";
    }
  };

  return (
    <form onSubmit={handleSubmit} className="prompt-box">
      <div className="prompt-box__inner">
        {/* CSV upload button */}
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          className="prompt-box__upload-btn"
          title="Upload CSV"
          disabled={isLoading}
        >
          <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleFileChange}
        />

        {/* Prompt input */}
        <input
          id="prompt-input"
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ask a question about your data…"
          className="prompt-box__input"
          disabled={isLoading}
        />

        {/* Submit button */}
        <button
          type="submit"
          disabled={isLoading || !prompt.trim()}
          className="prompt-box__send-btn"
        >
          {isLoading ? (
            <span className="prompt-box__spinner" />
          ) : (
            <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          )}
        </button>
      </div>
    </form>
  );
}
