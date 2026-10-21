'use server';

import { fastApiClient } from '@/infrastructure/bff/fastApiClient';
import { Order } from '@/domain/models';
import { v4 as uuidv4 } from 'uuid';
import { updateTag } from 'next/cache';

export async function createOrderAction(orderData: Partial<Order>) {
  try {
    const idempotencyKey = uuidv4();
    
    const newOrder = await fastApiClient.post<Order>('/orders', orderData, {
      requireAuth: true,
      headers: {
        'Idempotency-Key': idempotencyKey,
      }
    });

    // Revalidate catalog as stock might have changed
    updateTag('catalog');

    return { success: true, data: newOrder };
  } catch (error: any) {
    console.error('Order creation failed:', error);
    return { 
      success: false, 
      error: error.message || 'An error occurred while creating the order',
      status: error.status 
    };
  }
}

