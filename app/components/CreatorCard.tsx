"use client";

import { motion } from "framer-motion";
import { Shield, Code2, Cpu, CheckCircle2 } from "lucide-react";
import Image from "next/image";

export default function CreatorCard() {
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="relative group w-full max-w-2xl mx-auto"
    >
      {/* Glow Effect */}
      <div className="absolute -inset-1 bg-linear-to-r from-emerald-500 to-cyan-500 rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
      
      {/* Card Content */}
      <div className="relative bg-black border border-zinc-800 rounded-xl p-8 overflow-hidden">
        
        {/* Background Texture */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-size-[16px_16px] pointer-events-none opacity-20"></div>
        
        <div className="relative z-10 flex flex-col md:flex-row items-center gap-8">
          
          {/* Avatar Section */}
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-zinc-900 border-2 border-emerald-500/30 flex items-center justify-center relative z-10 overflow-hidden group-hover:border-emerald-500 transition-colors">
              {/* Placeholder for Avatar - Shows behind image if image fails or is loading */}
              <div className="absolute inset-0 bg-zinc-800 flex items-center justify-center">
                 <span className="text-3xl font-bold text-white font-mono">DG</span>
              </div>
              <Image 
                src="/avatar.png" 
                alt="Double Green" 
                width={96} 
                height={96} 
                className="object-cover w-full h-full relative z-10"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />
            </div>
            {/* Orbiting Elements */}
            <motion.div 
              animate={{ rotate: 360 }}
              transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 -m-2 border border-dashed border-emerald-500/20 rounded-full z-0"
            />
            <div className="absolute -bottom-2 -right-2 bg-black border border-emerald-500/50 rounded-full p-1.5 z-20" title="Verified Creator">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
            </div>
          </div>

          {/* Info Section */}
          <div className="flex-1 text-center md:text-left space-y-3">
            
            <div className="flex flex-col md:flex-row items-center gap-3 justify-center md:justify-start">
              <h3 className="text-2xl font-bold text-white tracking-tight">Double Green</h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase tracking-wider">
                Creator Engineer & IP Owner
              </span>
            </div>
            
            <p className="text-zinc-400 text-sm font-mono leading-relaxed">
              &quot;Building the tools I wish I had when I started. This ecosystem is not just code; it&apos;s an extension of my will to win.&quot;
            </p>

            {/* Tech Stack / Badges */}
            <div className="flex items-center gap-4 justify-center md:justify-start pt-2">
              <div className="flex items-center gap-1.5 text-xs text-zinc-500 font-mono border border-zinc-800 px-2 py-1 rounded bg-zinc-900/50">
                <Code2 className="w-3 h-3 text-blue-400" />
                <span>Python Core</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-zinc-500 font-mono border border-zinc-800 px-2 py-1 rounded bg-zinc-900/50">
                <Cpu className="w-3 h-3 text-orange-400" />
                <span>HFT Algo</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs text-zinc-500 font-mono border border-zinc-800 px-2 py-1 rounded bg-zinc-900/50">
                <Shield className="w-3 h-3 text-purple-400" />
                <span>Risk Logic</span>
              </div>
            </div>

          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-6 border-t border-zinc-800/50 flex justify-between items-center text-xs font-mono text-zinc-600">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span>OPERATIONAL</span>
          </div>
          <div>ID: 0xDG...PARTNER</div>
        </div>

      </div>
    </motion.div>
  );
}
