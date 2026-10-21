"use client";

import Link from "next/link";
import { useMemo, useState, useEffect, useRef } from "react";
import { useVideoGamesQuery } from "@/application/hooks/useVideoGamesQuery";
import { usePaymentMethodsQuery, useAddPaymentMethodMutation, useCreateOrderMutation } from "@/application/hooks/useOrderMutations";
import { useLoginMutation, useRegisterMutation } from "@/application/hooks/useAuthMutations";
import { VideoGame } from "@/domain/models";
import ChatBotOrb from "@/presentation/components/3d/ChatBotOrb";
import {
  Check,
  ChevronDown,
  ChevronUp,
  CircleUserRound,
  CreditCard,
  Eye,
  EyeOff,
  KeyRound,
  LogIn,
  Mail,
  Minus,
  Plus,
  Search,
  ShoppingCart,
  Trash2,
  UserRound,
  X,
  ArrowLeft,
  LockKeyhole,
  LayoutDashboard,
  PlusCircle,
  Package,
  Pencil,
  ShieldCheck,
  Gamepad2,
  AlertCircle,
  AlertTriangle,
  Loader2,
  Image as ImageIcon,
  Bot,
  Send,
  MessageSquare,
  CornerDownLeft
} from "lucide-react";

const fondo =
  "https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Gemini_Generated_Image_7zucnk7zucnk7zuc-V9arNlyp5diSNLzvYFbfj17Cbc3b3e.jpg";

export type Product = VideoGame;

const filtros = {
  plataformas: ["PC", "PS5", "Xbox", "Switch"],
  géneros: ["Action RPG", "Souls-like", "Open World"],
};
type CartLine = Product & { cartId: string; quantity: number };
function Logo() {
  return (
    <div className="flex shrink-0 items-center gap-2 sm:gap-4 transition-transform active:scale-95 cursor-pointer group">
      <img 
        src="/logo.png" 
        alt="Gamma Terminal Logo" 
        className="h-10 sm:h-14 w-auto object-contain drop-shadow-[0_0_15px_rgba(72,200,216,0.3)] transition-all duration-300 group-hover:drop-shadow-[0_0_25px_rgba(255,69,0,0.4)] group-hover:scale-105" 
        onError={(e) => {
          // Fallback en caso de que la imagen no esté en public/logo.png
          e.currentTarget.style.display = 'none';
          e.currentTarget.nextElementSibling?.classList.remove('hidden');
        }}
      />
      {/* Fallback box si no carga la imagen */}
      <div className="relative hidden size-10 items-center justify-center bg-zinc-100 rounded-sm sm:size-12">
        <div className="absolute inset-1 border-[3px] border-zinc-950 rounded-sm" />
        <div className="absolute size-2 bg-transparent rounded-full" />
      </div>
      <div className="leading-none">
        <div className="text-[17px] font-black tracking-tighter text-zinc-100 sm:text-[25px]">
          GAMMA
        </div>
        <div className="text-[11px] font-mono tracking-[0.05em] text-cyan-500 sm:text-[14px]">
          TERMINAL
        </div>
      </div>
    </div>
  );
}

function ProductSkeleton() {
  return (
    <div className="flex flex-col p-4 rounded-2xl border border-white/5 bg-white/5 backdrop-blur-md animate-pulse">
      <div className="mb-3 h-3 w-12 rounded bg-white/10" />
      <div className="aspect-[.78] rounded-xl bg-white/10" />
      <div className="mt-4 h-5 w-3/4 rounded bg-white/10" />
      <div className="mt-2 h-6 w-1/3 rounded bg-white/10" />
      <div className="mt-4 h-10 w-full rounded-xl bg-white/10" />
    </div>
  );
}

function Toast({ message, visible }: { message: string; visible: boolean }) {
  if (!visible) return null;
  return (
    <div className="fixed bottom-6 left-1/2 z-50 flex -translate-x-1/2 items-center gap-3 rounded-full bg-[#48c8d8] px-6 py-3 font-bold text-[#08232a] shadow-[0_10px_40px_rgba(72,200,216,0.3)] animate-in slide-in-from-bottom-5 fade-in duration-300">
      <Check size={18} strokeWidth={3} />
      {message}
    </div>
  );
}

