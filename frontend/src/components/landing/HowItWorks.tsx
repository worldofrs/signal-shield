const STEPS = [
  {
    number: "01",
    title: "Upload your audio",
    description: "Drag and drop any WAV or MP3 file. Podcasts, voiceovers, music \u2014 anything with your voice.",
  },
  {
    number: "02",
    title: "Choose your shields",
    description: "Pick which AI models to defend against. More models means broader protection. We recommend using all three.",
  },
  {
    number: "03",
    title: "Download protected file",
    description: "Get back your audio with invisible protection baked in. It sounds identical \u2014 but AI cloning tools can\u2019t use it.",
  },
  {
    number: "04",
    title: "Publish with confidence",
    description: "Share your content anywhere. Your voice is protected before it ever reaches the internet.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-28 bg-navy">
      <div className="max-w-[1200px] mx-auto px-8">
        <div className="text-center mb-16">
          <span className="inline-block rounded-full bg-teal/20 px-4 py-1.5 text-[13px] font-medium text-teal">
            How It Works
          </span>
          <h2 className="mt-4 text-[clamp(2rem,4vw,2.9rem)] font-bold text-white leading-tight tracking-[-1.16px]">
            Up and running in minutes.
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {STEPS.map(({ number, title, description }) => (
            <div key={number}>
              <div className="text-[64px] font-bold text-white/10 leading-none">
                {number}
              </div>
              <h3 className="mt-4 text-lg font-semibold text-white">{title}</h3>
              <p className="mt-2 text-[15px] text-white/60 leading-relaxed">
                {description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
