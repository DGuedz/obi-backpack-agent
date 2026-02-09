"use client";

import { useState } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Search, ShoppingCart, Zap, ArrowLeft, Shield, Cpu, Globe, Lock, Activity, Layers, Server } from "lucide-react";
import Link from "next/link";
import BrandHeader3D from "../components/BrandHeader3D";

type SectionContent = {
  role: string;
  desc_1: string;
  desc_2: string;
  features: string[];
};

const CONTENT = {
  en: {
    nav_back: "BACK TO TERMINAL",
    search_placeholder: "Search access...",
    title: "BLACKLIST ACCESS",
    subtitle_1: "Request your exclusive access to the OBI WORK ecosystem. Each Tier is represented by a non-transferable",
    sbt_highlight: "Soulbound Token (SBT)",
    subtitle_2: ".",
    limited_spots: "⚠️ Only 15 spots for Early Adopters in this phase.",
    season_pass: "/ Reveal @ Launch",
    mint_action: "APPLY",
    explore_action: "EXPLORE DATA",
    sections: {
      scout: {
        role: "The Soldier",
        desc_1: "Entry and Validation. The **PARTNER SCOUT** is for those who want to stop losing money and start trading with discipline.",
        desc_2: "Your mission is simple: **Survive, Validate, and Accumulate.**",
        features: [
          "Basic Script Access (CLI)",
          "Phoenix V2 Strategy (RSI + Bollinger)",
          "Single Pair Limit (Total Focus)"
        ]
      },
      commander: {
        role: "The Captain",
        desc_1: "Passive Income and Constant Volume. The **LIQUIDITY PROVIDER** unleashes the power of Weaver Grid and Delta Neutral.",
        desc_2: "Ideal for those seeking **Yield Farming** without directional market exposure.",
        features: [
          "Weaver Grid V2 (Infinite Grid)",
          "Delta Neutral Bot (Spot + Short)",
          "Multi-Pair (Up to 3 Assets)"
        ]
      },
      architect: {
        role: "The General",
        desc_1: "Competitive Edge. The **INSTITUTIONAL PARTNER** offers full access to OBI infrastructure and data.",
        desc_2: "For those operating large size and needing **Zero Latency and Privileged Information.**",
        features: [
          "Market Proxy Oracle (OBI Data)",
          "Flash Scalper HFT (High Frequency)",
          "Iron Dome VPS (Total Shielding)"
        ]
      }
    }
  }
};

const t = CONTENT['en'];

// --- Data Structure for Tiers (Dynamic) ---
const getTiers = () => [
  {
    id: "scout",
    name: "PARTNER SCOUT",
    role: t.sections.scout.role,
    price: "DYNAMIC PEG",
    sbt: "OBI-SCOUT",
    color: "emerald",
    gradient: "from-emerald-900/40 to-black",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
    bg: "bg-emerald-500",
    features: [
      { icon: Zap, label: "CLI Access & Sentinel" },
      { icon: Activity, label: "Phoenix V2 Strategy" },
      { icon: Shield, label: "Single Pair Limit" }
    ],
    description: "Entry and Validation. For those who want to stop losing money and start trading with discipline."
  },
  {
    id: "commander",
    name: "LIQUIDITY PROVIDER",
    role: t.sections.commander.role,
    price: "DYNAMIC PEG",
    sbt: "OBI-CMDR",
    color: "blue",
    gradient: "from-blue-900/40 to-black",
    border: "border-blue-500/30",
    text: "text-blue-400",
    bg: "bg-blue-500",
    features: [
      { icon: Layers, label: "Delta Neutral (Yield)" },
      { icon: Activity, label: "Weaver Grid V2" },
      { icon: Cpu, label: "Multi-Pair (3x)" }
    ],
    description: "Passive Income and Constant Volume. Use Weaver Grid and Delta Neutral to farm 24/7 without directional risk."
  },
  {
    id: "architect",
    name: "INSTITUTIONAL PARTNER",
    role: t.sections.architect.role,
    price: "DYNAMIC PEG",
    sbt: "OBI-ARCH",
    color: "yellow",
    gradient: "from-yellow-900/40 to-black",
    border: "border-yellow-500/30",
    text: "text-yellow-400",
    bg: "bg-yellow-500",
    features: [
      { icon: Globe, label: "Market Proxy Oracle" },
      { icon: Zap, label: "Flash Scalper HFT" },
      { icon: Server, label: "Iron Dome VPS" }
    ],
    description: "Competitive Edge. Full access to infrastructure, OBI Oracle, and priority execution."
  }
];