function ProductCard({
  product,
  onAdd,
  onSelect,
}: {
  product: Product;
  onAdd: () => void;
  onSelect: () => void;
}) {
  const imageUrl = product.image_url || product.image || "";
  const cardRef = useRef<HTMLElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLElement>) => {
    if (!cardRef.current || !glowRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    // Rotate max 10 degrees
    const rotateX = ((y - centerY) / centerY) * -10;
    const rotateY = ((x - centerX) / centerX) * 10;
    
    cardRef.current.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
    glowRef.current.style.transform = `translate(${x - rect.width}px, ${y - rect.height}px)`;
    glowRef.current.style.opacity = "1";
  };

  const handleMouseLeave = () => {
    if (!cardRef.current || !glowRef.current) return;
    cardRef.current.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
    glowRef.current.style.opacity = "0";
  };

  return (
    <article 
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className="group relative flex min-w-0 flex-col rounded-xl bg-black/40 p-4 transition-all duration-300 ease-out hover:z-10 shadow-lg border border-white/5 backdrop-blur-md"
      style={{ transformStyle: 'preserve-3d' }}
    >
      {/* Dynamic Glow Effect */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-xl">
        <div 
          ref={glowRef}
          className="absolute h-[200%] w-[200%] opacity-0 transition-opacity duration-300 pointer-events-none"
          style={{ background: 'radial-gradient(circle at center, rgba(72,200,216,0.15) 0%, transparent 50%)' }}
        />
      </div>

      {/* Floating Image Container */}
      <button 
        onClick={onSelect} 
        className="relative z-10 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500 rounded-sm outline-none"
        aria-label={`Ver detalles de ${product.title}`}
        style={{ transform: 'translateZ(30px)' }}
      >
        <div className="mb-3 flex items-center gap-2">
          <span className="rounded-sm bg-zinc-800/80 px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider text-zinc-300 border border-white/10 group-hover:border-cyan-500/50 group-hover:text-cyan-400 transition-colors shadow-[0_0_10px_rgba(0,0,0,0.5)]">
            {product.platform?.name || "PC"}
          </span>
          <span className="rounded-sm bg-zinc-800/80 px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider text-zinc-300 border border-white/10 group-hover:border-orange-500/50 group-hover:text-orange-400 transition-colors shadow-[0_0_10px_rgba(0,0,0,0.5)]">
            {product.genres && product.genres.length > 0 ? product.genres[0].name : "Clásico"}
          </span>
        </div>
        
        <div className="relative aspect-[.78] overflow-hidden rounded-lg bg-black/50 flex items-center justify-center ring-1 ring-inset ring-white/10 group-hover:ring-cyan-500/50 transition-colors shadow-[0_10px_20px_rgba(0,0,0,0.5)]">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={`Portada de ${product.title}`}
              className="h-full w-full object-cover"
              loading="lazy"
            />
          ) : (
            <ImageIcon size={32} className="text-zinc-700" />
          )}
          {/* Edge reflection */}
          <div className="absolute inset-0 bg-gradient-to-tr from-white/5 to-transparent pointer-events-none" />
        </div>
        
        <h3 className="mt-4 truncate text-lg font-black text-zinc-100 transition-colors group-hover:text-cyan-400" style={{ textShadow: '0 2px 10px rgba(0,0,0,0.8)' }}>
          {product.title}
        </h3>
      </button>

      {/* Footer Content */}
      <div className="relative z-10 mt-2 flex items-center justify-between" style={{ transform: 'translateZ(20px)' }}>
        <span className="text-xl font-black text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.3)]">
          $ {product.price_clp?.toLocaleString("es-CL") || 0}
        </span>
      </div>

      <button
        onClick={onAdd}
        className="relative z-10 mt-4 flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-cyan-600 to-[#48c8d8] py-2.5 text-xs font-black text-[#062029] transition-all duration-300 hover:from-orange-500 hover:to-[#ff5500] hover:text-white hover:shadow-[0_0_20px_rgba(255,85,0,0.6)] active:scale-95 border border-white/20 shadow-[inset_0_1px_1px_rgba(255,255,255,0.4)]"
        aria-label={`Añadir ${product.title} al carrito`}
        style={{ transform: 'translateZ(40px)' }}
      >
        <ShoppingCart size={16} className="transition-transform group-hover:-rotate-12 group-hover:scale-110" /> AÑADIR
      </button>
    </article>
  );
}

function Overlay({
  children,
  onClose,
  wide = false,
}: {
  children: React.ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md animate-in fade-in duration-200"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div
        className={`relative max-h-[92vh] w-full overflow-auto rounded-3xl border border-white/10 bg-black/60 backdrop-blur-2xl p-6 shadow-[inset_0_2px_20px_rgba(255,255,255,0.05),0_0_60px_rgba(0,0,0,0.8)] animate-in zoom-in-95 duration-200 ${wide ? "max-w-3xl" : "max-w-lg"}`}
        role="dialog"
        aria-modal="true"
      >
        <button
          aria-label="Cerrar modal"
          onClick={onClose}
          className="absolute right-5 top-5 rounded-full p-2 text-white/50 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#48c8d8]"
        >
          <X size={22} />
        </button>
        {children}
      </div>
    </div>
  );
}

