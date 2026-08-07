"use client";

import { useState, useEffect } from "react";
import LandingHero from "@/components/LandingHero";
import FileUploader from "@/components/FileUploader";
import EncoderSelector from "@/components/EncoderSelector";
import ProcessingStatus from "@/components/ProcessingStatus";
import { protectAudio } from "@/lib/api";

export default function Home() {
  const [status, setStatus] = useState<"idle" | "processing" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ blob: Blob; filename: string } | null>(null);
  const [selectedEncoders, setSelectedEncoders] = useState<string[]>(["resemblyzer", "ecapa", "hubert"]);
  const [file, setFile] = useState<File | null>(null);

  // Auto-download when processing completes
  useEffect(() => {
    if (status === "done" && result) {
      const url = URL.createObjectURL(result.blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = result.filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }, [status, result]);

  function handleFileSelected(f: File) {
    setFile(f);
    setStatus("idle");
    setError(null);
    setResult(null);
  }

  async function handleProcess() {
    if (!file) return;
    setStatus("processing");
    setError(null);
    setResult(null);
    try {
      const blob = await protectAudio(file, selectedEncoders);
      const name = file.name.replace(/\.[^.]+$/, "");
      setResult({ blob, filename: `protected_${name}.wav` });
      setStatus("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setStatus("error");
    }
  }

  return (
    <div className="flex flex-col flex-1 items-center bg-zinc-50 dark:bg-black">
      <main className="w-full max-w-2xl px-6 py-12">
        <LandingHero />
        <FileUploader
          onFileSelected={handleFileSelected}
          disabled={status === "processing"}
        />

        {file && status !== "processing" && (
          <div className="mt-4 flex items-center gap-3 rounded-lg border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-700 dark:bg-zinc-900">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-zinc-500">
              <path d="M9 18V5l12-2v13" />
              <circle cx="6" cy="18" r="3" />
              <circle cx="18" cy="16" r="3" />
            </svg>
            <span className="text-sm text-zinc-700 dark:text-zinc-300 truncate flex-1">{file.name}</span>
            <span className="text-xs text-zinc-400">{(file.size / (1024 * 1024)).toFixed(1)} MB</span>
          </div>
        )}

        <EncoderSelector
          selected={selectedEncoders}
          onChange={setSelectedEncoders}
          disabled={status === "processing"}
        />

        {file && status !== "processing" && status !== "done" && (
          <div className="flex justify-center mt-6">
            <button
              onClick={handleProcess}
              disabled={selectedEncoders.length === 0}
              className="inline-flex items-center gap-2 rounded-lg bg-zinc-900 px-6 py-3 text-sm font-medium text-white hover:bg-zinc-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              Protect Audio
            </button>
          </div>
        )}

        <ProcessingStatus status={status} error={error} />

        {status === "done" && result && (
          <div className="flex justify-center py-6">
            <p className="text-sm text-green-600 dark:text-green-400 font-medium">
              Download started automatically.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
