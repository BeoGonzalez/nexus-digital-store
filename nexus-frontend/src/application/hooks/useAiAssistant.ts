import { useState, useCallback, useRef, useEffect } from 'react';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface RecommendedProduct {
  id: string;
  title: string;
  price_clp: string;
}

export function useAiAssistant() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content: '¡Hola! Soy NexusBot, tu asesor gamer en Nexus Digital Store. 🎮 ¿Qué tipo de juego o aventura estás buscando hoy en la tienda?',
    },
  ]);
  const [recommendedProducts, setRecommendedProducts] = useState<RecommendedProduct[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionIdRef = useRef<string>('');

  useEffect(() => {
    // Generar o recuperar session_id persistente para memoria multi-turno
    const existing = typeof window !== 'undefined' ? sessionStorage.getItem('nexus_chat_session_id') : null;
    if (existing) {
      sessionIdRef.current = existing;
    } else {
      const generated = `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      sessionIdRef.current = generated;
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('nexus_chat_session_id', generated);
      }
    }
  }, []);

  const getSmartFallback = (query: string): string => {
    const q = query.toLowerCase().trim();
    if (/^(hola|buenas|hey|saludos|que tal|buen dia)/.test(q)) {
      return '¡Hola gamer! 👾 ¿Qué buscas jugar hoy? Tenemos grandes aventuras de rol, shooters intensos, mundos abiertos y cooperativos para disfrutar.';
    }
    if (q.includes('hambre') || q.includes('comes') || q.includes('comida') || q.includes('almuerzo') || q.includes('cena')) {
      return '¡Jaja! Como inteligencia artificial no tengo estómago ni procesos biológicos, así que no estoy relacionado con el hambre ni necesito comer. ¡Mi única energía son los servidores y los buenos videojuegos! 🍕🎮 Pero si tú tienes hambre, un buen refrigerio siempre acompaña una buena partida. ¿Qué juego estás buscando hoy?';
    }
    if (q.includes('clima') || q.includes('tiempo') || q.includes('llueve') || q.includes('temperatura') || q.includes('calor') || q.includes('frio')) {
      return 'No puedo ver el clima exterior ni tengo sensores meteorológicos para decirte cómo está la temperatura afuera... ☀️🌧️ Pero desde la terminal de Nexus cualquier día es perfecto para quedarse jugando con una buena ventilación. ¿Buscas alguna recomendación?';
    }
    if (q.includes('auto') || q.includes('coche') || q.includes('carro') || q.includes('mecanica') || q.includes('motor')) {
      return 'Sobre mecánica o vehículos reales: como IA de Nexus no soy mecánico ni tengo un taller de autos, ¡pero en la velocidad y el asfalto virtual soy experto! 🏎️💨 ¿Te gustaría ver recomendaciones de juegos de carreras o simulación para PC?';
    }
    if (q.includes('salud') || q.includes('medico') || q.includes('medicina') || q.includes('dolor') || q.includes('enfermo')) {
      return 'Respecto a tu consulta de salud: soy un asistente virtual de videojuegos y no tengo formación médica (¡aquí solo manejamos botiquines en pantalla!). Si no te sientes bien, consulta a un profesional. Y para despejar la mente, ¿qué juego te gustaría explorar?';
    }
    if (q.includes('tarea') || q.includes('matematica') || q.includes('calculo') || q.includes('colegio') || q.includes('universidad')) {
      return 'Sobre tus tareas o estudios: en Nexus me especializo al 100% en videojuegos de PC, por lo que no resuelvo deberes académicos. ¡Pero cuando termines de estudiar, el catálogo te espera para celebrar! ¿Qué juego tienes en mente?';
    }
    if (q.includes('terror') || q.includes('miedo') || q.includes('horror')) {
      return `Los juegos de terror son una experiencia increíble con luces apagadas. Te recomiendo revisar títulos de supervivencia y horror en nuestro catálogo como Resident Evil o Silent Hill si están en lista. ¿Prefieres terror psicológico o supervivencia con disparos?`;
    }
    if (q.includes('rpg') || q.includes('rol') || q.includes('historia')) {
      return `¡Los RPG son el corazón del gaming inmersivo! En Nexus contamos con opciones de mundo abierto y campañas profundas. ¿Buscas rol por turnos, RPG de acción en tercera persona o fantasía medieval?`;
    }
    if (q.includes('precio') || q.includes('oferta') || q.includes('barato') || q.includes('descuento')) {
      return `En Nexus Digital Store todos nuestros precios están actualizados en pesos chilenos (CLP) con excelentes promociones. ¿Tienes algún rango de presupuesto en mente para sugerirte las mejores ofertas?`;
    }
    return `Para tu consulta sobre "${query}", te sugiero explorar los filtros de categorías de nuestro catálogo destacado o ingresar términos específicos en la barra de búsqueda. ¿Buscas algún juego en solitario o para jugar con amigos?`;
  };

  const sendMessage = useCallback(async (content: string) => {
    const trimmed = content.trim();
    if (!trimmed) return;

    const userMessage: ChatMessage = { role: 'user', content: trimmed };
    const historySnapshot = [...messages, userMessage];
    
    setMessages((prev) => [...prev, userMessage, { role: 'assistant', content: '' }]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: trimmed,
          message: trimmed,
          chat_history: historySnapshot.map((m) => ({ role: m.role, content: m.content })),
          session_id: sessionIdRef.current,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error en servidor: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No se recibió stream del backend');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let receivedAnyToken = false;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const event of events) {
          const lines = event.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const parsed = JSON.parse(line.substring(6));
                if (parsed.type === 'token' && typeof parsed.data === 'string') {
                  receivedAnyToken = true;
                  setMessages((prev) => {
                    const next = [...prev];
                    const last = next[next.length - 1];
                    if (last && last.role === 'assistant') {
                      next[next.length - 1] = {
                        ...last,
                        content: last.content + parsed.data,
                      };
                    }
                    return next;
                  });
                } else if (parsed.type === 'products' && Array.isArray(parsed.data)) {
                  setRecommendedProducts(parsed.data);
                }
              } catch {
                // Si la línea no es JSON parseable, tratar como texto directo
                const text = line.substring(6);
                if (text) {
                  receivedAnyToken = true;
                  setMessages((prev) => {
                    const next = [...prev];
                    const last = next[next.length - 1];
                    if (last && last.role === 'assistant') {
                      next[next.length - 1] = { ...last, content: last.content + text };
                    }
                    return next;
                  });
                }
              }
            }
          }
        }
      }

      // Si por alguna razón el stream terminó sin tokens, aplicar fallback contextual
      if (!receivedAnyToken) {
        const fallback = getSmartFallback(trimmed);
        setMessages((prev) => {
          const next = [...prev];
          const last = next[next.length - 1];
          if (last && last.role === 'assistant') {
            next[next.length - 1] = { ...last, content: fallback };
          }
          return next;
        });
      }
    } catch (err: any) {
      console.warn('Chat assistant fallback activado:', err.message);
      const fallback = getSmartFallback(trimmed);
      setMessages((prev) => {
        const next = [...prev];
        const last = next[next.length - 1];
        if (last && last.role === 'assistant') {
          next[next.length - 1] = {
            ...last,
            content: last.content ? last.content : fallback,
          };
        }
        return next;
      });
    } finally {
      setIsLoading(false);
    }
  }, [messages]);

  const clearChat = useCallback(() => {
    setMessages([
      {
        role: 'assistant',
        content: '¡Conversación reiniciada! ¿En qué puedo orientarte ahora?',
      },
    ]);
    setRecommendedProducts([]);
  }, []);

  return {
    messages,
    isLoading,
    error,
    recommendedProducts,
    sendMessage,
    clearChat,
  };
}
