import { Suspense } from "react";
import Hero from "./components/Hero";
import AirdropCalculator from "./components/AirdropCalculator";
import ProofSection from "./components/ProofSection";
import PricingSection from "./components/PricingSection";

export default function Home() {
  return (
    <main>
      <Hero />
      <AirdropCalculator />
      <ProofSection />
      <Suspense fallback={null}>
        <PricingSection />
      </Suspense>
    </main>
  );
}
