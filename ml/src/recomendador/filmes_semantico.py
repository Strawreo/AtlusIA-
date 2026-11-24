"""Recomendador SEMÂNTICO de filmes baseado em alinhamento léxico (TF-IDF)
e projeção em dimensões latentes de gênero (IMDb).

Migrado e modularizado a partir de ml/notebooks/ModeloProjeto.ipynb.

Arquitetura e Fluxo de Inferência:
1. Jogos e filmes compartilham um espaço vetorial léxico TF-IDF de 13.916 termos.
2. Um classificador multi-rótulo projeta ambos em 21 dimensões contínuas de gênero.
3. Para uma biblioteca de jogos do usuário:
   - Extrai os appIDs e pondera pelo tempo de jogo: peso = log(1 + horas) + 0.5.
   - Gera os centróides normalizados no espaço léxico (u_texto) e de gênero (u_genero).
4. Similaridades de cosseno:
   - sim_texto = X_filmes @ u_texto.T
   - sim_genero = G_filmes @ u_genero.T
   - Score = alpha * sim_texto + (1 - alpha) * sim_genero + beta * rating_norm
5. Filtro de elegibilidade (votes >= 1000) e ordenação Top-K em < 15 ms.
6. Geração de justificativas explicativas ("por_que" / "because") com os termos e
   gêneros de maior contribuição no produto vetorial.
"""

from collections.abc import Sequence
import logging
import math
from pathlib import Path
from typing import Any
import warnings

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)

DEFAULT_ALPHA = 0.50
DEFAULT_BETA = 0.15
DEFAULT_MIN_VOTOS = 1000

GENEROS_IMDB_PADRAO = [
    "Action", "Adventure", "Animation", "Biography", "Comedy", "Crime",
    "Documentary", "Drama", "Family", "Fantasy", "History", "Horror",
    "Music", "Musical", "Mystery", "Romance", "Sci-Fi", "Sport",
    "Thriller", "War", "Western",
]


