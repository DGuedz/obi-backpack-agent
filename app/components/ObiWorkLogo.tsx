interface LogoProps {
  className?: string;
  size?: "sm" | "md" | "lg" | "xl";
}

export default function ObiWorkLogo({ className = "", size = "md" }: LogoProps) {
  const sizeClasses = {
    sm: "w-8 h-8",
    md: "w-12 h-12",
    lg: "w-16 h-16",
    xl: "w-24 h-24"
  };

  const textSizes = {
    sm: "text-lg",
    md: "text-xl",
    lg: "text-2xl",
    xl: "text-4xl"
  };

  const subTextSizes = {
    sm: "text-[6px]",
    md: "text-[8px]",
    lg: "text-[10px]",
    xl: "text-xs"
  };

  return (
    <div className={`flex flex-col items-center gap-4 select-none ${className}`}>
      <div className={`relative flex items-center justify-center ${sizeClasses[size]}`}>
        {/* Glow Effect */}
        <div className="absolute inset-0 bg-emerald-500/20 blur-xl rounded-full"></div>
        
        {/* Sniper Scope SVG */}
        <svg 
          viewBox="0 0 100 100" 
          className="w-full h-full text-emerald-500 relative z-10 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]"
          fill="none" 
          stroke="currentColor" 
          strokeWidth="2"
        >
          {/* Outer Ring with Gaps */}
          <path d="M 50 5 A 45 45 0 0 1 95 50" strokeOpacity="0.8" strokeDasharray="10 5" />
          <path d="M 95 50 A 45 45 0 0 1 50 95" strokeOpacity="0.8" strokeDasharray="10 5" />
          <path d="M 50 95 A 45 45 0 0 1 5 50" strokeOpacity="0.8" strokeDasharray="10 5" />
          <path d="M 5 50 A 45 45 0 0 1 50 5" strokeOpacity="0.8" strokeDasharray="10 5" />
          
          {/* Inner Brackets (Scope Corners) */}
          <path d="M 30 20 L 20 20 L 20 30" strokeWidth="2" strokeLinecap="round" />
          <path d="M 70 20 L 80 20 L 80 30" strokeWidth="2" strokeLinecap="round" />
          <path d="M 30 80 L 20 80 L 20 70" strokeWidth="2" strokeLinecap="round" />
          <path d="M 70 80 L 80 80 L 80 70" strokeWidth="2" strokeLinecap="round" />

          {/* Crosshairs with Mil-Dots */}
          <line x1="50" y1="10" x2="50" y2="90" strokeWidth="1" />
          <line x1="10" y1="50" x2="90" y2="50" strokeWidth="1" />
          
          {/* Vertical Mil-Dots */}
          <line x1="48" y1="30" x2="52" y2="30" strokeWidth="1" />
          <line x1="48" y1="40" x2="52" y2="40" strokeWidth="1" />
          <line x1="48" y1="60" x2="52" y2="60" strokeWidth="1" />
          <line x1="48" y1="70" x2="52" y2="70" strokeWidth="1" />

          {/* Horizontal Mil-Dots */}
          <line x1="30" y1="48" x2="30" y2="52" strokeWidth="1" />
          <line x1="40" y1="48" x2="40" y2="52" strokeWidth="1" />
          <line x1="60" y1="48" x2="60" y2="52" strokeWidth="1" />
          <line x1="70" y1="48" x2="70" y2="52" strokeWidth="1" />

          {/* Center Target (Open Cross) */}
          <circle cx="50" cy="50" r="15" strokeWidth="0.5" strokeOpacity="0.5" />
          
          {/* Radar Pulse Effect - Multiple Rings */}
          <circle cx="50" cy="50" r="10" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.2">
            <animate attributeName="r" from="0" to="25" dur="3s" repeatCount="indefinite" />
            <animate attributeName="opacity" from="0.6" to="0" dur="3s" repeatCount="indefinite" />
          </circle>
          <circle cx="50" cy="50" r="10" stroke="currentColor" strokeWidth="0.5" strokeOpacity="0.2">
            <animate attributeName="r" from="0" to="25" dur="3s" begin="1.5s" repeatCount="indefinite" />
            <animate attributeName="opacity" from="0.6" to="0" dur="3s" begin="1.5s" repeatCount="indefinite" />
          </circle>
          
          {/* Red Dot Pulse (Dead Center) */}
          <circle cx="50" cy="50" r="2" fill="#ef4444" className="animate-pulse" />
        </svg>
      </div>
      
      <div className="flex flex-col items-center justify-center leading-none">
        <div className="flex items-baseline">
            <span className={`font-mono font-bold text-white tracking-tighter ${textSizes[size]}`}>OBI</span>
            <span className={`font-mono font-light text-zinc-400 tracking-tighter ${textSizes[size]}`}>WORK</span>
        </div>
        <div className="flex items-center gap-2 mt-2">
            <span className={`font-mono text-emerald-500 tracking-[0.3em] uppercase ${subTextSizes[size]}`}>
            Sniper Precision
            </span>
            {/* Live Indicator */}
            <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></div>
        </div>
      </div>
    </div>
  );
}
