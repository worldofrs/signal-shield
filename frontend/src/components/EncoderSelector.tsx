"use client";

const ENCODERS = [
  { id: "resemblyzer", label: "Resemblyzer (LSTM)" },
  { id: "ecapa", label: "ECAPA (CNN)" },
  { id: "hubert", label: "HuBERT (Transformer)" },
] as const;

interface EncoderSelectorProps {
  selected: string[];
  onChange: (encoders: string[]) => void;
  disabled: boolean;
}

export default function EncoderSelector({ selected, onChange, disabled }: EncoderSelectorProps) {
  function toggle(id: string) {
    if (selected.includes(id)) {
      if (selected.length === 1) return;
      onChange(selected.filter((e) => e !== id));
    } else {
      onChange([...selected, id]);
    }
  }

  return (
    <fieldset className="mt-6 mb-2" disabled={disabled}>
      <legend className="text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
        Target encoders
      </legend>
      <div className="flex flex-wrap gap-3">
        {ENCODERS.map(({ id, label }) => {
          const checked = selected.includes(id);
          const isLast = checked && selected.length === 1;
          return (
            <label
              key={id}
              className={`
                flex items-center gap-2 rounded-lg border px-3 py-2 text-sm
                transition-colors select-none
                ${disabled
                  ? "border-zinc-200 text-zinc-400 cursor-not-allowed dark:border-zinc-800 dark:text-zinc-600"
                  : checked
                    ? "border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300 dark:border-blue-600"
                    : "border-zinc-300 text-zinc-600 hover:border-zinc-400 dark:border-zinc-700 dark:text-zinc-400 dark:hover:border-zinc-600"
                }
              `}
            >
              <input
                type="checkbox"
                checked={checked}
                disabled={disabled || isLast}
                onChange={() => toggle(id)}
                className="accent-blue-600"
              />
              {label}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
