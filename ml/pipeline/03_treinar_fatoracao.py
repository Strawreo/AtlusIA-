"""
Etapa 3 — Treino de Fatoração de Matrizes (filtragem colaborativa) com as notas do MovieLens.

O modelo aprende um vetor de "gosto" (fatores latentes) para cada usuário e cada filme:

    nota_prevista(u, i) = média_global + viés_u + viés_i + p_u · q_i

  - viés_u : o quanto o usuário u costuma dar notas acima/abaixo da média
  - viés_i : o quanto o filme i costuma receber notas acima/abaixo da média
  - p_u, q_i : vetores de K números aprendidos (o "gosto" do usuário e o "perfil" do filme)

Treino: gradiente descendente estocástico em mini-lotes (mini-batch SGD), minimizando
o erro quadrático + regularização L2 (evita decorar os dados = overfitting).

Saída: data/processed/fatores_filmes.npz -> vetores q_i dos filmes, usados depois
no recomendador híbrido para achar filmes "que quem gostou de X também gostou".

Rodar (da raiz do projeto):  python notebooks/03_treinar_fatoracao.py
"""
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # salva o gráfico em arquivo, sem abrir janela
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")

# ------------------------- Hiperparâmetros -------------------------
K = 32                # tamanho dos vetores latentes
EPOCAS = 20           # quantas vezes o modelo passa por todos os dados
TAXA_APRENDIZADO = 0.1     # passo do gradiente (0.5 explode, testado)
REGULARIZACAO = 0.1       # força da penalidade L2 (melhor valor entre 0.05, 0.1, 0.2, 0.3)
TAMANHO_LOTE = 20_000
MIN_NOTAS_FILME = 10      # filmes com poucas notas geram vetores ruins
MAX_USUARIOS = 60_000     # amostra de usuários para o treino caber na RAM/tempo (None = todos)
SEED = 42

rng = np.random.default_rng(SEED)

# ------------------------- 1. Carregar dados -------------------------
t0 = time.time()
notas = pd.read_csv(
    RAW / "ratings.csv",
    usecols=["userId", "movieId", "rating"],
    dtype={"userId": "int32", "movieId": "int32", "rating": "float32"},
)
links = pd.read_csv(RAW / "links.csv", usecols=["movieId", "tmdbId"]).dropna()
links["tmdbId"] = links["tmdbId"].astype("int32")
catalogo = pd.read_parquet(OUT / "filmes.parquet", columns=["id", "title"])
print(f"Notas carregadas: {len(notas):,} ({time.time() - t0:.0f}s)")

# MovieLens usa movieId próprio; convertemos para o id do TMDB (o mesmo do catálogo)
notas = notas.merge(links, on="movieId")
notas = notas[notas["tmdbId"].isin(catalogo["id"])]

# Amostra de usuários (o dataset completo tem ~270 mil)
if MAX_USUARIOS:
    usuarios = notas["userId"].unique()
    if len(usuarios) > MAX_USUARIOS:
        escolhidos = rng.choice(usuarios, MAX_USUARIOS, replace=False)
        notas = notas[notas["userId"].isin(escolhidos)]

# Remove filmes com poucas notas
contagem = notas["tmdbId"].value_counts()
notas = notas[notas["tmdbId"].isin(contagem[contagem >= MIN_NOTAS_FILME].index)]

# IDs viram índices 0..N-1 (posição na matriz de vetores)
notas["u"], ids_usuarios = pd.factorize(notas["userId"])
notas["i"], ids_filmes = pd.factorize(notas["tmdbId"])
n_usuarios, n_filmes = len(ids_usuarios), len(ids_filmes)
print(f"Para treino: {len(notas):,} notas | {n_usuarios:,} usuários | {n_filmes:,} filmes")

# ------------------------- 2. Separar treino e teste -------------------------
u_all = notas["u"].to_numpy()
i_all = notas["i"].to_numpy()
r_all = notas["rating"].to_numpy(dtype=np.float32)

idx = rng.permutation(len(r_all))
corte = int(0.9 * len(idx))  # 90% treino, 10% teste
tr, te = idx[:corte], idx[corte:]
u_tr, i_tr, r_tr = u_all[tr], i_all[tr], r_all[tr]
u_te, i_te, r_te = u_all[te], i_all[te], r_all[te]

# ------------------------- 3. Modelo -------------------------
media = r_tr.mean()
P = rng.normal(0, 0.1, (n_usuarios, K)).astype(np.float32)  # vetores dos usuários
Q = rng.normal(0, 0.1, (n_filmes, K)).astype(np.float32)    # vetores dos filmes
bu = np.zeros(n_usuarios, dtype=np.float32)                 # viés dos usuários
bi = np.zeros(n_filmes, dtype=np.float32)                   # viés dos filmes


def prever(u, i):
    return media + bu[u] + bi[i] + np.sum(P[u] * Q[i], axis=1)


def rmse(u, i, r):
    return float(np.sqrt(np.mean((r - np.clip(prever(u, i), 0.5, 5.0)) ** 2)))


