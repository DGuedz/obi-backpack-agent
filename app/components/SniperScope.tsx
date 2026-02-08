"use client";

import { Target } from "lucide-react";

export default function SniperScope({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative group flex items-center justify-center">
      {/* --- SCOPE IMAGE OVERLAY --- */}
      <div className="absolute inset-0 z-30 pointer-events-none flex items-center justify-center overflow-hidden">
         {/* The Scope Image - REMOVED (Replaced by Inline SVG in Hero.tsx) */}
      </div>

      {/* --- HUD STATUS OVERLAY (Additional Dynamic Elements) --- */}
      <div className="absolute inset-0 z-40 pointer-events-none p-6 flex flex-col justify-between">
        
        {/* Top Status */}
        <div className="flex justify-between items-start">
           <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400 bg-black/50 px-2 py-0.5 rounded border border-emerald-900/50 backdrop-blur-sm">
                 <span className="animate-pulse w-1.5 h-1.5 bg-red-500 rounded-full"></span> 
                 LIVE FEED
              </div>
           </div>
           
           <div className="text-right">
              <div className="text-[10px] font-mono text-emerald-500/70 bg-black/50 px-2 py-0.5 rounded border border-emerald-900/50 backdrop-blur-sm">
                 TGT: ETH-PERP
              </div>
           </div>
        </div>

        {/* Bottom Status */}
        <div className="flex justify-between items-end">
           <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-500/70 bg-black/50 px-2 py-0.5 rounded border border-emerald-900/50 backdrop-blur-sm">
              <Target className="w-3 h-3" />
              <span>AUTO-LOCK: ENGAGED</span>
           </div>
           
           <div className="text-[10px] font-mono text-emerald-500/50 bg-black/50 px-2 py-0.5 rounded border border-emerald-900/50 backdrop-blur-sm">
              ZOOM: 8.0x
           </div>
        </div>

      </div>

      {/* --- CONTENT CONTAINER (TERMINAL) --- */}
      {/* Reduced padding to fit inside the circular scope view if needed, or just centered behind */}
      <div className="relative z-10 w-full bg-black/90 backdrop-blur-md rounded-lg overflow-hidden border border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.15)]">
        {/* Dark overlay to blend with scope */}
        <div className="absolute inset-0 bg-emerald-900/5 pointer-events-none mix-blend-overlay"></div>
        {children}
      </div>

    </div>
  );
}
