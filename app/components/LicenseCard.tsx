import { useState } from 'react';
import { useBuyClone } from '../hooks/useBuyClone';
import { Loader2, CheckCircle, AlertCircle, CreditCard } from 'lucide-react';
import CreditCardForm from './CreditCardForm';

interface LicenseCardProps {
  tierId: number;
  title: string;
  price: number;
  features: string[];
}

export default function LicenseCard({ tierId, title, price, features }: LicenseCardProps) {
  const { handleBuy, step, errorMsg, txHash } = useBuyClone(tierId, price);
  const [showCard, setShowCard] = useState(false);
  const [cardPaid, setCardPaid] = useState(false);

  return (
    <>
      {showCard && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <CreditCardForm 
            amount={price} 
            onSuccess={() => { setCardPaid(true); setShowCard(false); }} 
            onCancel={() => setShowCard(false)} 
          />
        </div>
      )}

      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 hover:border-emerald-500/50 transition-all group relative overflow-hidden">
        {/* Glow Effect */}
        <div className="absolute inset-0 bg-linear-to-br from-emerald-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
        
        <div className="relative z-10">
          <h3 className="text-2xl font-mono font-bold text-white mb-2">{title}</h3>
          <div className="text-3xl font-bold text-emerald-400 mb-6">${price} <span className="text-sm text-zinc-500 font-normal">USDC</span></div>
          
          <ul className="space-y-3 mb-8">
            {features.map((feat, i) => (
              <li key={i} className="flex items-center text-sm text-zinc-400">
                <CheckCircle className="w-4 h-4 text-emerald-500 mr-2 shrink-0" />
                {feat}
              </li>
            ))}
          </ul>

          {errorMsg && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center text-xs text-red-400">
              <AlertCircle className="w-4 h-4 mr-2" />
              {errorMsg}
            </div>
          )}

          {step === 'success' || cardPaid ? (
            <div className="w-full py-3 bg-emerald-500/20 border border-emerald-500/50 text-emerald-400 rounded-lg font-mono font-bold text-center flex items-center justify-center gap-2">
              <CheckCircle className="w-5 h-5" />
              LICENSE ACTIVE
            </div>
          ) : (
            <div className="space-y-2">
              <button
                onClick={handleBuy}
                disabled={step === 'approving' || step === 'buying'}
                className="w-full py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-mono font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {step === 'approving' && <Loader2 className="w-4 h-4 animate-spin" />}
                {step === 'buying' && <Loader2 className="w-4 h-4 animate-spin" />}
                
                {step === 'approving' ? 'VERIFYING ASSETS...' : 
                 step === 'buying' ? 'ISSUING CREDENTIALS...' : 
                 'PAY WITH CRYPTO (USDC)'}
              </button>

              <button
                onClick={() => setShowCard(true)}
                className="w-full py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border border-zinc-700 rounded-lg font-mono font-bold transition-all flex items-center justify-center gap-2"
              >
                <CreditCard className="w-4 h-4" />
                PAY WITH CARD
              </button>
            </div>
          )}
          
          {txHash && (
            <a 
              href={`https://scan.backpack.exchange/tx/${txHash}`} // Exemplo de explorer
              target="_blank" 
              rel="noreferrer"
              className="block mt-4 text-center text-xs text-zinc-600 hover:text-emerald-500 underline"
            >
              Verify On-Chain
            </a>
          )}
        </div>
      </div>
    </>
  );
}
