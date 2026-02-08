"use client";

import { LanguageProvider } from "./context/LanguageContext";
import LanguageSwitcher from "./components/LanguageSwitcher";
import { WalletContextProvider } from "./context/WalletContextProvider";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <WalletContextProvider>
      <LanguageProvider>
        <LanguageSwitcher />
        {children}
      </LanguageProvider>
    </WalletContextProvider>
  );
}