# Baselines: o modelo só presta se bater esses
rmse_media = float(np.sqrt(np.mean((r_te - media) ** 2)))
print(f"\nBaseline (sempre prever a média {media:.2f}): RMSE teste = {rmse_media:.4f}")

# ------------------------- 4. Treino (mini-batch SGD) -------------------------
hist_treino, hist_teste = [], []
for epoca in range(1, EPOCAS + 1):
    t0 = time.time()
    ordem = rng.permutation(len(r_tr))
    for ini in range(0, len(ordem), TAMANHO_LOTE):
        b = ordem[ini:ini + TAMANHO_LOTE]
        u, i, r = u_tr[b], i_tr[b], r_tr[b]

        pu, qi = P[u], Q[i]
        erro = r - (media + bu[u] + bi[i] + np.sum(pu * qi, axis=1))  # quanto erramos
        e = erro[:, None]

        # Gradientes: anda na direção que diminui o erro (+ penalidade L2).
        # Um filme popular aparece muitas vezes no mesmo lote; se somássemos os
        # ajustes, o passo ficaria gigante e o treino explodiria. Por isso usamos
        # a MÉDIA do gradiente de cada usuário/filme dentro do lote.
        lr, reg = TAXA_APRENDIZADO, REGULARIZACAO
        cont_u = np.bincount(u, minlength=n_usuarios)[:, None].astype(np.float32)
        cont_i = np.bincount(i, minlength=n_filmes)[:, None].astype(np.float32)
        ativos_u, ativos_i = cont_u[:, 0] > 0, cont_i[:, 0] > 0

        g_bu = np.zeros(n_usuarios, np.float32); np.add.at(g_bu, u, erro)
        g_bi = np.zeros(n_filmes, np.float32);   np.add.at(g_bi, i, erro)
        g_P = np.zeros_like(P); np.add.at(g_P, u, e * qi)
        g_Q = np.zeros_like(Q); np.add.at(g_Q, i, e * pu)

        bu[ativos_u] += lr * (g_bu[ativos_u] / cont_u[ativos_u, 0] - reg * bu[ativos_u])
        bi[ativos_i] += lr * (g_bi[ativos_i] / cont_i[ativos_i, 0] - reg * bi[ativos_i])
        P[ativos_u] += lr * (g_P[ativos_u] / cont_u[ativos_u] - reg * P[ativos_u])
        Q[ativos_i] += lr * (g_Q[ativos_i] / cont_i[ativos_i] - reg * Q[ativos_i])

    hist_treino.append(rmse(u_tr, i_tr, r_tr))
    hist_teste.append(rmse(u_te, i_te, r_te))
    print(f"Época {epoca:2d} | RMSE treino {hist_treino[-1]:.4f} | RMSE teste {hist_teste[-1]:.4f} "
          f"| {time.time() - t0:.1f}s")

melhora = 100 * (1 - hist_teste[-1] / rmse_media)
print(f"\nRMSE final no teste: {hist_teste[-1]:.4f}  ({melhora:.1f}% melhor que prever a média)")

# ------------------------- 5. Curva de aprendizado -------------------------
plt.figure(figsize=(7, 4))
plt.plot(range(1, EPOCAS + 1), hist_treino, marker="o", label="Treino")
plt.plot(range(1, EPOCAS + 1), hist_teste, marker="o", label="Teste")
plt.axhline(rmse_media, color="gray", linestyle="--", label="Baseline (média)")
plt.xlabel("Época")
plt.ylabel("RMSE")
plt.title("Curva de aprendizado — Fatoração de Matrizes")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(OUT / "curva_aprendizado.png", dpi=120)
print("Gráfico salvo:", OUT / "curva_aprendizado.png")

# ------------------------- 6. Teste de sanidade -------------------------
# Filmes vizinhos no espaço aprendido: se o modelo aprendeu algo, devem fazer sentido
titulos = catalogo.set_index("id")["title"]
Qn = Q / np.linalg.norm(Q, axis=1, keepdims=True)


def vizinhos(titulo, n=6):
    ids = catalogo.loc[catalogo["title"] == titulo, "id"]
    pos = np.flatnonzero(np.isin(ids_filmes, ids))
    if len(pos) == 0:
        return f"'{titulo}' não está no modelo"
    sim = Qn @ Qn[pos[0]]
    top = [j for j in np.argsort(-sim) if j != pos[0]][:n]
    return ", ".join(titulos[ids_filmes[j]] for j in top)


print()
for t in ["The Matrix", "Toy Story", "The Shining", "Saving Private Ryan", "The Lord of the Rings: The Fellowship of the Ring"]:
    print(f"Parecidos com {t}: {vizinhos(t)}")

# ------------------------- 7. Salvar -------------------------
np.savez(OUT / "fatores_filmes.npz", tmdb_ids=np.asarray(ids_filmes), Q=Q, bi=bi, media=media)
print("\nModelo salvo:", OUT / "fatores_filmes.npz")