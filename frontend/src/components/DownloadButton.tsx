"use client";

import { useEffect, useState } from "react";

interface DownloadButtonProps {
  blob: Blob;
  filename: string;
}

export default function DownloadButton({ blob, filename }: DownloadButtonProps) {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    const objectUrl = URL.createObjectURL(blob);
    setUrl(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [blob]);

  if (!url) return null;

  return (
    <div className="flex justify-center py-6">
      <a
        href={url}
        download={filename}
        className="inline-flex items-center gap-2 rounded-full bg-[#0a0b0d] px-8 py-3.5 text-[15px] font-medium text-white hover:bg-[#0a2540] transition-colors shadow-[0px_4px_3px_rgba(0,0,0,0.1),0px_2px_2px_rgba(0,0,0,0.1)]"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        Download protected file
      </a>
    </div>
  );
}
