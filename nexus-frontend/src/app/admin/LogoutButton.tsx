"use client";

import { useState } from "react";
import { LogOut, X, AlertTriangle } from "lucide-react";

export default function LogoutButton() {
  const [showConfirm, setShowConfirm] = useState(false);

  function handleLogout() {
    localStorage.removeItem("nexus_token");
    window.location.href = "/";
  }

  return (
    <>
      <button 
        onClick={() => setShowConfirm(true)}
        className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-[#f3343b] transition-colors hover:bg-[#f3343b]/10"
      >
        <LogOut size={18} /> Cerrar Sesión
      </button>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md">
          <div className="w-full max-w-sm rounded-3xl border border-white/10 bg-[#121418] p-6 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center gap-4 mb-4 text-[#f3343b]">
              <div className="size-12 rounded-full bg-[#f3343b]/10 flex items-center justify-center">
                <AlertTriangle size={24} />
              </div>
              <h3 className="text-xl font-black text-white">¿Cerrar sesión?</h3>
            </div>
            <p className="mb-6 text-sm text-white/60">
              ¿Estás seguro de que deseas cerrar sesión? Tendrás que volver a ingresar tus credenciales para acceder al panel de administración.
            </p>
            <div className="flex gap-3">
              <button 
                onClick={() => setShowConfirm(false)}
                className="flex-1 rounded-xl px-4 py-3 text-sm font-bold text-white/70 hover:bg-white/5 transition-colors"
              >
                CANCELAR
              </button>
              <button 
                onClick={handleLogout}
                className="flex-1 rounded-xl bg-[#f3343b] px-4 py-3 text-sm font-black text-white hover:bg-[#ff4f56] transition-colors shadow-[0_0_15px_rgba(243,52,59,0.3)]"
              >
                SÍ, CERRAR SESIÓN
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