// --- 3D Card Component ---
function TierCard3D({ tier }: { tier: ReturnType<typeof getTiers>[0] }) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);

  const mouseX = useSpring(x, { stiffness: 500, damping: 100 });
  const mouseY = useSpring(y, { stiffness: 500, damping: 100 });

  function onMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
    const { left, top, width, height } = currentTarget.getBoundingClientRect();
    x.set(clientX - left - width / 2);
    y.set(clientY - top - height / 2);
  }

  const rotateX = useTransform(mouseY, [-300, 300], [15, -15]);
  const rotateY = useTransform(mouseX, [-300, 300], [-15, 15]);

  return (
    <div className="perspective-1000">
      <motion.div
        style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
        onMouseMove={onMouseMove}
        onMouseLeave={() => {
          x.set(0);
          y.set(0);
        }}
        className={`relative w-full h-full bg-black rounded-xl border ${tier.border} group hover:shadow-2xl transition-all duration-300`}
      >
        {/* Holographic Background */}
        <div className={`absolute inset-0 bg-gradient-to-br ${tier.gradient} opacity-20 rounded-xl pointer-events-none`} />
        
        <div className="relative p-8 flex flex-col h-full transform-style-3d">
          
          {/* Header (Floating) */}
          <div className="transform translate-z-20 mb-6">
            <div className={`text-xs font-bold tracking-widest uppercase mb-1 ${tier.text}`}>{tier.role}</div>
            <h3 className="text-3xl font-bold text-white mb-2">{tier.name}</h3>
            <div className="flex items-center gap-2">
              <Lock className="w-4 h-4 text-zinc-500" />
              <span className="text-xl font-bold text-zinc-500 select-none tracking-tight">DYNAMIC PEG</span>
              <span className="text-xs text-zinc-600 ml-1 animate-pulse">CALCULATING...</span>
            </div>
          </div>

          {/* Features (Depth Layer) */}
          <div className="transform translate-z-10 space-y-4 mb-8 flex-grow">
            {tier.features.map((feat, idx) => (
              <div key={idx} className="flex items-center gap-3 text-sm text-zinc-300">
                <div className={`p-1.5 rounded-full bg-zinc-900 border border-zinc-800 ${tier.text}`}>
                  <feat.icon className="w-3.5 h-3.5" />
                </div>
                <span>{feat.label}</span>
              </div>
            ))}
            <p className="text-xs text-zinc-500 mt-4 leading-relaxed border-t border-zinc-800 pt-4">
              {tier.description}
            </p>
          </div>

          {/* Action Button (Floating High) */}
          <div className="transform translate-z-30 mt-auto">
            <Link href={`/marketplace/${tier.id}`}>
              <button className={`w-full py-3 ${tier.bg} text-black font-bold text-sm rounded uppercase tracking-wider hover:opacity-90 transition-opacity shadow-lg shadow-${tier.color}-500/20`}>
                {t.mint_action} FOR BLACKLIST
              </button>
            </Link>
          </div>
          
          {/* Decorative Corner */}
          <div className={`absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl ${tier.gradient} opacity-20 rounded-bl-full pointer-events-none`} />
        </div>
      </motion.div>
    </div>
  );
}

