import { NextResponse } from 'next/server';
import { fastApiClient } from '@/infrastructure/bff/fastApiClient';
import { PaymentMethod } from '@/domain/models';

export async function GET(request: Request) {
  try {
    const paymentMethods = await fastApiClient.get<PaymentMethod[]>('/orders/payment-methods', { requireAuth: true });
    return NextResponse.json(paymentMethods);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch payment methods' },
      { status: error.status || 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const newPaymentMethod = await fastApiClient.post<PaymentMethod>('/orders/payment-methods', body, { requireAuth: true });
    return NextResponse.json(newPaymentMethod, { status: 201 });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to create payment method' },
      { status: error.status || 500 }
    );
  }
}
