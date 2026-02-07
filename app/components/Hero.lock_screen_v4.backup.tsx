"use client"; 
 
 import { motion, useMotionValue, useSpring, useTransform, AnimatePresence } from "framer-motion"; 
 import { Terminal, Shield, Cpu, ChevronRight, Compass, Target } from "lucide-react"; 
 import Link from "next/link"; 
 import { useState, useRef, useEffect } from "react"; 
 import ObiWorkLogo from "./ObiWorkLogo"; 
import SniperScope from "./SniperScope"; 

// Chart Background Component (Simulated Market Data)
const ChartBackground = () => (
  <div className="absolute inset-0 flex items-center justify-center opacity-60 mix-blend-screen pointer-events-none">
    <svg width="100%" height="100%" viewBox="0 0 800 600" preserveAspectRatio="none" className="w-full h-full opacity-50">
      {/* Grid Lines */}
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(16, 185, 129, 0.1)" strokeWidth="0.5" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid)" />
      
      {/* Candles */}
      <g transform="translate(0, 100) scale(1, 0.8)">
         {/* Random Candles Left */}
         <rect x="250" y="200" width="10" height="40" fill="#ef4444" opacity="0.6" />
         <line x1="255" y1="180" x2="255" y2="260" stroke="#ef4444" strokeWidth="1" />
         
         <rect x="280" y="220" width="10" height="20" fill="#10b981" opacity="0.6" />
         <line x1="285" y1="210" x2="285" y2="250" stroke="#10b981" strokeWidth="1" />

         <rect x="310" y="190" width="10" height="60" fill="#ef4444" opacity="0.6" />
         <line x1="315" y1="170" x2="315" y2="270" stroke="#ef4444" strokeWidth="1" />

         {/* TARGET GREEN CANDLE (CENTER) */}
         {/* Positioned to align with crosshair center */}
         <g className="animate-pulse">
            <rect x="390" y="180" width="20" height="120" fill="#10b981" className="drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]" />
            <line x1="400" y1="140" x2="400" y2="340" stroke="#10b981" strokeWidth="2" />
         </g>

         {/* Random Candles Right */}
         <rect x="430" y="160" width="10" height="30" fill="#10b981" opacity="0.6" />
         <line x1="435" y1="150" x2="435" y2="200" stroke="#10b981" strokeWidth="1" />

         <rect x="460" y="180" width="10" height="50" fill="#ef4444" opacity="0.6" />
         <line x1="465" y1="160" x2="465" y2="250" stroke="#ef4444" strokeWidth="1" />
      </g>
    </svg>
  </div>
);

