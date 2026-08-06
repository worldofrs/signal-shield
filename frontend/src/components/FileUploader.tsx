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
        relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
        transition-colors
        ${disabled
          ? "border-zinc-200 bg-zinc-50 text-zinc-400 cursor-not-allowed dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-600"
          : dragging
            ? "border-blue-500 bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400"
            : "border-zinc-300 hover:border-zinc-400 text-zinc-600 dark:border-zinc-700 dark:hover:border-zinc-600 dark:text-zinc-400"
        }
      `}
    >
      <label
        htmlFor="audio-upload"
        className="relative block cursor-pointer"
        onClick={() => inputRef.current?.click()}
      >
        <p className="text-lg font-medium">
          {disabled ? "Processing..." : dragging ? "Drop your file here" : "Drag & drop an audio file here"}
        </p>
        <p className="mt-2 text-sm">
          {disabled ? "" : "or click to browse — .wav, .mp3, or .m4a, up to 50MB"}
        </p>
        <input
          ref={inputRef}
          id="audio-upload"
          type="file"
          accept=".wav,.mp3,.m4a,audio/wav,audio/mpeg,audio/mp4,audio/x-m4a"
          onChange={onChange}
          disabled={disabled}
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
        />
      </label>
    </div>
  );
}
