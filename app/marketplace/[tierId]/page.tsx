"use client";

import { useParams } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowLeft, Check, Shield, Layers, Cpu, Server, Lock, UserPlus } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useLanguage, type Language } from "../../context/LanguageContext";

// --- Dictionary ---
type TierId = "scout" | "commander" | "architect";

type TierSpec = { label: string; value: string };

type TierContent = {
  role: string;
  tagline: string;
  desc: string;
  benefits: string[];
  specs: TierSpec[];
};

type PageContent = {
  back: string;
  secure_connection: string;
  access_denied: string;
  return: string;
  soulbound: string;
  core_benefits: string;
  total_investment: string;
  season_pass: string;
  available: string;
  verifying: string;
  minting: string;
  success: string;
  join: string;
  dashboard: string;
  harvester: string;
  tech_specs: string;
  spots_warning: string;
  sections: {
    scout: TierContent;
    commander: TierContent;
    architect: TierContent;
  };
};

type TierData = {
  id: TierId;
  name: string;
  role: string;
  price: number;
  sbt: string;
  color: string;
  accent: string;
  border: string;
  bg_gradient: string;
  icon: LucideIcon;
  tagline: string;
  description: string;
  benefits: string[];
  technical_specs: TierSpec[];
};

const CONTENT: Record<Language, PageContent> = {
  pt: {
    back: "VOLTAR AO MARKETPLACE",
    secure_connection: "CONEXÃO SEGURA",
    access_denied: "ACESSO NEGADO",
    return: "Voltar ao Marketplace",
    soulbound: "SOULBOUND TOKEN:",
    core_benefits: "BENEFÍCIOS PRINCIPAIS",
    total_investment: "Contribuição Inicial",
    season_pass: "Passe de Temporada",
    available: "Apenas Whitelist",
    verifying: "VERIFICANDO VAGAS...",
    minting: "INICIANDO APLICAÇÃO...",
    success: "REDIRECIONANDO",
    join: "APLICAR PARA BLACKLIST",
    dashboard: "ACESSAR TERMINAL",
    harvester: "Inclui contrato de 3% de Taxa de Sucesso (The Harvester).",
    spots_warning: "Vagas limitadas. Confirmação manual necessária.",
    tech_specs: "ESPECIFICAÇÕES TÉCNICAS",
    sections: {
      scout: {
        role: "O Soldado",
        tagline: "Sobreviva. Acumule. Execute.",
        desc: "O PARTNER SCOUT é a sua porta de entrada. Você recebe acesso ao CLI (Command Line Interface) para operar com a mesma infraestrutura dos profissionais, mas com proteções ativas (Sentinel) que impedem erros fatais.",
        benefits: [
          "Acesso Vitalício ao CLI",
          "Estratégia Phoenix V2 (RSI + Bollinger)",
          "Proteção Sentinel (Stop-Loss Inteligente)",
          "Fee Saver Logic (Maker-Only)",
          "Comunidade Discord (Scout Access)"
        ],
        specs: [
          { label: "Velocidade Execução", value: "Padrão (API)" },
          { label: "Max Threads", value: "1 Instância" },
          { label: "Motor de Risco", value: "Modo Conservador" }
        ]
      },
      commander: {
        role: "O Capitão",
        tagline: "Escalabilidade. Yield. Volume.",
        desc: "Para quem joga o jogo do volume. O LIQUIDITY PROVIDER libera o poder das Subcontas e estratégias de Delta Neutral, permitindo que você farme Airdrops e taxas de Funding sem se expor à volatilidade do preço.",
        benefits: [
          "Tudo do Tier Scout",
          "Módulo Delta Neutral (Yield Harvester)",
          "Weaver Grid V2 (Volatility Harvesting)",
          "Gestão de Subcontas (Multi-Strategy)",
          "Prioridade na Fila de Execução"
        ],
        specs: [
          { label: "Velocidade Execução", value: "Alta (Async)" },
          { label: "Max Threads", value: "5 Instâncias" },
          { label: "Motor de Risco", value: "Hedging Dinâmico" }
        ]
      },
      architect: {
        role: "O General",
        tagline: "Visão Total. Domínio Absoluto.",
        desc: "O ápice da cadeia alimentar. O INSTITUTIONAL PARTNER oferece acesso direto aos dados de Order Book Imbalance (OBI) e consultoria dedicada para transformar sua infraestrutura em um bunker financeiro.",
        benefits: [
          "Tudo do Tier Commander",
          "Market Proxy Oracle (Acesso Dados OBI)",
          "Websockets Dedicados (HFT)",
          "Iron Dome Setup (VPS Blindada)",
          "Consultoria 1-on-1 com Core Team"
        ],
        specs: [
          { label: "Velocidade Execução", value: "Ultra-Baixa Latência" },
          { label: "Max Threads", value: "Ilimitado" },
          { label: "Motor de Risco", value: "Customizável" }
        ]
      }
    }
  },
  en: {
    back: "BACK TO MARKETPLACE",
    secure_connection: "SECURE CONNECTION",
    access_denied: "ACCESS DENIED",
    return: "Return to Marketplace",
    soulbound: "SOULBOUND TOKEN:",
    core_benefits: "CORE BENEFITS",
    total_investment: "Initial Contribution",
    season_pass: "Season Pass",
    available: "Whitelist Only",
    verifying: "CHECKING SPOTS...",
    minting: "STARTING APPLICATION...",
    success: "REDIRECTING",
    join: "APPLY FOR BLACKLIST",
    dashboard: "ACCESS TERMINAL",
    harvester: "Includes 3% Success Fee Contract (The Harvester).",
    spots_warning: "Limited spots. Manual approval required.",
    tech_specs: "TECHNICAL SPECIFICATIONS",
    sections: {
      scout: {
        role: "The Soldier",
        tagline: "Survive. Accumulate. Execute.",
        desc: "The PARTNER SCOUT is your entry point. You get access to the CLI (Command Line Interface) to trade with the same infrastructure as professionals, but with active protections (Sentinel) that prevent fatal errors.",
        benefits: [
          "Lifetime CLI Access",
          "Phoenix V2 Strategy (RSI + Bollinger)",
          "Sentinel Protection (Smart Stop-Loss)",
          "Fee Saver Logic (Maker-Only)",
          "Discord Community (Scout Access)"
        ],
        specs: [
          { label: "Execution Speed", value: "Standard (API)" },
          { label: "Max Threads", value: "1 Instance" },
          { label: "Risk Engine", value: "Conservative Mode" }
        ]
      },
      commander: {
        role: "The Captain",
        tagline: "Scalability. Yield. Volume.",
        desc: "For those playing the volume game. The LIQUIDITY PROVIDER unleashes the power of Subaccounts and Delta Neutral strategies, allowing you to farm Airdrops and Funding fees without price volatility exposure.",
        benefits: [
          "Everything in Scout Tier",
          "Delta Neutral Module (Yield Harvester)",
          "Weaver Grid V2 (Volatility Harvesting)",
          "Subaccount Management (Multi-Strategy)",
          "Execution Queue Priority"
        ],
        specs: [
          { label: "Execution Speed", value: "High (Async)" },
          { label: "Max Threads", value: "5 Instances" },
          { label: "Risk Engine", value: "Dynamic Hedging" }
        ]
      },
      architect: {
        role: "The General",
        tagline: "Total Vision. Absolute Dominion.",
        desc: "The apex of the food chain. The INSTITUTIONAL PARTNER offers direct access to Order Book Imbalance (OBI) data and dedicated consultancy to transform your infrastructure into a financial bunker.",
        benefits: [
          "Everything in Commander Tier",
          "Market Proxy Oracle (OBI Data Access)",
          "Dedicated Websockets (HFT)",
          "Iron Dome Setup (Armored VPS)",
          "1-on-1 Consultancy with Core Team"
        ],
        specs: [
          { label: "Execution Speed", value: "Ultra-Low Latency" },
          { label: "Max Threads", value: "Unlimited" },
          { label: "Risk Engine", value: "Customizable" }
        ]
      }
    }
  }
};

