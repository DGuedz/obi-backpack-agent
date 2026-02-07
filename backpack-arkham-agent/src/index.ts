import dotenv from 'dotenv';
import axios from 'axios';

dotenv.config();

const ARKHAM_API_KEY = process.env.ARKHAM_API_KEY;
const BACKPACK_API_KEY = process.env.BACKPACK_API_KEY;
const RPC_URL = process.env.RPC_URL;

if (!ARKHAM_API_KEY || !BACKPACK_API_KEY) {
  console.warn("️  Aviso: Chaves de API não configuradas no .env");
}

async function main() {
    console.log(" Backpack Arkham Agent Iniciado");
    console.log(" Ambiente Seguro: Variáveis carregadas.");
    
    // Placeholder para lógica futura
}

main().catch(console.error);
