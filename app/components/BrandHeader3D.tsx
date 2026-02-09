"use client";

import { motion } from "framer-motion";
import ObiWorkLogo from "./ObiWorkLogo";

export default function BrandHeader3D() {
  
  const SLOGANS = [
    "automated market traders",
    "elite snipers",
    "obi work",
    "community"
  ];

  const currentSlogans = SLOGANS;
  // Duplicate for infinite scroll
  const displaySlogans = [...currentSlogans, ...currentSlogans];

  return (
    <div className="relative perspective-1000 w-full flex justify-center py-12">
      <motion.div
        initial={{ rotateX: 20, rotateY: -10, scale: 0.9 }}
        animate={{ rotateX: 0, rotateY: 0, scale: 1 }}
        transition={{ 
          type: "spring", 
          stiffness: 100, 
          damping: 20,
          duration: 1.5 
        }}
        className="relative transform-style-3d group"
      >
        {/* Holographic Base Glow */}
        <div className="absolute -inset-10 bg-emerald-500/10 blur-3xl rounded-full opacity-50 group-hover:opacity-75 transition-opacity duration-500"></div>

        {/* 3D Container */}
        <div className="relative bg-zinc-950/80 border border-zinc-800/50 backdrop-blur-md p-8 rounded-2xl shadow-2xl transform-style-3d border-t-emerald-500/20 border-l-emerald-500/10">
          
          {/* Depth Layer 1: Logo */}
          <div className="transform translate-z-10 flex flex-col items-center">
             <ObiWorkLogo size="xl" />
          </div>

          {/* Depth Layer 2: Slogan Ring */}
          <div className="mt-6 transform translate-z-20 text-center">
             <div className="relative overflow-hidden py-2 px-4 border-y border-emerald-500/20 bg-emerald-950/20">
                <motion.div 
                  animate={{ x: ["0%", "-100%"] }}
                  transition={{ repeat: Infinity, ease: "linear", duration: 20 }}
                  className="whitespace-nowrap flex items-center gap-8 text-xs font-mono text-emerald-400 uppercase tracking-widest"
                >
                   {displaySlogans.map((slogan, idx) => (
                     <div key={idx} className="flex items-center gap-8">
                        <span>{slogan}</span>
                        <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                     </div>
                   ))}
                </motion.div>
             </div>
          </div>

          {/* Decorative Corners */}
          <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-emerald-500 rounded-tl-lg"></div>
          <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-emerald-500 rounded-tr-lg"></div>
          <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-emerald-500 rounded-bl-lg"></div>
          <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-emerald-500 rounded-br-lg"></div>

        </div>
      </motion.div>
    </div>
  );
}
