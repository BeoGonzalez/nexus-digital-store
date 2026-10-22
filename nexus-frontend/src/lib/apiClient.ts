const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiClient = {
  async getGames() {
    const res = await fetch(`${API_URL}/api/v1/video-games`, {
      next: { revalidate: 60 } // ISR - Revalida cada 60 segundos
    });
    if (!res.ok) throw new Error("Error al obtener el catálogo");
    return res.json();
  },
  
  async createOrder(orderData: any, token: string) {
    const res = await fetch(`${API_URL}/api/v1/orders`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}` 
      },
      body: JSON.stringify(orderData)
    });
    const data = await res.json();
    if (!res.ok) {
      console.error("Order creation error:", data);
      throw new Error(
        typeof data.detail === 'string' 
          ? data.detail 
          : JSON.stringify(data.detail, null, 2) || "Error al procesar la orden"
      );
    }
    return data;
  },

  async getPaymentMethods(token: string) {
    const res = await fetch(`${API_URL}/api/v1/orders/payment-methods`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Error al cargar métodos de pago");
    return data;
  },

  async addPaymentMethod(paymentData: any, token: string) {
    const res = await fetch(`${API_URL}/api/v1/orders/payment-methods`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}` 
      },
      body: JSON.stringify(paymentData)
    });
    const data = await res.json();
    if (!res.ok) {
      console.error("Payment method error:", data);
      throw new Error(
        typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail) || "Error al agregar método de pago"
      );
    }
    return data;
  },

  async createGame(gameData: any, token: string) {
    const res = await fetch(`${API_URL}/api/v1/video-games`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}` 
      },
      body: JSON.stringify(gameData)
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Error al crear el juego en el backend");
    }
    return data;
  },

  async updateGame(id: string, gameData: any, token: string) {
    const res = await fetch(`${API_URL}/api/v1/video-games/${id}`, {
      method: "PUT",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}` 
      },
      body: JSON.stringify(gameData)
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Error al actualizar el juego");
    }
    return data;
  },

  async deleteGame(id: string, token: string) {
    const res = await fetch(`${API_URL}/api/v1/video-games/${id}`, {
      method: "DELETE",
      headers: { 
        "Authorization": `Bearer ${token}` 
      }
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Error al eliminar el juego");
    }
    return data;
  },

  auth: {
    async register(email: string, password: string, name: string) {
      const res = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Error al registrar usuario en Cognito");
      }
      return data;
    },

    async login(email: string, password: string) {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || data.message || "Credenciales inválidas en Cognito");
      }
      return data;
    }
  }
};