export default function MarketplacePage() {
  const [search, setSearch] = useState("");
  const TIERS = getTiers();

  return (
    <div className="min-h-screen bg-black text-white font-mono selection:bg-emerald-500/30">
      
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-zinc-800 bg-black/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span>{t.nav_back}</span>
          </Link>
          <div className="flex items-center gap-4">
             <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                <input 
                  type="text" 
                  placeholder={t.search_placeholder} 
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="bg-zinc-900 border border-zinc-800 rounded-full py-1.5 pl-9 pr-4 text-sm focus:border-emerald-500 focus:outline-none w-48 transition-all focus:w-64"
                />
             </div>
             <button className="p-2 hover:bg-zinc-800 rounded-full transition-colors relative">
                <ShoppingCart className="w-5 h-5 text-zinc-400" />
                <span className="absolute top-0 right-0 w-2 h-2 bg-emerald-500 rounded-full"></span>
             </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 pb-20">
        
        {/* 3D Brand Header */}
        <BrandHeader3D />

        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">{t.title}</h2>
          <p className="text-zinc-400 max-w-2xl mx-auto mb-4">
            {t.subtitle_1} <strong className="text-emerald-400"> {t.sbt_highlight}</strong> {t.subtitle_2}
          </p>
          <div className="inline-block px-4 py-1.5 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-sm font-bold tracking-wide animate-pulse">
            {t.limited_spots}
          </div>
        </div>

        {/* 3D Tier Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
           {TIERS.map((tier) => (
             <TierCard3D key={tier.id} tier={tier} />
           ))}
        </div>

        {/* Detailed Clone Sections (Routes Simulation) */}
        <div className="mt-32 space-y-32">
          
          {/* Scout Section */}
          <section id="scout-section" className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div className="order-2 md:order-1 space-y-6">
              <div className="flex items-center gap-3 text-emerald-500 mb-2">
                <Shield className="w-6 h-6" />
                <span className="font-bold tracking-widest">TIER 1 CLONE</span>
              </div>
              <h3 className="text-4xl font-bold text-white">PARTNER SCOUT: {t.sections.scout.role}</h3>
              <p className="text-zinc-400 text-lg leading-relaxed">
                  <>
                    Entry and Validation. The **PARTNER SCOUT** is for those who want to stop losing money and start trading with discipline.
                    <br/><br/>
                    Your mission is simple: **Survive, Validate, and Accumulate.**
                  </>
              </p>
              <ul className="space-y-4">
                {t.sections.scout.features.map((feat, i) => (
                   <li key={i} className="flex items-center gap-3 text-zinc-300">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full"></span>
                    {feat}
                  </li>
                ))}
              </ul>
              <div className="pt-6">
                 <Link href="/marketplace/scout">
                    <button className="px-8 py-3 bg-zinc-900 border border-emerald-500/50 text-emerald-400 font-bold rounded hover:bg-emerald-500/10 transition-colors">
                      {t.explore_action}
                    </button>
                 </Link>
              </div>
            </div>
            <div className="order-1 md:order-2 relative h-[400px] bg-emerald-900/10 rounded-2xl border border-emerald-500/20 overflow-hidden group">
               <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20"></div>
               <div className="absolute inset-0 flex items-center justify-center">
                  <Shield className="w-32 h-32 text-emerald-500/20 group-hover:text-emerald-500/40 transition-colors duration-500 scale-110" />
               </div>
               {/* 3D Floating Element */}
               <motion.div 
                 animate={{ y: [0, -20, 0] }}
                 transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
                 className="absolute top-1/4 left-1/4 w-16 h-16 bg-emerald-500/20 rounded-lg backdrop-blur-md border border-emerald-400/30"
               />
               <motion.div 
                 animate={{ y: [0, 20, 0] }}
                 transition={{ repeat: Infinity, duration: 5, ease: "easeInOut", delay: 1 }}
                 className="absolute bottom-1/4 right-1/4 w-24 h-24 bg-emerald-900/40 rounded-full backdrop-blur-md border border-emerald-400/30"
               />
            </div>
          </section>

          {/* Commander Section */}
          <section id="commander-section" className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div className="relative h-[400px] bg-blue-900/10 rounded-2xl border border-blue-500/20 overflow-hidden group">
               <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20"></div>
               <div className="absolute inset-0 flex items-center justify-center">
                  <Layers className="w-32 h-32 text-blue-500/20 group-hover:text-blue-500/40 transition-colors duration-500 scale-110" />
               </div>
               {/* 3D Floating Element */}
               <motion.div 
                 animate={{ rotate: [0, 10, 0] }}
                 transition={{ repeat: Infinity, duration: 6, ease: "easeInOut" }}
                 className="absolute top-1/3 right-1/3 w-32 h-32 bg-blue-500/10 rounded-xl backdrop-blur-md border border-blue-400/30"
               />
            </div>
            <div className="space-y-6">
              <div className="flex items-center gap-3 text-blue-500 mb-2">
                <Layers className="w-6 h-6" />
                <span className="font-bold tracking-widest">TIER 2 CLONE</span>
              </div>
              <h3 className="text-4xl font-bold text-white">LIQUIDITY PROVIDER: {t.sections.commander.role}</h3>
              <p className="text-zinc-400 text-lg leading-relaxed">
                  <>
                    Passive Income and Constant Volume. The **LIQUIDITY PROVIDER** unleashes the power of Weaver Grid and Delta Neutral.
                    <br/><br/>
                    Ideal for those seeking **Yield Farming** without directional market exposure.
                  </>
              </p>
              <ul className="space-y-4">
                {t.sections.commander.features.map((feat, i) => (
                   <li key={i} className="flex items-center gap-3 text-zinc-300">
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full"></span>
                    {feat}
                  </li>
                ))}
              </ul>
              <div className="pt-6">
                 <Link href="/marketplace/commander">
                    <button className="px-8 py-3 bg-zinc-900 border border-blue-500/50 text-blue-400 font-bold rounded hover:bg-blue-500/10 transition-colors">
                      {t.explore_action}
                    </button>
                 </Link>
              </div>
            </div>
          </section>

          {/* Architect Section */}
          <section id="architect-section" className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div className="order-2 md:order-1 space-y-6">
              <div className="flex items-center gap-3 text-yellow-500 mb-2">
                <Cpu className="w-6 h-6" />
                <span className="font-bold tracking-widest">TIER 3 CLONE</span>
              </div>
              <h3 className="text-4xl font-bold text-white">INSTITUTIONAL PARTNER: {t.sections.architect.role}</h3>
              <p className="text-zinc-400 text-lg leading-relaxed">
                  <>
                    Competitive Advantage (Edge). The **INSTITUTIONAL PARTNER** offers full access to infrastructure and OBI data.
                    <br/><br/>
                    For those trading big who need **Zero Latency and Privileged Information.**
                  </>
              </p>
              <ul className="space-y-4">
                {t.sections.architect.features.map((feat, i) => (
                   <li key={i} className="flex items-center gap-3 text-zinc-300">
                    <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full"></span>
                    {feat}
                  </li>
                ))}
              </ul>
              <div className="pt-6">
                 <Link href="/marketplace/architect">
                    <button className="px-8 py-3 bg-zinc-900 border border-yellow-500/50 text-yellow-400 font-bold rounded hover:bg-yellow-500/10 transition-colors">
                      {t.explore_action}
                    </button>
                 </Link>
              </div>
            </div>
            <div className="order-1 md:order-2 relative h-[400px] bg-yellow-900/10 rounded-2xl border border-yellow-500/20 overflow-hidden group">
               <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20"></div>
               <div className="absolute inset-0 flex items-center justify-center">
                  <Cpu className="w-32 h-32 text-yellow-500/20 group-hover:text-yellow-500/40 transition-colors duration-500 scale-110" />
               </div>
               {/* 3D Floating Element */}
               <motion.div 
                 animate={{ scale: [1, 1.1, 1] }}
                 transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                 className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-yellow-500/5 rounded-full border border-yellow-400/20"
               />
            </div>
          </section>

        </div>

      </main>
    </div>
  );
}
