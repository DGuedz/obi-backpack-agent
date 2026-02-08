
interface CreditCardPayment {
  Customer: {
    Name: string;
    Identity?: string; // CPF/CNPJ
  };
  Payment: {
    Type: 'CreditCard';
    Amount: number; // In cents (e.g., 1000 = R$ 10,00)
    Installments: number;
    CreditCard: {
      CardNumber: string;
      Holder: string;
      ExpirationDate: string; // MM/YYYY
      SecurityCode: string;
      Brand: string; // Visa, Master, etc.
    };
  };
  MerchantOrderId: string;
}

export class CieloService {
  private merchantId: string;
  private merchantKey: string;
  private baseUrl: string;

  constructor() {
    this.merchantId = process.env.CIELO_MERCHANT_ID || '';
    this.merchantKey = process.env.CIELO_MERCHANT_KEY || '';
    // Default to Sandbox if not specified
    this.baseUrl = process.env.CIELO_ENV === 'production' 
      ? 'https://api.cieloecommerce.cielo.com.br/1' 
      : 'https://apisandbox.cieloecommerce.cielo.com.br/1';
    
    if (!this.merchantId || !this.merchantKey) {
      console.warn('️ Cielo Credentials missing in environment variables.');
    }
  }

  async createTransaction(data: CreditCardPayment) {
    try {
      const response = await fetch(`${this.baseUrl}/sales`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'MerchantId': this.merchantId,
          'MerchantKey': this.merchantKey,
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result[0]?.Message || 'Payment Failed');
      }

      return result;
    } catch (error) {
      console.error('Cielo Transaction Error:', (error as Error)?.message || String(error));
      throw error;
    }
  }
}
