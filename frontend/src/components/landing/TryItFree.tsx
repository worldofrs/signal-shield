const ENCODERS = [
  {
    name: "Resemblyzer",
    description: "GE2E-based model trained on VoxCeleb. Commonly used for speaker similarity and voice cloning pipelines.",
    color: "text-accent",
    checkBg: "bg-accent",
  },
  {
    name: "ECAPA-TDNN",
    description: "SpeechBrain\u2019s strong speaker embedding model. Strong on short utterances; top accuracy in voice auth tasks.",
    color: "text-green",
    checkBg: "bg-green",
  },
  {
    name: "HuBERT",
    description: "Self-supervised transformer from Meta AI. Powers RVC and many open-source voice cloning models.",
    color: "text-[#0891b2]",
    checkBg: "bg-[#0891b2]",
  },
];

export default function TryItFree() {
  return (
    <section className="py-28 bg-white">
      <div className="max-w-[1200px] mx-auto px-8">
        <div className="max-w-[860px] mx-auto">
          <div className="text-center mb-12">
            <span className="inline-block rounded-full bg-[#e0f0ff] px-4 py-1.5 text-[13px] font-medium text-accent">
              Try It Free
            </span>
            <h2 className="mt-4 text-[clamp(2rem,4vw,2.9rem)] font-bold text-text-heading tracking-[-1.16px]">
              Protect your voice in seconds.
            </h2>
            <p className="mt-4 text-[17px] text-text-body max-w-[520px] mx-auto leading-[1.625]">
              Upload an audio file and download a protected version that
              sounds identical to humans but is unusable for voice cloning.
            </p>
          </div>

          <div className="rounded-3xl border border-border bg-light-bg p-8">
            {/* Upload area */}
            <div className="border-2 border-dashed border-[#c8cdd5] rounded-2xl bg-white py-12 text-center min-h-[180px] flex flex-col items-center justify-center">
              <div className="w-14 h-14 rounded-2xl bg-[#e8edf4] flex items-center justify-center mb-4">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#52575c" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>
              <p className="text-base font-semibold text-text-heading">
                Drag &amp; drop an audio file here
              </p>
              <p className="text-sm text-text-muted mt-1">
                or <span className="text-accent underline">click to browse</span> &mdash; WAV, .mp3, up to 50MB
              </p>
            </div>

            {/* Encoder selector */}
            <div className="mt-8">
              <p className="text-[13px] font-medium text-text-body uppercase tracking-[0.65px] mb-3">
                Target encoders to defend against
              </p>
              <div className="space-y-3">
                {ENCODERS.map(({ name, description, color, checkBg }) => (
                  <div
                    key={name}
                    className="flex items-start gap-4 rounded-[14px] border border-accent/30 bg-white p-[17px] shadow-[0px_1px_1.5px_rgba(0,0,0,0.1),0px_1px_1px_rgba(0,0,0,0.1)]"
                  >
                    <div className="mt-1 flex-shrink-0">
                      <div className={`w-3 h-3 rounded-[6px] ${checkBg} flex items-center justify-center`}>
                        <svg width="9" height="9" viewBox="0 0 9 9" fill="none">
                          <path d="M1.5 4.5L3.5 6.5L7.5 2.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      </div>
                    </div>
                    <div>
                      <span className={`text-sm font-medium ${color}`}>{name}</span>
                      <p className="text-[13px] font-medium text-text-muted mt-0.5">{description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
