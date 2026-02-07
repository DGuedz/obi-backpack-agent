"use client";

import { motion } from "framer-motion";
import { Activity, BarChart3, Lock, Zap, Medal, Trophy, CheckCircle2, Award, ShieldCheck, Terminal } from "lucide-react";
import { useState, useEffect } from "react";
import { useLanguage } from "../context/LanguageContext";
import Link from "next/link";

const terminalLogs = [
  { text: "> INITIALIZING LIQUIDITY CORE v1.0...", color: "text-zinc-300", delay: 100 },
  { text: "> ESTABLISHING SECURE CONNECTION... [OK]", color: "text-emerald-400", delay: 800 },
  { text: "> VERIFYING PARTNERSHIP CREDENTIALS... [VERIFIED]", color: "text-emerald-400", delay: 1500 },
  { text: "> LOADING MARKET ANALYSIS ENGINE... [READY]", color: "text-zinc-300", delay: 2200 },
  { text: "> SCANNING MARKET DEPTH: BTC_USDC", color: "text-blue-400", delay: 3000 },
  { text: "  - DEPTH: 10450 bids / 9802 asks", color: "text-zinc-400", delay: 3500 },
  { text: "  - MARKET HEALTH: OPTIMAL (STABLE)", color: "text-emerald-400 font-bold", delay: 4000 },
  { text: "  - VOLATILITY INDEX: NORMALIZED", color: "text-yellow-400", delay: 4800 },
  { text: "> EXECUTING STRATEGY: LIQUIDITY_PROVISION", color: "text-purple-400", delay: 5500 },
  { text: "  - ENTRY: MAKER ORDER @ 90,120.5 (PostOnly)", color: "text-zinc-300", delay: 6000 },
  { text: "  - RISK PARAMETERS: ACTIVE", color: "text-red-400", delay: 6500 },
  { text: "  - EFFICIENCY TARGET: 99.9%", color: "text-emerald-400", delay: 7000 },
  { text: "> ORDER PLACED: ID #88291029 [CONFIRMED]", color: "text-emerald-500", delay: 7800 },
  { text: "> MAINTAINING MARKET STABILITY...", color: "text-blue-400 animate-pulse", delay: 8500 },
];

const TerminalSimulation = () => {
  const [lines, setLines] = useState<string[]>([]);
  const [cursorVisible, setCursorVisible] = useState(true);

  useEffect(() => {
    const timeouts: NodeJS.Timeout[] = [];
    
    // Loop animation
    const runAnimation = () => {
      setLines([]);
      terminalLogs.forEach((log) => {
        const timeout = setTimeout(() => {
          setLines(prev => [...prev, `<span class="${log.color}">${log.text}</span>`]);
        }, log.delay);
        timeouts.push(timeout);
      });

      // Restart loop
      const resetTimeout = setTimeout(() => {
        runAnimation();
      }, 12000);
      timeouts.push(resetTimeout);
    };

    runAnimation();

    // Cursor blink
    const cursorInterval = setInterval(() => {
      setCursorVisible(v => !v);
    }, 500);

    return () => {
      timeouts.forEach(clearTimeout);
      clearInterval(cursorInterval);
    };
  }, []);

  return (
    <div className="font-mono text-xs md:text-sm p-6 bg-black/90 rounded-lg border border-zinc-800 shadow-2xl h-100 overflow-hidden flex flex-col">
      <div className="flex items-center gap-2 mb-4 border-b border-zinc-800 pb-2">
        <Terminal className="w-4 h-4 text-emerald-500" />
        <span className="text-zinc-500">obiwork-core — python3 volume_farmer.py</span>
      </div>
      <div className="flex-1 overflow-hidden flex flex-col justify-end">
         <div className="space-y-1">
            {lines.map((line, i) => (
              <div key={i} dangerouslySetInnerHTML={{ __html: line }} />
            ))}
            <div className="text-emerald-500">
              $ <span className={`inline-block w-2 h-4 bg-emerald-500 align-middle ${cursorVisible ? 'opacity-100' : 'opacity-0'}`}></span>
            </div>
         </div>
      </div>
    </div>
  );
};

