"""
Etapa 2 — Recomendador de filmes com TF-IDF + similaridade de cosseno.

O código do recomendador agora mora no pacote `src/recomendador/`:
  - mapeamentos.py  -> TAG_PARA_TERMOS (tags da Steam -> vocabulário dos filmes)
  - filmes_tfidf.py -> classe RecomendadorFilmes
  - personas.py     -> PERSONAS (bibliotecas fictícias de teste)

Este script só roda o recomendador nas personas e mostra os resultados.

Rodar (da raiz do projeto):  python notebooks/02_recomendador_filmes.py
"""
import sys
from pathlib import Path

# Coloca a pasta `src/` no caminho de busca do Python, para o `import recomendador` funcionar.
# (parents[1] = pasta acima de notebooks/ = raiz do projeto)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from ml.src.recomendador.filmes_tfidf import RecomendadorFilmes
from ml.src.recomendador.personas import PERSONAS

if __name__ == "__main__":
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 45)

    rec = RecomendadorFilmes()
    print(f"Matriz TF-IDF: {rec.matriz.shape[0]} filmes x {rec.matriz.shape[1]} termos\n")

    for nome, jogos in PERSONAS.items():
        print(f"===== Persona: {nome} =====")
        print(rec.recomendar(jogos, n=8)[["title", "vote_average", "similaridade", "porque"]])
        print()
