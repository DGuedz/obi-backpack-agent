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
      <footer className="border-t border-zinc-800 bg-black text-zinc-400 text-xs sm:text-sm py-6 px-6">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-2">
          <span>Registro de Software: OBI Agent (VSC Protocol) © 2026 Diego Guedes Da Silva</span>
          <span>
            Licença:{" "}
            <a
              className="text-emerald-400 hover:text-emerald-300"
              href="https://creativecommons.org/licenses/by/4.0/"
              target="_blank"
              rel="noreferrer"
            >
              CC BY 4.0
            </a>{" "}
            · Repositório:{" "}
            <a
              className="text-emerald-400 hover:text-emerald-300"
              href="https://github.com/doublegreen/backpacktrading"
              target="_blank"
              rel="noreferrer"
            >
              https://github.com/doublegreen/backpacktrading
            </a>{" "}
            · Autor:{" "}
            <a
              className="text-emerald-400 hover:text-emerald-300"
              href="https://x.com/dg_doublegreen"
              target="_blank"
              rel="noreferrer"
            >
              https://x.com/dg_doublegreen
            </a>
          </span>
        </div>
      </footer>
    </main>
  );
}