// --- Data Generator ---
const getTiersData = (lang: Language): Record<TierId, TierData> => ({
  scout: {
    id: "scout",
    name: "PARTNER SCOUT",
    role: CONTENT[lang].sections.scout.role,
    price: 29.99,
    sbt: "OBI-SCOUT",
    color: "emerald",
    accent: "text-emerald-400",
    border: "border-emerald-500",
    bg_gradient: "from-emerald-900/20 to-black",
    icon: Shield,
    tagline: CONTENT[lang].sections.scout.tagline,
    description: CONTENT[lang].sections.scout.desc,
    benefits: CONTENT[lang].sections.scout.benefits,
    technical_specs: CONTENT[lang].sections.scout.specs
  },
  commander: {
    id: "commander",
    name: "LIQUIDITY PROVIDER",
    role: CONTENT[lang].sections.commander.role,
    price: 49.90,
    sbt: "OBI-CMDR",
    color: "blue",
    accent: "text-blue-400",
    border: "border-blue-500",
    bg_gradient: "from-blue-900/20 to-black",
    icon: Layers,
    tagline: CONTENT[lang].sections.commander.tagline,
    description: CONTENT[lang].sections.commander.desc,
    benefits: CONTENT[lang].sections.commander.benefits,
    technical_specs: CONTENT[lang].sections.commander.specs
  },
  architect: {
    id: "architect",
    name: "INSTITUTIONAL PARTNER",
    role: CONTENT[lang].sections.architect.role,
    price: 99.00,
    sbt: "OBI-ARCH",
    color: "yellow",
    accent: "text-yellow-400",
    border: "border-yellow-500",
    bg_gradient: "from-yellow-900/20 to-black",
    icon: Cpu,
    tagline: CONTENT[lang].sections.architect.tagline,
    description: CONTENT[lang].sections.architect.desc,
    benefits: CONTENT[lang].sections.architect.benefits,
    technical_specs: CONTENT[lang].sections.architect.specs
  }
});

