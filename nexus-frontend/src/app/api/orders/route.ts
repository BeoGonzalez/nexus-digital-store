import { NextResponse } from 'next/server';
import { fastApiClient } from '@/infrastructure/bff/fastApiClient';
import { Order } from '@/domain/models';
import { v4 as uuidv4 } from 'uuid';

export async function GET(request: Request) {
  try {
    const orders = await fastApiClient.get<Order[]>('/orders', { requireAuth: true });
    return NextResponse.json(orders);
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to fetch orders' },
      { status: error.status || 500 }
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    // We generate an idempotency key if not provided by the client, though 
    // it's generally better to generate it on the client or in a server action.
    // For this proxy, we'll pass headers along.
    const idempotencyKey = request.headers.get('Idempotency-Key') || uuidv4();
    
    const newOrder = await fastApiClient.post<Order>('/orders', body, {
      requireAuth: true,
      headers: {
        'Idempotency-Key': idempotencyKey
      }
    });
    
    return NextResponse.json(newOrder, { status: 201 });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message || 'Failed to create order' },
      { status: error.status || 500 }
    );
  }
}
