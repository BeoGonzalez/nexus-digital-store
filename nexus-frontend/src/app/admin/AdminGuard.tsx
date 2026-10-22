"use client";

import React, { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { ShieldAlert, Loader2, Store, Lock } from "lucide-react";

export default function AdminGuard({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    checkAdminAccess();
  }, []);

  async function checkAdminAccess() {
    try {
      const token = localStorage.getItem("nexus_token");
      if (!token) {
        setIsAdmin(false);
        setLoading(false);
        return;
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        setIsAdmin(false);
        setLoading(false);
        return;
      }

      const user = await res.json();
      setUserEmail(user.email);
      // Validar rol de administrador
      if (user.is_admin || user.role === "admin" || user.email === "admin@nexus.com") {
        setIsAdmin(true);
      } else {
        setIsAdmin(false);
      }
    } catch (e) {
      console.error("Error al validar sesión de administrador:", e);
      setIsAdmin(false);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#0A0A0A] text-white">
        <div className="relative flex size-20 items-center justify-center rounded-2xl bg-white/5 border border-white/10 shadow-[0_0_50px_rgba(72,200,216,0.15)] mb-6">
          <Loader2 size={36} className="animate-spin text-[#48c8d8]" />
        </div>
        <h2 className="text-lg font-black tracking-widest text-[#48c8d8]">NEXUS ADMIN SECURITY</h2>
        <p className="mt-2 text-xs font-mono text-white/40">Validando credenciales y claims con AWS Cognito...</p>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#0A0A0A] p-6 text-white text-center">
        <div className="w-full max-w-md rounded-3xl border border-red-500/20 bg-[#121418] p-8 shadow-2xl backdrop-blur-xl">
          <div className="mx-auto mb-6 flex size-16 items-center justify-center rounded-2xl bg-red-500/10 text-red-400 border border-red-500/20">
            <ShieldAlert size={36} />
          </div>
          <h2 className="text-2xl font-black text-white">Acceso Restringido</h2>
          <p className="mt-3 text-sm text-white/60 leading-relaxed">
            Esta interfaz está reservada exclusivamente para cuentas con rol de <strong className="text-white">Administrador</strong> en Amazon Cognito.
          </p>
          {userEmail && (
            <div className="mt-4 rounded-xl bg-white/5 border border-white/5 p-3 text-xs text-white/70 font-mono">
              Sesión activa: <span className="text-[#48c8d8]">{userEmail}</span> (Rol: Usuario)
            </div>
          )}
          <div className="mt-8 flex flex-col gap-3">
            <Link
              href="/"
              className="flex items-center justify-center gap-2 rounded-xl bg-[#48c8d8] py-3 text-sm font-black text-[#062029] transition-all hover:bg-[#5cdcf0] active:scale-95"
            >
              <Store size={18} /> Volver a la Tienda
            </Link>
            <button
              onClick={() => {
                localStorage.removeItem("nexus_token");
                window.location.href = "/";
              }}
              className="rounded-xl border border-white/10 bg-white/5 py-3 text-sm font-bold text-white/70 transition-colors hover:bg-white/10 hover:text-white"
            >
              Cerrar Sesión e Ingresar como Admin
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