export default function TierDetailPage() {
  const params = useParams();
  const tierId = params.tierId as string;
  const [status, setStatus] = useState<"idle" | "verifying" | "payment" | "processing" | "success" | "error">("idle");
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [paymentRef, setPaymentRef] = useState<string | null>(null);
  const [paymentForm, setPaymentForm] = useState({
    walletAddress: "",
    email: "",
    cardNumber: "",
    cardHolder: "",
    cardExpiry: "",
    cardCvc: "",
    cardBrand: "Visa"
  });
  const { language } = useLanguage();
  const t = CONTENT[language];
  const tiersData = getTiersData(language);
  const isValidTier = tierId === "scout" || tierId === "commander" || tierId === "architect";
  const tier = isValidTier ? tiersData[tierId as TierId] : undefined;

  const handleMint = () => {
    setPaymentError(null);
    setStatus("verifying");
    setTimeout(() => {
      setStatus("payment");
    }, 700);
  };

  const handlePayment = async () => {
    setPaymentError(null);
    if (!tier) {
      setPaymentError(language === "pt" ? "Plano inválido." : "Invalid tier.");
      setStatus("payment");
      return;
    }
    if (!paymentForm.walletAddress || !paymentForm.cardNumber || !paymentForm.cardHolder || !paymentForm.cardExpiry || !paymentForm.cardCvc) {
      setPaymentError(language === "pt" ? "Preencha todos os campos obrigatórios." : "Fill in all required fields.");
      return;
    }
    setStatus("processing");
    try {
      const res = await fetch("/api/payments/cielo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          walletAddress: paymentForm.walletAddress,
          tierId: tier.id,
          amount: tier.price,
          email: paymentForm.email,
          customerName: paymentForm.cardHolder,
          cardData: {
            number: paymentForm.cardNumber,
            holder: paymentForm.cardHolder,
            expiry: paymentForm.cardExpiry,
            cvc: paymentForm.cardCvc,
            brand: paymentForm.cardBrand
          }
        })
      });
      const data = await res.json();
      const paymentId = data?.Payment?.PaymentId;
      if (!res.ok || !paymentId) {
        setPaymentError(language === "pt" ? "Falha no pagamento. Tente novamente." : "Payment failed. Try again.");
        setStatus("payment");
        return;
      }
      setPaymentRef(paymentId);
      setStatus("success");
    } catch {
      setPaymentError(language === "pt" ? "Falha no pagamento. Tente novamente." : "Payment failed. Try again.");
      setStatus("payment");
    }
  };

  if (!tier) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center font-mono">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">{t.access_denied}</h1>
          <Link href="/marketplace" className="text-emerald-500 hover:underline">{t.return}</Link>
        </div>
      </div>
    );
  }

  const TierIcon = tier.icon;

  return (
    <div className="min-h-screen bg-black text-white font-mono selection:bg-emerald-500/30 pb-20">
      
      {/* Navigation */}
      <nav className="border-b border-zinc-800 bg-black/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/marketplace" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span>{t.back}</span>
          </Link>
          <div className="flex items-center gap-2 text-sm font-bold tracking-wider">
            <span className="text-zinc-500">{t.secure_connection}</span>
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
          </div>
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-6 pt-12">
        
        {/* Hero Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-16">
          
          {/* Left: Visual Identity */}
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            className={`relative rounded-2xl overflow-hidden border ${tier.border}/30 bg-gradient-to-br ${tier.bg_gradient} p-10 flex flex-col items-center justify-center min-h-[400px] group`}
          >
            <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10"></div>
            
            <motion.div
              animate={{ rotateY: [0, 180, 360] }}
              transition={{ repeat: Infinity, duration: 20, ease: "linear" }}
              className="relative z-10"
            >
               <TierIcon className={`w-40 h-40 ${tier.accent} drop-shadow-[0_0_30px_rgba(255,255,255,0.2)]`} />
            </motion.div>

            <div className="mt-8 text-center z-10">
              <div className={`text-sm font-bold tracking-[0.2em] uppercase mb-2 ${tier.accent}`}>{tier.role}</div>
              <h1 className="text-5xl font-bold text-white mb-4">{tier.name}</h1>
              <div className="inline-flex items-center gap-2 px-4 py-1 rounded-full bg-black/50 border border-zinc-700 text-xs text-zinc-400">
                <Lock className="w-3 h-3" />
                {t.soulbound} {tier.sbt}
              </div>
            </div>
          </motion.div>

          {/* Right: Offer Details */}
          <motion.div 
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-8"
          >
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">{tier.tagline}</h2>
              <p className="text-zinc-400 leading-relaxed">
                {tier.description}
              </p>
            </div>

            <div className="space-y-4">
              <h3 className="text-sm font-bold text-zinc-500 uppercase tracking-wider">{t.core_benefits}</h3>
              <ul className="space-y-3">
                {tier.benefits.map((benefit: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-3 text-zinc-300">
                    <Check className={`w-5 h-5 ${tier.accent} shrink-0`} />
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="p-6 bg-zinc-900/50 rounded-xl border border-zinc-800">
               <div className="flex justify-between items-center mb-2">
                  <span className="text-zinc-400 text-sm font-mono">{t.total_investment}</span>
                  <div className="text-right">
                     <div className="flex items-center justify-end gap-2">
                       <Lock className="w-4 h-4 text-zinc-500" />
                       <span className="block text-2xl font-bold text-zinc-300 font-mono blur-[4px] select-none">$999.00</span>
                     </div>
                     <span className="text-[10px] text-zinc-500 uppercase tracking-wider">{t.season_pass}</span>
                  </div>
               </div>

               <button 
                 onClick={handleMint}
                 disabled={status !== "idle"}
                 className={`w-full py-4 bg-white hover:bg-zinc-200 text-black font-bold font-mono rounded flex items-center justify-center gap-3 transition-all transform hover:scale-[1.01] mb-2 ${status !== "idle" ? "opacity-80 cursor-wait" : ""}`}
               >
                  {status === "idle" && (
                    <>
                      <UserPlus className="w-5 h-5 fill-black" />
                      {t.join}
                    </>
                  )}
                  {status === "verifying" && (
                    <>
                       <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin"></div>
                       {t.verifying}
                    </>
                  )}
               </button>
               {status === "payment" && (
                 <div className="space-y-3 mt-4">
                   <input
                     value={paymentForm.walletAddress}
                     onChange={(event) => setPaymentForm((prev) => ({ ...prev, walletAddress: event.target.value }))}
                     placeholder="Wallet Address"
                     className="w-full bg-black/50 border border-zinc-700 rounded-xl p-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500"
                   />
                   <input
                     value={paymentForm.email}
                     onChange={(event) => setPaymentForm((prev) => ({ ...prev, email: event.target.value }))}
                     placeholder="Email"
                     className="w-full bg-black/50 border border-zinc-700 rounded-xl p-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500"
                   />
                   <input
                     value={paymentForm.cardNumber}
                     onChange={(event) => setPaymentForm((prev) => ({ ...prev, cardNumber: event.target.value }))}
                     placeholder="Card Number"
                     className="w-full bg-black/50 border border-zinc-700 rounded-xl p-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500"
                   />
                   <div className="grid grid-cols-2 gap-3">
                     <input
                       value={paymentForm.cardExpiry}
                       onChange={(event) => setPaymentForm((prev) => ({ ...prev, cardExpiry: event.target.value }))}
                       placeholder="MM/YY"
                       className="w-full bg-black/50 border border-zinc-700 rounded-xl p-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500"
                     />
                     <input
                       value={paymentForm.cardCvc}
                       onChange={(event) => setPaymentForm((prev) => ({ ...prev, cardCvc: event.target.value }))}
                       placeholder="CVC"
                       className="w-full bg-black/50 border border-zinc-700 rounded-xl p-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500"
                     />
                   </div>
                   <input
                     value={paymentForm.cardHolder}
                     onChange={(event) => setPaymentForm((prev) => ({ ...prev, cardHolder: event.target.value }))}
                     placeholder="Card Holder"
                     className="w-full bg-black/50 border border-zinc-700 rounded-xl p-3 text-sm text-white placeholder-zinc-600 focus:outline-none focus:border-emerald-500"
                   />
                   <button
                     onClick={handlePayment}
                     className="w-full py-4 bg-emerald-500 hover:bg-emerald-400 text-black font-bold font-mono rounded flex items-center justify-center gap-3 transition-all"
                   >
                     {t.minting}
                   </button>
                   {paymentError && (
                     <div className="text-xs text-red-400">{paymentError}</div>
                   )}
                 </div>
               )}
               {status === "processing" && (
                 <div className="flex items-center justify-center gap-2 text-xs text-zinc-400 mt-4">
                   <div className="w-4 h-4 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin"></div>
                   {t.minting}
                 </div>
               )}
               {status === "success" && (
                 <div className="mt-4 space-y-2">
                   {paymentRef && (
                     <div className="text-[10px] text-zinc-500 font-mono break-all">
                       Payment ID: {paymentRef}
                     </div>
                   )}
                   <Link href="/dashboard">
                     <button className="w-full py-3 bg-white text-black font-bold font-mono rounded">
                       {t.dashboard}
                     </button>
                   </Link>
                 </div>
               )}

               <div className="text-center mb-4">
                  <span className="text-[10px] text-red-400 font-bold tracking-widest animate-pulse">
                    {t.spots_warning}
                  </span>
               </div>
               
               <p className="text-center text-xs text-zinc-600 mt-3">
                 {t.harvester}
               </p>
            </div>
          </motion.div>
        </div>

        {/* Technical Specs */}
        <div className="border-t border-zinc-800 pt-16">
          <h3 className="text-xl font-bold text-white mb-8 flex items-center gap-2">
            <Server className="w-5 h-5 text-zinc-500" />
            {t.tech_specs}
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {tier.technical_specs.map((spec, idx) => (
              <div key={idx} className="p-6 bg-zinc-900/30 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors">
                <div className="text-xs text-zinc-500 uppercase tracking-wider mb-2">{spec.label}</div>
                <div className="text-lg font-bold text-white font-mono">{spec.value}</div>
              </div>
            ))}
          </div>
        </div>

      </main>
    </div>
  );
}
