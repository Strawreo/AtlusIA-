# Projeto IA — Recomendação de filmes e músicas a partir da biblioteca Steam

Projeto da disciplina de Inteligência Artificial. O aluno está **aprendendo**: explique o que
cada parte faz e por quê, comente o código em **português**, e prefira soluções simples e
didáticas a soluções "de produção". Depois de cada etapa, **rode o código e mostre os resultados**.

## Ambiente
- Windows, VS Code, terminal PowerShell. Projeto em `C:\Users\gabri\OneDrive\Área de Trabalho\Projeto-IA`.
- Venv em `.venv` na raiz. Rode tudo **a partir da raiz** (os caminhos são relativos: `data/raw`, `data/processed`).
- Dependências já instaladas: pandas, pyarrow, scikit-learn, numpy, matplotlib.
- **Não instale PyTorch / TensorFlow / sentence-transformers** sem perguntar (pesados). Mantenha um `requirements.txt` atualizado.
- Segredos (API key da Steam) ficam em `.env` (python-dotenv) e `.env` vai no `.gitignore`.

## Arquitetura (decidida — não trocar sem perguntar)
Sistema de recomendação **híbrido**:
1. **TF-IDF + cosseno (conteúdo)** — ponte entre jogos e filmes. Tags de jogo são traduzidas
   para o vocabulário dos filmes pela tabela `TAG_PARA_TERMOS`.
2. **Fatoração de Matrizes treinada (filtragem colaborativa)** — aprendida com as notas do
   MovieLens via mini-batch SGD implementado à mão em numpy. Dá os vetores latentes `Q` dos filmes.
3. **Músicas: K-Means + KNN** sobre audio features do Spotify (ainda não feito).

Perfil do usuário = média dos jogos ponderada por `log(1 + horas jogadas)`.

## Dados
`data/raw/` (NÃO alterar/apagar):
- `movies_metadata.csv`, `keywords.csv` — The Movies Dataset (TMDB). `id` = tmdbId.
- `ratings.csv` (~26M notas MovieLens: userId, movieId, rating) + `links.csv` (movieId → tmdbId).
- `dataset.csv` — Spotify Tracks (114k linhas, 89.740 faixas únicas, 114 `track_genre`).
- `credits.csv`, `world_imdb_movies_top_movies_per_year.csv` — não usados por enquanto (opcionais).

`data/processed/` (gerados):
- `filmes.parquet` — 9.106 filmes (≥50 votos, com sinopse). Colunas: id, imdb_id, title,
  release_date, vote_average, vote_count, generos (lista), keywords (lista), overview,
  poster_path, texto (gêneros 2x + keywords + sinopse; termos com espaço viram `_`).
- `musicas.parquet` — 89.740 faixas. Colunas: track_id, track_name, artists, album_name,
  popularity, track_genre, danceability, energy, valence, acousticness, instrumentalness,
  speechiness, liveness, tempo, loudness.
- `fatores_filmes.npz` — modelo treinado: `tmdb_ids`, `Q` (n_filmes × 32), `bi` (viés), `media`.
- `curva_aprendizado.png` — curva de treino.

## Scripts existentes (`notebooks/`)
- `01_preparar_dados.py` — limpeza → gera os dois parquets. Pronto.
- `02_recomendador_filmes.py` — classe `RecomendadorFilmes` (TF-IDF), `TAG_PARA_TERMOS`,
  `PERSONAS` (bibliotecas fictícias de teste) e explicação "porque" (termos que mais contribuíram).
- `03_treinar_fatoracao.py` — treino da fatoração. K=32, 20 épocas, lr=0.1, reg L2=0.1,
  lote 20k, gradiente **médio** por usuário/filme no lote (somar fazia o treino divergir),
  MAX_USUARIOS=60k. **Resultado: RMSE teste 0,834 vs 1,06 do baseline (21,2% melhor), sem
  overfitting.** Vizinhos no espaço aprendido fazem sentido (Toy Story → Pixar; O Iluminado → Kubrick).
  Não precisa retreinar.

Os nomes começando com número não são importáveis; código reutilizável deve ir para `src/`.

## Resultados para o relatório
Guardar números, tabelas e gráficos de cada etapa em `relatorio/` (markdown + png), para o
aluno montar o relatório depois.
