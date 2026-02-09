"use client";

import { motion } from "framer-motion";
import { Check, AlertTriangle, Cpu, Shield, Layers, Lock, UserPlus } from "lucide-react";
import { useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

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

const THEMES: Record<TierColor, Theme> = {
  emerald: {
    text: "text-emerald-400",
    bg: "bg-emerald-500/5",
    border: "border-emerald-500/20",
    ring: "group-hover:ring-emerald-500/30",
    gradient: "from-emerald-500/10 via-transparent to-transparent",
    glow: "group-hover:shadow-[0_0_40px_-10px_rgba(16,185,129,0.3)]",
    badge_bg: "bg-emerald-500/10",
    badge_border: "border-emerald-500/20"
  },
  blue: {
    text: "text-blue-400",
    bg: "bg-blue-500/5",
    border: "border-blue-500/20",
    ring: "group-hover:ring-blue-500/30",
    gradient: "from-blue-500/10 via-transparent to-transparent",
    glow: "group-hover:shadow-[0_0_40px_-10px_rgba(59,130,246,0.3)]",
    badge_bg: "bg-blue-500/10",
    badge_border: "border-blue-500/20"
  },
  yellow: {
    text: "text-yellow-400",
    bg: "bg-yellow-500/5",
    border: "border-yellow-500/20",
    ring: "group-hover:ring-yellow-500/30",
    gradient: "from-yellow-500/10 via-transparent to-transparent",
    glow: "group-hover:shadow-[0_0_40px_-10px_rgba(234,179,8,0.3)]",
    badge_bg: "bg-yellow-500/10",
    badge_border: "border-yellow-500/20"
  }
};

export default function PricingSection() {
  const searchParams = useSearchParams();
  const refCode = searchParams.get("ref");
  const [selectedTier, setSelectedTier] = useState<string | null>(null);

  const t = {
    title: "SEASON 4 BLACKLIST",
    subtitle_1: "Restricted access to the ",
    subtitle_2: "Liquidity Mining Guild",
    subtitle_3: ". Limited spots for Early Adopters.",
    desc: "Values revealed only at launch. Secure your position on the priority list. ",
    desc_highlight: "Only 15 initial spots.",
    harvester_notice: "THE HARVESTER: All tiers include a smart contractual obligation of 3% Success Fee. Access subject to approval.",
    mint_button: "APPLY FOR BLACKLIST",
    price_label: "Initial Contribution",
    network_label: "Network: Solana Native",
    badge_1: "RESTRICTED",
    badge_2: "BLACKLIST",
    tiers: [
      { 
        id: "scout", 
        name: "PARTNER SCOUT", 
        role: "The Soldier",
        price: "REVEAL @ LAUNCH", 
        weight: "1.0x", 
        features: ["CLI Access", "Phoenix V2 Strategy", "Single Pair Limit", "3% Success Fee"]
      },
      { 
        id: "commander", 
        name: "LIQUIDITY PROVIDER", 
        role: "The Captain",
        price: "REVEAL @ LAUNCH", 
        weight: "1.5x", 
        features: ["Weaver Grid V2", "Delta Neutral Bot", "Multi-Pair (3x)", "3% Success Fee"]
      },
      { 
        id: "architect", 
        name: "INSTITUTIONAL PARTNER", 
        role: "The General",
        price: "REVEAL @ LAUNCH", 
        weight: "2.0x", 
        features: ["Market Proxy Oracle", "Flash Scalper HFT", "Iron Dome VPS", "Priority RPC"]
      },
    ]
  };
  
  // Map icons and colors to tiers
  const TIER_META = [
    { id: "scout", icon: Shield, color: "emerald" as TierColor },
    { id: "commander", icon: Layers, color: "blue" as TierColor },
    { id: "architect", icon: Cpu, color: "yellow" as TierColor }
  ];

  return (
    <section className="py-24 bg-zinc-950 relative overflow-hidden" id="pricing">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-900/40 via-zinc-950 to-zinc-950 pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[500px] bg-emerald-500/5 blur-[120px] rounded-full pointer-events-none" />

      <div className="container mx-auto px-4 relative z-10">
        
        {/* Header */}
        <div className="max-w-3xl mx-auto text-center mb-20">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-red-500/20 bg-red-500/5 text-red-400 text-xs font-mono mb-6"
          >
            <Lock className="w-3 h-3" />
            <span className="font-bold">{t.badge_1}</span>
            <span className="w-px h-3 bg-red-500/20" />
            <span>{t.badge_2}</span>
          </motion.div>

          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-3xl md:text-5xl font-bold font-mono text-white mb-6 tracking-tight"
          >
            {t.title}
          </motion.h2>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg text-zinc-400 font-mono leading-relaxed"
          >
            {t.subtitle_1} <span className="text-white font-bold">{t.subtitle_2}</span>{t.subtitle_3}
            <br className="hidden md:block" />
            {t.desc} <span className="text-emerald-400 border-b border-emerald-400/20 pb-0.5">{t.desc_highlight}</span>
          </motion.p>
        </div>

        {/* Pricing Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl mx-auto mb-16">
          {t.tiers.map((tier, i) => {
            const meta = TIER_META.find(m => m.id === tier.id)!;
            const theme = THEMES[meta.color];
            const Icon = meta.icon;
            
            return (
              <motion.div
                key={tier.id}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 + 0.3 }}
                className={`
                  group relative rounded-2xl border ${theme.border} ${theme.bg} 
                  p-8 flex flex-col h-full transition-all duration-300
                  hover:ring-1 ${theme.ring} ${theme.glow}
                `}
                onMouseEnter={() => setSelectedTier(tier.id)}
                onMouseLeave={() => setSelectedTier(null)}
              >
                {/* Glow Effect */}
                <div className={`absolute inset-0 bg-gradient-to-b ${theme.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-2xl`} />

                {/* Header */}
                <div className="relative z-10 mb-8">
                  <div className="flex justify-between items-start mb-4">
                    <div className={`p-3 rounded-lg ${theme.badge_bg} ${theme.badge_border} border`}>
                      <Icon className={`w-6 h-6 ${theme.text}`} />
                    </div>
                    <div className={`px-2 py-1 rounded text-[10px] font-mono font-bold uppercase tracking-wider ${theme.badge_bg} ${theme.text} border ${theme.badge_border}`}>
                      Weight {tier.weight}
                    </div>
                  </div>
                  
                  <h3 className="text-xl font-bold text-white font-mono mb-1">{tier.name}</h3>
                  <div className={`text-xs font-mono ${theme.text} mb-6`}>{tier.role}</div>
                  
                  <div className="flex items-baseline gap-2">
                    <span className="text-2xl font-bold text-zinc-500 font-mono tracking-tighter">???</span>
                    <span className="text-xs text-zinc-600 font-mono uppercase">USDC / {t.price_label}</span>
                  </div>
                </div>

                {/* Features */}
                <div className="relative z-10 flex-grow space-y-4 mb-8">
                  {tier.features.map((feature, idx) => (
                    <div key={idx} className="flex items-start gap-3 group/item">
                      <Check className={`w-4 h-4 ${theme.text} mt-0.5 shrink-0 opacity-50 group-hover/item:opacity-100 transition-opacity`} />
                      <span className="text-sm text-zinc-400 font-mono group-hover/item:text-zinc-300 transition-colors">
                        {feature}
                      </span>
                    </div>
                  ))}
                </div>

                {/* CTA */}
                <div className="relative z-10 mt-auto">
                  <Link 
                    href={`/apply?tier=${tier.id}${refCode ? `&ref=${refCode}` : ''}`}
                    className={`
                      w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg
                      border ${theme.border} bg-zinc-900/50 text-zinc-300 font-mono text-sm
                      hover:bg-zinc-900 hover:text-white hover:border-zinc-700
                      transition-all duration-300 group-hover:shadow-lg
                    `}
                  >
                    <UserPlus className="w-4 h-4" />
                    {t.mint_button}
                  </Link>
                  <div className="text-[10px] text-center text-zinc-600 font-mono mt-3">
                    {t.network_label}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Disclaimer */}
        <motion.div 
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="max-w-2xl mx-auto flex items-start gap-3 p-4 rounded-lg bg-yellow-500/5 border border-yellow-500/10"
        >
          <AlertTriangle className="w-5 h-5 text-yellow-500/50 shrink-0 mt-0.5" />
          <p className="text-xs text-yellow-500/50 font-mono leading-relaxed">
            {t.harvester_notice}
          </p>
        </motion.div>

      </div>
    </section>
  );
}
