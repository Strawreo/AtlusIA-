"""
Recomendador de filmes com TF-IDF + similaridade de cosseno (parte "conteúdo" do híbrido).

Ideia:
  1. Cada filme vira um vetor TF-IDF (a partir da coluna `texto`: gêneros + keywords + sinopse).
  2. Cada jogo vira um vetor TF-IDF a partir das suas tags, "traduzidas" para o
     vocabulário de filmes pela tabela TAG_PARA_TERMOS (ver mapeamentos.py).
  3. O perfil do usuário é a média dos vetores dos jogos, ponderada por log(1 + horas).
  4. Recomenda os filmes com maior cosseno em relação ao perfil.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from .mapeamentos import tags_para_texto

# Caminho relativo: rode os scripts a partir da raiz do projeto
ARQ_FILMES = Path("data/processed/filmes.parquet")


class RecomendadorFilmes:
    def __init__(self, caminho=ARQ_FILMES):
        self.filmes = pd.read_parquet(caminho)
        self.vetorizador = TfidfVectorizer(
            stop_words="english",
            max_features=30_000,
            min_df=2,          # ignora palavras que aparecem em 1 filme só
            sublinear_tf=True, # log na frequência: palavra repetida não domina
        )
        self.matriz = self.vetorizador.fit_transform(self.filmes["texto"])
        self.vocab = np.array(self.vetorizador.get_feature_names_out())

    def perfil_usuario(self, jogos: list[dict]):
        """jogos = [{"nome": ..., "tags": [...], "horas": float}, ...]"""
        textos = [tags_para_texto(j["tags"]) for j in jogos]
        pesos = np.array([np.log1p(j["horas"]) for j in jogos])

        vetores = normalize(self.vetorizador.transform(textos))  # cada jogo com norma 1
        perfil = vetores.T @ pesos / pesos.sum()                 # média ponderada
        return normalize(perfil.reshape(1, -1))

    def recomendar(self, jogos: list[dict], n=10, peso_nota=0.15):
        perfil = self.perfil_usuario(jogos)
        similaridade = (self.matriz @ perfil.T).ravel()  # cosseno (vetores já normalizados)

        # Pequeno bônus para filmes bem avaliados, para desempatar a favor de filmes bons
        nota = self.filmes["vote_average"].fillna(0).to_numpy() / 10
        score = (1 - peso_nota) * similaridade + peso_nota * nota

        top = np.argsort(-score)[:n]
        resultado = self.filmes.iloc[top][["title", "release_date", "vote_average", "generos"]].copy()
        resultado["similaridade"] = similaridade[top].round(3)
        resultado["porque"] = [self._explicar(perfil, i) for i in top]
        return resultado.reset_index(drop=True)

    def _explicar(self, perfil, idx, k=3):
        """Termos que mais contribuíram para a similaridade (bom para mostrar no front)."""
        contrib = self.matriz[idx].multiply(perfil).toarray().ravel()
        melhores = np.argsort(-contrib)[:k]
        return ", ".join(self.vocab[i].replace("_", " ") for i in melhores if contrib[i] > 0)
