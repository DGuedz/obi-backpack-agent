import { ActionGetResponse, ActionPostRequest, ActionPostResponse, ACTIONS_CORS_HEADERS, createPostResponse } from "@solana/actions";
import { PublicKey, SystemProgram, Transaction, Connection, clusterApiUrl } from "@solana/web3.js";

// Configuração Básica
const OBI_TREASURY_WALLET = new PublicKey("FiMC2XB1vXhKA..."); // Exemplo (Sua Wallet)
const MINT_PRICE_SOL = 0.5; // Preço do Passe em SOL (Placeholder)

// GET: Retorna os metadados do Action (Título, Ícone, Descrição)
// Isso é o que aparece no Twitter/X quando o link é compartilhado.
export async function GET(request: Request) {
  const payload: ActionGetResponse = {
    icon: "https://obi.work/obiwork_logo.png", // URL da logo
    title: "Mint OBI Work Pass",
    description: "Desbloqueie o acesso aos Agentes de IA da Backpack. Infraestrutura de Liquidez On-Chain.",
    label: `Mint Pass (${MINT_PRICE_SOL} SOL)`,
    links: {
        actions: [
            {
                label: `Comprar Passe (${MINT_PRICE_SOL} SOL)`,
                href: "/api/actions/mint-pass",
            }
        ]
    }
  };

  return new Response(JSON.stringify(payload), {
    headers: ACTIONS_CORS_HEADERS,
  });
}

// OPTIONS: Necessário para CORS (Cross-Origin Resource Sharing)
export const OPTIONS = GET;

// POST: Constrói a transação quando o usuário clica no botão
export async function POST(request: Request) {
  try {
    const body: ActionPostRequest = await request.json();

    // Validar a conta do usuário (quem vai pagar)
    let account: PublicKey;
    try {
      account = new PublicKey(body.account);
    } catch (err) {
      return new Response('Invalid "account" provided', {
        status: 400,
        headers: ACTIONS_CORS_HEADERS,
      });
    }

    // Conectar à Solana (Mainnet ou Devnet)
    const connection = new Connection(clusterApiUrl("mainnet-beta"));

    // Criar a transação (Neste MVP, é uma transferência simples de SOL)
    // No futuro, aqui chamaremos o Programa Anchor `mint_license`
    const transaction = new Transaction();
    
    // Instrução 1: Transferir SOL para o Tesouro
    transaction.add(
      SystemProgram.transfer({
        fromPubkey: account,
        toPubkey: OBI_TREASURY_WALLET,
        lamports: MINT_PRICE_SOL * 1_000_000_000, // Converter SOL para Lamports
      })
    );
    
    // Nota: A lógica real de Mint (SPL Token) viria aqui como instrução adicional
    
    transaction.feePayer = account;
    
    // Obter o blockhash recente para validar a transação
    const { blockhash } = await connection.getLatestBlockhash();
    transaction.recentBlockhash = blockhash;

    // Retornar a transação serializada para o usuário assinar
    const payload: ActionPostResponse = await createPostResponse({
      fields: {
        transaction,
        message: "Bem-vindo ao OBI Work! Seu passe está sendo gerado.", // Mensagem de sucesso
      },
    });

    return new Response(JSON.stringify(payload), {
      headers: ACTIONS_CORS_HEADERS,
    });

  } catch (err) {
    console.error(err);
    return new Response(JSON.stringify({ error: 'Erro ao processar transação' }), {
      status: 500,
      headers: ACTIONS_CORS_HEADERS,
    });
  }
}
