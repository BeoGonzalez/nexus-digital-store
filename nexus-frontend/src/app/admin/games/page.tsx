"use client";

import { useState, useEffect } from "react";
import { Plus, Search, MoreVertical, Edit, Trash2, Check, X, Loader2, Gamepad2 } from "lucide-react";
import { apiClient } from "@/lib/apiClient";
import { Product } from "@/app/page";

export default function AdminGamesPage() {
  const [games, setGames] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingGame, setEditingGame] = useState<Product | null>(null);
  const [deletingGame, setDeletingGame] = useState<Product | null>(null);

  useEffect(() => {
    fetchGames();
  }, []);

  async function fetchGames() {
    try {
      setLoading(true);
      const data = await apiClient.getGames();
      setGames(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddGame(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setSaving(true);
    try {
      const payload = {
        title: String(data.get("title")),
        description: String(data.get("description")),
        price_clp: Number(data.get("price")),
        stock: 99, // default para este mock UI
        platform_name: String(data.get("platform")),
        image_url: String(data.get("image")),
        genre_names: ["Nuevo"] // mock genre
      };
      
      const token = localStorage.getItem("nexus_token");
      if (!token) {
        alert("No estás autenticado como administrador o el token expiró.");
        return;
      }
      
      const newGame = await apiClient.createGame(payload, token);
      
      // Añadir al inicio del array de juegos local para visualización rápida
      setGames([newGame, ...games]);
      setModalOpen(false);
    } catch (error: any) {
      console.error(error);
      alert(error.message || "Error al crear el juego");
    } finally {
      setSaving(false);
    }
  }

  async function handleEditGame(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!editingGame) return;
    const data = new FormData(e.currentTarget);
    setSaving(true);
    try {
      const payload = {
        title: String(data.get("title")),
        description: String(data.get("description")),
        price_clp: Number(data.get("price")),
        stock: 99, 
        platform_name: String(data.get("platform")),
        image_url: String(data.get("image")),
      };
      
      const token = localStorage.getItem("nexus_token");
      if (!token) {
        alert("No estás autenticado como administrador o el token expiró.");
        return;
      }
      
      const updatedGame = await apiClient.updateGame(editingGame.id, payload, token);
      
      setGames(games.map(g => g.id === editingGame.id ? updatedGame : g));
      setEditingGame(null);
    } catch (error: any) {
      console.error(error);
      alert(error.message || "Error al actualizar el juego");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteConfirm() {
    if (!deletingGame) return;
    setSaving(true);
    try {
      const token = localStorage.getItem("nexus_token");
      if (!token) {
        alert("No estás autenticado como administrador o el token expiró.");
        return;
      }
      
      await apiClient.deleteGame(deletingGame.id, token);
      
      setGames(games.filter(g => g.id !== deletingGame.id));
      setDeletingGame(null);
    } catch (error: any) {
      console.error(error);
      alert(error.message || "Error al eliminar el juego");
    } finally {
      setSaving(false);
    }
  }

  const filtered = games.filter(g => g.title.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Catálogo de Juegos</h1>
          <p className="text-white/50 mt-1">Gestiona el inventario, precios y plataformas.</p>
        </div>
        <button 
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-[#48c8d8] px-6 py-3.5 text-sm font-black text-[#062029] transition-all hover:bg-[#5cdcf0] active:scale-95"
        >
          <Plus size={18} /> AÑADIR JUEGO
        </button>
      </div>

      <div className="mb-6 flex max-w-md items-center rounded-xl border border-white/10 bg-white/5 px-4 py-3">
        <Search className="mr-3 shrink-0 text-white/50" size={18} />
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar por título..."
          className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-white/40"
        />
      </div>

      <div className="rounded-3xl border border-white/5 bg-[#121418] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-white/70">
            <thead className="border-b border-white/10 bg-white/5 text-xs font-bold uppercase tracking-widest text-white/50">
              <tr>
                <th className="px-6 py-4">Juego</th>
                <th className="px-6 py-4">Plataforma</th>
                <th className="px-6 py-4">Precio</th>
                <th className="px-6 py-4">Stock</th>
                <th className="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <Loader2 size={24} className="mx-auto animate-spin text-[#48c8d8]" />
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-white/50">
                    No se encontraron juegos.
                  </td>
                </tr>
              ) : (
                filtered.map((game) => (
                  <tr key={game.id} className="transition-colors hover:bg-white/5">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-4">
                        <div className="size-12 rounded-lg bg-[#0A0A0A] overflow-hidden shrink-0 flex items-center justify-center">
                          {game.image_url || game.image ? (
                            <img src={game.image_url || game.image || ""} alt={game.title} className="w-full h-full object-cover" />
                          ) : (
                            <Gamepad2 size={20} className="text-white/20" />
                          )}
                        </div>
                        <div>
                          <div className="font-bold text-white">{game.title}</div>
                          <div className="text-xs">{game.category || "N/A"}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-bold text-[#48c8d8]">
                      {typeof game.platform === 'string' ? game.platform : game.platform?.name || "PC"}
                    </td>
                    <td className="px-6 py-4 font-medium text-white">
                      ${game.price_clp?.toLocaleString("es-CL")}
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-bold text-emerald-400">
                        <span className="size-1.5 rounded-full bg-emerald-400"></span> 99+
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button 
                          onClick={() => setEditingGame(game)}
                          className="rounded-lg p-2 text-white/50 transition-colors hover:bg-white/10 hover:text-white"
                        >
                          <Edit size={16} />
                        </button>
                        <button 
                          onClick={() => setDeletingGame(game)}
                          className="rounded-lg p-2 text-white/50 transition-colors hover:bg-[#f3343b]/10 hover:text-[#f3343b]"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md">
          <div className="w-full max-w-2xl rounded-3xl border border-white/10 bg-[#121418] p-8 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-black">Añadir Nuevo Juego</h2>
              <button onClick={() => setModalOpen(false)} className="rounded-full p-2 text-white/50 hover:bg-white/10 hover:text-white transition-colors">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAddGame} className="space-y-6">
              <div className="grid gap-6 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-bold text-white/70">TÍTULO DEL JUEGO</label>
                  <input name="title" required className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]" placeholder="Ej. Cyberpunk 2077" />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-white/70">PLATAFORMA</label>
                  <select name="platform" required className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]">
                    <option value="PC">PC</option>
                    <option value="PS5">PS5</option>
                    <option value="Xbox Series X">Xbox Series X</option>
                    <option value="Nintendo Switch">Nintendo Switch</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-xs font-bold text-white/70">DESCRIPCIÓN</label>
                <textarea name="description" rows={3} required className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]" placeholder="Sinopsis del juego..." />
              </div>

              <div className="grid gap-6 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-bold text-white/70">PRECIO (CLP)</label>
                  <input name="price" type="number" required className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]" placeholder="49990" />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-white/70">URL IMAGEN (NEON S3)</label>
                  <input name="image" type="url" required className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]" placeholder="https://..." />
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-4 mt-8 border-t border-white/10">
                <button type="button" onClick={() => setModalOpen(false)} className="rounded-xl px-6 py-3 text-sm font-bold text-white/70 hover:bg-white/5 hover:text-white transition-colors">
                  CANCELAR
                </button>
                <button type="submit" disabled={saving} className="flex items-center gap-2 rounded-xl bg-[#48c8d8] px-8 py-3 text-sm font-black text-[#062029] transition-all hover:bg-[#5cdcf0] active:scale-95 disabled:opacity-50">
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />} 
                  {saving ? "GUARDANDO..." : "GUARDAR JUEGO"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Editar Juego */}
      {editingGame && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md">
          <div className="w-full max-w-md rounded-3xl border border-white/10 bg-[#121418] p-6 shadow-2xl animate-in zoom-in-95">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="text-xl font-black text-white">Editar Juego</h3>
              <button 
                onClick={() => setEditingGame(null)}
                className="rounded-full bg-white/5 p-2 text-white/50 transition-colors hover:bg-white/10 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>
            
            <form onSubmit={handleEditGame} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-bold text-white/50">TÍTULO</label>
                <input 
                  name="title" 
                  defaultValue={editingGame.title}
                  required 
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]" 
                />
              </div>
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="mb-1.5 block text-xs font-bold text-white/50">PRECIO (CLP)</label>
                  <input 
                    name="price" 
                    type="number" 
                    defaultValue={editingGame.price_clp}
                    required 
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]" 
                  />
                </div>
                <div className="flex-1">
                  <label className="mb-1.5 block text-xs font-bold text-white/50">PLATAFORMA</label>
                  <select 
                    name="platform"
                    defaultValue={editingGame.platform?.name || "PC"}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8] appearance-none"
                  >
                    <option value="PC">PC</option>
                    <option value="PlayStation">PlayStation</option>
                    <option value="Xbox">Xbox</option>
                    <option value="Nintendo">Nintendo</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-bold text-white/50">URL IMAGEN (Neon Storage)</label>
                <input 
                  name="image" 
                  defaultValue={editingGame.image_url}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]" 
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-bold text-white/50">DESCRIPCIÓN</label>
                <textarea 
                  name="description" 
                  defaultValue={editingGame.description}
                  rows={3} 
                  required
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]" 
                />
              </div>
              
              <button 
                type="submit" 
                disabled={saving}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-[#48c8d8] py-3.5 text-sm font-black text-[#062029] transition-colors hover:bg-[#5cdcf0] disabled:opacity-50"
              >
                {saving ? <Loader2 size={18} className="animate-spin" /> : "ACTUALIZAR JUEGO"}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Modal Eliminar Juego */}
      {deletingGame && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md">
          <div className="w-full max-w-sm rounded-3xl border border-white/10 bg-[#121418] p-6 shadow-2xl animate-in zoom-in-95">
            <div className="flex items-center gap-4 mb-4 text-[#f3343b]">
              <div className="size-12 rounded-full bg-[#f3343b]/10 flex items-center justify-center shrink-0">
                <Trash2 size={24} />
              </div>
              <h3 className="text-xl font-black text-white">¿Eliminar {deletingGame.title}?</h3>
            </div>
            <p className="mb-6 text-sm text-white/60">
              Esta acción es irreversible y eliminará el juego del catálogo permanentemente.
            </p>
            <div className="flex gap-3">
              <button 
                onClick={() => setDeletingGame(null)}
                disabled={saving}
                className="flex-1 rounded-xl px-4 py-3 text-sm font-bold text-white/70 hover:bg-white/5 transition-colors"
              >
                CANCELAR
              </button>
              <button 
                onClick={handleDeleteConfirm}
                disabled={saving}
                className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-[#f3343b] px-4 py-3 text-sm font-black text-white hover:bg-[#ff4f56] transition-colors shadow-[0_0_15px_rgba(243,52,59,0.3)] disabled:opacity-50"
              >
                {saving ? <Loader2 size={18} className="animate-spin" /> : "ELIMINAR"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
