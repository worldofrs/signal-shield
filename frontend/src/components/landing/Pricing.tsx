import Link from "next/link";

const TIERS = [
  {
    name: "Free",
    price: "$0",
    period: "",
    description: "Try it out. No credit card required.",
    features: [
      "5 minutes of audio per month",
      "All 3 protection models included",
      "Full audio quality preservation",
      "No overage charges",
    ],
    cta: "Get Started",
    highlighted: false,
  },
  {
    name: "Creator",
    price: "$0",
    period: "/mo",
    description: "For podcasters, streamers, and voice actors.",
    features: [
      "Pay as you go \u2014 no monthly fee",
      "$0.30 per minute of audio",
      "All 3 protection models included",
      "Full audio quality preservation",
    ],
    cta: "Get Started",
    highlighted: true,
  },
  {
    name: "Pro",
    price: "$9.99",
    period: "/mo",
    description: "For professionals with regular uploads.",
    features: [
      "120 minutes of audio per month",
      "$0.10 per minute overage",
      "All 3 protection models included",
      "Priority processing",
    ],
    cta: "Get Started",
    highlighted: false,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="py-28 bg-light-bg">
      <div className="max-w-[1100px] mx-auto px-8">
        <div className="text-center">
          <span className="inline-block rounded-full bg-[#e0f0ff] px-4 py-1.5 text-[13px] font-medium text-accent">
            Pricing
          </span>
          <h2 className="mt-4 text-[clamp(2rem,4vw,2.9rem)] font-bold text-text-heading tracking-[-1.16px]">
            Simple, transparent pricing.
          </h2>
        </div>

        <div className="mt-6 flex justify-center">
          <span className="text-[15px] font-medium text-text-heading">Monthly</span>
        </div>

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
          {TIERS.map(({ name, price, period, description, features, cta, highlighted }) => (
            <div
              key={name}
              className={`rounded-2xl flex flex-col ${
                highlighted
                  ? "bg-navy text-white shadow-[0px_20px_25px_0px_rgba(0,0,0,0.1),0px_8px_10px_0px_rgba(0,0,0,0.1)]"
                  : "border border-border bg-white"
              }`}
            >
              <div className={`p-8 flex flex-col flex-1 ${highlighted ? "" : ""}`}>
                {highlighted && (
                  <span className="inline-block self-start rounded-full bg-accent px-3 py-1 text-[11px] font-medium text-white mb-4">
                    Most Popular
                  </span>
                )}
                <h3 className={`text-lg font-semibold ${highlighted ? "text-white" : "text-text-heading"}`}>
                  {name}
                </h3>
                <p className={`text-[13px] mt-1 ${highlighted ? "text-white/60" : "text-text-body"}`}>
                  {description}
                </p>
                <div className="mt-4 flex items-baseline gap-1 mb-6">
                  <span className={`text-[52px] font-bold leading-none ${highlighted ? "text-white" : "text-text-heading"}`}>
                    {price}
                  </span>
                  {period && (
                    <span className={`text-[15px] ${highlighted ? "text-white/60" : "text-text-muted"}`}>
                      {period}
                    </span>
                  )}
                </div>
                <ul className="flex-1 space-y-3 mb-8">
                  {features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2 text-sm">
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 16 16"
                        fill="none"
                        className={`flex-shrink-0 ${highlighted ? "text-accent" : "text-accent"}`}
                      >
                        <path
                          d="M4 8L7 11L12 5"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      <span className={highlighted ? "text-white/80" : "text-text-body"}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
                <Link
                  href="/app"
                  target="_blank"
                  className={`inline-flex items-center justify-center rounded-full px-4 py-3.5 text-[15px] font-medium transition-colors ${
                    highlighted
                      ? "bg-accent text-white hover:bg-accent-hover"
                      : "bg-text-heading text-white hover:bg-navy"
                  }`}
                >
                  {cta}
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
