import { ReactNode } from "react";
import ObiWorkLogo from "../components/ObiWorkLogo";
import { User, LogOut, LayoutDashboard, Calendar, Settings, Home } from "lucide-react";
import Link from "next/link";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-zinc-950 text-white font-mono flex">
      
      {/* Sidebar */}
      <aside className="w-64 border-r border-zinc-900 bg-zinc-950 flex flex-col fixed h-full">
        <div className="p-6 border-b border-zinc-900 flex items-center justify-between">
          <ObiWorkLogo size="sm" />
          <Link href="/" className="p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded transition-colors" title="Back to Home">
            <Home className="w-4 h-4" />
          </Link>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          <div className="px-4 py-2 text-xs text-zinc-500 uppercase tracking-wider">Workroom</div>
          <a href="/dashboard" className="flex items-center gap-3 px-4 py-3 bg-zinc-900 text-white rounded hover:bg-zinc-800 transition-colors">
            <LayoutDashboard className="w-4 h-4 text-emerald-500" />
            <span>Overview</span>
          </a>
          <a href="/dashboard/mentorship" className="flex items-center gap-3 px-4 py-3 text-zinc-400 hover:text-white hover:bg-zinc-900 rounded transition-colors">
            <Calendar className="w-4 h-4" />
            <span>Mentorship</span>
          </a>
          <a href="/dashboard/settings" className="flex items-center gap-3 px-4 py-3 text-zinc-400 hover:text-white hover:bg-zinc-900 rounded transition-colors">
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </a>
        </nav>

        <div className="p-4 border-t border-zinc-900">
          <div className="flex items-center gap-3 px-4 py-3 text-zinc-400">
            <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
              <User className="w-4 h-4" />
            </div>
            <div className="flex-1 overflow-hidden">
              <div className="text-xs text-white truncate">0x123...456</div>
              <div className="text-[10px] text-emerald-500">CLONE #04</div>
            </div>
            <button className="hover:text-white">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 p-8 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
