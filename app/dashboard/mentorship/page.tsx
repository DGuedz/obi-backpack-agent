"use client";

import { useState, useEffect } from "react";
import { Calendar, Video, Clock, ChevronRight, Lock, RefreshCw } from "lucide-react";

interface CalendarEvent {
  id?: string | number;
  summary?: string;
  description?: string;
  start?: {
    dateTime?: string | null;
  };
}

export default function MentorshipHub() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const [missingEnv, setMissingEnv] = useState<string[]>([]);

  useEffect(() => {
      const fetchEvents = async () => {
          try {
              const res = await fetch('/api/mentorship/events');
              const data = await res.json();
              setEvents(data.events || []);
              setConnected(data.connected);
              setMissingEnv(data.missingEnv || []);
          } catch (e) {
              console.error(e);
          } finally {
              setLoading(false);
          }
      };
      fetchEvents();
  }, []);

  const recordings = [
    { id: 1, title: "Liquidity Strategy Breakdown", date: "Jan 15, 2026", duration: "45m 12s" },
    { id: 2, title: "Market Depth Analysis 101", date: "Jan 08, 2026", duration: "1h 02m" },
    { id: 3, title: "Infrastructure Setup (VPS)", date: "Jan 01, 2026", duration: "30m 00s" },
  ];

  const formatDate = (isoString: string) => {
      const date = new Date(isoString);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="space-y-8">
      
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold font-mono text-white">MENTORSHIP HUB</h1>
          <p className="text-zinc-400 text-sm font-mono">Connect with the Black Mindz network.</p>
        </div>
        <button className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-mono text-sm flex items-center gap-2 transition-colors">
          <Calendar className="w-4 h-4" />
          Book Solo Call
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upcoming Schedule */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-xl p-6">
          <h3 className="text-sm text-zinc-400 font-mono mb-6 uppercase tracking-wider flex items-center justify-between">
            <span className="flex items-center gap-2"><Clock className="w-4 h-4" /> Upcoming Sessions</span>
            {loading && <RefreshCw className="w-3 h-3 animate-spin" />}
          </h3>
          
          <div className="space-y-4 mt-4">
            {events.length > 0 ? events.map((event, index) => (
              <div key={event.id ?? `${event.summary ?? "event"}-${index}`} className="flex items-center justify-between p-4 bg-zinc-950/50 border border-zinc-800 rounded-lg hover:border-emerald-500/30 transition-colors group">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-400 group-hover:text-emerald-500 transition-colors">
                    <Video className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="text-white font-bold font-mono">{event.summary}</div>
                    <div className="text-xs text-zinc-500 font-mono flex items-center gap-2">
                      <span>{event.start?.dateTime ? formatDate(event.start.dateTime) : 'TBA'}</span>
                      <span className="w-1 h-1 rounded-full bg-zinc-700"></span>
                      <span className="text-emerald-500">{event.description || 'Community'}</span>
                    </div>
                  </div>
                </div>
                <button className="px-3 py-1 bg-zinc-800 text-zinc-300 text-xs font-mono rounded border border-zinc-700 hover:bg-emerald-900/20 hover:text-emerald-400 hover:border-emerald-500/50 transition-all">
                  JOIN ROOM
                </button>
              </div>
            )) : (
                <div className="text-center py-8 text-zinc-500 font-mono text-sm">No upcoming sessions scheduled.</div>
            )}
          </div>

          <div className={`mt-8 p-4 border rounded flex gap-3 items-start ${connected ? "bg-blue-900/10 border-blue-900/30" : "bg-yellow-900/10 border-yellow-900/30"}`}>
             <div className={`p-1 rounded ${connected ? "bg-blue-500/20" : "bg-yellow-500/20"}`}>
                <Calendar className={`w-4 h-4 ${connected ? "text-blue-400" : "text-yellow-400"}`} />
             </div>
             <div>
                <h4 className={`${connected ? "text-blue-400" : "text-yellow-400"} font-bold font-mono text-sm mb-1`}>
                    {connected ? "Google Calendar Synced" : "Calendar Sync Pending"}
                </h4>
                <p className={`text-xs font-mono ${connected ? "text-blue-200/60" : "text-yellow-200/60"}`}>
                   {connected 
                    ? "Your sessions are automatically synced to your Google Calendar. Check your invite for the Meet link."
                    : missingEnv.length > 0
                      ? `Missing env: ${missingEnv.join(", ")}`
                      : "Configure GOOGLE_CLIENT_EMAIL in .env to enable real-time sync."}
                </p>
             </div>
          </div>
        </div>

        {/* Recordings Archive */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 flex flex-col">
          <h3 className="text-sm text-zinc-400 font-mono mb-6 uppercase tracking-wider flex items-center gap-2">
            <Lock className="w-4 h-4" /> Restricted Archive
          </h3>
          
          <div className="flex-1 space-y-1">
            {recordings.map((rec) => (
              <button key={rec.id} className="w-full text-left p-3 rounded hover:bg-zinc-800 transition-colors group">
                <div className="flex justify-between items-start mb-1">
                  <span className="text-sm font-mono text-zinc-300 group-hover:text-white transition-colors">{rec.title}</span>
                  <ChevronRight className="w-4 h-4 text-zinc-600 group-hover:text-emerald-500 transition-colors" />
                </div>
                <div className="flex justify-between text-[10px] font-mono text-zinc-500">
                  <span>{rec.date}</span>
                  <span>{rec.duration}</span>
                </div>
              </button>
            ))}
          </div>
          
          <div className="mt-6 pt-6 border-t border-zinc-800 text-center">
            <button className="text-xs font-mono text-emerald-500 hover:text-emerald-400 hover:underline">
              View All 12 Recordings -&gt;
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
