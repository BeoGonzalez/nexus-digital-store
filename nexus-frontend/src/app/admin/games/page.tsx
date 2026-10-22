"use client";

import React, { useState, useEffect, type FormEvent, type ChangeEvent, type MouseEvent } from "react";
import { Plus, Search, Edit, Trash2, Check, X, Loader2, Gamepad2, AlertTriangle, Image as ImageIcon } from "lucide-react";
import { apiClient } from "@/lib/apiClient";
import { Product } from "@/app/page";

const AVAILABLE_GENRES = [
  "RPG",
  "Acción",
  "Aventura",
  "Shooter",
  "Estrategia",
  "Deportes",
  "Simulación",
  "Terror / Survival",
  "Lucha",
  "Mundo Abierto"
];

const PLATFORMS = ["PC", "PS5", "Xbox Series X", "Nintendo Switch"];

export default function AdminGamesPage() {
  const [games, setGames] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingGame, setEditingGame] = useState<Product | null>(null);
  const [deletingGame, setDeletingGame] = useState<Product | null>(null);

  // Estados para preview de imagen en modales
  const [addImagePreview, setAddImagePreview] = useState("");
  const [editImagePreview, setEditImagePreview] = useState("");

  useEffect(() => {
    fetchGames();
  }, []);

  async function fetchGames() {
    try {
      setLoading(true);
      const data = await apiClient.getGames();
      setGames(data);
    } catch (e) {
      console.error("Error al cargar juegos:", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleAddGame(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    setSaving(true);
    try {
      const token = localStorage.getItem("nexus_token");
      if (!token) {
        alert("Sesión no iniciada o token expirado. Por favor ingresa nuevamente.");
        return;
      }

      const selectedGenre = String(data.get("genre") || "Acción");
      const customGenre = String(data.get("custom_genre") || "").trim();
      const genre = customGenre || selectedGenre;

      const payload = {
        title: String(data.get("title")),
        description: String(data.get("description")),
        price_clp: Number(data.get("price")),
        stock: Number(data.get("stock") ?? 0),
        platform_name: String(data.get("platform")),
        image_url: String(data.get("image")),
        genre_names: [genre],
      };

      const newGame = await apiClient.createGame(payload, token);
      setGames([newGame, ...games]);
      setModalOpen(false);
      setAddImagePreview("");
    } catch (error: any) {
      console.error(error);
      alert(error.message || "Error al crear el producto en el catálogo");
    } finally {
      setSaving(false);
    }
  }

  async function handleEditGame(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!editingGame) return;
    const data = new FormData(e.currentTarget);
    setSaving(true);
    try {
      const token = localStorage.getItem("nexus_token");
      if (!token) {
        alert("Sesión no iniciada o token expirado.");
        return;
      }

      const selectedGenre = String(data.get("genre") || "Acción");
      const customGenre = String(data.get("custom_genre") || "").trim();
      const genre = customGenre || selectedGenre;

      const payload = {
        title: String(data.get("title")),
        description: String(data.get("description")),
        price_clp: Number(data.get("price")),
        stock: Number(data.get("stock") ?? 0),
        platform_name: String(data.get("platform")),
        image_url: String(data.get("image")),
        genre_names: [genre],
      };

      const updatedGame = await apiClient.updateGame(editingGame.id, payload, token);
      setGames(games.map((g: Product) => (g.id === editingGame.id ? updatedGame : g)));
      setEditingGame(null);
    } catch (error: any) {
      console.error(error);
      alert(error.message || "Error al actualizar el producto");
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
        alert("Sesión no iniciada o token expirado.");
        return;
      }

      await apiClient.deleteGame(deletingGame.id, token);
      setGames(games.filter((g: Product) => g.id !== deletingGame.id));
      setDeletingGame(null);
    } catch (error: any) {
      console.error(error);
      alert(error.message || "Error al eliminar el producto");
    } finally {
      setSaving(false);
    }
  }

  async function handleQuickStockZero(game: Product) {
    const token = localStorage.getItem("nexus_token");
    if (!token) return;
    try {
      const updated = await apiClient.updateGame(game.id, { stock: 0 }, token);
      setGames(games.map((g: Product) => (g.id === game.id ? { ...g, stock: 0 } : g)));
    } catch (err: any) {
      alert("Error al actualizar stock: " + (err.message || ""));
    }
  }

  const filtered = games.filter(
    (g: Product) =>
      g.title.toLowerCase().includes(search.toLowerCase()) ||
      (g.category && g.category.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-white">Catálogo de Productos</h1>
          <p className="text-white/50 mt-1">
            Administra nombres, imágenes S3, roles/géneros, stocks y descripciones en Aurora PostgreSQL.
          </p>
        </div>
        <button
          onClick={() => {
            setAddImagePreview("");
            setModalOpen(true);
          }}
          className="flex items-center gap-2 rounded-xl bg-[#48c8d8] px-6 py-3.5 text-sm font-black text-[#062029] transition-all hover:bg-[#5cdcf0] active:scale-95 shadow-[0_0_20px_rgba(72,200,216,0.3)]"
        >
          <Plus size={18} /> AÑADIR PRODUCTO
        </button>
      </div>

      <div className="mb-6 flex max-w-md items-center rounded-xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-md">
        <Search className="mr-3 shrink-0 text-white/50" size={18} />
        <input
          value={search}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
          placeholder="Buscar por título o género/rol..."
          className="min-w-0 flex-1 bg-transparent text-sm text-white outline-none placeholder:text-white/40"
        />
      </div>

      <div className="rounded-3xl border border-white/5 bg-[#121418] overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-white/70">
            <thead className="border-b border-white/10 bg-white/5 text-xs font-bold uppercase tracking-widest text-white/50">
              <tr>
                <th className="px-6 py-4">Juego / Nombre</th>
                <th className="px-6 py-4">Rol / Género</th>
                <th className="px-6 py-4">Plataforma</th>
                <th className="px-6 py-4">Precio (CLP)</th>
                <th className="px-6 py-4">Stock</th>
                <th className="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16 text-center">
                    <Loader2 size={28} className="mx-auto animate-spin text-[#48c8d8]" />
                    <p className="mt-3 text-xs text-white/40 font-mono">Cargando catálogo desde Aurora...</p>
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-16 text-center text-white/50">
                    No se encontraron videojuegos en el catálogo.
                  </td>
                </tr>
              ) : (
                filtered.map((game: Product) => {
                  const stockNumber = Number(game.stock ?? 0);
                  const isOutOfStock = stockNumber <= 0;
                  return (
                    <tr key={game.id} className="transition-colors hover:bg-white/5">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-4">
                          <div className="size-14 rounded-xl bg-[#0A0A0A] border border-white/10 overflow-hidden shrink-0 flex items-center justify-center">
                            {game.image_url || game.image ? (
                              <img
                                src={game.image_url || game.image || ""}
                                alt={game.title}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <Gamepad2 size={24} className="text-white/20" />
                            )}
                          </div>
                          <div>
                            <div className="font-bold text-white text-base">{game.title}</div>
                            <div className="text-xs text-white/40 line-clamp-1 max-w-xs">{game.description}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex rounded-md bg-white/5 border border-white/10 px-2.5 py-1 text-xs font-semibold text-white/80">
                          {game.category || (Array.isArray(game.genres) && game.genres[0]?.name) || "Acción"}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-bold text-[#48c8d8]">
                        {typeof game.platform === "string" ? game.platform : game.platform?.name || "PC"}
                      </td>
                      <td className="px-6 py-4 font-bold text-white">
                        ${game.price_clp?.toLocaleString("es-CL")}
                      </td>
                      <td className="px-6 py-4">
                        {isOutOfStock ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/10 px-3 py-1 text-xs font-bold text-red-400 border border-red-500/20">
                            <span className="size-1.5 rounded-full bg-red-400"></span> Agotado (0)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-400 border border-emerald-500/20">
                            <span className="size-1.5 rounded-full bg-emerald-400"></span> {stockNumber} disp.
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            title="Editar producto"
                            onClick={() => {
                              setEditingGame(game);
                              setEditImagePreview(game.image_url || game.image || "");
                            }}
                            className="rounded-lg p-2.5 text-white/60 transition-colors hover:bg-white/10 hover:text-white"
                          >
                            <Edit size={16} />
                          </button>
                          <button
                            title="Eliminar producto"
                            onClick={() => setDeletingGame(game)}
                            className="rounded-lg p-2.5 text-white/60 transition-colors hover:bg-red-500/10 hover:text-red-400"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* MODAL: AÑADIR PRODUCTO */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md overflow-y-auto">
          <div className="w-full max-w-2xl rounded-3xl border border-white/10 bg-[#121418] p-8 shadow-2xl animate-in zoom-in-95 my-8">
            <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
              <div>
                <h2 className="text-2xl font-black text-white">Añadir Nuevo Producto</h2>
                <p className="text-xs text-white/50 mt-1">Ingresa los datos para registrar el juego en el catálogo.</p>
              </div>
              <button
                onClick={() => setModalOpen(false)}
                className="rounded-full p-2 text-white/50 hover:bg-white/10 hover:text-white transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleAddGame} className="space-y-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div>
                  <label className="mb-2 block text-xs font-bold text-white/70">NOMBRE DEL JUEGO *</label>
                  <input
                    name="title"
                    required
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                    placeholder="Ej. Cyberpunk 2077"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-white/70">ROL / GÉNERO DE JUEGO *</label>
                  <select
                    name="genre"
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                  >
                    {AVAILABLE_GENRES.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-xs font-bold text-white/70">DESCRIPCIÓN DEL JUEGO *</label>
                <textarea
                  name="description"
                  rows={3}
                  required
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                  placeholder="Sinopsis, características y mecánicas del juego..."
                />
              </div>

              <div className="grid gap-5 sm:grid-cols-3">
                <div>
                  <label className="mb-2 block text-xs font-bold text-white/70">PRECIO (CLP) *</label>
                  <input
                    name="price"
                    type="number"
                    min="1"
                    required
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                    placeholder="39990"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-white/70">STOCK DISPONIBLE *</label>
                  <input
                    name="stock"
                    type="number"
                    min="0"
                    defaultValue={50}
                    required
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                    placeholder="50"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-xs font-bold text-white/70">PLATAFORMA *</label>
                  <select
                    name="platform"
                    className="w-full rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                  >
                    {PLATFORMS.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-xs font-bold text-white/70">URL IMAGEN (S3 Bucket / Web) *</label>
                <div className="flex gap-4 items-start">
                  <input
                    name="image"
                    type="url"
                    required
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setAddImagePreview(e.target.value)}
                    className="flex-1 rounded-xl border border-white/10 bg-black/40 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                    placeholder="https://bucket.s3.amazonaws.com/covers/juego.jpg"
                  />
                  <div className="size-16 rounded-xl border border-white/10 bg-black/60 overflow-hidden shrink-0 flex items-center justify-center">
                    {addImagePreview ? (
                      <img src={addImagePreview} alt="Preview" className="w-full h-full object-cover" onError={() => setAddImagePreview("")} />
                    ) : (
                      <ImageIcon size={20} className="text-white/20" />
                    )}
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-4 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="rounded-xl px-6 py-3 text-sm font-bold text-white/70 hover:bg-white/5 hover:text-white transition-colors"
                >
                  CANCELAR
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 rounded-xl bg-[#48c8d8] px-8 py-3 text-sm font-black text-[#062029] transition-all hover:bg-[#5cdcf0] active:scale-95 disabled:opacity-50"
                >
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
                  {saving ? "GUARDANDO..." : "GUARDAR EN CATÁLOGO"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: EDITAR PRODUCTO & STOCK */}
      {editingGame && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-md overflow-y-auto">
          <div className="w-full max-w-2xl rounded-3xl border border-white/10 bg-[#121418] p-8 shadow-2xl animate-in zoom-in-95 my-8">
            <div className="mb-6 flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <h3 className="text-2xl font-black text-white">Editar Producto</h3>
                <p className="text-xs text-white/50 mt-1">Modifica nombre, stock, imagen, rol o descripción.</p>
              </div>
              <button
                onClick={() => setEditingGame(null)}
                className="rounded-full bg-white/5 p-2 text-white/50 transition-colors hover:bg-white/10 hover:text-white"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleEditGame} className="space-y-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs font-bold text-white/60">NOMBRE DEL JUEGO *</label>
                  <input
                    name="title"
                    defaultValue={editingGame.title}
                    required
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-bold text-white/60">ROL / GÉNERO *</label>
                  <select
                    name="genre"
                    defaultValue={editingGame.category || (Array.isArray(editingGame.genres) && editingGame.genres[0]?.name) || "Acción"}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                  >
                    {AVAILABLE_GENRES.map((g) => (
                      <option key={g} value={g}>
                        {g}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-bold text-white/60">DESCRIPCIÓN DEL JUEGO *</label>
                <textarea
                  name="description"
                  defaultValue={editingGame.description}
                  rows={3}
                  required
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                />
              </div>

              <div className="grid gap-5 sm:grid-cols-3">
                <div>
                  <label className="mb-1.5 block text-xs font-bold text-white/60">PRECIO (CLP) *</label>
                  <input
                    name="price"
                    type="number"
                    min="1"
                    defaultValue={editingGame.price_clp}
                    required
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                  />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="block text-xs font-bold text-white/60">STOCK DISPONIBLE</label>
                    <button
                      type="button"
                      onClick={(e: MouseEvent<HTMLButtonElement>) => {
                        const input = (e.currentTarget.parentElement?.nextElementSibling as HTMLInputElement);
                        if (input) input.value = "0";
                      }}
                      className="text-[10px] font-bold text-red-400 hover:text-red-300 transition-colors"
                    >
                      Vaciar (0)
                    </button>
                  </div>
                  <input
                    name="stock"
                    type="number"
                    min="0"
                    defaultValue={editingGame.stock ?? 0}
                    required
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                  />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-bold text-white/60">PLATAFORMA</label>
                  <select
                    name="platform"
                    defaultValue={typeof editingGame.platform === "string" ? editingGame.platform : editingGame.platform?.name || "PC"}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                  >
                    {PLATFORMS.map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-bold text-white/60">URL IMAGEN (S3 Bucket)</label>
                <div className="flex gap-4 items-start">
                  <input
                    name="image"
                    defaultValue={editingGame.image_url || editingGame.image}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => setEditImagePreview(e.target.value)}
                    className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none focus:border-[#48c8d8]"
                  />
                  <div className="size-16 rounded-xl border border-white/10 bg-black/60 overflow-hidden shrink-0 flex items-center justify-center">
                    {editImagePreview ? (
                      <img src={editImagePreview} alt="Preview" className="w-full h-full object-cover" onError={() => setEditImagePreview("")} />
                    ) : (
                      <ImageIcon size={20} className="text-white/20" />
                    )}
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setEditingGame(null)}
                  className="rounded-xl px-5 py-3 text-sm font-bold text-white/70 hover:bg-white/5 transition-colors"
                >
                  CANCELAR
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 rounded-xl bg-[#48c8d8] px-8 py-3 text-sm font-black text-[#062029] transition-all hover:bg-[#5cdcf0] active:scale-95 disabled:opacity-50"
                >
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
                  {saving ? "ACTUALIZANDO..." : "ACTUALIZAR JUEGO"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: ELIMINAR PRODUCTO */}
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
              Esta acción eliminará el producto del catálogo de Aurora PostgreSQL permanentemente.
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
