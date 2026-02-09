"use client";

import { Suspense } from "react";
import Hero from "./components/Hero";
import AirdropCalculator from "./components/AirdropCalculator";
import ProofSection from "./components/ProofSection";
import PricingSection from "./components/PricingSection";
import ColosseumPositioning from "./components/ColosseumPositioning";
import { useLanguage } from "./context/LanguageContext";

function Footer() {
  const { language } = useLanguage();

  const TRANSLATIONS = {
    pt: {
      copyright: "Registro de Software: OBI Agent (VSC Protocol) © 2026 Diego Guedes Da Silva",
      license_label: "Licença:",
      repo_label: "Repositório:",
      author_label: "Autor:"
    },
    en: {
      copyright: "Software Registration: OBI Agent (VSC Protocol) © 2026 Diego Guedes Da Silva",
      license_label: "License:",
      repo_label: "Repository:",
      author_label: "Author:"
    }
  };

  const t = TRANSLATIONS[language];

  return (
    <footer className="border-t border-zinc-700 bg-black text-zinc-100 text-xs sm:text-sm py-6 px-6">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-2">
        <span>{t.copyright}</span>
        <span>
          {t.license_label}{" "}
          <a
            className="text-emerald-300 hover:text-emerald-200"
            href="https://creativecommons.org/licenses/by/4.0/"
            target="_blank"
            rel="noreferrer"
          >
            CC BY 4.0
          </a>{" "}
          · {t.repo_label}{" "}
          <a
            className="text-emerald-300 hover:text-emerald-200"
            href="https://github.com/doublegreen/backpacktrading"
            target="_blank"
            rel="noreferrer"
          >
            https://github.com/doublegreen/backpacktrading
          </a>{" "}
          · {t.author_label}{" "}
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
