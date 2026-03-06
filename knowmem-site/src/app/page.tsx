import { Navbar } from "@/components/navbar";
import { HeroSection } from "@/components/landing/hero";
import { ProblemSection } from "@/components/landing/problem-section";
import { HowItWorksSection } from "@/components/landing/how-it-works";
import { BenchmarkSection } from "@/components/landing/benchmark-table";
import { ArchitectureSection } from "@/components/landing/architecture";
import { CTASection } from "@/components/landing/cta-section";
import { Footer } from "@/components/footer";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">
        <HeroSection />
        <ProblemSection />
        <HowItWorksSection />
        <BenchmarkSection />
        <ArchitectureSection />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
