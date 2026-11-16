"""
Etapa 4 — Comparação: TF-IDF puro x Híbrido (TF-IDF + fatoração) com vários ALFA.

Para cada persona roda:
  (a) TF-IDF puro (RecomendadorFilmes)
  (b) Híbrido com ALFA = 0.3, 0.6 e 0.9 (RecomendadorHibrido)
Mostra o top-10 de cada um lado a lado e algumas métricas simples:
  - iguais_tfidf : quantos dos 10 também estão no top-10 do TF-IDF puro
  - tfidf_medio  : similaridade TF-IDF média (o quanto os filmes "batem" com o tema dos jogos)
  - nota_media   : vote_average médio (qualidade segundo o TMDB)
  - votos_mediana: mediana de vote_count (popularidade; alto = filmes mais conhecidos)

Salva tudo em relatorio/comparacao_filmes.md.

Rodar (da raiz do projeto):  python notebooks/04_comparar_filmes.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from ml.src.recomendador.filmes_hibrido import RecomendadorHibrido
from ml.src.recomendador.filmes_tfidf import RecomendadorFilmes
from ml.src.recomendador.personas import PERSONAS

N = 10
ALFAS = [0.3, 0.6, 0.9]
SAIDA = Path("relatorio/comparacao_filmes.md")


def rotulo(df):
    """'Título (ano)' para cada linha."""
    ano = df["release_date"].astype(str).str[:4]
    return df["title"] + " (" + ano + ")"


def metricas(df, ref, catalogo, tfidf_rec, jogos):
    """Métricas de um top-N. `ref` = rótulos do top-N do TF-IDF puro."""
    rot = rotulo(df)
    # junta com o catálogo para pegar vote_count e a similaridade TF-IDF de cada filme
    info = df.merge(catalogo, on=["title", "release_date"], how="left")
    return {
        "iguais_tfidf": int(rot.isin(ref).sum()),
        "tfidf_medio": float(info["sim_tfidf"].mean()),
        "nota_media": float(df["vote_average"].mean()),
        "votos_mediana": float(info["vote_count"].median()),
    }


def tabela_md(df):
    """DataFrame -> tabela markdown (sem depender do pacote `tabulate`)."""
    linhas = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    for _, row in df.iterrows():
        celulas = [str(v).replace("|", "\\|") for v in row]
        linhas.append("| " + " | ".join(celulas) + " |")
    return "\n".join(linhas)


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_colwidth", 34)

    tfidf = RecomendadorFilmes()
    hibrido = RecomendadorHibrido(tfidf=tfidf)  # reaproveita a matriz TF-IDF já montada
    print(f"Filmes no catálogo: {len(tfidf.filmes)} | no modelo de fatoração: {hibrido.no_modelo.sum()}\n")

    # (title, release_date) identifica o filme no catálogo — confere se é único
    catalogo = tfidf.filmes[["title", "release_date", "vote_count"]].copy()
    assert not catalogo.duplicated(["title", "release_date"]).any()

    md = [
        "# Comparação: TF-IDF puro x Híbrido (TF-IDF + Fatoração de Matrizes)",
        "",
        "Gerado por `notebooks/04_comparar_filmes.py`.",
        "",
        f"- Catálogo: {len(tfidf.filmes)} filmes; {hibrido.no_modelo.sum()} estão no modelo de fatoração.",
        "- TF-IDF puro: `score = 0.85 * tfidf + 0.15 * nota/10`.",
        "- Híbrido: `score = ALFA * colab + (1 - ALFA) * tfidf + 0.1 * nota/10` "
        f"({hibrido.n_sementes} sementes); filmes fora do modelo: `tfidf + 0.1 * nota/10`.",
        "- Métricas: `iguais_tfidf` = filmes em comum com o top-10 do TF-IDF puro; "
        "`tfidf_medio` = aderência ao tema dos jogos; `nota_media` = vote_average médio; "
        "`votos_mediana` = popularidade.",
        "",
    ]

    for nome, jogos in PERSONAS.items():
        # similaridade TF-IDF de todos os filmes para esta persona (usada nas métricas)
        perfil = tfidf.perfil_usuario(jogos)
        catalogo["sim_tfidf"] = np.asarray(tfidf.matriz @ perfil.T).ravel()

        resultados = {"TF-IDF puro": tfidf.recomendar(jogos, n=N)}
        for a in ALFAS:
            resultados[f"Híbrido α={a}"] = hibrido.recomendar(jogos, n=N, alfa=a)

        ref = set(rotulo(resultados["TF-IDF puro"]))
        lado_a_lado = pd.DataFrame({k: rotulo(v).to_numpy() for k, v in resultados.items()})
        lado_a_lado.index = range(1, N + 1)
        tab_metricas = pd.DataFrame(
            {k: metricas(v, ref, catalogo, tfidf, jogos) for k, v in resultados.items()}
        ).T.round(3)

        # ---- terminal ----
        jogos_txt = ", ".join(f"{j['nome']} ({j['horas']}h)" for j in jogos)
        print(f"===== Persona: {nome} =====\nJogos: {jogos_txt}\n")
        print(lado_a_lado, "\n")
        print(tab_metricas, "\n")

        # ---- markdown ----
        md += [f"## Persona: {nome}", "", f"Jogos: {jogos_txt}", "", "### Top-10 lado a lado", ""]
        md += [tabela_md(lado_a_lado.reset_index(names="#")), "", "### Métricas", ""]
        md += [tabela_md(tab_metricas.reset_index(names="Modelo")), ""]
        md += ["### Detalhes (scores e explicação)", ""]
        for k, v in resultados.items():
            cols = ["title", "vote_average"] + [c for c in ["similaridade", "tfidf", "colab", "score"] if c in v] + ["porque"]
            md += [f"**{k}**", "", tabela_md(v[cols].reset_index(drop=True)), ""]

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text("\n".join(md), encoding="utf-8")
    print("Relatório salvo:", SAIDA)
