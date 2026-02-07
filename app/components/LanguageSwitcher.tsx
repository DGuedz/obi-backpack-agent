"use client";

import { useLanguage } from '../context/LanguageContext';
import { Globe } from 'lucide-react';
import { motion } from 'framer-motion';

export default function LanguageSwitcher() {
  const { language, setLanguage } = useLanguage();

  return (
    <motion.button 
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={() => setLanguage(language === 'en' ? 'pt' : 'en')}
      className="fixed top-6 right-6 z-50 flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/80 border border-zinc-800 backdrop-blur-md text-xs font-bold text-zinc-400 hover:text-white hover:border-emerald-500 hover:shadow-[0_0_15px_rgba(16,185,129,0.3)] transition-all cursor-pointer group"
    >
      <Globe className="w-3.5 h-3.5 text-zinc-500 group-hover:text-emerald-400 transition-colors" />
      <span className="min-w-[20px] text-center">{language.toUpperCase()}</span>
    </motion.button>
  );
}
