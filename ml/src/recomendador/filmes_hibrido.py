"""
Recomendador HÍBRIDO de filmes: conteúdo (TF-IDF) + filtragem colaborativa (fatoração).

Por que híbrido?
  - O TF-IDF é a única ponte entre jogos e filmes (via tags -> termos), mas só enxerga
    PALAVRAS: um filme com "knight" e "medieval" na sinopse parece bom mesmo que seja ruim
    ou sem relação real com o gosto do jogador.
  - A fatoração (treinada com as notas do MovieLens) sabe "quem gostou de X também gostou
    de Y", mas não sabe nada de jogos.
  - Juntando: o TF-IDF escolhe filmes "semente" que combinam com os jogos, e a fatoração
    expande a partir deles para filmes que o PÚBLICO considera parecidos.

Passo a passo (método `recomendar`):
  1. Perfil TF-IDF do usuário a partir dos jogos (reaproveita RecomendadorFilmes).
  2. Sementes = os N_SEMENTES filmes com maior similaridade TF-IDF que existem no modelo
     de fatoração.
  3. Perfil colaborativo = média dos vetores Q (normalizados) das sementes, ponderada
     pela similaridade TF-IDF de cada semente.
  4. Score colaborativo = cosseno entre o perfil colaborativo e o Q de cada filme.
  5. Score final = ALFA * colaborativo + (1 - ALFA) * tfidf + PESO_NOTA * (vote_average / 10).
     Filmes fora do modelo de fatoração não têm vetor Q, então usam só o TF-IDF:
     score = tfidf + PESO_NOTA * (vote_average / 10).
  6. "porque": termos do TF-IDF e/ou "parecido com <semente>".
"""
from pathlib import Path

import numpy as np

from .filmes_tfidf import RecomendadorFilmes

ARQ_FATORES = Path("data/processed/fatores_filmes.npz")

ALFA = 0.6        # peso da parte colaborativa (0 = só TF-IDF, 1 = só colaborativo)
N_SEMENTES = 30   # quantos filmes do TF-IDF servem de ponto de partida
PESO_NOTA = 0.1   # bônus para filmes bem avaliados


class RecomendadorHibrido:
    def __init__(self, tfidf: RecomendadorFilmes | None = None, caminho_fatores=ARQ_FATORES,
                 alfa=ALFA, n_sementes=N_SEMENTES):
        # Dá para passar um RecomendadorFilmes já pronto (evita montar o TF-IDF duas vezes)
        self.tfidf = tfidf if tfidf is not None else RecomendadorFilmes()
        self.filmes = self.tfidf.filmes
        self.alfa = alfa
        self.n_sementes = n_sementes

        # --- Carrega os vetores aprendidos na etapa 3 ---
        fatores = np.load(caminho_fatores)
        Q = fatores["Q"]
        # Normaliza cada vetor (norma 1): assim o produto escalar vira cosseno e
        # filmes com vetor "comprido" (muito populares) não dominam só pelo tamanho.
        self.Qn = Q / np.linalg.norm(Q, axis=1, keepdims=True)

        # --- Liga cada linha do catálogo à linha correspondente em Q ---
        # pos_q[i] = linha de Q do filme i do catálogo, ou -1 se ele não está no modelo
        linha_por_tmdb = {int(t): k for k, t in enumerate(fatores["tmdb_ids"])}
        self.pos_q = np.array([linha_por_tmdb.get(int(t), -1) for t in self.filmes["id"]])
        self.no_modelo = self.pos_q >= 0

    def recomendar(self, jogos: list[dict], n=10, alfa=None):
        alfa = self.alfa if alfa is None else alfa

        # 1. Perfil TF-IDF e similaridade de conteúdo com todos os filmes
        perfil = self.tfidf.perfil_usuario(jogos)
        sim_tfidf = np.asarray(self.tfidf.matriz @ perfil.T).ravel()

        # 2. Sementes: os mais parecidos (TF-IDF) entre os que existem no modelo de fatoração
        candidatos = np.flatnonzero(self.no_modelo & (sim_tfidf > 0))
        sementes = candidatos[np.argsort(-sim_tfidf[candidatos])][:self.n_sementes]

        # 3. Perfil colaborativo = média dos Q das sementes, ponderada pela similaridade
        Q_sementes = self.Qn[self.pos_q[sementes]]          # (n_sementes x K)
        pesos = sim_tfidf[sementes]
        sim_colab = np.full(len(self.filmes), np.nan)       # NaN = filme fora do modelo
        if pesos.sum() > 0:  # se nenhuma tag do usuário for conhecida, não há sementes
            perfil_colab = pesos @ Q_sementes / pesos.sum()
            perfil_colab /= np.linalg.norm(perfil_colab)

            # 4. Score colaborativo = cosseno entre o perfil colaborativo e cada filme
            sim_colab[self.no_modelo] = self.Qn[self.pos_q[self.no_modelo]] @ perfil_colab

        # 5. Score final (fora do modelo -> só TF-IDF)
        nota = self.filmes["vote_average"].fillna(0).to_numpy() / 10
        score = np.where(
            np.isnan(sim_colab),
            sim_tfidf,
            alfa * np.nan_to_num(sim_colab) + (1 - alfa) * sim_tfidf,
        ) + PESO_NOTA * nota

        top = np.argsort(-score)[:n]
        resultado = self.filmes.iloc[top][
            ["id", "imdb_id", "title", "release_date", "vote_average", "generos", "poster_path"]
        ].copy()
        resultado["tfidf"] = sim_tfidf[top].round(3)
        resultado["colab"] = sim_colab[top].round(3)
        resultado["score"] = score[top].round(3)
        resultado["porque"] = [self._explicar(perfil, i, sementes, pesos) for i in top]
        return resultado.reset_index(drop=True)

    def _explicar(self, perfil, idx, sementes, pesos):
        """Termos do TF-IDF e/ou a semente que mais 'puxou' este filme no score colaborativo."""
        partes = []
        termos = self.tfidf._explicar(perfil, idx)
        if termos:
            partes.append(termos)

        if self.no_modelo[idx] and len(sementes) > 0:
            # Contribuição de cada semente = peso da semente * cosseno(semente, filme).
            # Ignora o próprio filme (não faz sentido dizer "parecido com ele mesmo").
            contrib = pesos * (self.Qn[self.pos_q[sementes]] @ self.Qn[self.pos_q[idx]])
            contrib[sementes == idx] = -np.inf
            melhor = int(np.argmax(contrib))
            if np.isfinite(contrib[melhor]) and contrib[melhor] > 0:
                partes.append(f"parecido com {self.filmes['title'].iloc[sementes[melhor]]}")

        return " | ".join(partes)
