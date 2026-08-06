"use client";

import { useState, useEffect } from "react";

const messages = [
  "Analyzing voice patterns...",
  "Generating adversarial perturbation...",
  "Optimizing against speaker encoders...",
  "Applying signal protection...",
  "Finalizing protected audio...",
];

interface ProcessingStatusProps {
  status: "idle" | "processing" | "done" | "error";
  error: string | null;
}

export default function ProcessingStatus({ status, error }: ProcessingStatusProps) {
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    if (status !== "processing") {
      setMessageIndex(0);
      return;
    }
    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 3000);
    return () => clearInterval(interval);
  }, [status]);

  if (status === "processing") {
    return (
      <div className="flex items-center justify-center gap-3 py-6 text-[#52575c]">
        <svg className="animate-spin h-5 w-5 text-[#0047ab]" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
        <span className="text-sm">{messages[messageIndex]}</span>
      </div>
    );
  }

  if (status === "error" && error) {
    return (
      <div className="py-6 text-center">
        <p className="font-medium text-red-600">Processing failed</p>
        <p className="mt-1 text-sm text-red-500">{error}</p>
      </div>
    );
  }

  return null;
}
