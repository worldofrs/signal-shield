"use client";

import { useCallback, useState, DragEvent, ChangeEvent } from "react";

interface FileUploaderProps {
  onFileSelected: (file: File) => void;
  disabled: boolean;
}

export default function FileUploader({ onFileSelected, disabled }: FileUploaderProps) {
  const [dragging, setDragging] = useState(false);

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
      setDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onDragOver = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      if (!disabled) setDragging(true);
    },
    [disabled]
  );

  const onDragLeave = useCallback(() => setDragging(false), []);

  const onChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  return (
    <div
      onDrop={onDrop}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      className={`
        border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
        transition-colors
        ${disabled
          ? "border-zinc-200 bg-zinc-50 text-zinc-400 cursor-not-allowed dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-600"
          : dragging
            ? "border-blue-500 bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400"
            : "border-zinc-300 hover:border-zinc-400 text-zinc-600 dark:border-zinc-700 dark:hover:border-zinc-600 dark:text-zinc-400"
        }
      `}
    >
      <label className="cursor-pointer">
        <p className="text-lg font-medium">
          {disabled ? "Processing..." : dragging ? "Drop your file here" : "Drag & drop an audio file here"}
        </p>
        <p className="mt-2 text-sm">
          {disabled ? "" : "or click to browse — .wav or .mp3, up to 50MB"}
        </p>
        <input
          type="file"
          accept=".wav,.mp3"
          onChange={onChange}
          disabled={disabled}
          className="hidden"
        />
      </label>
    </div>
  );
}
