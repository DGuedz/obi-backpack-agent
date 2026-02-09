"use client";

import { Suspense } from "react";
import Hero from "./components/Hero";
import AirdropCalculator from "./components/AirdropCalculator";
import ProofSection from "./components/ProofSection";
import PricingSection from "./components/PricingSection";
import ColosseumPositioning from "./components/ColosseumPositioning";

function Footer() {
  return (
    <footer className="border-t border-zinc-700 bg-black text-zinc-100 text-xs sm:text-sm py-6 px-6">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-2">
        <span>Software Registration: OBI Agent (VSC Protocol) © 2026 Diego Guedes Da Silva</span>
        <span>
          License:{" "}
          <a
            className="text-emerald-300 hover:text-emerald-200"
            href="https://creativecommons.org/licenses/by/4.0/"
            target="_blank"
            rel="noreferrer"
          >
            CC BY 4.0
          </a>{" "}
          · Repository:{" "}
          <a
            className="text-emerald-300 hover:text-emerald-200"
            href="https://github.com/doublegreen/backpacktrading"
            target="_blank"
            rel="noreferrer"
          >
            https://github.com/doublegreen/backpacktrading
          </a>{" "}
          · Author:{" "}
          <a
            className="text-emerald-300 hover:text-emerald-200"
            href="https://x.com/dg_doublegreen"
            target="_blank"
            rel="noreferrer"
          >
            https://x.com/dg_doublegreen
          </a>
        </span>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <main>
      <Hero />
      <ColosseumPositioning />
      <AirdropCalculator />
      <ProofSection />
      <Suspense fallback={null}>
        <PricingSection />
      </Suspense>
      <Footer />
    </main>
  );
}
