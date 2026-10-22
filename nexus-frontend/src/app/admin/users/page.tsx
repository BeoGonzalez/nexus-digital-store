"use client";

import React from "react";
import { Users, Search, Loader2 } from "lucide-react";

export default function AdminUsersPage() {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Usuarios</h1>
          <p className="text-white/50 mt-1">Gestiona las cuentas de clientes y administradores.</p>
        </div>
      </div>

      <div className="mb-6 flex max-w-md items-center rounded-xl border border-white/10 bg-white/5 px-4 py-3">
        <Search className="mr-3 shrink-0 text-white/50" size={18} />
        <input
          placeholder="Buscar por email o nombre..."
          className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-white/40"
        />
      </div>

      <div className="flex h-64 flex-col items-center justify-center rounded-3xl border border-white/5 bg-[#121418] text-center">
        <div className="mb-4 flex size-16 items-center justify-center rounded-full bg-white/5 text-white/40">
          <Users size={32} />
        </div>
        <h3 className="text-lg font-bold text-white">Módulo en Construcción</h3>
        <p className="mt-2 max-w-sm text-sm text-white/50">
          La gestión de usuarios mediante Amazon Cognito estará disponible en una próxima actualización.
        </p>
      </div>
    </div>
  );
}
