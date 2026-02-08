"use client";

import { motion } from "framer-motion";
import { CheckCircle2, ArrowLeft, Wallet, ShieldCheck, Zap } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import ObiWorkLogo from "../components/ObiWorkLogo";

export default function AccessPage() {
  const [step, setStep] = useState<"idle" | "connecting" | "signing" | "success">("idle");
  const [walletAddress, setWalletAddress] = useState(() => {
    if (typeof window === "undefined") {
      return "";
    }
    return window.localStorage.getItem("obi_access_wallet") ?? "";
  });
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleConnect = async () => {
    setError(null);
    const trimmedWallet = walletAddress.trim();
    if (!trimmedWallet) {
      setError("Informe uma wallet válida.");
      return;
    }

    setStep("connecting");
    try {
      const res = await fetch("/api/access/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ walletAddress: trimmedWallet })
      });
      const data = await res.json();
      if (!res.ok || !data?.ok) {
        setError("Falha ao validar acesso. Tente novamente.");
        setStep("idle");
        return;
      }
      const allowed = Boolean(data?.gatekeeper?.allowed);
      if (!allowed) {
        setError("Acesso pendente. Sua wallet não possui permissão.");
        setStep("idle");
        return;
      }
      setStep("signing");
      window.localStorage.setItem("obi_access_wallet", trimmedWallet);
      window.localStorage.setItem("obi_access_allowed", "true");
      setTimeout(() => {
        setStep("success");
        setTimeout(() => {
          router.push("/dashboard");
        }, 1500);
      }, 700);
    } catch {
      setError("Falha ao validar acesso. Tente novamente.");
      setStep("idle");
    }
  };

  return (
    <div className="min-h-screen bg-black text-white font-mono selection:bg-emerald-500/30 flex flex-col relative overflow-hidden">
       
       {/* Background Effects */}
       <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10 pointer-events-none" />
       <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-emerald-500/5 rounded-full blur-[100px] pointer-events-none" />

       <nav className="border-b border-zinc-800 p-6 relative z-10">
         <Link href="/" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors w-fit">
            <ArrowLeft className="w-4 h-4" />
            <span>RETURN TO BASE</span>
         </Link>
       </nav>

       <main className="flex-1 flex flex-col items-center justify-center p-6 text-center relative z-10">
          
          <motion.div 
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="w-full max-w-md"
          >
             <div className="flex justify-center mb-8">
                <ObiWorkLogo size="lg" />
             </div>

             <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-1 overflow-hidden shadow-2xl backdrop-blur-xl">
                <div className="p-8 md:p-10 flex flex-col items-center">
                    
                    {/* ICON STATE */}
                    <div className="mb-8 relative">
                        <div className={`w-24 h-24 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${
                            step === "success" ? "bg-emerald-500/20 border-emerald-500 text-emerald-500" :
                            step === "signing" ? "bg-blue-500/20 border-blue-500 text-blue-500" :
                            step === "connecting" ? "bg-yellow-500/20 border-yellow-500 text-yellow-500" :
                            "bg-zinc-800 border-zinc-700 text-zinc-400"
                        }`}>
                            {step === "success" ? <CheckCircle2 className="w-10 h-10" /> :
                             step === "signing" ? <ShieldCheck className="w-10 h-10 animate-pulse" /> :
                             step === "connecting" ? <Zap className="w-10 h-10 animate-pulse" /> :
                             <Wallet className="w-10 h-10" />}
                        </div>
                        
                        {/* Orbiting particles for connecting state */}
                        {(step === "connecting" || step === "signing") && (
                            <motion.div 
                                animate={{ rotate: 360 }}
                                transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                                className="absolute inset-0 rounded-full border-t-2 border-r-2 border-transparent"
                                style={{ 
                                    borderColor: step === "signing" ? "rgba(59, 130, 246, 0.5)" : "rgba(234, 179, 8, 0.5)",
                                    borderTopColor: "transparent", 
                                    borderRightColor: "transparent"
                                }} 
                            />
                        )}
                    </div>

                    {/* TEXT STATE */}
                    <h1 className="text-2xl font-bold mb-2">
                        {step === "success" ? "ACCESS GRANTED" :
                         step === "signing" ? "VERIFYING CREDENTIALS" :
                         step === "connecting" ? "CONNECTING..." :
                         "CONNECT WALLET"}
                    </h1>
                    
                    <p className="text-zinc-500 text-sm mb-6 h-10">
                        {step === "success" ? "Redirecting to Command Center..." :
                         step === "signing" ? "Signing cryptographic handshake..." :
                         step === "connecting" ? "Establishing secure channel with Backpack..." :
                         "Sync your Backpack Wallet to access the OBIWORK Terminal."}
                    </p>

                    {step === "idle" && (
                        <input
                            type="text"
                            value={walletAddress}
                            onChange={(event) => setWalletAddress(event.target.value)}
                            placeholder="Wallet Address (Solana/Backpack)"
                            className="w-full mb-6 bg-black/50 border border-zinc-700 rounded-xl p-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 transition-all"
                        />
                    )}

                    {/* ACTION BUTTON */}
                    {step === "idle" && (
                        <button 
                            onClick={handleConnect}
                            className="w-full group relative overflow-hidden rounded-xl bg-gradient-to-br from-red-600 to-red-700 p-px hover:shadow-[0_0_20px_rgba(220,38,38,0.4)] transition-all duration-300"
                        >
                            <div className="relative h-14 w-full bg-black rounded-xl flex items-center justify-center gap-3 group-hover:bg-zinc-900 transition-colors">
                                <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white font-bold text-xs">
                                    
                                </div>
                                <span className="font-bold text-white tracking-wider">CONNECT BACKPACK</span>
                            </div>
                        </button>
                    )}

                    {step !== "idle" && (
                        <div className="w-full h-14 flex items-center justify-center gap-2 text-xs font-mono text-zinc-600 bg-black/50 rounded-xl border border-zinc-800/50">
                            <div className="flex gap-1">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse delay-75"></span>
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse delay-150"></span>
                            </div>
                            ENCRYPTED CONNECTION
                        </div>
                    )}

                    {error && (
                        <div className="mt-6 text-sm text-red-400">
                            {error}
                        </div>
                    )}
                </div>
                
                {/* Footer of Card */}
                <div className="bg-zinc-900/80 p-4 border-t border-zinc-800 flex justify-between items-center text-[10px] text-zinc-500 font-mono">
                    <span>STATUS: {step === "idle" ? "WAITING" : "ACTIVE"}</span>
                    <span>V4.0.2 STABLE</span>
                </div>
             </div>

             <div className="mt-8 text-zinc-600 text-xs">
                By connecting, you agree to the <span className="text-zinc-400 hover:text-white cursor-pointer underline">Harvester Protocol</span> terms.
             </div>
          </motion.div>

       </main>
    </div>
  );
}
