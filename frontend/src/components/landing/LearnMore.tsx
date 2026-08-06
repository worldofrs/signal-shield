export default function LearnMore() {
  return (
    <section id="learn-more" className="py-28 bg-white">
      <div className="max-w-[1100px] mx-auto px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <span className="inline-block rounded-full bg-green/30 px-4 py-1.5 text-[13px] font-medium text-green mb-4">
              API
            </span>
            <h2 className="text-[clamp(2rem,4vw,2.9rem)] font-bold text-text-heading tracking-[-1.16px] mb-4">
              Learn more
            </h2>

            <div className="text-[17px] text-text-body leading-[1.625] space-y-4">
              <p>
                Sound has two properties at every frequency: loudness (how
                loud that frequency is) and phase (the timing offset of the
                sound wave). Human ears are sensitive to loudness but mostly
                deaf to phase, especially at high frequencies.
              </p>
              <p>
                Cloning models, however, use both. Signal Shield scrambles
                the phase above 10,000 Hz. Humans can&apos;t hear the difference,
                but cloning models get corrupted input.
              </p>
            </div>
          </div>

          <div className="rounded-2xl bg-navy p-6 overflow-x-auto shadow-[0px_20px_25px_-5px_rgba(0,0,0,0.1),0px_8px_10px_-6px_rgba(0,0,0,0.1)]">
            <pre className="text-sm font-mono leading-7">
              <code>
                <span className="text-text-muted">{"// Protect a voice file in one line"}</span>
                {"\n\n"}
                <span className="text-teal">import</span>
                <span className="text-white"> SignalShield </span>
                <span className="text-teal">from</span>
                <span className="text-orange-400"> &apos;@signalshield/sdk&apos;</span>
                {"\n\n"}
                <span className="text-teal">const</span>
                <span className="text-white"> protected = </span>
                <span className="text-teal">await</span>
                <span className="text-[#f8d06b]"> shield</span>
                <span className="text-white">.protect(</span>
                {"\n"}
                <span className="text-white">  audioFile,</span>
                {"\n"}
                <span className="text-white">  {"{ "}</span>
                <span className="text-sky-300">mode</span>
                <span className="text-white">: </span>
                <span className="text-orange-400">&apos;voice&apos;</span>
                <span className="text-white">, </span>
                <span className="text-sky-300">strength</span>
                <span className="text-white">: </span>
                <span className="text-[#f8d06b]">0.9</span>
                <span className="text-white">{" }"}</span>
                {"\n"}
                <span className="text-white">)</span>
                {"\n\n"}
                <span className="text-green">{"// \u2713 Protected \u2014 AI cloning blocked"}</span>
              </code>
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}
