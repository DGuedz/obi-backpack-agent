"use client";

import { motion } from "framer-motion";
import { Check, AlertTriangle, Cpu, Shield, Layers, Lock, UserPlus } from "lucide-react";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { useLanguage } from "../context/LanguageContext";

type TierColor = "emerald" | "blue" | "yellow";

type Theme = {
  text: string;
  bg: string;
  border: string;
  ring: string;
  gradient: string;
  glow: string;
  badge_bg: string;
  badge_border: string;
};

const CONTENT = {
  pt: {
    title: "SEASON 4 BLACKLIST",
    subtitle_1: "Acesso restrito à ",
    subtitle_2: "Guilda de Mineração de Liquidez",
    subtitle_3: ". Vagas limitadas para Early Adopters.",
    desc: "Valores revelados apenas no lançamento. Garanta sua posição na lista de prioridade. ",
    desc_highlight: "Apenas 15 vagas iniciais.",
    harvester_notice: "O HARVESTER: Todos os tiers incluem uma obrigação contratual inteligente de 3% de Taxa de Sucesso. Acesso sujeito a aprovação.",
    mint_button: "APLICAR PARA BLACKLIST",
    price_label: "Contribuição Inicial",
    network_label: "Rede: Solana Native",
    badge_1: "RESTRICTED",
    badge_2: "BLACKLIST",
    features: {
      access: "Acesso ao Nível",
      ecosystem: "Integração ao Ecossistema",
      risk: "Framework de Risco Avançado",
      community: "Acesso à Comunidade Privada",
      updates: "Atualizações Contínuas"
    }
  },
  en: {
    title: "SEASON 4 BLACKLIST",
    subtitle_1: "Restricted access to the ",
    subtitle_2: "Liquidity Mining Guild",
    subtitle_3: ". Limited spots for Early Adopters.",
    desc: "Pricing revealed at launch. Secure your position on the priority list. ",
    desc_highlight: "Only 15 initial spots.",
    harvester_notice: "THE HARVESTER: All tiers include a smart contract obligation of 3% Success Fee. Access subject to approval.",
    mint_button: "APPLY FOR BLACKLIST",
    price_label: "Initial Contribution",
    network_label: "Network: Solana Native",
    badge_1: "RESTRICTED",
    badge_2: "BLACKLIST",
    features: {
      access: "Access to",
      ecosystem: "Ecosystem Integration",
      risk: "Advanced Risk Framework",
      community: "Private Community Access",
      updates: "Continuous Updates"
    }
  }
};

const TIERS = [
  { 
    id: "scout", 
    name: "PARTNER SCOUT", 
    role: "The Soldier",
    price: "REVEAL @ LAUNCH", 
    weight: "1.0x", 
    color: "emerald" as TierColor,
    icon: Shield,
    features: ["CLI Access", "Phoenix V2 Strategy", "Single Pair Limit", "3% Success Fee"]
  },
  { 
    id: "commander", 
    name: "LIQUIDITY PROVIDER", 
    role: "The Captain",
    price: "REVEAL @ LAUNCH", 
    weight: "1.5x", 
    color: "blue" as TierColor,
    icon: Layers,
    features: ["Weaver Grid V2", "Delta Neutral Bot", "Multi-Pair (3x)", "3% Success Fee"]
  },
  { 
    id: "architect", 
    name: "INSTITUTIONAL PARTNER", 
    role: "The General",
    price: "REVEAL @ LAUNCH", 
    weight: "2.0x", 
    color: "yellow" as TierColor,
    icon: Cpu,
    features: ["Market Proxy Oracle", "Flash Scalper HFT", "Iron Dome VPS", "Priority RPC"]
  },
];

