"use client";

import { motion } from "framer-motion";
import { ShieldCheck, ArrowLeft, Terminal, Shield, Layers, Cpu, Crosshair } from "lucide-react";
import Link from "next/link";
import BrandHeader3D from "../components/BrandHeader3D";

const CLONE_MODELS = [
  {
    id: "scout",
    name: "OBI SCOUT",
    codename: "THE GATEKEEPER",
    desc: "Unidade tática leve. Focada em sobrevivência e proteção de capital.",
    icon: Shield,
    color: "text-emerald-500",
    border: "border-emerald-500/30",
    bg: "bg-emerald-900/10",
    specs: ["CLI Access", "Sentinel Shield", "Phoenix V2"]
  },
  {
    id: "commander",
    name: "OBI COMMANDER",
    codename: "THE FARMER",
    desc: "Unidade de campo pesado. Especialista em colheita de yield e volume.",
    icon: Layers,
    color: "text-blue-500",
    border: "border-blue-500/30",
    bg: "bg-blue-900/10",
    specs: ["Delta Neutral", "Grid Weaver", "Multi-Account"]
  },
  {
    id: "architect",
    name: "OBI ARCHITECT",
    codename: "THE GOD MODE",
    desc: "Unidade de comando estratégico. Visão total e infraestrutura dedicada.",
    icon: Cpu,
    color: "text-yellow-500",
    border: "border-yellow-500/30",
    bg: "bg-yellow-900/10",
    specs: ["OBI Oracle", "HFT Execution", "Iron Dome VPS"]
  }
];

export default function ClonesPage() {
  return (
    <div className="min-h-screen bg-black text-white font-mono selection:bg-emerald-500/30 pb-20">
      
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-zinc-800 bg-black/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span>BACK TO TERMINAL</span>
          </Link>
          <div className="flex items-center gap-2 text-emerald-500 font-bold tracking-wider">
            <Terminal className="w-4 h-4" />
            <span>CLONE.ARMORY</span>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 pt-12">
        
        <BrandHeader3D />

        <div className="text-center mb-16 mt-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/30 border border-emerald-900 text-emerald-400 text-xs mb-6">
            <ShieldCheck className="w-3 h-3" />
            VERIFIED OPERATORS ONLY
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">CHOOSE YOUR <span className="text-emerald-500">WEAPON</span></h1>
          <p className="text-zinc-400 max-w-2xl mx-auto">
            Cada Clone é uma licença de software autônoma, calibrada para um perfil operacional específico.
            <br/>
            <span className="text-zinc-500">Selecione o modelo para iniciar a sequência de aquisição.</span>
          </p>
        </div>

        {/* Clones Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
           {CLONE_MODELS.map((model, i) => (
             <Link href={`/marketplace/${model.id}`} key={model.id} className="group">
               <motion.div
                 initial={{ opacity: 0, y: 20 }}
                 animate={{ opacity: 1, y: 0 }}
                 transition={{ delay: i * 0.1 }}
                 className={`h-full p-8 rounded-2xl border ${model.border} ${model.bg} hover:bg-opacity-20 transition-all duration-300 relative overflow-hidden`}
               >
                  {/* Hover Glow */}
                  <div className={`absolute inset-0 bg-gradient-to-br from-transparent to-black opacity-50 group-hover:opacity-30 transition-opacity`} />
                  
                  <div className="relative z-10 flex flex-col h-full items-center text-center">
                     <div className={`w-20 h-20 rounded-full border border-zinc-700 bg-black flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 ${model.color}`}>
                        <model.icon className="w-10 h-10" />
                     </div>
                     
                     <div className={`text-xs font-bold tracking-[0.2em] mb-2 ${model.color}`}>{model.codename}</div>
                     <h3 className="text-2xl font-bold text-white mb-4">{model.name}</h3>
                     <p className="text-sm text-zinc-400 mb-8 leading-relaxed">
                       {model.desc}
                     </p>

                     <div className="mt-auto space-y-3 w-full">
                        {model.specs.map((spec, idx) => (
                          <div key={idx} className="flex items-center justify-center gap-2 text-xs text-zinc-500 border-t border-zinc-800/50 pt-2">
                             <Crosshair className="w-3 h-3" />
                             {spec}
                          </div>
                        ))}
                     </div>

                     <div className="mt-8 w-full">
                        <button className={`w-full py-3 rounded border border-zinc-700 bg-black text-white text-xs font-bold uppercase tracking-wider group-hover:${model.color} group-hover:border-current transition-colors`}>
                           INSPECT MODEL
                        </button>
                     </div>
                  </div>
               </motion.div>
             </Link>
           ))}
        </div>

        {/* Footer Warning */}
        <div className="mt-20 text-center max-w-2xl mx-auto p-6 border border-red-900/30 bg-red-950/10 rounded-xl">
           <h4 className="text-red-500 font-bold mb-2 flex items-center justify-center gap-2">
             <Shield className="w-4 h-4" />
             PROTOCOL WARNING
           </h4>
           <p className="text-xs text-zinc-400">
             A utilização de Clones não autorizados (piratas) resultará em banimento imediato da rede OBI.
             Sempre verifique o hash do seu SBT após a emissão.
           </p>
        </div>

      </main>
    </div>
  );
}
