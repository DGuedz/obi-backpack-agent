import { useState, useEffect } from 'react';
import { useAccount, useReadContract, useWriteContract, useWaitForTransactionReceipt } from 'wagmi';
import { erc20Abi, parseUnits } from 'viem';

// ABI Parcial do Contrato OBI Work
const OBI_LICENSE_ABI = [
  {
    inputs: [{ internalType: "uint256", name: "tierId", type: "uint256" }],
    name: "buyLicense",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function"
  },
  {
    inputs: [{ internalType: "address", name: "user", type: "address" }],
    name: "userTier",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function"
  }
] as const;

// Endereços (Devem vir de .env)
const USDC_ADDRESS = process.env.NEXT_PUBLIC_USDC_ADDRESS as `0x${string}`;
const LICENSE_CONTRACT_ADDRESS = process.env.NEXT_PUBLIC_LICENSE_CONTRACT_ADDRESS as `0x${string}`;

export function useBuyClone(tierId: number, price: number) {
  const { address, isConnected } = useAccount();
  const [errorMsg, setErrorMsg] = useState('');

  const zeroAddress = '0x0000000000000000000000000000000000000000' as `0x${string}`;

  // 1. Verificar Saldo USDC
  const { data: usdcBalance } = useReadContract({
    address: USDC_ADDRESS,
    abi: erc20Abi,
    functionName: 'balanceOf',
    args: [address ?? zeroAddress],
    query: { enabled: !!address },
  });

  // 2. Verificar Aprovação (Allowance)
  const { data: allowance, refetch: refetchAllowance } = useReadContract({
    address: USDC_ADDRESS,
    abi: erc20Abi,
    functionName: 'allowance',
    args: [address ?? zeroAddress, LICENSE_CONTRACT_ADDRESS],
    query: { enabled: !!address },
  });

  // Preparar Aprovação
  const { writeContract: approveUSDC, data: approveHash } = useWriteContract();
  const { isLoading: isApproving, isSuccess: approveSuccess } = useWaitForTransactionReceipt({
    hash: approveHash,
  });

  // Preparar Compra (Buy License)
  const { writeContract: buyLicense, data: buyHash } = useWriteContract();
  const { isLoading: isBuying, isSuccess: isBought } = useWaitForTransactionReceipt({
    hash: buyHash,
  });

  useEffect(() => {
    if (approveSuccess) {
      refetchAllowance();
      buyLicense({
        address: LICENSE_CONTRACT_ADDRESS,
        abi: OBI_LICENSE_ABI,
        functionName: 'buyLicense',
        args: [BigInt(tierId)],
      });
    }
  }, [approveSuccess, refetchAllowance, buyLicense, tierId]);

  const step: 'idle' | 'approving' | 'buying' | 'success' | 'error' =
    errorMsg ? 'error' : isBought ? 'success' : isBuying ? 'buying' : isApproving ? 'approving' : 'idle';

  const handleBuy = async () => {
    setErrorMsg('');
    if (!isConnected) {
      setErrorMsg('Conecte sua carteira primeiro.');
      return;
    }
    
    if (!usdcBalance || usdcBalance < parseUnits(price.toString(), 6)) {
      setErrorMsg('Saldo de USDC insuficiente.');
      return;
    }

    try {
      // Se não tem allowance suficiente, aprova primeiro
      if (!allowance || allowance < parseUnits(price.toString(), 6)) {
        approveUSDC({
          address: USDC_ADDRESS,
          abi: erc20Abi,
          functionName: 'approve',
          args: [LICENSE_CONTRACT_ADDRESS, parseUnits(price.toString(), 6)],
        });
      } else {
        // Se já tem, compra direto
        buyLicense({
          address: LICENSE_CONTRACT_ADDRESS,
          abi: OBI_LICENSE_ABI,
          functionName: 'buyLicense',
          args: [BigInt(tierId)],
        });
      }
    } catch (err: unknown) {
      console.error(err);
      const message = err instanceof Error ? err.message : 'Erro na transação.';
      setErrorMsg(message);
    }
  };

  return {
    handleBuy,
    step,
    errorMsg,
    isApproving,
    isBuying,
    isBought,
    txHash: buyHash
  };
}