export default function Hero() { 
   // Mouse Interaction State 
   const ref = useRef<HTMLDivElement>(null); 
   const [isFiring, setIsFiring] = useState(false); 
  const [isUnlocked, setIsUnlocked] = useState(false); // Default: Locked 
  const [isHit, setIsHit] = useState(false); // Visual feedback for shot impact
  const [textIndex, setTextIndex] = useState(0); 

  const PHRASES = [ 
     "SKIN IN THE GAME", 
     "EXECUÇÃO SOBERANA", 
     "PROTEÇÃO ATÔMICA", 
     "OBI AGENT V4", 
     "VALIDADO ON-CHAIN: BACKPACK AIRDROP" 
   ]; 
 
   useEffect(() => { 
     if (isUnlocked) return; 
     const interval = setInterval(() => { 
         setTextIndex((prev) => (prev + 1) % PHRASES.length); 
     }, 2000); // Synced with animate-pulse (2s duration) 
     return () => clearInterval(interval); 
   }, [isUnlocked]); 
   
   // Motion Values for Mouse Tracking 
   const x = useMotionValue(0); 
   const y = useMotionValue(0); 
   
   // Smooth Spring Physics for Aiming 
   const mouseX = useSpring(x, { stiffness: 150, damping: 15 }); 
   const mouseY = useSpring(y, { stiffness: 150, damping: 15 }); 
 
   // Handle Mouse Move 
   function handleMouseMove(event: React.MouseEvent<HTMLDivElement>) { 
     // If unlocked, we don't need to track mouse for scope anymore (unless we want parallax) 
     // But for the locked state, we need it. 
     // Since we are changing structure, let's keep tracking on the main container or window if possible, 
     // or just the overlay. 
     const centerX = window.innerWidth / 2; 
     const centerY = window.innerHeight / 2; 
     x.set((event.clientX - centerX) / 15); 
     y.set((event.clientY - centerY) / 15); 
   } 
 
   // Handle Fire Click (Unlock Mechanism) 
  function handleFire() { 
    if (isFiring || isUnlocked) return; 
    setIsFiring(true); 
    
    // 1. Visual Impact (Shake)
    setTimeout(() => {
        setIsHit(true);
    }, 100);

    // 2. Unlock sequence
    setTimeout(() => { 
        setIsUnlocked(true); 
        setIsFiring(false); 
        setIsHit(false);
        // Scroll to top immediately after unlock
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }, 800); 
  } 
 
   return ( 
     <div 
         className="relative min-h-screen flex flex-col items-center bg-zinc-950 text-white selection:bg-emerald-500/30 overflow-x-hidden" 
         onMouseMove={handleMouseMove} // Global mouse tracking for scope effect 
     > 
       
       {/* GLOBAL BACKGROUND (Always Visible) */} 
       <div className="fixed inset-0 z-0 pointer-events-none"> 
         <div className="absolute inset-0 bg-black opacity-90" /> 
         <div className="absolute inset-0 bg-size-[24px_24px] [background-image:linear-gradient(to_right,#1f2937_1px,transparent_1px),linear-gradient(to_bottom,#1f2937_1px,transparent_1px)] opacity-20" /> 
         <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-125 h-125 bg-emerald-500/10 rounded-full blur-[120px]" /> 
       </div> 
 
       {/* ------------------------------------------------------------------ */} 
       {/* LOCKED STATE: SNIPER OVERLAY (FIXED HUD)                           */} 
       {/* ------------------------------------------------------------------ */} 
       <AnimatePresence> 
         {!isUnlocked && ( 
             <motion.div 
                 key="lock-screen" 
                 initial={{ opacity: 1 }} 
                 exit={{ opacity: 0, scale: 1.5, filter: "blur(20px)" }} 
                 transition={{ duration: 0.8, ease: "easeInOut" }} 
                 className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/40 backdrop-blur-[3px] cursor-crosshair" 
                 onClick={handleFire} 
             > 
                 {/* INSTRUCTIONS / COPY (SLIDER CENTERED) */} 
                 <div className="absolute inset-0 flex flex-col items-center justify-center z-50 pointer-events-none pb-20"> 
                     <AnimatePresence mode="wait"> 
                         <motion.div 
                            key={textIndex} 
                            initial={{ opacity: 0, scale: 0.9, filter: "blur(10px)" }} 
                            animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }} 
                            exit={{ opacity: 0, scale: 1.1, filter: "blur(10px)" }} 
                            transition={{ duration: 0.4, ease: "easeOut" }} 
                            className="text-center" 
                        > 
                            <h2 className="text-5xl md:text-7xl font-thin font-sans text-white tracking-widest mb-4 drop-shadow-[0_0_25px_rgba(255,255,255,0.4)]"> 
                                {PHRASES[textIndex]} 
                            </h2> 
                        </motion.div> 
                     </AnimatePresence> 
                     
                     <motion.p 
                         initial={{ opacity: 0 }} 
                         animate={{ opacity: [0.5, 1, 0.5] }} 
                         transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }} 
                         className="text-emerald-500 font-mono text-sm md:text-base tracking-[0.3em] mt-4" 
                     > 
                         &lt; CLICK TO SHOOT & UNLOCK ALPHA /&gt; 
                     </motion.p> 
                 </div> 
 
                 {/* SNIPER SCOPE VISUALS */} 
                    <div className="relative w-full h-full flex items-center justify-center pointer-events-none"> 
                        <SniperScope> 
                        <div className="relative w-[85vmin] h-[85vmin] max-w-[1000px] max-h-[1000px] flex items-center justify-center"> 
                            
                            {/* Moving Scope Layer */} 
                           <motion.div 
                              className="w-full h-full relative"
                              style={{ x: mouseX, y: mouseY }}
                           >
                              {/* CHART BACKGROUND (Target) */}
                              <ChartBackground />

                              <motion.img 
                                  src="/mira.png" 
                                  alt="Sniper Scope" 
                                  className="relative z-20 w-full h-full object-contain drop-shadow-[0_0_30px_rgba(16,185,129,0.3)]"
                                  animate={{ scale: [1, 1.02, 1] }}
                                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                              />
                              
                              {/* HIT MARKER (Impact on Green Candle) */}
                              {isHit && (
                                <motion.div
                                    initial={{ opacity: 1, scale: 0 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ duration: 0.1, type: "spring" }}
                                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-30"
                                >
                                    {/* Core Impact */}
                                    <div className="w-4 h-4 bg-white rounded-full shadow-[0_0_20px_rgba(255,255,255,1)] animate-ping" />
                                    {/* Debris/Sparks */}
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <div className="w-12 h-0.5 bg-yellow-300 rotate-45" />
                                        <div className="w-12 h-0.5 bg-yellow-300 -rotate-45" />
                                    </div>
                                    {/* Permanent Mark (Hole) */}
                                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-black border border-zinc-500 rounded-full opacity-80" />
                                </motion.div>
                              )}

                              {/* MUZZLE FLASH EFFECT (Realistic) */}
                              {isFiring && (
                                  <div className="absolute inset-0 z-50 flex items-center justify-center pointer-events-none">
                                      {/* Core Flash */}
                                      <motion.div 
                                          initial={{ opacity: 1, scale: 0.5 }}
                                          animate={{ opacity: 0, scale: 2.5 }}
                                          transition={{ duration: 0.15, ease: "easeOut" }}
                                          className="w-[150px] h-[150px] bg-white rounded-full blur-[20px] mix-blend-overlay"
                                      />
                                      {/* Shockwave */}
                                      <motion.div 
                                          initial={{ opacity: 0.8, scale: 0.8, borderWidth: "10px" }}
                                          animate={{ opacity: 0, scale: 1.5, borderWidth: "0px" }}
                                          transition={{ duration: 0.2 }}
                                          className="w-[300px] h-[300px] rounded-full border-emerald-300 absolute"
                                      />
                                      {/* Lens Flare Streak */}
                                      <motion.div
                                          initial={{ width: "10%", opacity: 0 }}
                                          animate={{ width: "150%", opacity: [0, 1, 0] }}
                                          transition={{ duration: 0.1 }}
                                          className="h-[2px] bg-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 shadow-[0_0_20px_white]"
                                      />
                                  </div>
                              )}
                           </motion.div>
                        </div>
                     </SniperScope> 
                </div> 
            </motion.div> 
        )} 
      </AnimatePresence>
 
       {/* --- LAYER 1: CONTENT (Dark Reveal Mode) --- */}
       {/* Content Wrapper that blurs/darkens when locked - Scrollable but non-interactive */}
      <motion.div 
         animate={isHit ? { x: [-10, 10, -10, 10, 0], scale: [1, 0.99, 1] } : {}}
         transition={{ duration: 0.4 }}
         className={`relative z-10 w-full flex flex-col items-center transition-all duration-1000 ease-in-out ${isUnlocked ? 'opacity-100 grayscale-0 blur-0' : 'opacity-40 grayscale blur-sm pointer-events-none'}`}
      >
         
         {/* BRAND HEADER (Absolute Top) */}
          <div className="absolute top-0 left-0 w-full p-6 flex justify-between items-center z-50">
              <div className="flex items-center gap-2 opacity-50 hover:opacity-100 transition-opacity">
                 <ObiWorkLogo size="sm" />
              </div>
              <div className="hidden md:flex gap-6 text-xs font-mono text-zinc-500">
                 <Link href="/manifesto" className="hover:text-emerald-500 cursor-pointer transition-colors">MANIFESTO</Link>
                 <Link href="/marketplace" className="hover:text-emerald-500 cursor-pointer transition-colors">MARKET</Link>
                 <Link href="/access" className="hover:text-emerald-500 cursor-pointer transition-colors">ACCESS</Link>
              </div>
          </div>

          <div className="container px-4 md:px-6 relative z-10 flex flex-col items-center text-center mt-20">
            
            {/* Badge */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 text-xs font-mono mb-8"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              SYSTEM ONLINE // V4.0.2
            </motion.div>

            {/* LOGO HERO */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="mb-8"
            >
               <ObiWorkLogo size="xl" className="justify-center" />
            </motion.div>

            {/* Subtitle */}
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg md:text-xl text-zinc-400 max-w-2xl mb-10 font-mono"
            >
              A <span className="text-emerald-400 font-bold">Hybrid Trading Infrastructure</span>.
              <br />
              <span className="text-white">Python Brain (Off-Chain)</span> + <span className="text-emerald-500">Solana Heart (On-Chain)</span>.
              <br />
              <span className="text-xs text-zinc-500 uppercase tracking-widest mt-2 block">
                Universal Adapter: Backpack • Binance • Bybit • Hyperliquid
              </span>
            </motion.p>

            {/* Buttons */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-4"
            >
              <button className="group relative px-8 py-3 bg-white text-black font-bold font-mono rounded hover:bg-zinc-200 transition-colors flex items-center gap-2">
                ENTER WORKROOM
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
              <Link href="/manifesto">
                <button className="px-8 py-3 bg-zinc-900 border border-zinc-800 text-zinc-300 font-mono rounded hover:bg-zinc-800 transition-colors flex items-center gap-2 cursor-pointer">
                  <Terminal className="w-4 h-4" />
                  READ MANIFESTO
                </button>
              </Link>
            </motion.div>

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 text-left w-full max-w-5xl">
              <div className="p-6 rounded-lg border border-zinc-800 bg-zinc-900/50 hover:border-emerald-500/50 transition-colors">
                <Shield className="w-8 h-8 text-emerald-500 mb-4" />
                <h3 className="text-xl font-bold font-mono mb-2">Sovereign Execution</h3>
                <p className="text-zinc-400 text-sm">
                  Conecte-se à sua exchange de confiança. OBI é agnóstico. 
                  Sua estratégia, suas chaves, sua custódia.
                </p>
              </div>
              <div className="p-6 rounded-lg border border-zinc-800 bg-zinc-900/50 hover:border-emerald-500/50 transition-colors">
                <Terminal className="w-8 h-8 text-emerald-500 mb-4" />
                <h3 className="text-xl font-bold font-mono mb-2">Universal Adapter</h3>
                <p className="text-zinc-400 text-sm">
                  Uma lógica, múltiplos mercados. Arbitragem de latência e Hedge Cruzado 
                  entre Binance e Backpack em milissegundos.
                </p>
              </div>
              <div className="p-6 rounded-lg border border-zinc-800 bg-zinc-900/50 hover:border-emerald-500/50 transition-colors">
                <Cpu className="w-8 h-8 text-emerald-500 mb-4" />
                <h3 className="text-xl font-bold font-mono mb-2">On-Chain Oracle</h3>
                <p className="text-zinc-400 text-sm">
                  Não adivinhamos. Lemos o fluxo. OBI (Order Book Imbalance) dita a regra do jogo.
                </p>
              </div>
            </div>

          </div>
       </motion.div>
     </div> 
   ); 
 }
