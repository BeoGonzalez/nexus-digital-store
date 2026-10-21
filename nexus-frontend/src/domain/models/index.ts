export interface Platform {
  id: string;
  name: string;
}

export interface Genre {
  id: string;
  name: string;
}

export interface VideoGame {
  id: string;
  title: string;
  description?: string;
  price_clp: number;
  stock: number;
  platform?: Platform;
  genres?: Genre[];
  image_url?: string;
  image?: string;
  created_at?: string;
  category?: string;
}

export interface OrderItem {
  video_game_id: string;
  quantity: number;
}

export interface OrderPayload {
  items: OrderItem[];
}

export interface PaymentMethod {
  id: string;
  user_id: string;
  card_last_4: string;
  card_brand: string;
  is_default: boolean;
}

export interface CreatePaymentMethodPayload {
  card_number: string;
  card_brand: string;
  is_default: boolean;
}

export interface ApiErrorDetail {
  loc?: string[];
  msg: string;
  type?: string;
}

export interface Order {
  id: string;
  userId: string;
  items: { videoGameId: string; quantity: number; price: number }[];
  totalAmount: number;
  status: 'PENDING' | 'COMPLETED' | 'CANCELLED';
  paymentMethodId: string;
  createdAt: string;
  updatedAt: string;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'USER' | 'ADMIN';
}
