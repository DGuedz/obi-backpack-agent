"use client";

import { LanguageProvider } from "./context/LanguageContext";
import LanguageSwitcher from "./components/LanguageSwitcher";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <LanguageProvider>
      <LanguageSwitcher />
      {children}
    </LanguageProvider>
  );
}
