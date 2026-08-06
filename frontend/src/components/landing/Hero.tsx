import Link from "next/link";
import Image from "next/image";

export default function Hero() {
  return (
    <section className="relative bg-white pt-[208px] pb-0 overflow-hidden">
      {/* Background waveform image */}
      <div className="absolute top-[67px] right-0 w-[68%] h-[631px] pointer-events-none">
        <Image
          src="/hero-waveform.png"
          alt=""
          fill
          className="object-contain"
          priority
        />
      </div>
      {/* White gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-white via-white/80 to-transparent pointer-events-none" />

      <div className="relative z-10 max-w-[1200px] mx-auto px-8">
        <div className="max-w-[900px]">
          <h1 className="text-[clamp(3rem,6vw,5.8rem)] font-bold text-text-heading leading-[1.05] tracking-[-3px]">
            Protect your{" "}
            <em className="italic font-serif font-bold text-navy">voice</em>
            <br />
            before it&apos;s stolen.
          </h1>

          <p className="mt-10 text-lg text-text-body max-w-[560px] leading-[1.65]">
            SignalShield prevents deepfakes at the source. By adding invisible,
            inaudible protection directly to your voice recordings, it scrambles
            AI tools before they can clone you.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-start gap-4">
            <Link
              href="/app"
              target="_blank"
              className="inline-flex items-center rounded-full bg-accent px-8 py-4 text-base font-medium text-white hover:bg-accent-hover transition-colors shadow-[0px_10px_7.5px_rgba(0,0,0,0.1),0px_4px_3px_rgba(0,0,0,0.1)]"
            >
              Start Protecting Now
            </Link>
            <a
              href="#how-it-works"
              className="inline-flex items-center rounded-full border border-[#dde1e6] bg-white px-8 py-4 text-base font-medium text-text-heading hover:bg-light-bg transition-colors"
            >
              See How It Works
            </a>
          </div>
        </div>
      </div>

      {/* Bottom banner */}
      <div className="relative z-10 mt-24 bg-navy py-4 overflow-hidden">
        <div className="flex animate-marquee whitespace-nowrap gap-6">
          {[...Array(2)].map((_, rep) => (
            <div key={rep} className="flex items-center gap-6">
              {[
                "Deepfake Prevention",
                "Voice Cloning Protection",
                "Invisible Watermarking",
                "AI Scrambling Tech",
                "API Access",
              ].map((label) => (
                <span key={`${rep}-${label}`} className="flex items-center gap-2 text-sm text-white/80 px-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                  {label}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
