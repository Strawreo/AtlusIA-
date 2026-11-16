# Recomendação de filmes e músicas a partir da biblioteca Steam

Projeto da disciplina de Inteligência Artificial. A partir dos **jogos que uma pessoa tem na
Steam** (e de quantas horas jogou cada um), o sistema recomenda **filmes** e, em breve, **músicas**.

O desafio central é **atravessar domínios**: não existe nenhum dado que ligue "quem jogou
Elden Ring" a "quem gosta de Excalibur". Por isso o sistema combina três técnicas, cada uma
resolvendo uma parte do problema.

---

## Sumário
1. [Visão geral da arquitetura](#1-visão-geral-da-arquitetura)
2. [Estrutura de pastas](#2-estrutura-de-pastas)
3. [Como rodar](#3-como-rodar)
4. [Etapa 1 — Preparação dos dados](#4-etapa-1--preparação-dos-dados)
5. [Etapa 2 — Recomendador por conteúdo (TF-IDF)](#5-etapa-2--recomendador-por-conteúdo-tf-idf)
6. [Etapa 3 — Fatoração de Matrizes (filtragem colaborativa)](#6-etapa-3--fatoração-de-matrizes-filtragem-colaborativa)
7. [Etapa 4 — Recomendador híbrido e comparação](#7-etapa-4--recomendador-híbrido-e-comparação)
8. [Status e próximos passos](#8-status-e-próximos-passos)

---

## 1. Visão geral da arquitetura

```
Biblioteca Steam (tags de cada jogo + horas jogadas)
        │
        ▼
 TAG_PARA_TERMOS  ── traduz tags de jogo ("Souls-like") para palavras de filme ("dark fantasy", "knight")
        │
        ▼
 [1] TF-IDF + cosseno ───────► filmes com o MESMO TEMA dos jogos            (conteúdo)
        │
        ▼
 [2] Fatoração de Matrizes ──► filmes que o MESMO PÚBLICO costuma gostar    (colaborativo)
        │                      (aprendida com 26 milhões de notas do MovieLens)
        ▼
 Recomendação híbrida de filmes, com explicação ("porque")

 [3] K-Means + KNN sobre características de áudio do Spotify ──► músicas     (a fazer)
```

**Perfil do usuário** = média dos jogos, ponderada por `log(1 + horas jogadas)`.

| Técnica | O que sabe | O que NÃO sabe |
|---|---|---|
| TF-IDF | o tema/assunto de cada filme (gêneros, palavras-chave, sinopse) | se o filme é bom ou se o público o considera parecido com outro |
| Fatoração de Matrizes | "quem gostou de X também gostou de Y" | nada sobre jogos |

Por isso o TF-IDF é a **ponte** entre jogos e filmes, e a fatoração entra para refinar.

---

## 2. Estrutura de pastas

```
Projeto-IA/
├── README.md
├── requirements.txt
├── CLAUDE.md                      # instruções do projeto para o assistente de IA
├── data/
│   ├── raw/                       # dados brutos (NÃO versionados — baixar do Kaggle)
│   └── processed/                 # dados limpos e modelo treinado (versionados, ~14 MB)
│       ├── filmes.parquet         # 9.106 filmes
│       ├── musicas.parquet        # 89.740 faixas
│       ├── fatores_filmes.npz     # vetores aprendidos pela fatoração
│       └── curva_aprendizado.png
├── notebooks/                     # scripts de cada etapa (rodar em ordem)
│   ├── 01_preparar_dados.py
│   ├── 02_recomendador_filmes.py
│   ├── 03_treinar_fatoracao.py
│   └── 04_comparar_filmes.py
├── src/recomendador/              # código reutilizável (importável)
│   ├── mapeamentos.py             # TAG_PARA_TERMOS: tags da Steam -> vocabulário de filmes
│   ├── filmes_tfidf.py            # classe RecomendadorFilmes (TF-IDF)
│   ├── filmes_hibrido.py          # classe RecomendadorHibrido (TF-IDF + fatoração)
│   └── personas.py                # bibliotecas de jogos fictícias para teste
├── relatorio/                     # tabelas e resultados para o relatório
│   └── comparacao_filmes.md
├── backend/                       # API FastAPI e integração com a Steam
└── frontend/                      # (a fazer)
```

**Por que `notebooks/` e `src/` separados?** Arquivos cujo nome começa com número
(`02_...py`) não podem ser importados em Python. Então os scripts numerados ficam só como
"roteiros" de cada etapa, e o código que será reaproveitado (pelos scripts e, depois, pelo
backend) mora no pacote `src/recomendador/`.

---

## 3. Como rodar

Usamos Python 3.14 no Windows (PowerShell). **Rode tudo a partir da raiz do projeto**,
porque os caminhos são relativos (`data/raw`, `data/processed`).

```powershell
# 1. Criar e ativar o ambiente virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Rodar os recomendadores (usam data/processed/, que já vem no repositório)
python notebooks/02_recomendador_filmes.py
python notebooks/04_comparar_filmes.py
```

### Só se quiser refazer tudo do zero
Baixe os dados brutos do Kaggle e coloque os CSVs em `data/raw/`:

| Dataset | Arquivos usados |
|---|---|
| [The Movies Dataset](https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset) | `movies_metadata.csv`, `keywords.csv`, `ratings.csv`, `links.csv` |
| [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) | `dataset.csv` |

```powershell
python notebooks/01_preparar_dados.py     # gera filmes.parquet e musicas.parquet
python notebooks/03_treinar_fatoracao.py  # treina a fatoração (lê os 26M de notas; demora)
```

---

## 4. Etapa 1 — Preparação dos dados

**Script:** `notebooks/01_preparar_dados.py`

### Filmes
- **Limpeza do `id`:** algumas linhas do dataset são corrompidas (com uma data no lugar do id).
  São convertidas com `pd.to_numeric(errors="coerce")` e descartadas.
- **Gêneros e keywords** vêm como texto que parece lista de Python
  (`"[{'id': 28, 'name': 'Action'}]"`); `ast.literal_eval` converte para lista de verdade e
  ficamos só com os nomes.
- **Filtro de qualidade:** só filmes com **≥ 50 votos e com sinopse** → **9.106 filmes**.
  Filmes obscuros recomendariam mal e não teriam texto para o TF-IDF.
- **Coluna `texto`** (o que vira vetor depois): `gêneros + gêneros + keywords + sinopse`.
  - Gêneros aparecem **duas vezes** para pesarem mais que palavras soltas da sinopse.
  - Termos com espaço viram uma palavra só (`Science Fiction` → `Science_Fiction`), para não
    serem quebrados em "science" e "fiction".

### Músicas
- A mesma faixa aparece várias vezes (uma por gênero) → deduplicada por `track_id`,
  mantendo a linha mais popular → **89.740 faixas**.
- Ficam as **audio features** (`danceability`, `energy`, `valence`, `acousticness`, `tempo`...),
  que serão usadas no K-Means/KNN.

Os resultados são salvos em **Parquet** (mais rápido e menor que CSV, e preserva colunas do tipo lista).

---

## 5. Etapa 2 — Recomendador por conteúdo (TF-IDF)

**Código:** `src/recomendador/filmes_tfidf.py`, `src/recomendador/mapeamentos.py`
**Script:** `notebooks/02_recomendador_filmes.py`

### 5.1 A ponte: `TAG_PARA_TERMOS`
Tags da Steam ("Souls-like", "Farming Sim") não aparecem em texto de filme nenhum. Um
dicionário feito à mão traduz cada tag para termos do vocabulário dos filmes:

```python
"Souls-like": ["dark fantasy", "sword and sorcery", "knight", "medieval", "demon", "survival"]
```

Cada jogo vira então um "documento" falso com esses termos. Tags sem sentido temático
(Indie, Singleplayer, Co-op) ficam de fora de propósito.

### 5.2 TF-IDF
Cada filme vira um vetor com um peso para cada palavra do vocabulário (19.858 palavras):
- **TF** (*term frequency*): quantas vezes a palavra aparece no filme.
- **IDF** (*inverse document frequency*): alto para palavras **raras** no catálogo.
  "knight" (rara) pesa muito; "life" (em milhares de sinopses) pesa pouco.

Parâmetros do `TfidfVectorizer`:

| Parâmetro | Efeito | Motivo |
|---|---|---|
| `stop_words="english"` | remove "the", "and", "of"... | não carregam significado |
| `min_df=2` | ignora palavras presentes em 1 filme só | ruído (erros, nomes próprios) |
| `sublinear_tf=True` | usa `1 + log(tf)` | palavra repetida 10× não vale 10× mais |

Os vetores saem **normalizados (tamanho 1)**, o que permite calcular a similaridade de
cosseno com um simples produto de matrizes.

### 5.3 Perfil do usuário
1. Cada jogo → texto traduzido → vetor TF-IDF (normalizado, para jogos com muitas tags não dominarem).
2. Perfil = média dos vetores ponderada por `log(1 + horas)`.

**Por que log?** Com 180h, 90h e 40h os pesos ficam 5,2 / 4,5 / 3,7: o jogo mais jogado pesa
mais, mas não engole a biblioteca inteira (sem log, pesaria 4,5× o de 40h).

### 5.4 Recomendação
```
similaridade = cosseno(perfil, filme)               # para os 9.106 filmes de uma vez
score        = 0.85 * similaridade + 0.15 * nota/10  # bônus para filmes bem avaliados
```

### 5.5 Explicação ("porque")
O cosseno é uma **soma** de contribuições, uma por palavra (peso no filme × peso no perfil).
As 3 maiores parcelas viram a explicação mostrada ao usuário, por exemplo
*"knight, medieval, fantasy"*. A explicação é exata, não uma aproximação.

### Resultados (top-3 por persona fictícia)
| Persona | Recomendações | Porque (do 1º lugar) |
|---|---|---|
| Souls-like | Nightbreed, DragonHeart, Onibaba | dark fantasy, fantasy, monster |
| Cozy | Miss You Already, Barbie as The Princess & the Pauper, Over the Garden Wall | friendship, family, comedy |
| FPS / Guerra | We Were Soldiers, Midway, '71 | soldier, war, battle |
| Sci-fi / Cyberpunk | Titan A.E., Ender's Game, Avatar | alien, space, science fiction |

---

## 6. Etapa 3 — Fatoração de Matrizes (filtragem colaborativa)

**Script:** `notebooks/03_treinar_fatoracao.py` → gera `data/processed/fatores_filmes.npz`

### 6.1 Ideia
Uma tabela usuários × filmes com as notas do MovieLens está quase toda vazia (cada pessoa
avaliou poucos filmes). A fatoração supõe que cada nota é explicada por poucos "gostos escondidos":

```
nota(u, i) ≈ média + viés_u + viés_i + p_u · q_i
```
- `viés_u`: o usuário é exigente (−) ou generoso (+).
- `viés_i`: o filme é bem avaliado em geral (+) ou não (−).
- `p_u`, `q_i`: vetores de **K = 32** números aprendidos. Ninguém define o que cada dimensão
  significa: o treino descobre sozinho.

### 6.2 Dados
- Notas do MovieLens convertidas para o id do TMDB (via `links.csv`) e filtradas para o nosso catálogo.
- Amostra de **60 mil usuários** (para caber na memória e no tempo); filmes com **≥ 10 notas**
  → **7.665 filmes** no modelo.
- Divisão aleatória: **90% treino / 10% teste**. O teste mede se o modelo generaliza ou só decorou.

### 6.3 Treino: mini-batch SGD implementado à mão em numpy
Para cada lote de 20 mil notas:
```
erro = nota_real − nota_prevista
p_u += lr * (erro * q_i − reg * p_u)
q_i += lr * (erro * p_u − reg * q_i)
```
Se a nota real foi maior que a prevista, `p_u` e `q_i` se aproximam (a próxima previsão sobe),
e vice-versa. A **regularização L2** (`reg * p_u`) puxa os vetores para zero e evita que o
modelo decore os dados (overfitting).

Hiperparâmetros: K=32, 20 épocas, taxa de aprendizado 0,1, regularização 0,1, lote 20.000.

**Detalhes de implementação importantes:**
- **`np.add.at`:** o mesmo filme aparece várias vezes no lote. Em numpy, `g[idx] += x` com
  índices repetidos **não acumula** (conta só uma vez); `np.add.at(g, idx, x)` acumula corretamente.
- **Gradiente MÉDIO, não somado:** um filme popular pode aparecer centenas de vezes num lote.
  Somando, o passo ficava gigante e o treino **divergia**. Dividindo pela contagem
  (`np.bincount`), o treino ficou estável.

### 6.4 Resultados
| Modelo | RMSE no teste |
|---|---|
| Baseline (sempre prever a média) | 1,06 |
| **Fatoração de Matrizes** | **0,834** (21,2% melhor) |

Sem overfitting (curva de treino e teste descem juntas — ver `data/processed/curva_aprendizado.png`).

**Teste de sanidade:** filmes vizinhos no espaço aprendido fazem sentido —
*Toy Story* → *Toy Story 2, Toy Story 3, A Bug's Life, Finding Nemo, The Incredibles*.

---

## 7. Etapa 4 — Recomendador híbrido e comparação

**Código:** `src/recomendador/filmes_hibrido.py`
**Script:** `notebooks/04_comparar_filmes.py` → gera `relatorio/comparacao_filmes.md`

### 7.1 Método
1. Perfil TF-IDF do usuário (como na etapa 2).
2. **Sementes:** os 30 filmes mais parecidos pelo TF-IDF que existem no modelo de fatoração.
3. **Perfil colaborativo:** média dos vetores `q` (normalizados) das sementes, ponderada pela
   similaridade TF-IDF de cada uma.
4. **Score colaborativo:** cosseno entre o perfil colaborativo e o `q` de cada filme.
5. **Score final:** `ALFA * colaborativo + (1 − ALFA) * tfidf + 0.1 * nota/10`.
   Filmes fora do modelo de fatoração usam só o TF-IDF.
6. **Explicação:** termos do TF-IDF + "parecido com <semente que mais contribuiu>".

### 7.2 Resultado: o híbrido, nesta forma, **piorou** a maioria dos casos
Comparação com ALFA = 0,3 / 0,6 / 0,9 (tabelas completas em `relatorio/comparacao_filmes.md`):

| Persona | Melhor | Observação |
|---|---|---|
| Souls-like | empate (TF-IDF ≈ α 0,3) | α 0,3 mais coerente (só espada e feitiçaria), mas com notas menores; α 0,9 traz *Fist Fight* e *Max Payne* |
| Cozy | α 0,3 (leve) | troca *Miss You Already* (drama sobre câncer) por clássicos como *The Fox and the Hound* |
| FPS / Guerra | **TF-IDF puro** | α ≥ 0,6 traz *The Big Short*, *Taking Woodstock* |
| Sci-fi / Cyberpunk | **TF-IDF puro** | híbrido puxa ficção científica de segunda (*Meet Dave*, *Lockout*) |

**Por que piorou (diagnóstico):**
1. **Escalas diferentes:** o cosseno colaborativo dos melhores filmes fica em 0,6–0,9; o do
   TF-IDF, em 0,15–0,35. Mesmo com ALFA = 0,3, o colaborativo já pesa tanto quanto o TF-IDF.
2. **Sementes incoerentes:** o cosseno médio entre duas sementes, no espaço colaborativo, vai
   de 0,04 a 0,17. Filmes que compartilham a palavra "soldier" não são considerados parecidos
   pelo público. A média de 30 vetores quase sem relação vira um perfil vago.
3. **A fatoração aprende o PÚBLICO, não o TEMA:** os vizinhos de *Saving Private Ryan* são
   *Shawshank*, *Braveheart* e *Good Will Hunting* (populares dos anos 90), não filmes de guerra.

**Melhorias planejadas:** usar o colaborativo só para **reordenar** os ~100 melhores do TF-IDF
(o tema fica garantido); colocar os dois scores na mesma escala antes de combinar; usar menos
sementes e só filmes com mais votos.

---

## 8. Status e próximos passos

| Parte | Status |
|---|---|
| Preparação dos dados | ✅ pronto |
| Recomendador TF-IDF | ✅ pronto |
| Fatoração de Matrizes | ✅ treinada (RMSE 0,834) |
| Recomendador híbrido | ⚠️ implementado, precisa de ajuste (ver seção 7) |
| Músicas (K-Means + KNN) | ⏳ a fazer |
| Integração com a API da Steam | ⚙️ serviço inicial criado; falta integrar tags e recomendador |
| Backend e frontend | 🚧 base FastAPI criada; frontend ainda a fazer |

### Limitações conhecidas
- `TAG_PARA_TERMOS` cobre ~55 tags; tags fora da tabela são ignoradas.
- Avaliação ainda é qualitativa (personas fictícias): não existe "gabarito" de jogo → filme.
- Cada música ficou com um único gênero após a deduplicação.

### Dependências
`pandas`, `pyarrow`, `numpy`, `scikit-learn`, `matplotlib` (versões em `requirements.txt`).
