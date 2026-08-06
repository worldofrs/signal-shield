const STATS = [
  { value: "105k", label: "Deepfakes made a year" },
  { value: "96%", label: "Victims are non-consenting" },
  { value: "17%", label: "in personal identity theft" },
  { value: "1", label: "deepfake every five mins" },
];

export default function Problem() {
  return (
    <section id="problem" className="py-28 bg-light-bg">
      <div className="max-w-[1200px] mx-auto px-8">
        <div className="text-center">
          <span className="inline-block rounded-full bg-green/30 px-4 py-1.5 text-[13px] font-medium text-green">
            The Problem
          </span>
          <h2 className="mt-4 text-[clamp(2rem,4vw,3.25rem)] font-bold text-text-heading leading-tight tracking-[-1.3px]">
            Your identity is being stolen
            <br />
            right now.
          </h2>
          <p className="mt-4 text-[17px] text-text-body max-w-[580px] mx-auto leading-[1.625]">
            AI tools can clone any voice in minutes. Deepfakes occur at a rate of
            once every 5 minutes.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-2 lg:grid-cols-4 gap-6">
          {STATS.map(({ value, label }) => (
            <div
              key={value}
              className="rounded-2xl border border-border bg-white px-6 py-6 text-center shadow-[0px_1px_1.5px_rgba(0,0,0,0.1),0px_1px_1px_rgba(0,0,0,0.1)]"
            >
              <div className="text-5xl font-bold text-accent">{value}</div>
              <p className="mt-2 text-sm font-medium text-text-body">{label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
