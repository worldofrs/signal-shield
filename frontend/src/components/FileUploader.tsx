"use client";

import { useCallback, useRef, useState, DragEvent, ChangeEvent } from "react";

interface FileUploaderProps {
  onFileSelected: (file: File) => void;
  disabled: boolean;
}

export default function FileUploader({ onFileSelected, disabled }: FileUploaderProps) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      if (disabled) return;
      onFileSelected(file);
    },
    [disabled, onFileSelected]
  );

  const onDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(false);

      const file = e.dataTransfer?.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onDragEnter = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled && e.dataTransfer.types.includes("Files")) {
        setDragging(true);
      }
    },
    [disabled]
  );

  const onDragOver = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      if (!disabled && e.dataTransfer.types.includes("Files")) {
        setDragging(true);
        e.dataTransfer.dropEffect = "copy";
      }
    },
    [disabled]
  );

  const onDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
  }, []);

  const onChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      e.currentTarget.value = "";
    },
    [handleFile]
  );

  return (
    <div
      onDrop={onDrop}
      onDragEnter={onDragEnter}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      className={`
        relative border-2 border-dashed rounded-2xl min-h-[180px] text-center cursor-pointer
        transition-colors flex flex-col items-center justify-center py-12
        ${disabled
          ? "border-[#c8cdd5] bg-[#f8f9fc] text-[#878b8f] cursor-not-allowed"
          : dragging
            ? "border-[#0047ab] bg-[#e0f0ff] text-[#0047ab]"
            : "border-[#c8cdd5] bg-white hover:border-[#0047ab]/40 text-[#52575c]"
        }
      `}
    >
      <label
        htmlFor="audio-upload"
        className="relative flex flex-col items-center cursor-pointer"
        onClick={() => inputRef.current?.click()}
      >
        <div className="w-14 h-14 rounded-2xl bg-[#e8edf4] flex items-center justify-center mb-4">
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#52575c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <p className="text-base font-semibold text-[#0a0b0d]">
          {disabled ? "Processing..." : dragging ? "Drop your file here" : "Drag & drop an audio file here"}
        </p>
        <p className="mt-1 text-sm text-[#878b8f]">
          {disabled ? "" : (
            <>or <span className="text-[#0047ab] underline">click to browse</span> &mdash; WAV, .mp3, up to 50MB</>
          )}
        </p>
        <input
          ref={inputRef}
          id="audio-upload"
          type="file"
          accept=".wav,.mp3"
          onChange={onChange}
          disabled={disabled}
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
        />
      </label>
    </div>
  );
}
