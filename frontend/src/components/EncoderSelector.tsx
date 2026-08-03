"use client";

const ENCODERS = [
  {
    id: "resemblyzer",
    label: "Resemblyzer",
    description: "LSTM-based encoder trained on speaker verification. Fast and lightweight.",
  },
  {
    id: "ecapa",
    label: "ECAPA-TDNN",
    description: "CNN-based encoder with channel attention. Strong on short utterances.",
  },
  {
    id: "hubert",
    label: "HuBERT",
    description: "Transformer-based self-supervised model. Captures deep speech features.",
  },
] as const;

interface EncoderSelectorProps {
  selected: string[];
  onChange: (encoders: string[]) => void;
  disabled: boolean;
}

export default function EncoderSelector({ selected, onChange, disabled }: EncoderSelectorProps) {
  const noneSelected = selected.length === 0;

  function toggle(id: string) {
    if (selected.includes(id)) {
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
      <div className="flex flex-col gap-3">
        {ENCODERS.map(({ id, label, description }) => {
          const checked = selected.includes(id);
          return (
            <label
              key={id}
              className={`
                flex items-start gap-3 rounded-lg border px-3 py-2 text-sm
                transition-colors select-none cursor-pointer
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
                disabled={disabled}
                onChange={() => toggle(id)}
                className="accent-blue-600 mt-0.5"
              />
              <div>
                <span className="font-medium">{label}</span>
                <p className={`text-xs mt-0.5 ${checked ? "text-blue-600 dark:text-blue-400" : "text-zinc-500 dark:text-zinc-500"}`}>
                  {description}
                </p>
              </div>
            </label>
          );
        })}
      </div>
      {noneSelected && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">
          At least one encoder must be selected.
        </p>
      )}
    </fieldset>
  );
}
