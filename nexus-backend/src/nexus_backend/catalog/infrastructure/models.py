import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from nexus_backend.shared.infrastructure.models import Base, TimestampMixin


# ──────────────────────────────────────────────────────────────
# Genre — Tabla maestra de géneros (1NF: atomicidad)
# ──────────────────────────────────────────────────────────────
# BCNF: {id} → {name}  y  {name} → {id}
# Ambos determinantes son superclaves (PK + UNIQUE).
# ──────────────────────────────────────────────────────────────
class Genre(TimestampMixin, Base):
    __tablename__ = "genres"

    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True,
    )

    video_games: Mapped[list["VideoGame"]] = relationship(
        secondary="video_game_genres", back_populates="genres",
    )

    def __repr__(self) -> str:
        return f"<Genre {self.name}>"


# ──────────────────────────────────────────────────────────────
# VideoGameGenre — Tabla de unión N:M (sin atributos no-clave)
# ──────────────────────────────────────────────────────────────
# BCNF trivial: clave compuesta (video_game_id, genre_id)
# determina la fila; no hay atributos no-clave que puedan
# generar dependencias funcionales no triviales.
# ──────────────────────────────────────────────────────────────
class VideoGameGenre(Base):
    __tablename__ = "video_game_genres"

    video_game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("video_games.id", ondelete="CASCADE"), primary_key=True,
    )
    genre_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True,
    )


# ──────────────────────────────────────────────────────────────
# VideoGame — Producto principal del catálogo
# ──────────────────────────────────────────────────────────────
# BCNF: {id} → {title, description, price_clp, stock, embedding, ...}
# Única clave candidata es `id` (PK).
# Los géneros están externalizados a video_game_genres (N:M),
# eliminando la violación de 1NF por multivalor.
#
# CHECK constraints:
# • price_clp > 0  — un videojuego debe tener precio positivo (CLP enteros)
# • stock >= 0     — stock negativo es un error de dominio
# ──────────────────────────────────────────────────────────────
class VideoGame(TimestampMixin, Base):
    __tablename__ = "video_games"
    __table_args__ = (
        CheckConstraint("price_clp > 0", name="ck_video_games_positive_price"),
        CheckConstraint("stock >= 0", name="ck_video_games_non_negative_stock"),
        Index(
            "ix_video_games_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price_clp: Mapped[int] = mapped_column(Integer, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384), nullable=True,
    )

    genres: Mapped[list["Genre"]] = relationship(
        secondary="video_game_genres", back_populates="video_games", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<VideoGame {self.title}>"
