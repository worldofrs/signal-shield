import Link from "next/link";

const PRODUCT_LINKS = [
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
  { label: "How It Works", href: "#learn-more" },
];

export default function Footer() {
  return (
    <footer className="bg-text-heading py-16">
      <div className="max-w-[1200px] mx-auto px-8">
        <div className="flex flex-col md:flex-row justify-between gap-8">
          <div>
            <Link href="/" className="flex items-center gap-3 text-white">
              <div className="w-9 h-9 rounded-full bg-teal flex items-center justify-center">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L3 7V12C3 17.25 6.75 22.13 12 23C17.25 22.13 21 17.25 21 12V7L12 2Z" fill="white" fillOpacity="0.3" stroke="white" strokeWidth="1.5" />
                  <path d="M12 6L8 8.5V12C8 15 9.75 17.75 12 18.5C14.25 17.75 16 15 16 12V8.5L12 6Z" fill="white" fillOpacity="0.5" stroke="white" strokeWidth="1" />
                </svg>
              </div>
              <span className="text-lg font-semibold tracking-[-0.45px]">
                <span className="text-white">Signal</span>
                <span className="text-teal">Shield</span>
              </span>
            </Link>
            <p className="mt-4 text-sm text-white/50 max-w-[280px] leading-relaxed">
              Protecting your voice and identity from AI
              cloning and deepfake attacks.
            </p>
          </div>

          <div>
            <h4 className="text-[13px] font-semibold text-white/40 uppercase tracking-[0.65px] mb-4">
              Product
            </h4>
            <ul className="space-y-2.5">
              {PRODUCT_LINKS.map(({ label, href }) => (
                <li key={label}>
                  <a href={href} className="text-sm font-medium text-white/60 hover:text-white/80 transition-colors">
                    {label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </footer>
  );
}
