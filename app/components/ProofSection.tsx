"use client";

import { motion } from "framer-motion";
import { Activity, BarChart3, Lock, Medal, Trophy, CheckCircle2, Award, ShieldCheck, Terminal } from "lucide-react";
import { useState, useEffect } from "react";
import Link from "next/link";

const terminalLogs = [
  { text: "> INITIALIZING LIQUIDITY CORE v1.0...", color: "text-zinc-300", delay: 100 },
  { text: "> ESTABLISHING SECURE CONNECTION... [OK]", color: "text-emerald-400", delay: 800 },
  { text: "> VERIFYING PARTNERSHIP CREDENTIALS... [VERIFIED]", color: "text-emerald-400", delay: 1500 },
  { text: "> LOADING MARKET ANALYSIS ENGINE... [READY]", color: "text-zinc-300", delay: 2200 },
  { text: "> SCANNING MARKET DEPTH: SOL_USDC", color: "text-blue-400", delay: 3000 },
  { text: "  - DEPTH: 45,200 bids / 38,900 asks", color: "text-zinc-400", delay: 3500 },
  { text: "  - MARKET HEALTH: OPTIMAL (STABLE)", color: "text-emerald-400 font-bold", delay: 4000 },
  { text: "> EXECUTING STRATEGY: OBI_SEASON_4", color: "text-purple-400", delay: 5500 },
  { text: "  - TARGET: LEVEL 15 (PLATINUM)", color: "text-zinc-300", delay: 6000 },
  { text: "  - CURRENT TIER: LEVEL 14 (GOLD)", color: "text-yellow-400 font-bold", delay: 6500 },
  { text: "  - EFFICIENCY TARGET: 99.9%", color: "text-emerald-400", delay: 7000 },
  { text: "> PROOF GENERATED: HASH 37b2ff...afc0 [SIGNED]", color: "text-emerald-500", delay: 7800 },
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
    <div className="font-mono text-xs md:text-sm p-4 md:p-6 bg-black/90 rounded-lg border border-zinc-800 shadow-2xl h-80 md:h-100 overflow-hidden flex flex-col">
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

  const t = {
    title: "PROOF OF VOLUME. REAL.",
    desc_line1: "On-chain social proof with real metrics from Backpack.",
    desc_line2: "Logs and reports are part of the agent validation pipeline.",
    stats: {
      liquidity: "LIQUIDITY PROVIDED",
      rank: "SEASON 4 RANK",
      uptime: "SYSTEM UPTIME",
      level: "CURRENT LEVEL"
    },
    verification_title: "OFFICIAL PLATFORM VERIFICATION",
    latest_proof: "LATEST PROOF:",
    card_rank: {
      title: "CONSISTENT",
      subtitle: "Engagement Level",
      status: "STATUS: VERIFIED"
    },
    card_volume: {
      label: "VERIFIED CONTRIBUTOR",
      subtitle: "LIFETIME CONTRIBUTION",
      target: "Target: Level 15 (Plat)"
    },
    card_badges: {
      title: "Milestones",
      items: ["Top Contributor", "Consistent Liquidity", "Long-Term Holder", "Active Participant"]
    }
  };

  return (
    <section id="proof" className="relative py-16 md:py-24 bg-zinc-950 border-t border-zinc-900">
      <div className="container px-4 md:px-6 mx-auto">
        
        {/* Header */}
        <div className="mb-16 text-center">
          <h2 className="text-3xl md:text-5xl font-bold font-mono tracking-tighter mb-4 text-white">
            {t.title.split('.')[0]}. <span className="text-emerald-500">REAL.</span>
          </h2>
          <p className="text-zinc-400 max-w-2xl mx-auto font-mono">
            {t.desc_line1}
            <br />
            {t.desc_line2}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {[
            { label: t.stats.liquidity, value: "$2,272,666+", icon: BarChart3, color: "text-emerald-400" },
            { label: t.stats.rank, value: "GOLD (2,628 pts)", icon: Trophy, color: "text-yellow-400" },
            { label: t.stats.uptime, value: "99.9%", icon: Activity, color: "text-blue-400" },
            { label: t.stats.level, value: "LEVEL 14", icon: Medal, color: "text-emerald-400" },
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
          <h3 className="text-xs font-mono text-zinc-500 mb-6 text-center uppercase tracking-[0.2em]">{t.verification_title}</h3>
          
          {/* HASH PROOF */}
          <div className="flex justify-center mb-8">
             <div className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-900/50 border border-zinc-800 rounded font-mono text-[10px] text-zinc-500 max-w-full overflow-hidden">
                <Lock className="w-3 h-3 text-emerald-500 shrink-0" />
                <span className="hidden sm:inline text-zinc-600">{t.latest_proof}</span>
                <span className="text-emerald-500/80 truncate">37b2ff414d5eceaaac6d408f1e32faac89fe446df4fa3ee07565e8464d43afc0</span>
             </div>
          </div>

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
              <div className="text-4xl font-bold text-white font-mono mb-1">{t.card_rank.title}</div>
              <div className="text-zinc-400 font-mono text-xs uppercase tracking-wider mb-3">{t.card_rank.subtitle}</div>
              <div className="px-3 py-1 bg-yellow-950/20 rounded text-xs text-yellow-400 font-mono border border-yellow-900/50">{t.card_rank.status}</div>
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
                  <ShieldCheck className="w-3 h-3" /> {t.card_volume.label}
              </div>
              <div className="text-3xl font-bold text-white font-mono mb-1 tracking-tight">$2,272,000+</div>
              <div className="text-zinc-500 font-mono text-[10px] uppercase tracking-widest mb-6">{t.card_volume.subtitle}</div>
              
              <div className="w-full bg-zinc-950 h-3 rounded-full mb-2 overflow-hidden border border-zinc-800">
                  <div className="bg-emerald-500 h-full w-[94%] shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
              </div>
              <div className="flex justify-between w-full text-[10px] font-mono text-zinc-500 px-1">
                  <span>Level 14</span>
                  <span className="text-emerald-500/70">{t.card_volume.target}</span>
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
                <Trophy className="w-4 h-4 text-yellow-500" /> {t.card_badges.title}
              </div>
              <div className="space-y-3">
                  {[
                    { name: t.card_badges.items[0], color: "text-yellow-400", icon: Award, bg: "bg-yellow-950/20", border: "border-yellow-900/30" },
                    { name: t.card_badges.items[1], color: "text-emerald-400", icon: Award, bg: "bg-emerald-950/20", border: "border-emerald-900/30" },
                    { name: t.card_badges.items[2], color: "text-blue-400", icon: CheckCircle2, bg: "bg-blue-950/20", border: "border-blue-900/30" },
                    { name: t.card_badges.items[3], color: "text-orange-400", icon: Activity, bg: "bg-orange-950/20", border: "border-orange-900/30" },
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

      </div>
    </section>
  );
}
