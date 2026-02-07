"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Shield, ArrowRight, CheckCircle2, Lock, Loader2, AlertTriangle, FileText } from "lucide-react";
import Link from "next/link";
import { useLanguage } from "../context/LanguageContext";

const QUESTIONS = [
  { id: "q1", text: "Nome Completo (Full Name)", placeholder: "Ex: John Doe" },
  { id: "q2", text: "CPF / National ID (KYC Compliance)", placeholder: "Ex: 000.000.000-00" },
  { id: "q3", text: "Wallet Address (Solana/Backpack)", placeholder: "Ex: 5r6...xyz" },
  { id: "q4", text: "Email Principal", placeholder: "Ex: contact@domain.com" },
  { id: "q5", text: "Discord/Telegram Handle", placeholder: "Ex: @username" },
  { id: "q6", text: "Tempo de Mercado (Anos)", placeholder: "Ex: 2" },
  { id: "q7", text: "Capital Inicial Disponível (USDC)", placeholder: "Ex: 1000" },
  { id: "q8", text: "Perfil Técnico (Dev, Trader, ou Ambos?)", placeholder: "Ex: Trader" },
  { id: "q9", text: "Código de Referência (Referral)", placeholder: "Ex: OBI123 (Optional)" },
  { id: "q10", text: "Você aceita o Manifesto Black Mindz? (Sim/Não)", placeholder: "Sim" }
];

export default function ApplyPage() {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState<any>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const { language } = useLanguage();

  const handleNext = (e: React.FormEvent) => {
    e.preventDefault();
    if (step < QUESTIONS.length - 1) {
      setStep(step + 1);
    } else {
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    // Simulate API call
    setTimeout(() => {
      setIsSubmitting(false);
      setIsSuccess(true);
    }, 2000);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [QUESTIONS[step].id]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-black text-white font-mono flex flex-col">
      {/* Header */}
      <nav className="border-b border-zinc-800 p-6 flex justify-between items-center bg-zinc-900/50 backdrop-blur">
        <div className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-emerald-500" />
            <span className="font-bold tracking-widest">OBI WHITELIST</span>
        </div>
        <div className="text-xs text-zinc-500 uppercase tracking-widest">
            Protocol VSC v1.0
        </div>
      </nav>

      <div className="flex-1 flex items-center justify-center p-6 relative overflow-hidden">
        {/* Background Grid */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5 pointer-events-none"></div>

        <div className="w-full max-w-2xl relative z-10">
          
          <AnimatePresence mode="wait">
            {!isSuccess ? (
              <motion.div 
                key="form"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 md:p-12 shadow-2xl"
              >
                {/* Progress Bar */}
                <div className="w-full h-1 bg-zinc-800 rounded-full mb-8 overflow-hidden">
                    <motion.div 
                        className="h-full bg-emerald-500"
                        initial={{ width: 0 }}
                        animate={{ width: `${((step + 1) / QUESTIONS.length) * 100}%` }}
                    />
                </div>

                <form onSubmit={handleNext}>
                    <div className="mb-2 text-emerald-500 text-sm font-bold tracking-widest uppercase">
                        Question {step + 1} of {QUESTIONS.length}
                    </div>
                    
                    <h2 className="text-2xl md:text-3xl font-bold mb-8 text-white">
                        {QUESTIONS[step].text}
                    </h2>

                    <input
                        autoFocus
                        type="text"
                        value={formData[QUESTIONS[step].id] || ""}
                        onChange={handleChange}
                        placeholder={QUESTIONS[step].placeholder}
                        className="w-full bg-black/50 border border-zinc-700 rounded-xl p-4 text-lg text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/50 transition-all mb-8"
                    />

                    <div className="flex justify-between items-center">
                        <button
                            type="button"
                            onClick={() => setStep(Math.max(0, step - 1))}
                            disabled={step === 0}
                            className={`text-sm text-zinc-500 hover:text-white transition-colors ${step === 0 ? "opacity-0 pointer-events-none" : ""}`}
                        >
                            PREVIOUS
                        </button>

                        <button
                            type="submit"
                            disabled={!formData[QUESTIONS[step].id]}
                            className="bg-white hover:bg-zinc-200 text-black px-8 py-3 rounded-lg font-bold flex items-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isSubmitting ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    PROCESSING...
                                </>
                            ) : step === QUESTIONS.length - 1 ? (
                                "SUBMIT APPLICATION"
                            ) : (
                                <>
                                    NEXT STEP
                                    <ArrowRight className="w-4 h-4" />
                                </>
                            )}
                        </button>
                    </div>
                </form>
              </motion.div>
            ) : (
              <motion.div
                key="success"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-zinc-900 border border-zinc-800 rounded-2xl p-8 md:p-12 text-center shadow-2xl relative overflow-hidden"
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-emerald-500 via-emerald-400 to-emerald-600"></div>
                
                <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-emerald-500/20">
                    <CheckCircle2 className="w-10 h-10 text-emerald-500" />
                </div>

                <h2 className="text-3xl font-bold text-white mb-4">Application Received</h2>
                
                <div className="bg-black/30 border border-zinc-800 rounded-xl p-6 mb-8 text-left space-y-4">
                    <div className="flex gap-3">
                        <Lock className="w-5 h-5 text-zinc-400 shrink-0 mt-0.5" />
                        <div>
                            <h3 className="font-bold text-white text-sm mb-1">Under Review (5 Days)</h3>
                            <p className="text-xs text-zinc-400 leading-relaxed">
                                Your application is now with the Gatekeeper Team. We conduct a manual KYC and Wallet History check to ensure alignment with the Guild.
                            </p>
                        </div>
                    </div>
                    
                    <div className="flex gap-3">
                        <FileText className="w-5 h-5 text-zinc-400 shrink-0 mt-0.5" />
                        <div>
                            <h3 className="font-bold text-white text-sm mb-1">Payment & Access</h3>
                            <p className="text-xs text-zinc-400 leading-relaxed">
                                If approved, you will receive a <strong>Payment Link (USDC/SOL)</strong> via email/DM. Upon confirmation, your dashboard access and local installation code will be unlocked.
                            </p>
                        </div>
                    </div>
                </div>

                <Link href="/" className="block w-full">
                    <button className="w-full py-4 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-bold transition-colors">
                        RETURN TO HOME
                    </button>
                </Link>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="mt-8 text-center">
            <p className="text-[10px] text-zinc-600 uppercase tracking-widest">
                Protected by Shield Protocol • Gatekeeper Active
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
