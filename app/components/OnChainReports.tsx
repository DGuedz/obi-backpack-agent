"use client";

import { useEffect, useState } from "react";
import { 
  FileText, RefreshCw, Terminal, ShieldCheck, 
  Rocket, TrendingUp, Trophy, PieChart, Calendar, 
  Brain, Lightbulb, DollarSign, Coins, 
  Zap, BarChart2, Award, ArrowRight, History, ChevronDown
} from "lucide-react";

interface ReportHistoryItem {
  date: string;
  filename: string;
}

export default function OnChainReports() {
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [history, setHistory] = useState<ReportHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const fetchReport = async (date?: string) => {
    setLoading(true);
    try {
      let url = '/api/reports/latest';
      if (date) {
        url = `/api/reports/history?date=${date}`;
      }
      
      const res = await fetch(url);
      const data = await res.json();
      
      if (data.content) {
        setContent(data.content);
        setLastUpdated(new Date());
        setSelectedDate(date || null);
      }
    } catch (e) {
      console.error("Failed to fetch report", e);
      setContent("Error fetching report data.");
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
        const res = await fetch('/api/reports/history');
        const data = await res.json();
        if (data.ok && Array.isArray(data.history)) {
            setHistory(data.history);
        }
    } catch (e) {
        console.error("Failed to fetch history", e);
    }
  };

  useEffect(() => {
    fetchReport();
    fetchHistory();
  }, []);

  // Helper to choose icon based on header text
  const getHeaderIcon = (text: string) => {
    const lower = text.toLowerCase();
    if (lower.includes('relatório')) return <Rocket className="w-5 h-5 text-emerald-400 inline mr-2" />;
    if (lower.includes('resumo')) return <TrendingUp className="w-5 h-5 text-emerald-400 inline mr-2" />;
    if (lower.includes('performance')) return <Trophy className="w-5 h-5 text-yellow-400 inline mr-2" />;
    if (lower.includes('breakdown')) return <PieChart className="w-5 h-5 text-purple-400 inline mr-2" />;
    if (lower.includes('histórico')) return <Calendar className="w-5 h-5 text-blue-400 inline mr-2" />;
    if (lower.includes('análise')) return <Brain className="w-5 h-5 text-pink-400 inline mr-2" />;
    return <ArrowRight className="w-4 h-4 text-emerald-500/50 inline mr-2" />;
  };

  // Helper to choose icon for bullet points
  const getBulletIcon = (text: string) => {
    const lower = text.toLowerCase();
    if (lower.includes('volume')) return <DollarSign className="w-3 h-3 text-emerald-500" />;
    if (lower.includes('taxas') || lower.includes('fee')) return <Coins className="w-3 h-3 text-red-400" />;
    if (lower.includes('execuções') || lower.includes('fills')) return <Zap className="w-3 h-3 text-yellow-400" />;
    if (lower.includes('rank')) return <BarChart2 className="w-3 h-3 text-blue-400" />;
    if (lower.includes('tier')) return <Award className="w-3 h-3 text-purple-400" />;
    return <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />;
  };

  // Simple Markdown Parser for specific elements to make it look nicer
  const renderContent = (text: string) => {
    return text.split('\n').map((line, i) => {
      // Headers
      if (line.startsWith('# ')) {
        const title = line.replace('# ', '').replace(/|||||/g, '').trim();
        return (
          <div key={i} className="flex items-center mt-6 mb-3 border-b border-emerald-500/20 pb-2">
            {getHeaderIcon(title)}
            <h3 className="text-xl font-bold text-white tracking-tight">{title}</h3>
          </div>
        );
      }
      if (line.startsWith('## ')) {
        const title = line.replace('## ', '').replace(/|||||/g, '').trim();
        return (
          <div key={i} className="flex items-center mt-6 mb-2">
             {getHeaderIcon(title)}
             <h4 className="text-lg font-bold text-emerald-300/90 tracking-wide">{title}</h4>
          </div>
        );
      }
      
      // Horizontal Rule
      if (line.startsWith('---')) {
        return <hr key={i} className="border-zinc-800 my-4" />;
      }

      // Bullet points
      if (line.trim().startsWith('- ')) {
        const content = line.replace('- ', '');
        return (
          <div key={i} className="flex items-start gap-3 ml-2 mb-1 text-zinc-300 group hover:bg-zinc-800/30 p-1 rounded transition-colors">
            <div className="mt-1.5 shrink-0 opacity-80 group-hover:opacity-100 transition-opacity">
              {getBulletIcon(content)}
            </div>
            <span className="font-mono text-sm leading-relaxed" dangerouslySetInnerHTML={{ 
              __html: content.replace(/\*\*(.*?)\*\*/g, '<span class="text-emerald-400 font-bold">$1</span>') 
            }} />
          </div>
        );
      }

      // Recommendation highlight
      if (line.includes('**Recomendação:**')) {
        return (
           <div key={i} className="mt-4 p-4 bg-emerald-950/30 border border-emerald-500/20 rounded-lg flex gap-3">
              <Lightbulb className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-emerald-400 font-bold text-sm mb-1">RECOMENDAÇÃO TÁTICA</div>
                <div className="text-zinc-300 text-sm">{line.replace('**Recomendação:**', '').trim()}</div>
              </div>
           </div>
        );
      }

      // Table rows (simple detection)
      if (line.trim().startsWith('|')) {
        const cols = line.split('|').filter(c => c.trim() !== '');
        if (line.includes('---')) return null; // Skip separator lines for now
        return (
          <div key={i} className="grid grid-cols-4 gap-2 py-1 border-b border-zinc-800/50 text-xs md:text-sm">
             {cols.map((col, idx) => (
               <div key={idx} className={`${idx === 0 ? 'text-emerald-400 font-bold' : 'text-zinc-300'}`}>{col.trim()}</div>
             ))}
          </div>
        );
      }

      // Default paragraph (preserve whitespace for ASCII tables/logs)
      if (line.trim() === '') return <br key={i} />;
      
      return <div key={i} className="text-zinc-400 min-h-[1.5em] whitespace-pre-wrap">{line}</div>;
    });
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 p-4 opacity-10">
        <FileText className="w-24 h-24 text-emerald-500" />
      </div>

      <div className="flex justify-between items-center mb-6 relative z-10">
        <div>
          <h3 className="text-lg font-bold font-mono text-white flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-500" />
            PARTNER REPORTS
          </h3>
          <p className="text-zinc-400 text-xs font-mono mt-1">Immutable proof of liquidity provision & yield metrics.</p>
        </div>
        <div className="flex gap-2">
            <div className="relative">
                <button 
                    onClick={() => setShowHistory(!showHistory)}
                    className="flex items-center gap-2 px-3 py-2 bg-zinc-800/50 hover:bg-zinc-800 rounded-lg text-xs font-mono text-zinc-300 transition-colors border border-zinc-700/50"
                >
                    <History className="w-3 h-3" />
                    {selectedDate ? selectedDate : "LATEST"}
                    <ChevronDown className="w-3 h-3 opacity-50" />
                </button>
                {showHistory && (
                    <div className="absolute right-0 top-full mt-2 w-48 bg-zinc-900 border border-zinc-700 rounded-lg shadow-xl z-50 py-1 max-h-60 overflow-y-auto">
                        <button 
                            onClick={() => { fetchReport(); setShowHistory(false); }}
                            className="w-full text-left px-4 py-2 text-xs font-mono text-emerald-400 hover:bg-zinc-800"
                        >
                            LATEST REPORT
                        </button>
                        {history.map((h) => (
                            <button
                                key={h.date}
                                onClick={() => { fetchReport(h.date); setShowHistory(false); }}
                                className="w-full text-left px-4 py-2 text-xs font-mono text-zinc-400 hover:text-white hover:bg-zinc-800"
                            >
                                {h.date}
                            </button>
                        ))}
                    </div>
                )}
            </div>
            <button 
            onClick={() => fetchReport(selectedDate || undefined)} 
            disabled={loading}
            className="p-2 hover:bg-zinc-800 rounded-full transition-colors text-zinc-500 hover:text-white"
            >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
        </div>
      </div>

      <div className="bg-black/50 border border-zinc-800 rounded-lg p-4 font-mono text-sm overflow-auto max-h-125 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
        {loading && !content ? (
          <div className="flex flex-col items-center justify-center py-12 text-zinc-500">
            <RefreshCw className="w-8 h-8 animate-spin mb-2 opacity-50" />
            <span>Retrieving On-Chain Data...</span>
          </div>
        ) : (
          <div className="space-y-1">
             {renderContent(content)}
          </div>
        )}
      </div>

      {lastUpdated && (
        <div className="mt-4 flex items-center gap-2 text-[10px] text-zinc-500 font-mono">
          <Terminal className="w-3 h-3" />
          <span>LAST SYNC: {lastUpdated.toLocaleTimeString()}</span>
        </div>
      )}
    </div>
  );
}
