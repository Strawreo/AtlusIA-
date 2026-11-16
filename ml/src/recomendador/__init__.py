"""
Pacote `recomendador` — código reutilizável do projeto.

Os scripts em `notebooks/` (que têm nomes começando com número e por isso não podem
ser importados) usam o que está aqui. Mais tarde o backend também vai usar.

Módulos:
  - mapeamentos  : TAG_PARA_TERMOS (tags da Steam -> vocabulário dos filmes)
  - filmes_tfidf : RecomendadorFilmes (TF-IDF + similaridade de cosseno)
  - filmes_hibrido : RecomendadorHibrido (TF-IDF + vetores da fatoração de matrizes)
  - personas     : PERSONAS (bibliotecas de jogos fictícias para teste)
"""
from .filmes_hibrido import RecomendadorHibrido
from .filmes_tfidf import RecomendadorFilmes
from .mapeamentos import TAG_PARA_TERMOS, tags_para_texto
from .personas import PERSONAS

__all__ = ["RecomendadorFilmes", "RecomendadorHibrido","TAG_PARA_TERMOS", "tags_para_texto", "PERSONAS"]
