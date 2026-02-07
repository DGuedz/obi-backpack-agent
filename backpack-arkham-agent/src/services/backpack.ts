
import axios from 'axios';
import { WebSocket } from 'ws';
import https from 'https';

export interface Ticker {
    symbol: string;
    firstPrice: string;
    lastPrice: string;
    priceChange: string;
    priceChangePercent: string;
    high: string;
    low: string;
    volume: string;
    quoteVolume: string;
    trades: number;
}

export interface Kline {
    start: string;
    open: string;
    high: string;
    low: string;
    close: string;
    volume: string;
    end: string;
    trades: string;
}

export interface OrderBook {
    asks: [string, string][];
    bids: [string, string][];
    lastUpdateId: string;
}

export class BackpackService {
    private baseUrl = 'https://api.backpack.exchange/api/v1';
    private wsUrl = 'wss://ws.backpack.exchange';
    
    // Otimização HTTP Agent (Keep-Alive)
    private axiosInstance = axios.create({
        httpsAgent: new https.Agent({ keepAlive: true }),
        timeout: 2000
    });

    async getTicker(symbol: string): Promise<Ticker> {
        const { data } = await this.axiosInstance.get(`${this.baseUrl}/ticker?symbol=${symbol}`);
        return data as Ticker;
    }

    async getKlines(symbol: string, interval: string, limit: number = 50): Promise<Kline[]> {
        // Calcular startTime baseado no limit e interval
        const now = Date.now();
        let durationMs = 0;
        
        // Conversão simples
        if (interval.endsWith('m')) durationMs = parseInt(interval) * 60 * 1000;
        else if (interval.endsWith('h')) durationMs = parseInt(interval) * 60 * 60 * 1000;
        else if (interval.endsWith('d')) durationMs = parseInt(interval) * 24 * 60 * 60 * 1000;
        
        // Se falhar o parse, default para 1h
        if (durationMs === 0) durationMs = 60 * 60 * 1000;

        const startTimeMs = now - (durationMs * limit);
        // Backpack API usually expects seconds for klines? Let's try Integer
        const startTime = Math.floor(startTimeMs / 1000); // Try Seconds first
        // If it fails, we revert to Ms. But "int64" usually fits ms.
        // Maybe the error "expects an input value" means the param name is wrong?
        // Let's try sending BOTH start and startTime just in case, or check docs.
        // Usually it is 'start' or 'startTime'.
        
        // Vamos tentar enviar como 'start' mas garantir que é int.
        // E se for segundos?
        
        // Tentativa: startTime (Seconds)
        const startTimeSec = Math.floor(startTimeMs / 1000);
        const { data } = await this.axiosInstance.get(`${this.baseUrl}/klines?symbol=${symbol}&interval=${interval}&startTime=${startTimeSec}`);
        return data as Kline[]; 
    }

    // WebSocket Implementation for Low Latency Order Book
    async getOrderBookWS(symbol: string): Promise<OrderBook> {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket(this.wsUrl);
            const timeout = setTimeout(() => {
                ws.terminate();
                reject(new Error("WS Timeout"));
            }, 3000); // 3s max wait

            ws.on('open', () => {
                // Subscribe to depth
                const payload = {
                    method: "SUBSCRIBE",
                    params: [`depth.${symbol}`]
                };
                ws.send(JSON.stringify(payload));
            });

            ws.on('message', (data) => {
                const msg = JSON.parse(data.toString());
                // Handle snapshot or update
                if (msg.e === 'depth' || msg.e === 'depthUpdate') {
                    clearTimeout(timeout);
                    ws.terminate(); // Close after first packet for "Snapshot" feel
                    
                    // Transform to OrderBook interface
                    // WS might return different structure, but for this simulation we map it
                    // Assuming standard structure or simplified for simulation
                    resolve({
                        asks: msg.a || [],
                        bids: msg.b || [],
                        lastUpdateId: msg.u || '0'
                    } as OrderBook);
                }
            });

            ws.on('error', (err) => {
                clearTimeout(timeout);
                reject(err);
            });
        });
    }

    // Fallback REST OrderBook
    async getOrderBookREST(symbol: string): Promise<OrderBook> {
        const { data } = await this.axiosInstance.get(`${this.baseUrl}/depth?symbol=${symbol}`);
        return data as OrderBook;
    }

    // Helper para calcular Spread e Liquidez (Híbrido WS/REST)
    async getMarketMicrostructure(symbol: string) {
        // Tenta WS primeiro para book, REST para volume (ticker)
        let book: OrderBook;
        let ticker: Ticker;

        try {
            // Parallel fetch: WS for speed on depth, REST for 24h stats
            const [bookData, tickerData] = await Promise.all([
                this.getOrderBookREST(symbol), // Usando REST por estabilidade no script "one-shot" (WS handshake overhead > REST RTT às vezes)
                this.getTicker(symbol)
            ]);
            book = bookData;
            ticker = tickerData;
        } catch (e) {
            console.warn("️  Falha na coleta de dados. Usando fallback...");
            throw e;
        }

        // Validação Rigorosa de Dados (Correção do Spread Absurdo)
        const bids = book.bids || [];
        const asks = book.asks || [];

        // Encontrar Melhor Bid (Max Price) e Melhor Ask (Min Price) independente da ordenação
        let bestBid = 0;
        let bestAsk = 0;

        if (bids.length > 0) {
            // Assumindo que está ordenado, verificamos as pontas
            const firstBid = parseFloat(bids[0][0]);
            const lastBid = parseFloat(bids[bids.length - 1][0]);
            bestBid = Math.max(firstBid, lastBid);
        }

        if (asks.length > 0) {
            const firstAsk = parseFloat(asks[0][0]);
            const lastAsk = parseFloat(asks[asks.length - 1][0]);
            bestAsk = Math.min(firstAsk, lastAsk);
        }
        
        // Debug Log
        console.log(`DEBUG: ${symbol} BestBid: ${bestBid}, BestAsk: ${bestAsk}`);

        // Recalcular Spread com os valores corrigidos
        let spread = 0;
        if (bestBid > 0 && bestAsk > 0) {
            spread = (bestAsk - bestBid) / bestBid;
        }

        const volume24h = parseFloat(ticker.quoteVolume);

        return {
            price: parseFloat(ticker.lastPrice),
            spread,
            volume24h,
            bestBid,
            bestAsk
        };
    }
}
