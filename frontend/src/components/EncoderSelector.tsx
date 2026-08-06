"use client";

const ENCODERS = [
  {
    id: "xvector",
    label: "X-Vector",
    description: "TDNN-based encoder with statistics pooling. Fast and lightweight.",
    color: "text-[#0047ab]",
    checkBg: "bg-[#0047ab]",
    borderColor: "border-[#0047ab]/30",
  },
  {
    id: "ecapa",
    label: "ECAPA-TDNN",
    description: "CNN-based encoder with channel attention. Strong on short utterances.",
    color: "text-[#16a34a]",
    checkBg: "bg-[#16a34a]",
    borderColor: "border-[#16a34a]/30",
  },
  {
    id: "hubert",
    label: "HuBERT",
    description: "Transformer-based self-supervised model. Captures deep speech features.",
    color: "text-[#0891b2]",
    checkBg: "bg-[#0891b2]",
    borderColor: "border-[#0891b2]/30",
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
    <fieldset className="mt-8 mb-2" disabled={disabled}>
      <legend className="text-[13px] font-medium text-[#52575c] uppercase tracking-[0.65px] mb-3">
        Target encoders to defend against
      </legend>
      <div className="flex flex-col gap-3">
        {ENCODERS.map(({ id, label, description, color, checkBg, borderColor }) => {
          const checked = selected.includes(id);
          return (
            <label
              key={id}
              className={`
                flex items-start gap-4 rounded-[14px] border p-[17px] text-sm
                transition-colors select-none cursor-pointer
                shadow-[0px_1px_1.5px_rgba(0,0,0,0.1),0px_1px_1px_rgba(0,0,0,0.1)]
                ${disabled
                  ? "border-[#eaedf2] bg-[#f8f9fc] text-[#878b8f] cursor-not-allowed"
                  : checked
                    ? `${borderColor} bg-white`
                    : "border-[#eaedf2] bg-white hover:border-[#0047ab]/20"
                }
              `}
            >
              <div className="mt-1 flex-shrink-0">
                <div className={`w-3 h-3 rounded-[6px] flex items-center justify-center ${
                  checked ? checkBg : "bg-[#eaedf2]"
                }`}>
                  {checked && (
                    <svg width="9" height="9" viewBox="0 0 9 9" fill="none">
                      <path d="M1.5 4.5L3.5 6.5L7.5 2.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
                </div>
              </div>
              <div>
                <span className={`text-sm font-medium ${checked ? color : "text-[#0a0b0d]"}`}>{label}</span>
                <p className="text-[13px] font-medium text-[#878b8f] mt-0.5">
                  {description}
                </p>
              </div>
              <input
                type="checkbox"
                checked={checked}
                disabled={disabled}
                onChange={() => toggle(id)}
                className="sr-only"
              />
            </label>
          );
        })}
      </div>
      {noneSelected && (
        <p className="mt-2 text-sm text-red-600">
          At least one encoder must be selected.
        </p>
      )}
    </fieldset>
  );
}
