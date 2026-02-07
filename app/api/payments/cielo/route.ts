
import { NextResponse } from 'next/server';
import { CieloService } from '@/app/lib/cielo';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { cardData, amount, orderId, customerName } = body;

    if (!cardData || !amount) {
      return NextResponse.json({ error: 'Missing payment data' }, { status: 400 });
    }

    // Mock Mode Check
    if (!process.env.CIELO_MERCHANT_ID) {
        console.warn("️ Mocking Cielo Payment (No Credentials)");
        // Simulate processing delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        return NextResponse.json({
            Payment: {
                Status: 1, // Authorized
                PaymentId: "mock-payment-id-" + Date.now(),
                ReturnMessage: "Operation Successful (Mock)"
            }
        });
    }

    const cielo = new CieloService();

    const transaction = {
      MerchantOrderId: orderId || `ORDER-${Date.now()}`,
      Customer: {
        Name: customerName || 'Customer',
      },
      Payment: {
        Type: 'CreditCard' as const,
        Amount: amount * 100, // Convert to cents
        Installments: 1,
        CreditCard: {
          CardNumber: cardData.number,
          Holder: cardData.holder,
          ExpirationDate: cardData.expiry,
          SecurityCode: cardData.cvc,
          Brand: cardData.brand || 'Visa', // Should be detected
        },
      },
    };

    const result = await cielo.createTransaction(transaction);

    return NextResponse.json(result);
  } catch (error: any) {
    console.error('Payment API Error:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
