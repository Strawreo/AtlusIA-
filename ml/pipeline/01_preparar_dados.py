# %% [markdown]
# Etapa 1 — Exploração e limpeza dos datasets
# Rode célula por célula (VS Code / Jupyter). Ajuste os caminhos se necessário.

# %%
import ast
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

MIN_VOTOS = 50  # filtra filmes muito obscuros

# %% ---------------- FILMES ----------------
filmes = pd.read_csv(RAW / "movies_metadata.csv", low_memory=False)
print(filmes.shape)
print(filmes.columns.tolist())
filmes.head(3)

# %% Limpeza do id (algumas linhas têm datas no lugar do id)
filmes["id"] = pd.to_numeric(filmes["id"], errors="coerce")
filmes = filmes.dropna(subset=["id"])
filmes["id"] = filmes["id"].astype(int)
filmes = filmes.drop_duplicates(subset="id")

filmes["vote_count"] = pd.to_numeric(filmes["vote_count"], errors="coerce").fillna(0)
filmes["vote_average"] = pd.to_numeric(filmes["vote_average"], errors="coerce")
print("Nulos em overview:", filmes["overview"].isna().sum())


# %% Converte as colunas "lista de dicionários em texto" para listas de nomes
def extrair_nomes(valor):
    """'[{"id": 28, "name": "Action"}, ...]' -> ['Action', ...]"""
    try:
        return [d["name"] for d in ast.literal_eval(valor)]
    except (ValueError, SyntaxError, TypeError):
        return []


filmes["generos"] = filmes["genres"].apply(extrair_nomes)

# %% Keywords
kw = pd.read_csv(RAW / "keywords.csv")
kw["id"] = pd.to_numeric(kw["id"], errors="coerce")
kw = kw.dropna(subset=["id"]).drop_duplicates(subset="id")
kw["id"] = kw["id"].astype(int)
kw["keywords"] = kw["keywords"].apply(extrair_nomes)

filmes = filmes.merge(kw[["id", "keywords"]], on="id", how="left")
filmes["keywords"] = filmes["keywords"].apply(lambda x: x if isinstance(x, list) else [])

# %% Filtro de qualidade
filmes = filmes[(filmes["vote_count"] >= MIN_VOTOS) & filmes["overview"].notna()]
print("Filmes após filtro:", len(filmes))

# %% Distribuição de gêneros (bom para o relatório)
filmes["generos"].explode().value_counts().head(20)


# %% Monta o texto que vai virar vetor (gêneros e keywords repetidos = mais peso)
def montar_texto(row):
    generos = " ".join(g.replace(" ", "_") for g in row["generos"])
    keywords = " ".join(k.replace(" ", "_") for k in row["keywords"])
    return f"{generos} {generos} {keywords} {row['overview']}"


filmes["texto"] = filmes.apply(montar_texto, axis=1)

colunas = ["id", "imdb_id", "title", "release_date", "vote_average", "vote_count",
           "generos", "keywords", "overview", "poster_path", "texto"]
filmes[colunas].reset_index(drop=True).to_parquet(OUT / "filmes.parquet")
print("Salvo:", OUT / "filmes.parquet")

# %% ---------------- MÚSICAS ----------------
musicas = pd.read_csv(RAW / "dataset.csv")
print(musicas.shape)
print(musicas.columns.tolist())
musicas.head(3)

# %% A mesma faixa aparece em vários gêneros -> deduplica
print("Linhas:", len(musicas), "| track_id únicos:", musicas["track_id"].nunique())
musicas = musicas.dropna(subset=["track_name", "artists"])
musicas = musicas.sort_values("popularity", ascending=False).drop_duplicates("track_id")
print("Após deduplicar:", len(musicas))

# %% Gêneros disponíveis (útil para o mapeamento tag do jogo -> música)
print(sorted(musicas["track_genre"].unique()))

# %% Audio features que vão ser usadas no KNN
FEATURES = ["danceability", "energy", "valence", "acousticness",
            "instrumentalness", "speechiness", "liveness", "tempo", "loudness"]
musicas[FEATURES].describe().T

# %% Média das features por gênero (ajuda a montar o mapeamento heurístico)
musicas.groupby("track_genre")[["energy", "valence", "acousticness", "tempo"]].mean() \
    .sort_values("energy").round(2)

# %% Salva
colunas_m = ["track_id", "track_name", "artists", "album_name", "popularity",
             "track_genre"] + FEATURES
musicas[colunas_m].reset_index(drop=True).to_parquet(OUT / "musicas.parquet")
print("Salvo:", OUT / "musicas.parquet")