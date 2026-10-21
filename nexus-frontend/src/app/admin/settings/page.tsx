"use client";

import { Settings, Save } from "lucide-react";

export default function AdminSettingsPage() {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Configuración</h1>
          <p className="text-white/50 mt-1">Preferencias generales del e-commerce.</p>
        </div>
        <button 
          className="flex items-center gap-2 rounded-xl bg-[#48c8d8] px-6 py-3.5 text-sm font-black text-[#062029] transition-all hover:bg-[#5cdcf0] active:scale-95 opacity-50 cursor-not-allowed"
        >
          <Save size={18} /> GUARDAR CAMBIOS
        </button>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-3xl border border-white/5 bg-[#121418] p-6">
          <div className="mb-6 flex items-center gap-3 text-white">
            <div className="rounded-lg bg-white/5 p-2 text-white/50">
              <Settings size={20} />
            </div>
            <h2 className="text-lg font-bold">Información de la Tienda</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-bold text-white/50">NOMBRE DE LA TIENDA</label>
              <input 
                defaultValue="Gamma Game Store"
                disabled
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/50 outline-none cursor-not-allowed" 
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-bold text-white/50">MONEDA PRINCIPAL</label>
              <select 
                disabled
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/50 outline-none appearance-none cursor-not-allowed"
              >
                <option>CLP - Peso Chileno</option>
                <option>USD - Dólar Estadounidense</option>
              </select>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-center justify-center rounded-3xl border border-white/5 bg-[#121418] p-6 text-center">
          <p className="max-w-sm text-sm text-white/50">
            Las opciones de configuración globales estarán habilitadas una vez que finalicemos la integración de las preferencias del sistema.
          </p>
        </div>
      </div>
    </div>
  );
}
