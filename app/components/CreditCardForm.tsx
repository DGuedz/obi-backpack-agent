
"use client";

import { useState } from 'react';
import { CreditCard, Lock, Loader2, Calendar, User, AlertCircle } from 'lucide-react';

interface CreditCardFormProps {
  amount: number;
  onSuccess: (paymentId: string) => void;
  onCancel: () => void;
}

export default function CreditCardForm({ amount, onSuccess, onCancel }: CreditCardFormProps) {
  const [formData, setFormData] = useState({
    number: '',
    holder: '',
    expiry: '',
    cvc: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/payments/cielo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          amount: amount,
          cardData: formData,
          customerName: formData.holder,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Payment failed');
      }

      // Cielo Success Check (Status 1 = Authorized, 2 = Paid)
      if (data.Payment?.Status === 1 || data.Payment?.Status === 2) {
         onSuccess(data.Payment.PaymentId);
      } else {
         throw new Error(data.Payment?.ReturnMessage || 'Payment not authorized');
      }

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Transaction failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 w-full max-w-md mx-auto relative overflow-hidden">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-bold text-white font-mono flex items-center gap-2">
          <CreditCard className="w-5 h-5 text-emerald-500" />
          SECURE CHECKOUT
        </h3>
        <div className="text-right">
          <div className="text-xs text-zinc-500 font-mono">TOTAL</div>
          <div className="text-lg font-bold text-emerald-400">${amount.toFixed(2)}</div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs text-zinc-500 font-mono mb-1 uppercase">Card Number</label>
          <div className="relative">
            <input
              type="text"
              name="number"
              value={formData.number}
              onChange={handleChange}
              placeholder="0000 0000 0000 0000"
              className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-white font-mono focus:border-emerald-500 focus:outline-none pl-10"
              required
            />
            <CreditCard className="w-4 h-4 text-zinc-600 absolute left-3 top-3" />
          </div>
        </div>

        <div>
          <label className="block text-xs text-zinc-500 font-mono mb-1 uppercase">Card Holder</label>
          <div className="relative">
            <input
              type="text"
              name="holder"
              value={formData.holder}
              onChange={handleChange}
              placeholder="NAME ON CARD"
              className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-white font-mono focus:border-emerald-500 focus:outline-none pl-10"
              required
            />
            <User className="w-4 h-4 text-zinc-600 absolute left-3 top-3" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-zinc-500 font-mono mb-1 uppercase">Expiry</label>
            <div className="relative">
              <input
                type="text"
                name="expiry"
                value={formData.expiry}
                onChange={handleChange}
                placeholder="MM/YYYY"
                className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-white font-mono focus:border-emerald-500 focus:outline-none pl-10"
                required
              />
              <Calendar className="w-4 h-4 text-zinc-600 absolute left-3 top-3" />
            </div>
          </div>
          <div>
            <label className="block text-xs text-zinc-500 font-mono mb-1 uppercase">CVC</label>
            <div className="relative">
              <input
                type="text"
                name="cvc"
                value={formData.cvc}
                onChange={handleChange}
                placeholder="123"
                className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-white font-mono focus:border-emerald-500 focus:outline-none pl-10"
                required
              />
              <Lock className="w-4 h-4 text-zinc-600 absolute left-3 top-3" />
            </div>
          </div>
        </div>

        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/20 rounded flex items-center text-xs text-red-400 gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        <div className="pt-4 flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded font-mono font-bold text-sm transition-colors"
          >
            CANCEL
          </button>
          <button
            type="submit"
            disabled={loading}
            className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-mono font-bold text-sm transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
            {loading ? 'PROCESSING...' : 'PAY NOW'}
          </button>
        </div>

        <div className="mt-4 text-center">
            <p className="text-[10px] text-zinc-600 flex items-center justify-center gap-1">
                <Lock className="w-3 h-3" />
                Payments processed securely via Cielo
            </p>
        </div>
      </form>
    </div>
  );
}