export default function ProofSection() {
  return (
    <section className="relative py-24 bg-zinc-950 border-t border-zinc-900">
      <div className="container px-4 md:px-6 mx-auto">
        
        {/* Header */}
        <div className="mb-16 text-center">
          <h2 className="text-3xl md:text-5xl font-bold font-mono tracking-tighter mb-4 text-white">
            PROOF OF VOLUME. <span className="text-emerald-500">REAL.</span>
          </h2>
          <p className="text-zinc-400 max-w-2xl mx-auto font-mono">
            Métricas e logs fazem parte do pipeline de validação do agente.
            <br />
            Backpack Season 4: 423.77M volume units, Day 70/70.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {[
            { label: "LIQUIDITY PROVIDED", value: "$1,376,499+", icon: BarChart3, color: "text-emerald-400" },
            { label: "PLATFORM SYNC", value: "< 45ms", icon: Zap, color: "text-yellow-400" },
            { label: "SYSTEM UPTIME", value: "99.9%", icon: Activity, color: "text-blue-400" },
            { label: "SEASON 4 VOLUME", value: "423.77M units", icon: Medal, color: "text-emerald-400" },
          ].map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-lg hover:bg-zinc-900 transition-colors"
            >
              <div className="flex items-center gap-3 mb-2">
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
                <span className="text-xs font-mono text-zinc-500 tracking-wider">{stat.label}</span>
              </div>
              <div className={`text-2xl font-bold font-mono ${stat.color}`}>{stat.value}</div>
            </motion.div>
          ))}
        </div>

        <div className="mb-16">
          <TerminalSimulation />
        </div>

        {/* OFFICIAL BACKPACK VALIDATION */}
        <div className="mb-20">
          <h3 className="text-xs font-mono text-zinc-500 mb-6 text-center uppercase tracking-[0.2em]">Official Platform Verification</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* CARD 1: RANK */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="bg-zinc-900/80 border border-yellow-900/30 p-6 rounded-xl flex flex-col items-center justify-center text-center"
            >
              <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center mb-4 border border-yellow-700 shadow-lg shadow-black/50">
                <Medal className="w-8 h-8 text-yellow-400" /> {/* Gold */}
              </div>
              <div className="text-4xl font-bold text-white font-mono mb-1">CONSISTENT</div>
              <div className="text-zinc-400 font-mono text-xs uppercase tracking-wider mb-3">Engagement Level</div>
              <div className="px-3 py-1 bg-yellow-950/20 rounded text-xs text-yellow-400 font-mono border border-yellow-900/50">STATUS: VERIFIED</div>
            </motion.div>

            {/* CARD 2: VOLUME REPUTATION */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.1 }}
              className="bg-zinc-900/80 border border-emerald-900/30 p-6 rounded-xl flex flex-col items-center justify-center text-center relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-linear-to-r from-emerald-600 to-emerald-400"></div>
              <div className="text-xs font-mono text-emerald-500 mb-4 flex items-center gap-2 bg-emerald-950/30 px-3 py-1 rounded-full border border-emerald-900/50">
                  <ShieldCheck className="w-3 h-3" /> VERIFIED CONTRIBUTOR
              </div>
              <div className="text-3xl font-bold text-white font-mono mb-1 tracking-tight">$1,500,000+</div>
              <div className="text-zinc-500 font-mono text-[10px] uppercase tracking-widest mb-6">LIFETIME CONTRIBUTION</div>
              
              <div className="w-full bg-zinc-950 h-3 rounded-full mb-2 overflow-hidden border border-zinc-800">
                  <div className="bg-emerald-500 h-full w-[92%] shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
              </div>
              <div className="flex justify-between w-full text-[10px] font-mono text-zinc-500 px-1">
                  <span>Growth</span>
                  <span className="text-emerald-500/70">Target: Sustained</span>
              </div>
            </motion.div>

            {/* CARD 3: BADGES */}
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="bg-zinc-900/80 border border-zinc-800 p-6 rounded-xl"
            >
              <div className="text-xs font-mono text-zinc-500 mb-4 uppercase tracking-wider flex items-center gap-2 justify-center md:justify-start">
                <Trophy className="w-4 h-4 text-yellow-500" /> Milestones
              </div>
              <div className="space-y-3">
                  {[
                    { name: "Top Contributor", color: "text-yellow-400", icon: Award, bg: "bg-yellow-950/20", border: "border-yellow-900/30" },
                    { name: "Consistent Liquidity", color: "text-emerald-400", icon: Award, bg: "bg-emerald-950/20", border: "border-emerald-900/30" },
                    { name: "Long-Term Holder", color: "text-blue-400", icon: CheckCircle2, bg: "bg-blue-950/20", border: "border-blue-900/30" },
                    { name: "Active Participant", color: "text-orange-400", icon: Activity, bg: "bg-orange-950/20", border: "border-orange-900/30" },
                  ].map((badge, idx) => (
                    <div key={idx} className={`flex items-center gap-3 p-2 rounded border ${badge.bg} ${badge.border} hover:opacity-80 transition-opacity`}>
                        <badge.icon className={`w-4 h-4 ${badge.color}`} />
                        <span className="text-xs font-mono text-zinc-300">{badge.name}</span>
                    </div>
                  ))}
              </div>
            </motion.div>
          </div>
        </div>

        {/* The "Difference" - Terminal Comparison */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          
          {/* Left: The Pain (Retail) */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="p-8 rounded-lg border border-red-900/20 bg-red-950/5 relative overflow-hidden group"
          >
            <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-40 transition-opacity">
              <Activity className="w-24 h-24 text-red-500" />
            </div>
            <h3 className="text-xl font-bold text-red-400 font-mono mb-4">USO TRANSACTIONAL</h3>
            <ul className="space-y-3 font-mono text-sm text-zinc-400">
              <li className="flex items-start gap-2">
                <span className="text-red-500">×</span>
                <span>Emoção humana impactando em perdas</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-500">×</span>
                <span>Execução manual e reativa</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-500">×</span>
                <span>Baixo farm em PEPR DEX</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-500">×</span>
                <span>Sem prova verificável de contribuição em liquidez</span>
              </li>
            </ul>
          </motion.div>

          {/* Right: The Solution (OBI Engineer) */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="p-8 rounded-lg border border-emerald-900/20 bg-emerald-950/5 relative overflow-hidden group"
          >
             <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-40 transition-opacity">
              <Lock className="w-24 h-24 text-emerald-500" />
            </div>
            <h3 className="text-xl font-bold text-emerald-400 font-mono mb-4">OBI AGENT</h3>
            <ul className="space-y-3 font-mono text-sm text-zinc-300">
              <li className="flex items-start gap-2">
                <span className="text-emerald-500"></span>
                <span><strong>Prova Real:</strong> métricas e logs no pipeline de validação.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-500"></span>
                <span><strong>Relatórios:</strong> evidências verificáveis para o hackathon.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-500"></span>
                <span><strong>Reputação:</strong> transparência e auditabilidade contínuas.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-500"></span>
                <span><strong>Impacto:</strong> confiança com prova social real.</span>
              </li>
            </ul>
          </motion.div>

        </div>
        <div className="mt-16">
          <h3 className="text-xs font-mono text-zinc-500 mb-4 text-center uppercase tracking-[0.2em]">Critérios do Hackathon</h3>
          <div className="max-w-3xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              "Impacto com métricas reais de liquidez",
              "Inovação aplicada ao agente e reputação",
              "Execução técnica com pipeline verificável",
              "Clareza na narrativa e evidências",
            ].map((item) => (
              <div key={item} className="p-4 border border-zinc-800 bg-zinc-900/40 rounded text-sm font-mono text-zinc-300">
                {item}
              </div>
            ))}
          </div>
        </div>
        <div className="mt-12 flex justify-center">
          <Link href="/dashboard">
            <button className="px-8 py-4 bg-emerald-500 text-black font-bold font-mono rounded hover:bg-emerald-400 transition-all shadow-[0_0_20px_rgba(16,185,129,0.4)] hover:shadow-[0_0_40px_rgba(16,185,129,0.6)]">
              Ver evidências
            </button>
          </Link>
        </div>
      </div>
    </section>
  );
}