export default function PricingSection() {
  const [manualTierId, setManualTierId] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const { language } = useLanguage();
  const t = CONTENT[language];
  const selectedTierId = manualTierId ?? searchParams.get("tier") ?? TIERS[0].id;
  const selectedTier = TIERS.find((tier) => tier.id === selectedTierId) ?? TIERS[0];

  // Color Mapping Helper
  const getTheme = (color: TierColor): Theme => {
    const themes: Record<TierColor, Theme> = {
      emerald: {
        text: "text-emerald-400",
        bg: "bg-emerald-500",
        border: "border-emerald-500",
        ring: "ring-emerald-500",
        gradient: "from-emerald-900/20",
        glow: "bg-emerald-500/20",
        badge_bg: "bg-emerald-900/30",
        badge_border: "border-emerald-900/50"
      },
      blue: {
        text: "text-blue-400",
        bg: "bg-blue-500",
        border: "border-blue-500",
        ring: "ring-blue-500",
        gradient: "from-blue-900/20",
        glow: "bg-blue-500/20",
        badge_bg: "bg-blue-900/30",
        badge_border: "border-blue-900/50"
      },
      yellow: {
        text: "text-yellow-400",
        bg: "bg-yellow-500",
        border: "border-yellow-500",
        ring: "ring-yellow-500",
        gradient: "from-yellow-900/20",
        glow: "bg-yellow-500/20",
        badge_bg: "bg-yellow-900/30",
        badge_border: "border-yellow-900/50"
      }
    };
    return themes[color] ?? themes.emerald;
  };

  const theme = getTheme(selectedTier.color);

  return (
    <section className="relative py-16 md:py-24 bg-zinc-950 border-t border-zinc-900">
      <div className="container px-4 md:px-6 mx-auto">
        
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-start">
          
          {/* Left: The Offer */}
          <div className="text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono mb-6">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
                15 SPOTS FOR OBI EARLY ADOPTERS
            </div>

            <h2 className="text-3xl md:text-4xl font-bold font-mono text-white mb-6">
              THE <span className={theme.text}>{t.title}</span>
            </h2>
            <p className="text-zinc-400 font-mono mb-8">
              {t.subtitle_1}<strong>{t.subtitle_2}</strong>{t.subtitle_3}
              <br/>
              {t.desc}<strong>{t.desc_highlight}</strong>.
            </p>
            
            <div className="mb-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
               {TIERS.map((tier) => {
                 const tTheme = getTheme(tier.color);
                 const isSelected = selectedTierId === tier.id;
                 return (
                   <button
                     key={tier.id}
                     onClick={() => setManualTierId(tier.id)}
                     className={`p-4 rounded border text-left transition-all relative overflow-hidden group ${
                       isSelected
                       ? `bg-zinc-800 ${tTheme.border} ring-1 ${tTheme.ring}` 
                       : "bg-zinc-900/50 border-zinc-800 hover:bg-zinc-900"
                     }`}
                   >
                      {isSelected && <div className={`absolute top-0 left-0 w-full h-1 ${tTheme.bg}`} />}
                      <div className="flex justify-between items-start mb-2">
                        <span className={`text-[10px] font-mono uppercase tracking-wider ${isSelected ? "text-white" : "text-zinc-500"}`}>{tier.id}</span>
                        {isSelected && <Lock className="w-3 h-3 text-zinc-400" />}
                      </div>
                      <div className={`text-xs font-bold font-mono mb-1 ${isSelected ? "text-zinc-300" : "text-zinc-500"}`}>HIDDEN</div>
                      <div className={`text-[10px] font-mono ${isSelected ? tTheme.text : "text-zinc-600"}`}>{tier.role}</div>
                   </button>
                 );
               })}
            </div>

            <ul className="space-y-4 mb-8">
              {[
                `Access to ${selectedTier.name} Level`,
                "Ecosystem Integration",
                "Advanced Risk Framework",
                "Private Community Access",
                "Continuous Updates"
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3 text-zinc-300 font-mono text-sm">
                  <Check className={`w-5 h-5 ${theme.text} shrink-0`} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            <div className={`p-4 bg-zinc-900/50 border ${theme.border}/30 rounded flex gap-3 items-start`}>
              <AlertTriangle className={`w-5 h-5 ${theme.text} shrink-0 mt-0.5`} />
              <p className="text-xs text-zinc-400 font-mono">
                <strong>{t.harvester_notice}</strong>
              </p>
            </div>
          </div>

          {/* Right: The NFT Card Visualization */}
          <div className="flex flex-col items-center">
            <motion.div 
              key={selectedTier.id}
              initial={{ opacity: 0, rotateY: 90 }}
              animate={{ opacity: 1, rotateY: 0 }}
              transition={{ duration: 0.5 }}
              className={`w-full max-w-sm aspect-3/4 bg-zinc-900 rounded-xl border ${theme.border} relative overflow-hidden shadow-2xl shadow-${selectedTier.color}-900/20 group perspective-1000`}
            >
               {/* NFT Art Placeholder - Abstract Tech */}
               <div className="absolute inset-0 bg-gradient-to-br from-zinc-800 to-black transition-colors duration-500">
                  {/* Grid Pattern */}
                  <div className="absolute inset-0 bg-[size:24px_24px] [background-image:linear-gradient(to_right,rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.05)_1px,transparent_1px)] opacity-50"></div>
                  
                  {/* Holographic Chrome Effect */}
                  <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none transform translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-in-out z-20"></div>

                  <div className="absolute top-8 left-8 right-8 bottom-32 flex flex-col items-center justify-center border border-zinc-700/50 rounded-lg bg-zinc-900/50 backdrop-blur-sm overflow-hidden z-10 shadow-inner">
                      <div className="mb-4 transform scale-100 pt-4 relative">
                         <div className={`absolute inset-0 ${theme.glow} blur-xl rounded-full`}></div>
                         <div className="relative z-10">
                            <selectedTier.icon className={`w-20 h-20 ${theme.text} drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]`} />
                         </div>
                      </div>
                      <div className={`w-full overflow-hidden border-y ${theme.border}/20 ${theme.badge_bg} py-1 mb-4`}>
                         <motion.div 
                           animate={{ x: ["0%", "-50%"] }}
                           transition={{ repeat: Infinity, ease: "linear", duration: 15 }}
                           className={`whitespace-nowrap flex items-center gap-4 text-[8px] font-mono ${theme.text} uppercase tracking-widest`}
                         >
                            <span>{t.badge_1}</span>
                            <span className={`w-1 h-1 rounded-full ${theme.bg}`}></span>
                            <span>{selectedTier.role}</span>
                            <span className={`w-1 h-1 rounded-full ${theme.bg}`}></span>
                            <span>obi work</span>
                            <span className={`w-1 h-1 rounded-full ${theme.bg}`}></span>
                            <span>{t.badge_2}</span>
                            <span className={`w-1 h-1 rounded-full ${theme.bg}`}></span>
                            {/* Duplicate loop */}
                            <span>automated market traders</span>
                            <span className={`w-1 h-1 rounded-full ${theme.bg}`}></span>
                            <span>{selectedTier.role}</span>
                            <span className={`w-1 h-1 rounded-full ${theme.bg}`}></span>
                            <span>obi work</span>
                            <span className={`w-1 h-1 rounded-full ${theme.bg}`}></span>
                            <span>sovereign key</span>
                         </motion.div>
                      </div>
                      <div className="text-3xl font-mono font-bold text-white tracking-widest pb-4 uppercase">{selectedTier.id}</div>
                  </div>

                  <div className="absolute bottom-0 left-0 right-0 h-32 bg-zinc-950/90 backdrop-blur p-6 border-t border-zinc-800">
                      <div className="flex justify-between items-end mb-2">
                          <div>
                              <div className="text-xs text-zinc-500 font-mono uppercase">Role</div>
                              <div className="text-white font-mono font-bold">{selectedTier.name}</div>
                          </div>
                          <div className="text-right">
                              <div className="text-xs text-zinc-500 font-mono uppercase">Weight</div>
                              <div className={`font-mono font-bold ${theme.text}`}>{selectedTier.weight}</div>
                          </div>
                      </div>
                      <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden mb-2">
                          <div className={`h-full ${theme.bg}`} style={{ width: `${parseFloat(selectedTier.weight) * 50}%` }}></div>
                      </div>
                      
                      <div className="flex justify-between items-center pt-2 border-t border-zinc-800/50">
                          <div className="text-[10px] text-zinc-600 font-mono uppercase">Assigned Seat</div>
                          <div className="text-xs text-zinc-400 font-mono">TABLE {selectedTier.id.toUpperCase()}</div>
                      </div>
                  </div>
               </div>
            </motion.div>

            <div className="w-full max-w-sm mt-8">
               <div className="flex justify-between items-center mb-4 text-sm font-mono text-zinc-400">
                  <span>{t.price_label}</span>
                  <div className="flex items-center gap-2">
                    <Lock className="w-3 h-3 text-zinc-500" />
                    <span className="text-zinc-300 font-bold text-lg blur-[4px] select-none">$999.00</span>
                  </div>
               </div>
               <Link href={`/marketplace/${selectedTier.id}`} className="block w-full">
                 <button 
                   className={`w-full py-4 bg-white hover:bg-zinc-200 text-black font-bold font-mono rounded flex items-center justify-center gap-2 transition-all transform hover:scale-[1.02]`}
                 >
                    <UserPlus className="w-5 h-5" />
                    {t.mint_button}
                 </button>
               </Link>
              <p className="mt-3 text-center text-[10px] text-zinc-600 font-mono">
                {t.network_label}
              </p>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
}
