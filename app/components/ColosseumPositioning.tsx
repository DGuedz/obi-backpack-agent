"use client";

import Link from "next/link";
import { Target as TargetIcon } from "lucide-react";

export default function ColosseumPositioning() {

  const t = {
    badge: "COLOSSEUM S4 CANDIDATE",
    title_prefix: "OBI AGENT",
    title_suffix: "PROOF OF EXECUTION",
    desc_line1: "Autonomous agent that validates, simulates, and settles on-chain actions.",
    desc_line2: "Human operation limited to deploy and monitoring.",
    features: [
      { title: "AgentWallet", desc: "Secure isolated signing" },
      { title: "Heartbeat Sync", desc: "Real-time status endpoints" },
      { title: "On-Chain Settle", desc: "Atomic execution on Solana" },
    ],
    problem: {
      title: "THE PROBLEM",
      desc: "Lack of verifiable proof of liquidity contribution and fragile signals of real execution in current agents.",
      items: [
        "Human emotion impacting losses",
        "Low Farm in Perp Dex",
        "Off-chain execution without auditability"
      ]
    },
    solution: {
      title: "THE SOLUTION",
      desc: "Dashboard with real metrics, proofs, and reports validating the agent flow from pre-flight to settlement.",
      items: [
        "Pre-execution validation (State Check)",
        "AgentWallet (Key Isolation)",
        "Verifiable on-chain logs"
      ]
    }
  };

  return (
    <section className="relative z-10 py-16 md:py-24 bg-zinc-950 border-t border-zinc-800">
      {/* Background Grid - Subtle/Technical */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
      
      <div className="container mx-auto px-4 relative z-20">
        
        {/* Header Block */}
        <div className="max-w-4xl mx-auto text-center mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-xs font-mono mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            {t.badge}
          </div>
          
          <h2 className="text-3xl md:text-5xl font-bold font-mono text-white mb-6 tracking-tight">
            {t.title_prefix} <span className="text-zinc-500">{"///"}</span> {t.title_suffix}
          </h2>
          
          <p className="text-lg text-zinc-400 font-mono max-w-2xl mx-auto leading-relaxed">
            {t.desc_line1} <br className="hidden md:block"/>
            <span className="text-zinc-200">{t.desc_line2}</span>
          </p>
        </div>

        {/* Technical Features Strip */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-zinc-800 border border-zinc-800 rounded-lg overflow-hidden mb-20">
          {t.features.map((item, i) => (
            <div key={i} className="bg-zinc-950 p-6 hover:bg-zinc-900/80 transition-colors group">
              <div className="text-emerald-500 text-xs font-mono mb-2 opacity-50 group-hover:opacity-100 transition-opacity">0{i+1}</div>
              <div className="text-white font-mono font-bold text-sm mb-1">{item.title}</div>
              <div className="text-zinc-500 text-xs font-mono">{item.desc}</div>
            </div>
          ))}
        </div>

        {/* Deep Dive Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-20">
          
          {/* Problema */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
              <span className="w-1 h-4 bg-red-500/50 rounded-sm"></span>
              {t.problem.title}
            </h3>
            <div className="p-6 border border-zinc-800 bg-zinc-900/30 rounded-lg h-full hover:border-zinc-700 transition-colors">
              <p className="text-sm font-mono text-zinc-400 mb-6 leading-relaxed">
                {t.problem.desc}
              </p>
              <ul className="space-y-3">
                {t.problem.items.map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-xs font-mono text-zinc-500">
                    <span className="text-red-500/50 mt-0.5">×</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Solução */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
              <span className="w-1 h-4 bg-emerald-500 rounded-sm"></span>
              {t.solution.title}
            </h3>
            <div className="p-6 border border-zinc-800 bg-zinc-900/30 rounded-lg h-full hover:border-emerald-500/20 transition-colors relative overflow-hidden">
              <div className="absolute top-0 right-0 p-2 opacity-10">
                <TargetIcon />
              </div>
              <p className="text-sm font-mono text-zinc-300 mb-6 leading-relaxed">
                {t.solution.desc}
              </p>
              <ul className="space-y-3">
                {t.solution.items.map((item, i) => (
                  <li key={i} className="flex items-start gap-3 text-xs font-mono text-zinc-400">
                    <span className="text-emerald-500 mt-0.5">✓</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}
