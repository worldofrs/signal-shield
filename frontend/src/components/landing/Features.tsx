const FEATURES = [
  {
    title: "Frame-by-Frame Audio Disturbance",
    description:
      "A drag and drop interface that alters the inaudible frequencies of your audio so that your audio sounds the same, but a malicious bot is unable to misconstrue your words.",
  },
  {
    title: "Platform-Level Audio Noise Injection API",
    description:
      "A drag and drop interface that alters the inaudible frequencies of your audio so that your audio sounds the same, but a malicious bot is unable to misconstrue your words.",
  },
];

export default function Features() {
  return (
    <section id="features" className="py-28 bg-white">
      <div className="max-w-[1200px] mx-auto px-8">
        <div className="mb-12">
          <span className="inline-block rounded-full bg-[#e0f0ff] px-4 py-1.5 text-[13px] font-medium text-accent">
            Features
          </span>
          <h2 className="mt-4 text-[clamp(2rem,4vw,2.9rem)] font-bold text-text-heading leading-tight tracking-[-1.16px]">
            Everything you need to
            <br />
            stay unclonable.
          </h2>
        </div>

        <div className="max-w-[774px]">
          <div
            className="rounded-2xl border border-border p-7 shadow-[0px_1px_3px_0px_rgba(0,0,0,0.1),0px_1px_2px_0px_rgba(0,0,0,0.1)]"
            style={{
              backgroundImage:
                "linear-gradient(155deg, rgba(224, 240, 255, 0.267) 0%, rgba(241, 248, 255, 0.45) 15%, rgba(248, 252, 255, 0.633) 30%, rgb(255, 255, 255) 60%)",
            }}
          >
            {/* Shield icon */}
            <div className="mb-5">
              <div className="inline-flex items-center justify-center w-9 h-9 rounded-full bg-teal">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L3 7V12C3 17.25 6.75 22.13 12 23C17.25 22.13 21 17.25 21 12V7L12 2Z" fill="white" fillOpacity="0.3" stroke="white" strokeWidth="1.5" />
                  <path d="M12 6L8 8.5V12C8 15 9.75 17.75 12 18.5C14.25 17.75 16 15 16 12V8.5L12 6Z" fill="white" fillOpacity="0.5" stroke="white" strokeWidth="1" />
                </svg>
              </div>
            </div>

            <span className="text-xs font-medium text-teal uppercase tracking-[0.6px]">
              Audio
            </span>

            <div className="mt-4 space-y-6">
              {FEATURES.map(({ title, description }) => (
                <div key={title}>
                  <h3 className="text-[22px] font-bold text-text-heading">{title}</h3>
                  <p className="mt-3 text-[15px] text-text-body leading-relaxed">
                    {description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
