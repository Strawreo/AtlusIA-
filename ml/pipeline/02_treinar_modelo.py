"""Pipeline de Treinamento e Exportação do Modelo Semântico.

Modularizado a partir da seção 2 do notebook ModeloProjeto.ipynb.

Passo a passo:
1. Carrega steam_tratado.parquet e filmes_tratado.parquet.
2. Monta o texto de cada item (gêneros + tags/keywords + sinopse).
3. Ajusta o TF-IDF conjunto e filtra o vocabulário compartilhado (frequência >= 5 em ambos).
4. Treina o classificador de 21 gêneros do IMDb (OneVsRestClassifier + LogisticRegression).
5. Pré-computa e projeta as matrizes X_jogos, X_filmes, G_jogos, G_filmes.
6. Exporta os 7 artefatos finais para ml/artifacts/modelo_final/.
"""

import argparse
import os
from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer, normalize

ALPHA = 0.50
BETA = 0.15
MIN_VOTOS_FILME = 1000
MIN_OCORRENCIAS = 5

GENEROS_IMDB = [
    "Action", "Adventure", "Animation", "Biography", "Comedy", "Crime",
    "Documentary", "Drama", "Family", "Fantasy", "History", "Horror",
    "Music", "Musical", "Mystery", "Romance", "Sci-Fi", "Sport",
    "Thriller", "War", "Western",
]


def montar_texto(generos, tags, descricao, peso=2):
    rotulos = ", ".join(generos + tags)
    partes = [rotulos] * peso if rotulos else []
    if descricao:
        partes.append(str(descricao))
    return ". ".join(partes)


def treinar_modelo(caminho_steam: Path, caminho_filmes: Path, pasta_saida: Path):
    print(f"Lendo base Steam de {caminho_steam}...")
    df_steam = pd.read_parquet(caminho_steam)
    print(f"Lendo base Filmes de {caminho_filmes}...")
    df_filmes = pd.read_parquet(caminho_filmes)

    # 1. Filtros básicos
    jogos = df_steam.dropna(subset=["appID", "name"]).copy().reset_index(drop=True)
    filmes = df_filmes.dropna(subset=["id", "title"]).copy().reset_index(drop=True)

    print(f"Jogos elegíveis: {len(jogos):,}, Filmes elegíveis: {len(filmes):,}")

    # 2. Textos
    if "texto_modelo" not in jogos.columns or jogos["texto_modelo"].isna().all():
        jogos["texto_modelo"] = jogos["name"].fillna("")
    
    filmes["texto_modelo"] = filmes.apply(
        lambda r: montar_texto(r.get("genres", []), [], r.get("description", "")),
        axis=1
    )

    # 3. TF-IDF
    print("Ajustando vetorizador TF-IDF conjunto...")
    vectorizer = TfidfVectorizer(max_features=40000, stop_words="english", token_pattern=r"(?u)\b[a-zA-Z]{3,}\b")
    textos_todos = pd.concat([jogos["texto_modelo"], filmes["texto_modelo"]], ignore_index=True)
    vectorizer.fit(textos_todos)

    vocab = np.array(vectorizer.get_feature_names_out())
    X_j_full = vectorizer.transform(jogos["texto_modelo"])
    X_f_full = vectorizer.transform(filmes["texto_modelo"])

    # Filtra vocabulário compartilhado
    freq_j = np.asarray((X_j_full > 0).sum(axis=0)).ravel()
    freq_f = np.asarray((X_f_full > 0).sum(axis=0)).ravel()
    compartilhado = np.where((freq_j >= MIN_OCORRENCIAS) & (freq_f >= MIN_OCORRENCIAS))[0]
    vocab_final = vocab[compartilhado].tolist()
    print(f"Termos compartilhados: {len(vocab_final):,}")

    X_jogos = normalize(X_j_full[:, compartilhado])
    X_filmes = normalize(X_f_full[:, compartilhado])

    # 4. Classificador de Gêneros
    print("Treinando classificador de gêneros...")
    mlb = MultiLabelBinarizer(classes=sorted(GENEROS_IMDB))
    Y_filmes = mlb.fit_transform(filmes["genres"].map(lambda gs: [g for g in gs if g in GENEROS_IMDB] if isinstance(gs, list) else []))

    X_desc = normalize(vectorizer.transform(filmes["description"].fillna(""))[:, compartilhado])
    tem_genero = (Y_filmes.sum(axis=1) > 0) & (np.asarray((X_desc > 0).sum(axis=1)).ravel() >= 3)

    clf = OneVsRestClassifier(LogisticRegression(max_iter=1000, C=1.0, class_weight="balanced"))
    clf.fit(X_desc[tem_genero], Y_filmes[tem_genero])

    # 5. Projeções
    print("Projetando matrizes de gênero...")
    G_filmes = normalize(clf.predict_proba(X_filmes))
    G_jogos = normalize(clf.predict_proba(X_jogos))

    # 6. Salvar Artefatos
    pasta_saida.mkdir(parents=True, exist_ok=True)
    sparse.save_npz(pasta_saida / "X_jogos.npz", X_jogos)
    sparse.save_npz(pasta_saida / "X_filmes.npz", X_filmes)
    np.save(pasta_saida / "G_jogos.npy", G_jogos)
    np.save(pasta_saida / "G_filmes.npy", G_filmes)

    joblib.dump({
        "vectorizer": vectorizer,
        "clf": clf,
        "mlb": mlb,
        "vocab": vocab_final,
        "config": {"ALPHA": ALPHA, "BETA": BETA, "MIN_VOTOS_FILME": MIN_VOTOS_FILME},
    }, pasta_saida / "artefatos_modelo.joblib", compress=3)

    jogos[["appID", "name", "genres"]].to_parquet(pasta_saida / "catalogo_jogos.parquet", index=False)
    filmes[["id", "title", "genres", "description", "release_date", "rating", "votes"]].to_parquet(
        pasta_saida / "catalogo_filmes.parquet", index=False
    )
    print(f"Modelo final salvo com sucesso em: {pasta_saida}")


def main():
    parser = argparse.ArgumentParser(description="Treina e exporta o modelo semântico.")
    parser.add_argument("--steam", default="ml/artifacts/steam_tratado.parquet")
    parser.add_argument("--filmes", default="ml/artifacts/filmes_tratado.parquet")
    parser.add_argument("--out", default="ml/artifacts/modelo_final")
    args = parser.parse_args()

    treinar_modelo(Path(args.steam), Path(args.filmes), Path(args.out))


if __name__ == "__main__":
    main()
