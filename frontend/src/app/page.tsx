"use client";

// Step 1: Import React hooks and our components + API function
// useState lets us store data that changes over time (like which screen we're on)
import { useState } from "react";
import LandingHero from "@/components/LandingHero";
import FileUploader from "@/components/FileUploader";
import EncoderSelector from "@/components/EncoderSelector";
import ProcessingStatus from "@/components/ProcessingStatus";
import DownloadButton from "@/components/DownloadButton";
import { protectAudio } from "@/lib/api";

// This page has 4 possible states (a "state machine"):
//   idle       -> user hasn't done anything yet
//   processing -> file was uploaded, waiting for backend
//   done       -> backend returned protected audio
//   error      -> something went wrong
//
// The state determines what the user sees:
//   idle:       FileUploader enabled
//   processing: FileUploader disabled + spinner
//   done:       FileUploader enabled + download button
//   error:      FileUploader enabled + error message

export default function Home() {
  const [status, setStatus] = useState<"idle" | "ready" | "processing" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ blob: Blob, filename: string } | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedEncoders, setSelectedEncoders] = useState<string[]>(["xvector", "ecapa", "hubert"]);

  function handleFileSelected(file: File) {
    setSelectedFile(file);
    setStatus("ready");
    setError(null);
    setResult(null);
  }

  async function handleStartProcessing() {
    if (!selectedFile) return;
    setStatus("processing");
    setError(null);
    setResult(null);
    try {
      const blob = await protectAudio(selectedFile, selectedEncoders);
      const name = selectedFile.name.replace(/\.[^.]+$/, "");
      const filename = `protected_${name}.wav`;
      setResult({ blob, filename });
      setStatus("done");

      // Auto-download the protected file
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
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
          disabled={status === "processing" || selectedEncoders.length === 0}
        />

        {selectedFile && status !== "processing" && (
          <div className="mt-4 flex items-center justify-between rounded-lg border border-zinc-200 bg-white px-4 py-3 dark:border-zinc-700 dark:bg-zinc-900">
            <span className="text-sm text-zinc-600 dark:text-zinc-400 truncate">
              {selectedFile.name}
            </span>
            <button
              onClick={() => { setSelectedFile(null); setStatus("idle"); setResult(null); setError(null); }}
              className="ml-3 text-xs text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"
            >
              Remove
            </button>
          </div>
        )}

        <EncoderSelector
          selected={selectedEncoders}
          onChange={setSelectedEncoders}
          disabled={status === "processing"}
        />

        {selectedFile && (status === "ready" || status === "error") && (
          <div className="flex justify-center py-4">
            <button
              onClick={handleStartProcessing}
              disabled={selectedEncoders.length === 0}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-8 py-3 text-sm font-medium text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Protect Audio
            </button>
          </div>
        )}

        <ProcessingStatus status={status === "ready" ? "idle" : status} error={error} />
        {result && <DownloadButton blob={result.blob} filename={result.filename} />}
      </main>
    </div>
  );
}
