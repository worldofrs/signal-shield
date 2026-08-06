"use client";

import { useState } from "react";
import Link from "next/link";

const NAV_LINKS = [
  { label: "Problem", href: "#problem" },
  { label: "Features", href: "#features" },
  { label: "Pricing", href: "#pricing" },
  { label: "API", href: "#learn-more" },
];

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 px-5 pt-[38px]">
      <div className="max-w-[1120px] mx-auto bg-white border border-[#dde1e6] shadow-[0px_4px_12px_rgba(0,0,0,0.12)] rounded-full px-10 h-[81px] flex items-center justify-between">
        <Link href="/" className="flex items-center gap-[10px] text-text-heading">
          <div className="w-9 h-9 rounded-full bg-teal flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L3 7V12C3 17.25 6.75 22.13 12 23C17.25 22.13 21 17.25 21 12V7L12 2Z" fill="white" fillOpacity="0.3" stroke="white" strokeWidth="1.5" />
              <path d="M12 6L8 8.5V12C8 15 9.75 17.75 12 18.5C14.25 17.75 16 15 16 12V8.5L12 6Z" fill="white" fillOpacity="0.5" stroke="white" strokeWidth="1" />
            </svg>
          </div>
          <span className="text-lg font-semibold tracking-[-0.45px]">
            <span>Signal</span>
            <span className="text-accent">Shield</span>
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ label, href }) => (
            <a
              key={label}
              href={href}
              className="px-4 py-2 text-base font-medium text-[#0f161e] hover:text-accent transition-colors rounded-full"
            >
              {label}
            </a>
          ))}
        </div>

        <div className="hidden md:block">
          <Link
            href="/app"
            target="_blank"
            className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-[10px] text-[15px] font-medium text-white hover:bg-accent-hover transition-colors shadow-[0px_4px_3px_rgba(0,0,0,0.1),0px_2px_2px_rgba(0,0,0,0.1)]"
          >
            Get Started
          </Link>
        </div>

        {/* Mobile menu button */}
        <button
          onClick={() => setMenuOpen(!menuOpen)}
          className="md:hidden text-text-body hover:text-text-heading"
          aria-label="Toggle menu"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            {menuOpen ? (
              <path d="M6 6L18 18M6 18L18 6" />
            ) : (
              <path d="M4 6H20M4 12H20M4 18H20" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden mt-2 max-w-[1120px] mx-auto bg-white rounded-2xl border border-border shadow-sm px-6 py-4 flex flex-col gap-4">
          {NAV_LINKS.map(({ label, href }) => (
            <a
              key={label}
              href={href}
              onClick={() => setMenuOpen(false)}
              className="text-base font-medium text-[#0f161e] hover:text-accent transition-colors"
            >
              {label}
            </a>
          ))}
          <Link
            href="/app"
            target="_blank"
            className="inline-flex items-center justify-center rounded-full bg-accent px-6 py-[10px] text-[15px] font-medium text-white hover:bg-accent-hover transition-colors"
          >
            Get Started
          </Link>
        </div>
      )}
    </nav>
  );
}
