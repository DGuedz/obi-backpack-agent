"use client";

import { useState, useRef } from "react";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Search, Filter, ShoppingCart, Star, Zap, ChevronRight, ArrowLeft, Shield, Cpu, Globe, Lock, Activity, Layers, Server } from "lucide-react";
import Link from "next/link";
import BrandHeader3D from "../components/BrandHeader3D";
import { useLanguage } from "../context/LanguageContext";

// --- Dictionary ---
const CONTENT = {
  pt: {
    nav_back: "VOLTAR AO TERMINAL",
    search_placeholder: "Buscar acesso...",
    title: "ESCOLHA SEU ACESSO",
    subtitle_1: "Selecione seu nível de acesso ao ecossistema OBI WORK. Cada Tier é representado por um",
    sbt_highlight: "Soulbound Token (SBT)",
    subtitle_2: "intransferível.",
    season_pass: "/ Passe de Temporada",
    mint_action: "MINTAR",
    explore_action: "EXPLORAR DADOS",
    sections: {
      scout: {
        role: "O Soldado",
        desc_1: "Entrada e Validação. O **PARTNER SCOUT** é para quem quer parar de perder dinheiro e começar a operar com disciplina.",
        desc_2: "Sua missão é simples: **Sobreviver, Validar e Acumular.**",
        features: [
          "Acesso ao Script Básico (CLI)",
          "Estratégia Phoenix V2 (RSI + Bollinger)",
          "Limite de Par Único (Foco Total)"
        ]
      },
      commander: {
        role: "O Capitão",
        desc_1: "Renda Passiva e Volume Constante. O **LIQUIDITY PROVIDER** libera o poder do Weaver Grid e Delta Neutral.",
        desc_2: "Ideal para quem busca **Yield Farming** sem exposição direcional ao mercado.",
        features: [
          "Weaver Grid V2 (Grade Infinita)",
          "Delta Neutral Bot (Spot + Short)",
          "Multi-Par (Até 3 Ativos)"
        ]
      },
      architect: {
        role: "O General",
        desc_1: "Vantagem Competitiva (Edge). O **INSTITUTIONAL PARTNER** oferece acesso total à infraestrutura e dados OBI.",
        desc_2: "Para quem opera grande e precisa de **Latência Zero e Informação Privilegiada.**",
        features: [
          "Market Proxy Oracle (Dados OBI)",
          "Flash Scalper HFT (Alta Frequência)",
          "Iron Dome VPS (Blindagem Total)"
        ]
      }
    }
  },
  en: {
    nav_back: "BACK TO TERMINAL",
    search_placeholder: "Search access...",
    title: "CHOOSE YOUR ACCESS",
    subtitle_1: "Select your access level to the OBI WORK ecosystem. Each Tier is represented by a non-transferable",
    sbt_highlight: "Soulbound Token (SBT)",
    subtitle_2: ".",
    season_pass: "/ Season Pass",
    mint_action: "MINT",
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
        desc_1: "Competitive Advantage (Edge). The **INSTITUTIONAL PARTNER** offers full access to infrastructure and OBI data.",
        desc_2: "For those trading big who need **Zero Latency and Privileged Information.**",
        features: [
          "Market Proxy Oracle (OBI Data)",
          "Flash Scalper HFT (High Frequency)",
          "Iron Dome VPS (Total Shielding)"
        ]
      }
    }
  }
};

// --- Data Structure for Tiers (Dynamic) ---
const getTiers = (lang: 'pt' | 'en') => [
  {
    id: "scout",
    name: "PARTNER SCOUT",
    role: CONTENT[lang].sections.scout.role,
    price: 29.99,
    sbt: "OBI-SCOUT",
    color: "emerald",
    gradient: "from-emerald-900/40 to-black",
    border: "border-emerald-500/30",
    text: "text-emerald-400",
    bg: "bg-emerald-500",
    features: [
      { icon: Zap, label: lang === 'pt' ? "Acesso CLI & Sentinel" : "CLI Access & Sentinel" },
      { icon: Activity, label: "Phoenix V2 Strategy" },
      { icon: Shield, label: lang === 'pt' ? "Limite Par Único" : "Single Pair Limit" }
    ],
    description: lang === 'pt' 
      ? "Entrada e Validação. Para quem quer parar de perder dinheiro e começar a operar como um soldado disciplinado."
      : "Entry and Validation. For those who want to stop losing money and start trading with discipline."
  },
  {
    id: "commander",
    name: "LIQUIDITY PROVIDER",
    role: CONTENT[lang].sections.commander.role,
    price: 49.90,
    sbt: "OBI-CMDR",
    color: "blue",
    gradient: "from-blue-900/40 to-black",
    border: "border-blue-500/30",
    text: "text-blue-400",
    bg: "bg-blue-500",
    features: [
      { icon: Layers, label: "Delta Neutral (Yield)" },
      { icon: Activity, label: "Weaver Grid V2" },
      { icon: Cpu, label: lang === 'pt' ? "Multi-Par (3x)" : "Multi-Pair (3x)" }
    ],
    description: lang === 'pt'
      ? "Renda Passiva e Volume Constante. Use o Weaver Grid e Delta Neutral para farmar 24/7 sem risco direcional."
      : "Passive Income and Constant Volume. Use Weaver Grid and Delta Neutral to farm 24/7 without directional risk."
  },
  {
    id: "architect",
    name: "INSTITUTIONAL PARTNER",
    role: CONTENT[lang].sections.architect.role,
    price: 99.00,
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
    description: lang === 'pt'
      ? "Vantagem Competitiva (Edge). Acesso total à infraestrutura, OBI Oracle e execução prioritária."
      : "Competitive Advantage (Edge). Full access to infrastructure, OBI Oracle, and priority execution."
  }
];