export default function Page() {
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [open, setOpen] = useState({ plataformas: true, géneros: true });
  const [selected, setSelected] = useState<Product | null>(null);
  const [cartOpen, setCartOpen] = useState(false);
  const [checkout, setCheckout] = useState(false);
  const [complete, setComplete] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const [user, setUser] = useState<{name?: string; email?: string; role?: string} | null>(null);
  const loggedIn = !!user;
  const [loginError, setLoginError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [adminNotice, setAdminNotice] = useState("");
  
  const [toastMessage, setToastMessage] = useState("");

  const [token, setToken] = useState<string | null>(null);
  useEffect(() => {
    setToken(localStorage.getItem("nexus_token"));
  }, [loggedIn]);

  const { data: catalog = [], isLoading: catalogLoading } = useVideoGamesQuery();
  const { data: paymentMethods = [], isLoading: loadingPayments } = usePaymentMethodsQuery(token);

  const loginMutation = useLoginMutation();
  const registerMutation = useRegisterMutation();
  const addPaymentMethodMutation = useAddPaymentMethodMutation();
  const createOrderMutation = useCreateOrderMutation();

  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>("");
  const [showAddCard, setShowAddCard] = useState(false);
  const [newCard, setNewCard] = useState({ number: "", brand: "Visa" });
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<{sender: 'bot' | 'user', text: string}[]>([
    { sender: 'bot', text: '¡Hola! Soy GammaBot. ¿Qué juego estás buscando en la terminal espacial hoy?' }
  ]);

  useEffect(() => {
    if (paymentMethods.length > 0 && !selectedPaymentMethod) {
      setSelectedPaymentMethod(paymentMethods[0].id);
    }
  }, [paymentMethods, selectedPaymentMethod]);

  const shown = useMemo(() => {
    let filtered = [...catalog];
    if (query) {
      filtered = filtered.filter((p) => p.title.toLowerCase().includes(query.toLowerCase()));
    }
    return filtered;
  }, [catalog, query]);

  const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
  const total = cart.reduce((sum, item) => sum + (item.price_clp || 0) * item.quantity, 0);

  function showToast(message: string) {
    setToastMessage(message);
    setTimeout(() => setToastMessage(""), 3000);
  }

  function addToCart(product: Product) {
    setCart((current) => {
      const existing = current.find((item) => item.id === product.id);
      return existing
        ? current.map((item) =>
            item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
          )
        : [...current, { ...product, cartId: Date.now().toString(), quantity: 1 }];
    });
    setSelected(null);
    showToast(`${product.title} añadido al carrito`);
  }

  function updateQuantity(cartId: string, delta: number) {
    setCart((current) =>
      current
        .map((item) =>
          item.cartId === cartId ? { ...item, quantity: Math.max(0, item.quantity + delta) } : item
        )
        .filter((item) => item.quantity > 0)
    );
  }

  return (
    <main
      className="min-h-screen bg-transparent text-zinc-100 selection:bg-cyan-500/30 selection:text-white"
    >
      <header className="sticky top-4 z-40 mx-auto flex max-w-[1440px] px-4 sm:px-6 lg:px-10">
        <div className="relative w-full rounded-2xl sm:rounded-full bg-black/40 backdrop-blur-2xl shadow-[0_20px_40px_rgba(0,0,0,0.7),inset_0_1px_1px_rgba(255,255,255,0.1)] border border-white/10 p-3 sm:px-6 sm:py-4 transition-all duration-500 hover:bg-black/50 group flex flex-wrap sm:flex-nowrap items-center gap-3 sm:gap-6">
          {/* Glowing bottom edge inside the pill */}
          <div className="absolute bottom-0 left-1/2 h-[1px] w-3/4 -translate-x-1/2 bg-gradient-to-r from-transparent via-cyan-500 to-transparent opacity-40 shadow-[0_0_20px_rgba(6,182,212,1)] group-hover:w-full group-hover:opacity-100 transition-all duration-700" />
          
          <div className="shrink-0 drop-shadow-[0_0_10px_rgba(255,255,255,0.2)] transition-transform hover:scale-105">
            <Logo />
          </div>
          
          <form
            className="group/search ml-auto flex min-w-0 flex-1 max-w-[600px] items-center rounded-full border border-white/10 bg-black/60 backdrop-blur-md px-4 py-2 sm:px-5 sm:py-2.5 shadow-[inset_0_4px_20px_rgba(0,0,0,0.8)] transition-all duration-300 hover:border-cyan-500/30 focus-within:border-cyan-400 focus-within:bg-black/90 focus-within:shadow-[inset_0_4px_25px_rgba(0,0,0,1),0_0_25px_rgba(6,182,212,0.4)]"
            onSubmit={(e) => e.preventDefault()}
          >
            <div className="relative flex items-center justify-center mr-3 shrink-0">
              <Search className="text-cyan-500 transition-all duration-300 group-focus-within/search:text-cyan-300 group-focus-within/search:drop-shadow-[0_0_8px_rgba(6,182,212,1)]" size={18} />
              <div className="absolute inset-0 bg-cyan-500 blur-md opacity-0 group-focus-within/search:opacity-40 transition-opacity duration-300" />
            </div>
            <input
              aria-label="Buscar productos"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Analizar base de datos estelar..."
              className="min-w-0 flex-1 bg-transparent text-sm text-zinc-100 outline-none placeholder:text-zinc-600 font-mono tracking-wide selection:bg-cyan-500/40"
            />
            <div className="hidden items-center gap-2 border-l border-white/10 pl-4 ml-2 text-[10px] font-mono uppercase tracking-widest text-cyan-500 xl:flex">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500 shadow-[0_0_5px_rgba(6,182,212,0.8)]"></span>
              </span>
              <span>Scanner Activo</span>
            </div>
          </form>

          <div className="flex items-center gap-2 sm:gap-3 shrink-0 ml-auto sm:ml-0">
            {loggedIn && user?.email === "admin@nexus.com" && (
              <Link
                href="/admin"
                aria-label="Panel de Administración"
                className="hidden rounded-full bg-white/5 border border-white/5 p-3 text-white transition-all hover:bg-purple-500/20 hover:border-purple-500/50 hover:text-purple-400 hover:shadow-[0_0_20px_rgba(147,51,234,0.4)] active:scale-95 sm:block"
              >
                <LayoutDashboard size={20} />
              </Link>
            )}
            
            <button
              aria-label={loggedIn ? "Cuenta de usuario" : "Iniciar sesión"}
              onClick={() => setLoginOpen(true)}
              className="hidden rounded-full bg-white/5 border border-white/5 p-3 text-white transition-all hover:bg-cyan-500/20 hover:border-cyan-500/50 hover:text-cyan-400 hover:shadow-[0_0_20px_rgba(6,182,212,0.4)] active:scale-95 sm:block"
            >
              <UserRound size={20} />
            </button>

            <button
              aria-label="Ver carrito"
              onClick={() => setCartOpen(true)}
              className="relative rounded-full bg-gradient-to-tr from-cyan-900/40 to-purple-900/40 border border-white/10 p-3 text-white transition-all hover:border-cyan-400 hover:shadow-[0_0_25px_rgba(6,182,212,0.6)] active:scale-95 group/cart"
            >
              <ShoppingCart size={20} className="transition-transform group-hover/cart:scale-110" />
              {cartCount > 0 && (
                <span className="absolute -right-1 -top-1 flex size-5 items-center justify-center rounded-full bg-[#f3343b] text-[10px] font-black text-white shadow-[0_0_15px_rgba(243,52,59,0.8)] border border-black animate-in zoom-in duration-300">
                  {cartCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>
      
      <div className="mx-auto flex max-w-[1440px] gap-8 px-4 py-8 sm:px-6 lg:px-10 lg:py-10">
        <aside className="hidden w-[240px] shrink-0 xl:block">
          <div className="sticky top-[100px] rounded-3xl border border-white/5 bg-white/5 p-6 backdrop-blur-md">
            <h2 className="mb-6 text-sm font-bold uppercase tracking-widest text-[#48c8d8]">
              Filtros
            </h2>
            {Object.entries(filtros).map(([key, values]) => (
              <section key={key} className="mb-6 border-b border-white/10 pb-6 last:mb-0 last:border-0 last:pb-0">
                <button
                  className="flex w-full items-center justify-between text-base font-bold capitalize text-white/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#48c8d8] rounded-md"
                  onClick={() =>
                    setOpen((state) => ({
                      ...state,
                      [key]: !state[key as keyof typeof state],
                    }))
                  }
                  aria-expanded={open[key as keyof typeof open]}
                >
                  {key}
                  <span className="text-white/40 transition-transform">
                    {open[key as keyof typeof open] ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                  </span>
                </button>
                {open[key as keyof typeof open] && (
                  <div className="mt-4 space-y-3 animate-in fade-in slide-in-from-top-2 duration-200">
                    {values.map((value) => (
                      <label
                        key={value}
                        className="flex cursor-pointer items-center gap-3 text-sm text-white/70 transition-colors hover:text-white"
                      >
                        <div className="relative flex items-center justify-center">
                          <input
                            type="checkbox"
                            className="peer size-5 cursor-pointer appearance-none rounded border border-white/20 bg-black/20 transition-all checked:border-[#48c8d8] checked:bg-[#48c8d8] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#48c8d8]"
                          />
                          <Check size={14} strokeWidth={3} className="absolute text-[#062029] opacity-0 transition-opacity peer-checked:opacity-100 pointer-events-none" />
                        </div>
                        {value}
                      </label>
                    ))}
                  </div>
                )}
              </section>
            ))}
          </div>
        </aside>
        
        <section className="min-w-0 flex-1">
          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h1 className="text-3xl font-black tracking-tight lg:text-4xl">
                CATÁLOGO <span className="text-[#48c8d8]">DESTACADO</span>
              </h1>
              <p className="mt-2 text-white/50">Encuentra tu próxima aventura épica.</p>
            </div>
          </div>
          
          {catalogLoading ? (
            <div className="grid grid-cols-1 gap-5 xs:grid-cols-2 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
              {Array.from({ length: 10 }).map((_, i) => (
                <ProductSkeleton key={i} />
              ))}
            </div>
          ) : shown.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-3xl border border-white/5 bg-white/5 backdrop-blur-md py-20 text-center animate-in fade-in duration-500">
              <Search className="mb-4 text-[#48c8d8]" size={48} strokeWidth={1.5} />
              <h3 className="text-2xl font-black">No hay resultados</h3>
              <p className="mt-2 max-w-md text-white/50">
                No pudimos encontrar productos que coincidan con tu búsqueda. Intenta con otros términos o filtros.
              </p>
              <button 
                onClick={() => setQuery("")}
                className="mt-6 rounded-xl bg-white/10 px-6 py-3 text-sm font-bold transition-colors hover:bg-white/20 active:scale-95"
              >
                Limpiar búsqueda
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-5 xs:grid-cols-2 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
              {shown.map((product, index) => (
                <ProductCard
                  key={product.id || index}
                  product={product}
                  onSelect={() => setSelected(product)}
                  onAdd={() => addToCart(product)}
                />
              ))}
            </div>
          )}
        </section>
      </div>

      <Toast message={toastMessage} visible={!!toastMessage} />

      {loginOpen && (
        <Overlay onClose={() => setLoginOpen(false)}>
          <div className="mx-auto max-w-sm">
            <div className="mb-8 text-center">
              <div className="mx-auto mb-5 flex size-16 items-center justify-center rounded-2xl bg-[#48c8d8] text-[#062029] shadow-[0_0_30px_rgba(72,200,216,.3)]">
                <LogIn size={28} />
              </div>
              <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-[#48c8d8]">
                Gamma Game Store
              </p>
              <h2 className="mt-2 text-2xl font-black">
                {authMode === "login" ? "Acceso Seguro" : "Crea tu Cuenta"}
              </h2>
            </div>
            
            {loggedIn ? (
              <div className="py-4 text-center animate-in fade-in duration-300">
                <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-[#48c8d8]/10 text-[#48c8d8]">
                  <Check size={32} />
                </div>
                <h3 className="text-xl font-black">¡Hola de nuevo{user?.name ? `, ${user.name}` : ''}!</h3>
                <p className="mt-2 text-sm text-white/50">
                  Has iniciado sesión correctamente como <strong className="text-white">{user?.email}</strong>.
                </p>
                <button
                  onClick={() => {
                    setUser(null);
                    setLoginOpen(false);
                    localStorage.removeItem("nexus_token");
                  }}
                  className="mt-8 w-full rounded-xl border border-white/10 bg-white/5 backdrop-blur-md py-3 text-sm font-bold text-white transition-colors hover:bg-white/10 active:scale-95"
                >
                  Cerrar sesión
                </button>
              </div>
            ) : (
              <form
                onSubmit={async (event) => {
                  event.preventDefault();
                  const data = new FormData(event.currentTarget);
                  const email = String(data.get("email") || "");
                  const password = String(data.get("password") || "");
                  const name = String(data.get("name") || "");
                  
                  if (!email.includes("@") || password.length < 6) {
                    showToast("Credenciales inválidas. Verifica los campos.");
                    return;
                  }
                  
                  try {
                    if (authMode === "register") {
                      await registerMutation.mutateAsync({ email, password, name });
                      showToast("Cuenta creada exitosamente. Por favor, inicia sesión.");
                      setAuthMode("login");
                      return;
                    } 
                    
                    const response = await loginMutation.mutateAsync({ email, password });
                    if (response?.token) {
                      setToken(response.token);
                      setUser({ email, name: email.split("@")[0] });
                      showToast(`Bienvenido a Gamma`);
                      setLoginOpen(false);
                    }
                  } catch (err: any) {
                    showToast(err.message || "Ocurrió un error inesperado.");
                  }
                }}
                className="space-y-4 animate-in fade-in duration-300"
              >
                {(loginMutation.error || registerMutation.error) && (
                  <div role="alert" className="flex items-start gap-3 rounded-xl border border-[#f3343b]/30 bg-[#f3343b]/10 p-3 text-sm text-[#ff8b8f] animate-in slide-in-from-top-2">
                    <AlertCircle size={18} className="shrink-0 mt-0.5" />
                    <p>{(loginMutation.error as Error)?.message || (registerMutation.error as Error)?.message || "Ocurrió un error inesperado"}</p>
                  </div>
                )}
                
                {authMode === "register" && (
                  <div>
                    <label htmlFor="name" className="mb-2 block text-xs font-bold text-white/70">
                      NOMBRE
                    </label>
                    <div className="relative flex items-center">
                      <UserRound size={18} className="absolute left-4 text-white/40" />
                      <input
                         id="name"
                         name="name"
                         type="text"
                         required
                         disabled={loginMutation.isPending || registerMutation.isPending}
                         className="w-full rounded-xl border border-white/10 bg-black/40 shadow-[inset_0_2px_10px_rgba(0,0,0,0.8)] py-3 pl-11 pr-4 text-sm text-white outline-none transition-all focus:border-cyan-500/50 focus:bg-white/5 backdrop-blur-md focus:shadow-[inset_0_2px_10px_rgba(0,0,0,0.8),0_0_15px_rgba(72,200,216,0.3)] disabled:opacity-50"
                         placeholder="Tu nombre"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label htmlFor="email" className="mb-2 block text-xs font-bold text-white/70">
                    CORREO ELECTRÓNICO
                  </label>
                  <div className="relative flex items-center">
                    <Mail size={18} className="absolute left-4 text-white/40" />
                    <input
                      id="email"
                      name="email"
                      type="email"
                      required
                      disabled={loginMutation.isPending || registerMutation.isPending}
                      className="w-full rounded-xl border border-white/10 bg-black/40 shadow-[inset_0_2px_10px_rgba(0,0,0,0.8)] py-3 pl-11 pr-4 text-sm text-white outline-none transition-all focus:border-cyan-500/50 focus:bg-white/5 backdrop-blur-md focus:shadow-[inset_0_2px_10px_rgba(0,0,0,0.8),0_0_15px_rgba(72,200,216,0.3)] disabled:opacity-50"
                      placeholder="tu@email.com"
                    />
                  </div>
                </div>
                
                <div>
                  <label htmlFor="password" className="mb-2 block text-xs font-bold text-white/70">
                    CONTRASEÑA
                  </label>
                  <div className="relative flex items-center">
                    <KeyRound size={18} className="absolute left-4 text-white/40" />
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? "text" : "password"}
                      required
                      disabled={loginMutation.isPending || registerMutation.isPending}
                      className="w-full rounded-xl border border-white/10 bg-black/40 shadow-[inset_0_2px_10px_rgba(0,0,0,0.8)] py-3 pl-11 pr-12 text-sm text-white outline-none transition-all focus:border-cyan-500/50 focus:bg-white/5 backdrop-blur-md focus:shadow-[inset_0_2px_10px_rgba(0,0,0,0.8),0_0_15px_rgba(72,200,216,0.3)] disabled:opacity-50"
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                      onClick={() => setShowPassword(!showPassword)}
                      disabled={loginMutation.isPending || registerMutation.isPending}
                      className="absolute right-4 text-white/40 transition-colors hover:text-white disabled:opacity-50 focus-visible:outline-none focus-visible:text-[#48c8d8]"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
                
                <button
                  disabled={loginMutation.isPending || registerMutation.isPending}
                  className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan-600 to-[#48c8d8] py-3.5 text-sm font-black text-[#062029] transition-all hover:from-orange-500 hover:to-[#ff5500] hover:text-white hover:shadow-[0_0_20px_rgba(255,85,0,0.6)] active:scale-95 border border-white/20 shadow-[inset_0_1px_1px_rgba(255,255,255,0.4)] disabled:cursor-not-allowed disabled:opacity-70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-black focus-visible:ring-cyan-500"
                >
                  {(loginMutation.isPending || registerMutation.isPending) ? (
                    <>
                      <Loader2 size={18} className="animate-spin" /> {authMode === "login" ? "INICIANDO SESIÓN..." : "REGISTRANDO..."}
                    </>
                  ) : (
                    authMode === "login" ? "ACCEDER" : "REGISTRARSE"
                  )}
                </button>
                
                <div className="mt-4 text-center text-sm text-white/50">
                  {authMode === "login" ? "¿No tienes cuenta? " : "¿Ya tienes cuenta? "}
                  <button
                    type="button"
                    onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}
                    className="font-bold text-[#48c8d8] transition-colors hover:text-white"
                  >
                    {authMode === "login" ? "Regístrate aquí" : "Inicia sesión"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </Overlay>
      )}

      {selected && (
        <Overlay onClose={() => setSelected(null)} wide>
          <div className="grid gap-8 sm:grid-cols-[240px_1fr]">
            <div className="relative aspect-[.78] w-full overflow-hidden rounded-2xl shadow-2xl bg-black/40 backdrop-blur-md flex items-center justify-center">
              {selected.image_url || selected.image ? (
                <img
                  src={selected.image_url || selected.image || ""}
                  alt={`Portada de ${selected.title}`}
                  className="h-full w-full object-cover"
                />
              ) : (
                <ImageIcon size={64} className="text-white/10" />
              )}
            </div>
            <div className="flex flex-col justify-center">
              <div className="mb-3 flex items-center gap-3">
                <span className="rounded-md bg-[#48c8d8]/10 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-[#48c8d8]">
                  {selected.platform?.name || "PC"}
                </span>
                <span className="text-xs font-medium text-white/50">{selected.category || "Clásico"}</span>
              </div>
              <h2 className="text-3xl font-black sm:text-4xl">{selected.title}</h2>
              <p className="mt-4 leading-relaxed text-white/60">
                {selected.description || "Una aventura imprescindible para tu colección. Descubre mundos inolvidables, combates intensos y una experiencia optimizada para tu plataforma favorita."}
              </p>
              
              <div className="mt-auto pt-8">
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-widest text-white/40">Precio</p>
                    <span className="text-4xl font-black text-white">
                      $ {selected.price_clp?.toLocaleString("es-CL") || 0}
                    </span>
                  </div>
                  <button
                    onClick={() => addToCart(selected)}
                    className="flex items-center gap-2 rounded-xl bg-[#f3343b] px-6 py-4 text-sm font-black text-white transition-all hover:bg-[#ff4f56] hover:shadow-[0_0_20px_rgba(243,52,59,0.3)] active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#f3343b]"
                  >
                    <ShoppingCart size={18} /> AÑADIR AL CARRITO
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Overlay>
      )}

      {cartOpen && (
        <Overlay onClose={() => setCartOpen(false)} wide>
          <div className="pr-8">
            <h2 className="text-3xl font-black">Tu Carrito</h2>
            <p className="mt-1 text-sm text-white/50">
              Revisa los productos antes de finalizar la compra.
            </p>
          </div>
          
          {cart.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center animate-in fade-in duration-300">
              <div className="mb-6 flex size-20 items-center justify-center rounded-full bg-white/5 backdrop-blur-md">
                <ShoppingCart className="text-white/20" size={36} />
              </div>
              <h3 className="text-xl font-bold">Tu carrito está vacío</h3>
              <p className="mt-2 max-w-sm text-sm text-white/50">
                Explora nuestro catálogo y encuentra los mejores juegos para tu colección.
              </p>
              <button
                onClick={() => setCartOpen(false)}
                className="mt-8 rounded-xl bg-[#48c8d8] px-6 py-3 text-sm font-black text-[#062029] transition-transform hover:scale-105 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#48c8d8]"
              >
                EXPLORAR CATÁLOGO
              </button>
            </div>
          ) : (
            <div className="mt-8 animate-in fade-in duration-300">
              <div className="max-h-[50vh] space-y-3 overflow-y-auto pr-2">
                {cart.map((item) => (
                  <div
                    key={item.cartId}
                    className="group flex flex-col sm:flex-row sm:items-center gap-4 rounded-2xl border border-white/5 bg-black/40 backdrop-blur-md p-4 transition-all duration-300 hover:bg-white/5 hover:border-cyan-500/30 hover:shadow-[inset_0_0_20px_rgba(72,200,216,0.1),0_5px_15px_rgba(0,0,0,0.5)]"
                  >
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                      <div className="size-16 rounded-xl overflow-hidden bg-black/60 backdrop-blur-md shrink-0 flex items-center justify-center border border-white/10 group-hover:border-cyan-500/50 transition-colors shadow-inner">
                        {item.image_url || item.image ? (
                          <img
                            src={item.image_url || item.image || ""}
                            alt=""
                            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                          />
                        ) : (
                          <ImageIcon size={24} className="text-white/10" />
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <h3 className="truncate font-bold text-white">{item.title}</h3>
                        <p className="mt-0.5 text-xs text-white/50">
                          {item.platform?.name || "PC"}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between sm:justify-end gap-6 sm:w-auto w-full">
                      <span className="font-bold text-lg">
                        $ {((item.price_clp || 0) * item.quantity).toLocaleString("es-CL")}
                      </span>
                      <div className="flex items-center gap-3">
                        <div className="flex items-center gap-1 rounded-lg border border-white/10 bg-black/20 p-1">
                          <button
                            aria-label="Reducir cantidad"
                            onClick={() => updateQuantity(item.cartId, -1)}
                            className="rounded-md p-1.5 text-white/60 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#48c8d8]"
                          >
                            <Minus size={14} />
                          </button>
                          <span className="w-6 text-center text-sm font-medium">{item.quantity}</span>
                          <button
                            aria-label="Aumentar cantidad"
                            onClick={() => updateQuantity(item.cartId, 1)}
                            className="rounded-md p-1.5 text-white/60 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#48c8d8]"
                          >
                            <Plus size={14} />
                          </button>
                        </div>
                        <button
                          aria-label="Eliminar producto"
                          onClick={() => setCart((current) => current.filter((line) => line.cartId !== item.cartId))}
                          className="rounded-lg p-2 text-white/40 transition-colors hover:bg-[#f3343b]/20 hover:text-[#ff3d42] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#f3343b]"
                        >
                          <Trash2 size={18} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 border-t border-white/10 pt-6">
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-sm font-medium text-white/50">Total a pagar</p>
                    <strong className="text-3xl font-black text-white">
                      $ {total.toLocaleString("es-CL")}
                    </strong>
                  </div>
                  <button
                    onClick={() => {
                      setCartOpen(false);
                      setCheckout(true);
                    }}
                    className="flex items-center gap-2 rounded-xl bg-[#48c8d8] px-8 py-4 text-sm font-black text-[#062029] transition-all hover:bg-[#5cdcf0] hover:shadow-[0_0_20px_rgba(72,200,216,0.3)] active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#48c8d8]"
                  >
                    PROCEDER AL PAGO <ArrowLeft className="rotate-180" size={18} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </Overlay>
      )}

      {checkout && (
        <Overlay onClose={() => setCheckout(false)} wide>
          {complete ? (
            <div className="py-12 text-center animate-in zoom-in-95 duration-500">
              <div className="mx-auto mb-6 flex size-20 items-center justify-center rounded-full bg-[#48c8d8] text-[#062029] shadow-[0_0_40px_rgba(72,200,216,0.4)]">
                <Check size={40} strokeWidth={3} />
              </div>
              <h2 className="text-3xl font-black sm:text-4xl">¡Pago Exitoso!</h2>
              <p className="mx-auto mt-4 max-w-md leading-relaxed text-white/60">
                Tu pedido ha sido procesado correctamente. Hemos enviado un correo con tus claves digitales y el recibo de compra.
              </p>
              <button
                onClick={() => {
                  setCheckout(false);
                  setComplete(false);
                  setCart([]);
                }}
                className="mt-8 rounded-xl bg-white/10 px-8 py-3 text-sm font-bold transition-colors hover:bg-white/20 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
              >
                VOLVER AL INICIO
              </button>
            </div>
          ) : (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300">
              <div className="flex items-center gap-4 border-b border-white/10 pb-6">
                <button
                  onClick={() => setCheckout(false)}
                  className="rounded-full bg-white/5 backdrop-blur-md p-2 text-white/60 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#48c8d8]"
                  aria-label="Volver al carrito"
                >
                  <ArrowLeft size={20} />
                </button>
                <div>
                  <h2 className="text-2xl font-black">Finalizar Compra</h2>
                  <p className="text-xs font-medium text-white/50">Pago seguro encriptado</p>
                </div>
              </div>
              
              <div className="mt-8 grid gap-8 md:grid-cols-[1fr_300px]">
                <form
                  onSubmit={async (event) => {
                    event.preventDefault();
                    if (!token) {
                      showToast("Debes iniciar sesión para comprar.");
                      return;
                    }

                    try {
                      let activePaymentMethodId = selectedPaymentMethod;

                      if (showAddCard || paymentMethods.length === 0) {
                        const cleanNumber = newCard.number.replace(/\s+/g, '') || "0000";
                        const newPm = await addPaymentMethodMutation.mutateAsync({
                          card_number: cleanNumber,
                          card_brand: cleanNumber.startsWith("4") ? "Visa" : cleanNumber.startsWith("5") ? "Mastercard" : "AMEX",
                          is_default: paymentMethods.length === 0
                        });
                        activePaymentMethodId = newPm.id;
                        setSelectedPaymentMethod(newPm.id);
                        setShowAddCard(false);
                      } else if (!activePaymentMethodId) {
                        showToast("Por favor selecciona un método de pago.");
                        return;
                      }

                      const payload = {
                        items: cart.map(item => ({
                          video_game_id: item.id,
                          quantity: item.quantity
                        }))
                      };

                      await createOrderMutation.mutateAsync(payload);
                      setComplete(true);
                      setCart([]);
                    } catch (e: any) {
                      showToast(e.message || "Error inesperado procesando la orden");
                    }
                  }}
                  className="space-y-5"
                >
                  
                  <div className="space-y-4">
                    <h3 className="font-bold text-white">Datos de facturación</h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <label className="mb-1.5 block text-xs font-bold text-white/60">NOMBRE COMPLETO</label>
                        <input
                          required
                          className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none transition-all focus:border-[#48c8d8] focus:bg-white/5 backdrop-blur-md"
                          placeholder="Alex García"
                        />
                      </div>
                      <div>
                        <label className="mb-1.5 block text-xs font-bold text-white/60">EMAIL (ENVÍO DE CLAVES)</label>
                        <input
                          required
                          type="email"
                          className="w-full rounded-xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-white outline-none transition-all focus:border-[#48c8d8] focus:bg-white/5 backdrop-blur-md"
                          placeholder="alex@email.com"
                        />
                      </div>
                    </div>
                  </div>
                  
                  <div className="pt-4 space-y-4">
                    <h3 className="font-bold text-white flex items-center gap-2">
                      <CreditCard size={18} className="text-[#48c8d8]" /> Método de pago
                    </h3>

                    {loadingPayments ? (
                      <div className="flex justify-center py-4">
                        <Loader2 className="animate-spin text-[#48c8d8]" size={24} />
                      </div>
                    ) : (
                      <>
                        {paymentMethods.length > 0 && (
                          <div className="flex flex-col sm:flex-row gap-3 mb-4">
                            <button
                              type="button"
                              onClick={() => setShowAddCard(false)}
                              className={`flex-1 rounded-xl py-3 text-sm font-bold border transition-all ${!showAddCard ? 'bg-[#48c8d8]/20 border-[#48c8d8] text-[#48c8d8]' : 'bg-black/20 border-white/10 text-white/60 hover:text-white'}`}
                            >
                              Usar tarjeta guardada
                            </button>
                            <button
                              type="button"
                              onClick={() => setShowAddCard(true)}
                              className={`flex-1 rounded-xl py-3 text-sm font-bold border transition-all ${showAddCard ? 'bg-[#48c8d8]/20 border-[#48c8d8] text-[#48c8d8]' : 'bg-black/20 border-white/10 text-white/60 hover:text-white'}`}
                            >
                              Añadir nueva tarjeta
                            </button>
                          </div>
                        )}

                        {paymentMethods.length === 0 && (
                          <div className="mb-4 text-sm text-[#48c8d8] font-semibold bg-[#48c8d8]/10 p-3 rounded-xl border border-[#48c8d8]/20">
                            Añadir método de pago
                          </div>
                        )}

                        {paymentMethods.length > 0 && !showAddCard ? (
                          <div className="space-y-2">
                            {paymentMethods.map(pm => (
                              <label 
                                key={pm.id} 
                                className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
                                  selectedPaymentMethod === pm.id 
                                    ? "border-[#48c8d8] bg-[#48c8d8]/10" 
                                    : "border-white/10 bg-black/20 hover:border-white/20"
                                }`}
                              >
                                <input 
                                  type="radio" 
                                  name="payment_method" 
                                  value={pm.id}
                                  checked={selectedPaymentMethod === pm.id}
                                  onChange={() => setSelectedPaymentMethod(pm.id)}
                                  className="accent-[#48c8d8]"
                                />
                                <div className="flex flex-col">
                                  <span className="font-bold text-sm text-white">
                                    {pm.card_brand} terminada en {pm.card_last_4}
                                  </span>
                                  {pm.is_default && <span className="text-xs text-[#48c8d8]">Predeterminada</span>}
                                </div>
                              </label>
                            ))}
                          </div>
                        ) : (
                          <div className="space-y-4 rounded-xl border border-white/10 bg-black/20 p-4">
                            <div>
                              <label className="mb-1.5 block text-xs font-bold text-white/60">NÚMERO DE TARJETA</label>
                              <input
                                required={showAddCard || paymentMethods.length === 0}
                                inputMode="numeric"
                                value={newCard.number}
                                onChange={(e) => setNewCard({...newCard, number: e.target.value})}
                                className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none transition-all focus:border-[#48c8d8] focus:bg-white/5 backdrop-blur-md"
                                placeholder="0000 0000 0000 0000"
                                maxLength={19}
                              />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="mb-1.5 block text-xs font-bold text-white/60">CADUCIDAD</label>
                                <input
                                  required={showAddCard || paymentMethods.length === 0}
                                  className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none transition-all focus:border-[#48c8d8] focus:bg-white/5 backdrop-blur-md"
                                  placeholder="MM/AA"
                                  maxLength={5}
                                />
                              </div>
                              <div>
                                <label className="mb-1.5 block text-xs font-bold text-white/60">CVC</label>
                                <input
                                  required={showAddCard || paymentMethods.length === 0}
                                  type="password"
                                  className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none transition-all focus:border-[#48c8d8] focus:bg-white/5 backdrop-blur-md"
                                  placeholder="•••"
                                  maxLength={4}
                                />
                              </div>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                  
                  <button 
                    disabled={createOrderMutation.isPending || addPaymentMethodMutation.isPending}
                    className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-[#48c8d8] py-4 text-sm font-black text-[#062029] transition-all hover:bg-[#5cdcf0] hover:shadow-[0_0_20px_rgba(72,200,216,0.3)] active:scale-95 disabled:opacity-50"
                  >
                    {(createOrderMutation.isPending || addPaymentMethodMutation.isPending) ? <Loader2 className="animate-spin" size={18} /> : <LockKeyhole size={18} />}
                    {(createOrderMutation.isPending || addPaymentMethodMutation.isPending) ? "PROCESANDO..." : `PAGAR $ ${total.toLocaleString("es-CL")} SECURELY`}
                  </button>
                </form>
                
                <div className="rounded-2xl border border-white/5 bg-white/5 backdrop-blur-md p-6 h-fit">
                  <h3 className="font-bold border-b border-white/10 pb-4">Resumen</h3>
                  <div className="mt-4 max-h-[300px] overflow-y-auto space-y-3 pr-2">
                    {cart.map((item) => (
                      <div key={item.cartId} className="flex justify-between gap-3 text-sm">
                        <span className="text-white/70 line-clamp-2">
                          {item.quantity}x {item.title}
                        </span>
                        <span className="font-medium shrink-0">
                          $ {((item.price_clp || 0) * item.quantity).toLocaleString("es-CL")}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-6 border-t border-white/10 pt-4">
                    <div className="flex justify-between items-end">
                      <span className="text-sm text-white/60">Total</span>
                      <span className="text-2xl font-black text-[#48c8d8]">
                        $ {total.toLocaleString("es-CL")}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </Overlay>
      )}

      {/* Floating Chatbot Button & Modal */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-4">
        {chatOpen && (
          <div className="w-[320px] sm:w-[380px] h-[500px] max-h-[70vh] flex flex-col rounded-3xl border border-white/10 bg-black/60 backdrop-blur-2xl shadow-[inset_0_2px_20px_rgba(255,255,255,0.05),0_0_60px_rgba(0,0,0,0.8)] overflow-hidden animate-in slide-in-from-bottom-5 fade-in duration-300 origin-bottom-right">
            {/* Chat Header */}
            <div className="flex items-center justify-between border-b border-white/10 bg-black/40 p-4">
              <div className="flex items-center gap-3">
                <div className="relative flex size-12 items-center justify-center rounded-full shadow-[0_0_20px_rgba(139,92,246,0.5)] overflow-hidden">
                  <ChatBotOrb />
                </div>
                <div>
                  <h3 className="font-black text-white drop-shadow-[0_0_8px_rgba(139,92,246,0.8)]">GammaBot</h3>
                  <p className="text-xs text-cyan-400">Red Neuronal Activa</p>
                </div>
              </div>
              <button 
                onClick={() => setChatOpen(false)}
                className="rounded-full p-2 text-white/50 hover:bg-white/10 hover:text-white transition-colors"
              >
                <X size={18} />
              </button>
            </div>
            
            {/* Chat History */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 flex flex-col">
              {chatHistory.map((msg, i) => (
                <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
                    msg.sender === 'user' 
                      ? 'bg-gradient-to-r from-purple-600 to-cyan-500 text-white font-medium rounded-br-sm shadow-[0_5px_15px_rgba(139,92,246,0.3)]' 
                      : 'bg-white/10 text-white rounded-bl-sm border border-white/5 shadow-[inset_0_1px_5px_rgba(255,255,255,0.05)]'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            {/* Chat Input */}
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                if (!chatMessage.trim()) return;
                setChatHistory(curr => [...curr, { sender: 'user', text: chatMessage }]);
                setChatMessage("");
                setTimeout(() => {
                  setChatHistory(curr => [...curr, { sender: 'bot', text: 'Mi red neuronal aún se está calibrando en esta iteración. ¡Pero puedo sentir que quieres juegos increíbles!' }]);
                }, 1000);
              }}
              className="p-4 border-t border-white/10 bg-black/40"
            >
              <div className="relative flex items-center">
                <input 
                  type="text" 
                  value={chatMessage}
                  onChange={(e) => setChatMessage(e.target.value)}
                  placeholder="Escribe tu mensaje..."
                  className="w-full rounded-full border border-white/10 bg-black/40 py-3 pl-5 pr-12 text-sm text-white outline-none transition-all focus:border-cyan-500/50 focus:bg-white/5 shadow-[inset_0_2px_10px_rgba(0,0,0,0.8)] focus:shadow-[inset_0_2px_10px_rgba(0,0,0,0.8),0_0_15px_rgba(72,200,216,0.3)]"
                />
                <button 
                  type="submit"
                  disabled={!chatMessage.trim()}
                  className="absolute right-2 flex size-8 items-center justify-center rounded-full bg-gradient-to-r from-purple-500 to-cyan-500 text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100 shadow-[0_0_10px_rgba(139,92,246,0.5)]"
                >
                  <Send size={14} className="-ml-0.5" />
                </button>
              </div>
            </form>
          </div>
        )}
        
        <button
          onClick={() => setChatOpen(!chatOpen)}
          className={`relative flex size-14 sm:size-16 items-center justify-center rounded-full shadow-[0_0_30px_rgba(139,92,246,0.4)] transition-transform duration-300 hover:scale-110 active:scale-95 overflow-hidden border border-white/20 ${
            chatOpen 
              ? 'bg-black/60 text-white' 
              : 'text-white hover:shadow-[0_0_40px_rgba(6,182,212,0.6)]'
          }`}
          aria-label={chatOpen ? "Cerrar chat" : "Abrir chat"}
        >
          {!chatOpen && <ChatBotOrb />}
          {chatOpen && <X size={26} className="relative z-10" />}
        </button>
      </div>
    </main>
  );
}
