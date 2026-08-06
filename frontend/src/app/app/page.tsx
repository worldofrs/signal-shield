"use client";

import { useState } from "react";
import Link from "next/link";
import FileUploader from "@/components/FileUploader";
import EncoderSelector from "@/components/EncoderSelector";
import ProcessingStatus from "@/components/ProcessingStatus";
import DownloadButton from "@/components/DownloadButton";
import { protectAudio } from "@/lib/api";

export default function AppPage() {
  const [status, setStatus] = useState<"idle" | "ready" | "processing" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ blob: Blob; filename: string } | null>(null);
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
    <div className="flex flex-col flex-1 items-center bg-white min-h-screen">
      {/* Header */}
      <header className="w-full border-b border-[#eaedf2] bg-white">
        <div className="max-w-[860px] mx-auto px-6 py-4 flex items-center gap-2.5">
          <Link href="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
            <div className="w-9 h-9 rounded-full bg-[#58a0a9] flex items-center justify-center">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L3 7V12C3 17.25 6.75 22.13 12 23C17.25 22.13 21 17.25 21 12V7L12 2Z" fill="white" fillOpacity="0.3" stroke="white" strokeWidth="1.5" />
                <path d="M12 6L8 8.5V12C8 15 9.75 17.75 12 18.5C14.25 17.75 16 15 16 12V8.5L12 6Z" fill="white" fillOpacity="0.5" stroke="white" strokeWidth="1" />
              </svg>
            </div>
            <span className="font-semibold text-lg tracking-[-0.45px]">
              <span className="text-[#0a0b0d]">Signal</span>
              <span className="text-[#0047ab]">Shield</span>
            </span>
          </Link>
        </div>
      </header>

      {/* Main content */}
      <main className="w-full max-w-[860px] mx-auto px-6 py-12">
        <div className="text-center mb-10">
          <h1 className="text-[clamp(2rem,4vw,2.9rem)] font-bold tracking-[-1.16px] text-[#0a0b0d]">
            Protect your voice in seconds.
          </h1>
          <p className="mt-4 text-[17px] text-[#52575c] max-w-[520px] mx-auto leading-[1.625]">
            Upload an audio file and download a protected version that sounds identical to humans but is unusable for voice cloning.
          </p>
        </div>

        {/* Card matching the TryItFree section */}
        <div className="rounded-3xl border border-[#eaedf2] bg-[#f8f9fc] p-8">
          <FileUploader
            onFileSelected={handleFileSelected}
            disabled={status === "processing" || selectedEncoders.length === 0}
          />

          {selectedFile && status !== "processing" && (
            <div className="mt-4 flex items-center justify-between rounded-[14px] border border-[#eaedf2] bg-white px-5 py-3 shadow-[0px_1px_1.5px_rgba(0,0,0,0.1),0px_1px_1px_rgba(0,0,0,0.1)]">
              <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-[#e8edf4] flex items-center justify-center flex-shrink-0">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#52575c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M9 18V5l12-2v13" />
                    <circle cx="6" cy="18" r="3" />
                    <circle cx="18" cy="16" r="3" />
                  </svg>
                </div>
                <span className="text-sm font-medium text-[#0a0b0d] truncate">
                  {selectedFile.name}
                </span>
              </div>
              <button
                onClick={() => { setSelectedFile(null); setStatus("idle"); setResult(null); setError(null); }}
                className="ml-3 text-xs font-medium text-[#878b8f] hover:text-[#52575c] transition-colors"
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
            <div className="flex justify-center pt-6">
              <button
                onClick={handleStartProcessing}
                disabled={selectedEncoders.length === 0}
                className="inline-flex items-center gap-2 rounded-full bg-[#0047ab] px-10 py-3.5 text-[15px] font-medium text-white hover:bg-[#003d94] transition-colors shadow-[0px_10px_7.5px_rgba(0,0,0,0.1),0px_4px_3px_rgba(0,0,0,0.1)] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L3 7V12C3 17.25 6.75 22.13 12 23C17.25 22.13 21 17.25 21 12V7L12 2Z" />
                </svg>
                Protect Audio
              </button>
            </div>
          )}

          <ProcessingStatus status={status === "ready" ? "idle" : status} error={error} />
          {result && <DownloadButton blob={result.blob} filename={result.filename} />}
        </div>
      </main>
    </div>
  );
}
