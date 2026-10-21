import Link from "next/link";
import { 
  LayoutDashboard, 
  Gamepad2, 
  Users, 
  Settings, 
  Store 
} from "lucide-react";
import LogoutButton from "./LogoutButton";

export const metadata = {
  title: "Admin Dashboard - Gamma Game Store",
  description: "Panel de control administrativo",
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0A0A0A] text-white selection:bg-[#48c8d8]/30">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 bg-[#101214] hidden md:flex flex-col">
        <div className="flex h-16 items-center px-6 border-b border-white/5">
          <Link href="/admin" className="flex items-center gap-3 transition-opacity hover:opacity-80">
            <div className="relative flex size-8 items-center justify-center overflow-hidden rounded-full bg-[linear-gradient(135deg,#e92f3d_0_50%,#47c9d8_50%)]">
              <div className="absolute left-1/2 top-[22%] size-1 -translate-x-1/2 rounded-full bg-black" />
            </div>
            <span className="font-black text-sm tracking-widest text-[#48c8d8]">GAMMA ADMIN</span>
          </Link>
        </div>
        
        <nav className="flex-1 space-y-1.5 p-4">
          <Link 
            href="/admin" 
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-white/70 transition-colors hover:bg-white/5 hover:text-white"
          >
            <LayoutDashboard size={18} /> Dashboard
          </Link>
          <Link 
            href="/admin/games" 
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-white/70 transition-colors hover:bg-white/5 hover:text-white"
          >
            <Gamepad2 size={18} /> Juegos
          </Link>
          <Link 
            href="/admin/users" 
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-white/70 transition-colors hover:bg-white/5 hover:text-white"
          >
            <Users size={18} /> Usuarios
          </Link>
          <Link 
            href="/admin/settings" 
            className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-white/70 transition-colors hover:bg-white/5 hover:text-white"
          >
            <Settings size={18} /> Configuración
          </Link>
        </nav>

        <div className="p-4 border-t border-white/5">
          <Link 
            href="/" 
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-white/70 transition-colors hover:bg-white/5 hover:text-white"
          >
            <Store size={18} /> Volver a la Tienda
          </Link>
          <LogoutButton />
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        <header className="flex h-16 items-center justify-between border-b border-white/5 bg-[#101214]/50 px-6 backdrop-blur-md sticky top-0 z-10">
          <h2 className="text-sm font-bold text-white/50">Admin Workspace</h2>
          <div className="flex items-center gap-4">
            <div className="size-8 rounded-full bg-gradient-to-tr from-[#48c8d8] to-[#f3343b] p-0.5">
              <div className="size-full rounded-full bg-[#101214] border-2 border-transparent flex items-center justify-center text-xs font-bold">
                A
              </div>
            </div>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-6 lg:p-10 bg-[#0A0A0A]">
          {children}
        </div>
      </main>
    </div>
  );
}
