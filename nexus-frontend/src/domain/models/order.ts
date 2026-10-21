export enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
}

export interface OrderItem {
  id: string;
  videoGameId: string;
  quantity: number;
  unitPriceClp: number;
  subtotal: number;
  createdAt: string;
}

export interface OrderItemRequest {
  video_game_id: string;
  quantity: number;
}

export interface CreateOrderDTO {
  items: OrderItemRequest[];
}

export interface OrderResponse {
  id: string;
  userId: string;
  totalAmountClp: number;
  status: OrderStatus;
  items: OrderItem[];
  createdAt: string;
}
