"use client";

import { WalletContextProvider } from "./context/WalletContextProvider";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <WalletContextProvider>
      {children}
    </WalletContextProvider>
  );
}
