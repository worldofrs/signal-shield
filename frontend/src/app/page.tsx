import Navbar from "@/components/landing/Navbar";
import Hero from "@/components/landing/Hero";
import Problem from "@/components/landing/Problem";
import Comparison from "@/components/landing/Comparison";
import Features from "@/components/landing/Features";
import HowItWorks from "@/components/landing/HowItWorks";
import TryItFree from "@/components/landing/TryItFree";
import Pricing from "@/components/landing/Pricing";
import LearnMore from "@/components/landing/LearnMore";
import Footer from "@/components/landing/Footer";

export default function Home() {
  return (
    <>
      <Navbar />
      <Hero />
      <Problem />
      <Comparison />
      <Features />
      <HowItWorks />
      <TryItFree />
      <Pricing />
      <LearnMore />
      <Footer />
    </>
  );
}