class RecomendadorSemantico:
    """Motor de recomendação semântico e léxico para filmes baseado em perfil Steam."""

    def __init__(
        self,
        caminho_modelo: Path | str,
        alpha: float = DEFAULT_ALPHA,
        beta: float = DEFAULT_BETA,
        min_votos: int = DEFAULT_MIN_VOTOS,
    ) -> None:
        self.caminho = Path(caminho_modelo)
        self.alpha = alpha
        self.beta = beta
        self.min_votos = min_votos

        self._carregar_artefatos()

    def _carregar_artefatos(self) -> None:
        arquivos_necessarios = [
            "X_jogos.npz",
            "X_filmes.npz",
            "G_jogos.npy",
            "G_filmes.npy",
            "artefatos_modelo.joblib",
            "catalogo_jogos.parquet",
            "catalogo_filmes.parquet",
        ]
        faltando = [
            arq for arq in arquivos_necessarios
            if not (self.caminho / arq).is_file()
        ]
        if faltando:
            raise FileNotFoundError(
                f"Artefatos do modelo ausentes em '{self.caminho}': {', '.join(faltando)}"
            )

        logger.info("Carregando artefatos do modelo de %s...", self.caminho)
        self.X_jogos = sparse.load_npz(self.caminho / "X_jogos.npz")
        self.X_filmes = sparse.load_npz(self.caminho / "X_filmes.npz")
        self.G_jogos = np.load(self.caminho / "G_jogos.npy")
        self.G_filmes = np.load(self.caminho / "G_filmes.npy")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            artefatos = joblib.load(self.caminho / "artefatos_modelo.joblib")

        self.vocab = artefatos.get("vocab", [])
        mlb = artefatos.get("mlb")
        if mlb is not None and hasattr(mlb, "classes_"):
            self.classes = list(mlb.classes_)
        else:
            self.classes = artefatos.get("classes", GENEROS_IMDB_PADRAO)

        config = artefatos.get("config", {})
        self.alpha = config.get("ALPHA", self.alpha)
        self.beta = config.get("BETA", self.beta)
        self.min_votos = config.get("MIN_VOTOS_FILME", self.min_votos)

        self.jogos = pd.read_parquet(self.caminho / "catalogo_jogos.parquet")
        self.filmes = pd.read_parquet(self.caminho / "catalogo_filmes.parquet")

        # Mapeamento rápido appID -> índice de linha
        self.appid_to_idx = pd.Series(
            self.jogos.index.values, index=self.jogos["appID"]
        ).to_dict()

        # Mapeamento auxiliar por nome em minúsculas
        if "name" in self.jogos.columns:
            self.name_to_idx = pd.Series(
                self.jogos.index.values, index=self.jogos["name"].astype(str).str.lower()
            ).to_dict()
        else:
            self.name_to_idx = {}

        # Pré-cálculo de elegibilidade e nota normalizada
        votos = self.filmes["votes"].fillna(0).to_numpy()
        self.elegivel_filme = (votos >= self.min_votos).astype(bool)

        rating = pd.to_numeric(self.filmes["rating"], errors="coerce").fillna(5.0).to_numpy()
        self.rating_norm = np.clip((rating - 5.0) / 5.0, 0.0, 1.0)
        logger.info(
            "Modelo semântico pronto: %d jogos, %d filmes.",
            len(self.jogos),
            len(self.filmes),
        )

    def recomendar(
        self,
        biblioteca_steam: Sequence[Any],
        top_k: int = 10,
        alpha: float | None = None,
        beta: float | None = None,
        generos_excluir: Sequence[str] | None = None,
    ) -> pd.DataFrame:
        """Recomenda filmes a partir de uma lista de jogos da Steam.

        Aceita:
        - Lista de tuplas: [(appid, horas), ...]
        - Lista de dicts: [{'appid': 1245620, 'horas': 100.0, 'nome': 'Elden Ring'}, ...]
        - Lista de appIDs inteiros: [1245620, 292030, ...]
        """
        if not biblioteca_steam:
            raise ValueError("A biblioteca informada está vazia.")

        a = self.alpha if alpha is None else alpha
        b = self.beta if beta is None else beta

        itens: list[tuple[int, float]] = []
        for item in biblioteca_steam:
            appid = None
            horas = 1.0
            nome = None

            if isinstance(item, dict):
                appid = item.get("appid") or item.get("appID")
                horas = float(item.get("horas", item.get("hours_played", 1.0)))
                nome = item.get("nome") or item.get("name")
            elif isinstance(item, (tuple, list)):
                appid = item[0]
                horas = float(item[1]) if len(item) > 1 else 1.0
            else:
                appid = item
                horas = 1.0

            idx = None
            if appid is not None:
                try:
                    appid_int = int(appid)
                    idx = self.appid_to_idx.get(appid_int)
                except (ValueError, TypeError):
                    pass

            if idx is None and nome:
                idx = self.name_to_idx.get(str(nome).strip().lower())

            if idx is not None:
                peso = np.log1p(max(horas, 0.0)) + 0.5
                itens.append((idx, peso))

        if not itens:
            raise ValueError("Nenhum jogo do perfil foi encontrado no catálogo do modelo.")

        idxs = [i for i, _ in itens]
        pesos = np.array([w for _, w in itens], dtype=np.float32).reshape(-1, 1)

        # 1) Centróides do perfil do usuário (texto + gênero)
        u_texto = normalize(np.asarray(self.X_jogos[idxs].multiply(pesos).sum(axis=0)))
        u_genero = normalize((self.G_jogos[idxs] * pesos).sum(axis=0, keepdims=True))

        # 2) Similaridades contra o catálogo de filmes
        sim_texto = np.asarray(self.X_filmes @ u_texto.T).ravel()
        sim_genero = (self.G_filmes @ u_genero.T).ravel()

        score_final = a * sim_texto + (1.0 - a) * sim_genero + b * self.rating_norm

        # 3) Filtros de elegibilidade
        mascara = self.elegivel_filme.copy()
        if generos_excluir:
            excluir = set(generos_excluir)
            mascara &= ~self.filmes["genres"].map(
                lambda gs: bool(excluir.intersection(gs if isinstance(gs, (list, set)) else []))
            ).to_numpy()

        score_final = np.where(mascara, score_final, -np.inf)

        # Top-K
        k = min(top_k, int(mascara.sum()))
        if k <= 0:
            return pd.DataFrame()

        top_idx = np.argpartition(-score_final, k)[:k]
        top_idx = top_idx[np.argsort(-score_final[top_idx])]

        # 4) Monta resultado e justificativas
        u_texto_arr = np.asarray(u_texto).ravel()
        u_gen_arr = u_genero.ravel()
        resultados = []

        for i in top_idx:
            contrib_termos = u_texto_arr * self.X_filmes[i].toarray().ravel()
            top_t = [self.vocab[t] for t in np.argsort(-contrib_termos)[:3] if contrib_termos[t] > 0]

            contrib_gen = u_gen_arr * self.G_filmes[i]
            top_g = [self.classes[g] for g in np.argsort(-contrib_gen)[:2] if contrib_gen[g] > 0]

            genres_val = self.filmes.at[i, "genres"]
            if hasattr(genres_val, "tolist"):
                genres_list = genres_val.tolist()
            elif isinstance(genres_val, list):
                genres_list = genres_val
            elif isinstance(genres_val, str):
                genres_list = [g.strip() for g in genres_val.split(",") if g.strip()]
            else:
                genres_list = []

            rel_date = self.filmes.at[i, "release_date"]
            year_val = None
            if pd.notna(rel_date):
                if hasattr(rel_date, "year"):
                    year_val = int(rel_date.year)
                elif str(rel_date)[:4].isdigit():
                    year_val = int(str(rel_date)[:4])

            because_list = []
            if top_g:
                because_list.append(f"Gêneros: {', '.join(top_g)}")
            if top_t:
                because_list.append(f"Temas: {', '.join(top_t)}")

            por_que_str = " | ".join(because_list)
            movie_id = str(self.filmes.at[i, "id"])

            resultados.append({
                "id": movie_id,
                "title": str(self.filmes.at[i, "title"]),
                "year": year_val,
                "genres": genres_list,
                "rating": float(self.filmes.at[i, "rating"]) if pd.notna(self.filmes.at[i, "rating"]) else None,
                "score": round(float(score_final[i]), 4),
                "sim_texto": round(float(sim_texto[i]), 3),
                "sim_genero": round(float(sim_genero[i]), 3),
                "por_que": por_que_str,
                "porque": por_que_str,
                "because": because_list,
                "movie_link": f"https://www.imdb.com/title/{movie_id}/",
            })

        return pd.DataFrame(resultados)
