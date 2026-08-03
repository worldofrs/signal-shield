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
  // Step 2: Set up state variables
  // You need three pieces of state:
  //   - status: which state we're in ("idle", "processing", "done", or "error")
  //   - error: the error message string (or null if no error)
  //   - result: an object with { blob, filename } for the download (or null if no result yet)
  //
  // Syntax: const [value, setValue] = useState(initialValue)

  const [status, setStatus] = useState<"idle" | "processing" | "done" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ blob: Blob, filename: string } | null>(null);
  const [selectedEncoders, setSelectedEncoders] = useState<string[]>(["resemblyzer", "ecapa", "hubert"]);


  // Step 3: Write the handleFileSelected function
  // This runs when the user drops/selects a file. It should:
  //   1. Set status to "processing" (shows spinner, disables uploader)
  //   2. Clear any previous error and result
  //   3. Call protectAudio(file) from our API module (it returns a Promise<Blob>)
  //   4. If successful: set result to { blob: <the blob>, filename: "protected_<original name>" }
  //      and set status to "done"
  //   5. If it fails: set error to the error message and set status to "error"
  //
  // This needs to be an async function because protectAudio returns a Promise.
  // Use try/catch to handle success vs failure.
  //
  // YOUR CODE: write the function below
  // Hint:
  async function handleFileSelected(file: File) {
    setStatus("processing");
    setError(null);
    setResult(null);
    try {
      const blob = await protectAudio(file, selectedEncoders);
      const name = file.name.replace(/\.[^.]+$/, "");   // strip extension
      setResult({ blob, filename: `protected_${name}.wav` });
      setStatus("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setStatus("error");
    }
  }


  // Step 4: Render the components
  // The JSX below is already wired up. Once you write Steps 2 and 3,
  // it will work because each component reads from the state you defined.
  return (
    <div className="flex flex-col flex-1 items-center bg-zinc-50 dark:bg-black">
      <main className="w-full max-w-2xl px-6 py-12">
        {/* Always visible */}
        <LandingHero />
        <FileUploader
          onFileSelected={handleFileSelected}
          disabled={status === "processing"}
        />
        <EncoderSelector
          selected={selectedEncoders}
          onChange={setSelectedEncoders}
          disabled={status === "processing"}
        />
        <ProcessingStatus status={status} error={error} />
        {result && <DownloadButton blob={result.blob} filename={result.filename} />}
      </main>
    </div>
  );
}