// --- 3D Card Component ---
function TierCard3D({ tier, lang }: { tier: ReturnType<typeof getTiers>[0], lang: 'pt' | 'en' }) {
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
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-white">$</span>
              <span className="text-4xl font-bold text-white">${tier.price.toFixed(2)}</span>
              <span className="text-xs text-zinc-500 ml-2">{CONTENT[lang].season_pass}</span>
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
                {CONTENT[lang].mint_action} {tier.sbt}
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
  const [filter, setFilter] = useState("ALL");
  const [search, setSearch] = useState("");
  const { language } = useLanguage();
  const t = CONTENT[language];
  const TIERS = getTiers(language);

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
          <p className="text-zinc-400 max-w-2xl mx-auto">
            {t.subtitle_1} <strong className="text-emerald-400"> {t.sbt_highlight}</strong> {t.subtitle_2}
          </p>
        </div>

        {/* 3D Tier Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
           {TIERS.map((tier) => (
             <TierCard3D key={tier.id} tier={tier} lang={language} />
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
                {language === 'pt' ? 
                  <>
                    Entrada e Validação. O **PARTNER SCOUT** é para quem quer parar de perder dinheiro e começar a operar com disciplina.
                    <br/><br/>
                    Sua missão é simples: **Sobreviver, Validar e Acumular.**
                  </>
                  :
                  <>
                    Entry and Validation. The **PARTNER SCOUT** is for those who want to stop losing money and start trading with discipline.
                    <br/><br/>
                    Your mission is simple: **Survive, Validate, and Accumulate.**
                  </>
                }
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
                {language === 'pt' ?
                  <>
                    Renda Passiva e Volume Constante. O **LIQUIDITY PROVIDER** libera o poder do Weaver Grid e Delta Neutral.
                    <br/><br/>
                    Ideal para quem busca **Yield Farming** sem exposição direcional ao mercado.
                  </>
                  :
                  <>
                    Passive Income and Constant Volume. The **LIQUIDITY PROVIDER** unleashes the power of Weaver Grid and Delta Neutral.
                    <br/><br/>
                    Ideal for those seeking **Yield Farming** without directional market exposure.
                  </>
                }
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
          
          {/* Architect Section (Simplified for this file update) */}
           <section id="architect-section" className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div className="order-2 md:order-1 space-y-6">
              <div className="flex items-center gap-3 text-yellow-500 mb-2">
                <Cpu className="w-6 h-6" />
                <span className="font-bold tracking-widest">TIER 3 CLONE</span>
              </div>
              <h3 className="text-4xl font-bold text-white">INSTITUTIONAL PARTNER: {t.sections.architect.role}</h3>
              <p className="text-zinc-400 text-lg leading-relaxed">
                {language === 'pt' ?
                  <>
                    Vantagem Competitiva (Edge). O **INSTITUTIONAL PARTNER** oferece acesso total à infraestrutura e dados OBI.
                    <br/><br/>
                    Para quem opera grande e precisa de **Latência Zero e Informação Privilegiada.**
                  </>
                  :
                  <>
                    Competitive Advantage (Edge). The **INSTITUTIONAL PARTNER** offers full access to infrastructure and OBI data.
                    <br/><br/>
                    For those trading big who need **Zero Latency and Privileged Information.**
                  </>
                }
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
                 transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
                 className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-yellow-500/5 rounded-full backdrop-blur-sm border border-yellow-400/20"
               />
            </div>
          </section>

        </div>
      </main>
    </div>
  );
}
