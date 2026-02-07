import nacl from 'tweetnacl';

export class BackpackClient {
  private key: string;
  private secret: string;
  private baseUrl = "https://api.backpack.exchange";
  private static readonly paramsToString = (params: Record<string, string | number | boolean>) =>
    Object.fromEntries(Object.entries(params).map(([key, value]) => [key, String(value)]));

  constructor(key: string, secret: string) {
    this.key = key;
    this.secret = secret;
  }

  private getHeaders(instruction: string, params: Record<string, string | number | boolean> = {}) {
    const timestamp = Date.now();
    const window = 5000;

    const sortedKeys = Object.keys(params).sort();
    const queryParts = sortedKeys.map(key => {
        return `${key}=${String(params[key])}`;
    });
    const paramString = queryParts.join('&');

    let signaturePayload = instruction ? `instruction=${instruction}` : '';
    if (paramString) {
        signaturePayload += signaturePayload ? `&${paramString}` : paramString;
    }
    
    if (signaturePayload) {
        signaturePayload += `&timestamp=${timestamp}&window=${window}`;
    } else {
        signaturePayload = `timestamp=${timestamp}&window=${window}`;
    }

    const secretBytes = Buffer.from(this.secret, 'base64');
    let signingKey = secretBytes;
    
    if (secretBytes.length === 32) {
        signingKey = Buffer.from(nacl.sign.keyPair.fromSeed(secretBytes).secretKey);
    }

    const signatureBytes = nacl.sign.detached(
      Buffer.from(signaturePayload, 'utf-8'),
      signingKey
    );
    
    const signature = Buffer.from(signatureBytes).toString('base64');

    return {
      "X-Timestamp": timestamp.toString(),
      "X-Window": window.toString(),
      "X-API-Key": this.key,
      "X-Signature": signature,
      "Content-Type": "application/json; charset=utf-8"
    };
  }

  async get(endpoint: string, instruction: string, params: Record<string, string | number | boolean> = {}) {
    const headers = this.getHeaders(instruction, params);
    const queryString = new URLSearchParams(BackpackClient.paramsToString(params)).toString();
    const url = `${this.baseUrl}${endpoint}${queryString ? `?${queryString}` : ''}`;
    
    const response = await fetch(url, { 
      method: 'GET',
      headers
    });
    
    if (!response.ok) {
        const text = await response.text();
        console.error(`Backpack API Error: ${response.status} - ${text}`);
        throw new Error(`Backpack API Error: ${response.status}`);
    }
    return response.json();
  }
  
  async getBalance() {
      // Endpoint: /api/v1/capital/collateral
      // Instruction: collateralQuery
      // This returns { totalPortfolioValue, collateralAvailable, ... }
      return this.get('/api/v1/capital/collateral', 'collateralQuery');
  }

  async getPositions() {
      // Endpoint: /api/v1/position
      // Instruction: positionQuery
      return this.get('/api/v1/position', 'positionQuery');
  }
}
