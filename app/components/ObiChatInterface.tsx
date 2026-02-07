"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Shield, Terminal, Loader2, Search } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  id: string;
  role: "assistant" | "user";
  content: string;
  type?: "text" | "analysis" | "alert";
  data?: any;
}

export default function ObiChatInterface() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "OBI-OS Online. Ready to track wallets and analyze market flow. Try '/track <wallet>' to add allies, or '/scan <wallet>' to audit risks.",
      type: "text"
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [formStep, setFormStep] = useState<number | null>(null);
  const [formData, setFormData] = useState<any>({});
  const scrollRef = useRef<HTMLDivElement>(null);

  const WHITELIST_QUESTIONS = [
    { id: "q1", text: "Q1/10: Nome Completo (Full Name)" },
    { id: "q2", text: "Q2/10: CPF / National ID (KYC Compliance)" },
    { id: "q3", text: "Q3/10: Wallet Address (Solana/Backpack)" },
    { id: "q4", text: "Q4/10: Email Principal" },
    { id: "q5", text: "Q5/10: Discord/Telegram Handle" },
    { id: "q6", text: "Q6/10: Tempo de Mercado (Anos)" },
    { id: "q7", text: "Q7/10: Capital Inicial Disponível (USDC)" },
    { id: "q8", text: "Q8/10: Perfil Técnico (Dev, Trader, ou Ambos?)" },
    { id: "q9", text: "Q9/10: Código de Referência (Referral)" },
    { id: "q10", text: "Q10/10: Você aceita o Manifesto Black Mindz? (Sim/Não)" }
  ];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const processFormStep = (answer: string) => {
    if (formStep === null) return;

    const currentQ = WHITELIST_QUESTIONS[formStep];
    const newFormData = { ...formData, [currentQ.id]: answer };
    setFormData(newFormData);

    // Add user answer to chat
    const userMsg: Message = {
        id: Date.now().toString(),
        role: "user",
        content: answer
    };
    setMessages(prev => [...prev, userMsg]);
    setInput("");

    // Next Step
    if (formStep < WHITELIST_QUESTIONS.length - 1) {
        const nextStep = formStep + 1;
        setFormStep(nextStep);
        setTimeout(() => {
            setMessages(prev => [...prev, {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: WHITELIST_QUESTIONS[nextStep].text,
                type: "text"
            }]);
        }, 500);
    } else {
        // Form Complete
        setFormStep(null);
        setTimeout(() => {
            setMessages(prev => [...prev, {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: " Application Received. Analyzing compliance data...",
                type: "text"
            }]);
            
            // Here you would send 'newFormData' to the backend
            console.log("Form Data:", newFormData);
        }, 500);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    // Handle Form Input Mode
    if (formStep !== null) {
        processFormStep(input);
        return;
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input
    };

    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    // Check for 'obi list' or '/apply' command locally first
    if (input.toLowerCase() === "obi list" || input.toLowerCase() === "/apply") {
        setIsLoading(false);
        setFormStep(0);
        setTimeout(() => {
            setMessages(prev => [...prev, {
                id: (Date.now() + 1).toString(),
                role: "assistant",
                content: " **OBI WHITELIST PROTOCOL INITIATED**\nStarting 10-step verification process.\n\n" + WHITELIST_QUESTIONS[0].text,
                type: "text"
            }]);
        }, 500);
        return;
    }

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input })
      });
      
      const data = await res.json();
      
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.message,
        type: data.type || "text",
        data: data.data
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Error connecting to OBI Core. Check local connection.",
        type: "alert"
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl flex flex-col h-[500px] overflow-hidden relative shadow-2xl">
      {/* Header */}
      <div className="p-4 border-b border-zinc-800 bg-black/20 flex justify-between items-center backdrop-blur-sm">
        <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
                <Bot className="w-4 h-4 text-emerald-500" />
            </div>
            <div>
                <h3 className="text-sm font-bold text-white font-mono">OBI INTELLIGENCE</h3>
                <div className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-[10px] text-zinc-500 font-mono uppercase">System Active</span>
                </div>
            </div>
        </div>
        <div className="flex gap-2">
            <div className="px-2 py-1 rounded bg-zinc-800/50 border border-zinc-700/50 text-[10px] font-mono text-zinc-400">
                V4.1.0 (Tracker)
            </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent bg-black/40" ref={scrollRef}>
        <AnimatePresence initial={false}>
            {messages.map((msg) => (
            <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
                <div className={`max-w-[85%] rounded-lg p-3 text-sm font-mono ${
                    msg.role === "user" 
                        ? "bg-zinc-800 text-white border border-zinc-700" 
                        : "bg-emerald-950/20 text-emerald-100 border border-emerald-900/30"
                }`}>
                    {msg.type === "analysis" && msg.data ? (
                        <div className="space-y-2">
                            <div className="flex items-center gap-2 text-emerald-400 border-b border-emerald-900/30 pb-2 mb-2">
                                <Search className="w-4 h-4" />
                                <span className="font-bold">WALLET ANALYSIS REPORT</span>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                                <div className="text-zinc-400">Reputation:</div>
                                <div className={`${msg.data.risk_score > 50 ? "text-red-400" : "text-emerald-400"} font-bold`}>
                                    {msg.data.risk_score > 50 ? "HIGH RISK" : "SAFE"}
                                </div>
                                <div className="text-zinc-400">Created Tokens:</div>
                                <div>{msg.data.created_tokens_count || "0"}</div>
                            </div>
                            {msg.data.risks && msg.data.risks.length > 0 && (
                                <div className="mt-2 p-2 bg-red-950/30 rounded border border-red-900/30 text-xs text-red-300">
                                    WARNING: {msg.data.risks[0].name || "Detected Anomalies"}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                    )}
                </div>
            </motion.div>
            ))}
        </AnimatePresence>
        {isLoading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                <div className="bg-emerald-950/20 p-3 rounded-lg border border-emerald-900/30 flex items-center gap-2">
                    <Loader2 className="w-4 h-4 text-emerald-500 animate-spin" />
                    <span className="text-xs text-emerald-500 font-mono">Running analysis...</span>
                </div>
            </motion.div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-zinc-900 border-t border-zinc-800">
        <div className="relative">
            <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSend()}
                placeholder="Enter command (e.g., /scan <address>) or ask question..."
                className="w-full bg-black/50 border border-zinc-700 rounded-lg pl-4 pr-12 py-3 text-sm text-white focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 font-mono transition-all"
                disabled={isLoading}
            />
            <button 
                onClick={handleSend}
                disabled={isLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-zinc-800 hover:bg-emerald-600 text-zinc-400 hover:text-white rounded-md transition-all disabled:opacity-50"
            >
                <Send className="w-4 h-4" />
            </button>
        </div>
        <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
            {["/track", "/watchlist", "/activity", "/scan", "/market"].map(cmd => (
                <button 
                    key={cmd}
                    onClick={() => setInput(cmd + " ")}
                    className="px-2 py-1 bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-700/50 rounded text-[10px] text-zinc-400 font-mono transition-colors whitespace-nowrap"
                >
                    {cmd}
                </button>
            ))}
        </div>
      </div>
    </div>
  );
}
