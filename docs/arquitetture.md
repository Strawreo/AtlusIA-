# Arquitetura do Projeto

Sistema de recomendação baseado em conteúdo. O usuário informa o link do perfil Steam, o sistema lê a biblioteca de jogos e recomenda **filmes** e **outros jogos**.

Este documento é a referência dos 4 membros do grupo. Se algo mudar, atualize este arquivo no mesmo PR.

---

## 1. Escopo

**Dentro do MVP**

- Entrada: URL do perfil Steam (`/profiles/<SteamID64>` ou `/id/<vanity>`).
- Leitura da biblioteca via `GetOwnedGames`.
- Recomendação de filmes (IMDb + The Movies Dataset) e de jogos (dataset de jogos da Steam).
- Frontend com input, loading, mensagens de erro e duas listas de cards.
- Execução local.

**Fora do MVP**

- Deploy, autenticação, banco de dados, testes automatizados, internacionalização.
- Plano B para perfil privado (só mostramos um aviso).
- Modelo de classificação: não existe. O "modelo" é o recomendador por similaridade.

---

## 2. Visão geral

```
┌────────────┐  POST /api/v1/recommendations  ┌──────────────────────────┐
│  Frontend  │ ─────────────────────────────► │     Backend (FastAPI)    │
│  (React)   │ ◄───────────────────────────── │                          │
└────────────┘            JSON                │  steam.py → recommender  │
                                              └────────────┬─────────────┘
                                                           │ lê no startup
                                              ┌────────────▼─────────────┐
                                              │ ml/artifacts/            │
                                              │  movies.parquet + .npy   │
                                              │  games.parquet  + .npy   │
                                              └────────────▲─────────────┘
                                                           │ gerados por
                                              ┌────────────┴─────────────┐
                                              │ ml/ (pipeline offline)   │
                                              └──────────────────────────┘
```

**Ideia central.** Todo item (jogo ou filme) vira um vetor de embedding calculado a partir do texto (título, gêneros, tags e descrição/sinopse). Jogos e filmes ficam no mesmo espaço vetorial. O perfil do usuário é a média ponderada dos vetores dos jogos que ele possui, e os itens mais próximos (similaridade de cosseno) são recomendados.

**Consequência.** Como os embeddings do catálogo já vêm prontos, o backend não precisa de `torch` nem de `sentence-transformers`. Só usa `numpy`. Os modelos pesados ficam restritos ao `ml/`.

---

## 3. Estrutura do repositório

```
projeto/
├── frontend/                  # React + TypeScript + CSS Modules
│   ├── src/
│   │   ├── components/        # SteamForm.tsx, SteamForm.module.css, MovieCard.tsx, ...
│   │   ├── hooks/             # useRecommendations.ts
│   │   ├── services/          # api.ts (chamadas ao backend)
│   │   ├── types/             # tipos TypeScript do contrato da API
│   │   ├── App.tsx
│   │   ├── App.module.css
│   │   ├── index.css          # reset e variáveis CSS globais
│   │   └── main.tsx
│   ├── .env.example
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── main.py            # app FastAPI, CORS, startup, registra os routers
│   │   ├── routes/            # endpoints, um arquivo por domínio
│   │   │   ├── health.py
│   │   │   └── recommendations.py
│   │   ├── schemas/           # modelos Pydantic, um arquivo por domínio
│   │   │   ├── base.py        # CamelModel (base de todos os schemas)
│   │   │   ├── health.py
│   │   │   ├── steam.py       # OwnedGame
│   │   │   └── recommendations.py
│   │   ├── steam.py           # URL → SteamID, GetOwnedGames
│   │   ├── catalog.py         # carrega parquet + npy em memória
│   │   ├── recommender.py     # perfil e ranking (numpy)
│   │   └── config.py          # variáveis de ambiente
│   ├── requirements.txt
│   └── .env.example
│
├── ml/
│   ├── pipeline/              # scripts reprodutíveis (rodam em ordem)
│   │   ├── build_movies.py    # IMDb + TMDB → movies.parquet
│   │   ├── build_games.py     # dataset Steam → games.parquet
│   │   ├── build_embeddings.py# texto → *_emb.npy + manifest.json
│   │   └── text.py            # build_item_text(): título+gêneros+tags+descrição
│   ├── experiments/
│   │   ├── evaluate.py        # métricas (Recall@K, Precision@K)
│   │   └── configs/           # um YAML por experimento
│   ├── notebooks/             # EDA e exploração
│   ├── artifacts/             # saída do pipeline (fora do Git)
│   └── requirements.txt       # sentence-transformers, pandas, pyarrow...
│
├── data/                      # datasets brutos (fora do Git)
├── architecture.md            # este arquivo
├── README.md                  # como rodar
├── .env.example
└── .gitignore
```

**Regras de organização**

1. `frontend/`, `backend/` e `ml/` não importam código uns dos outros. A única ligação são os **artefatos** (`ml/artifacts/`) e o **contrato da API** (seção 6).
2. `ml/` produz os artefatos, o backend só consome. Nenhum código do backend gera embeddings.
3. Notebooks servem para explorar. Tudo que entra no resultado final deve estar em `ml/pipeline/` como script, para qualquer integrante reproduzir.
4. `data/` e `ml/artifacts/` ficam no `.gitignore`. O README diz onde baixar (Drive ou release do GitHub).
5. Segredos ficam em `.env` (no `.gitignore`). Só o `.env.example` é versionado.

---

## 4. Backend (FastAPI + Pydantic)

### 4.1 Arquivos

| Arquivo          | Responsabilidade                                                                                    |
| ---------------- | --------------------------------------------------------------------------------------------------- |
| `main.py`        | Cria o app, configura CORS, carrega o catálogo no startup e registra os routers                     |
| `routes/`        | Endpoints, um arquivo por domínio (`health.py`, `recommendations.py`)                               |
| `schemas/`       | Modelos Pydantic, um arquivo por domínio (`base.py`, `health.py`, `steam.py`, `recommendations.py`) |
| `steam.py`       | Interpreta a URL e chama a API da Steam (`httpx`)                                                   |
| `catalog.py`     | Lê `parquet` e `npy` uma vez e guarda em memória                                                    |
| `recommender.py` | Monta o perfil do usuário e ranqueia itens. Só `numpy`                                              |
| `config.py`      | Lê variáveis de ambiente (`pydantic-settings`)                                                      |

### 4.2 Rotas e schemas por domínio

Cada domínio tem um arquivo em `routes/` e, se precisar de modelos de dados, um arquivo com o mesmo nome em `schemas/`.

| Domínio         | `routes/`                                     | `schemas/`                                                                                            |
| --------------- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Health          | `health.py`: `GET /health`                    | `health.py`: `HealthResponse`                                                                         |
| Recommendations | `recommendations.py`: `POST /recommendations` | `recommendations.py`: `RecommendationsRequest`, `RecommendationsResponse`, `Profile`, `Movie`, `Game` |
| Steam           | (sem rota própria)                            | `steam.py`: `OwnedGame`                                                                               |

**Schemas**

```python
# schemas/base.py
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
```

```python
# schemas/steam.py
from app.schemas.base import CamelModel

class OwnedGame(CamelModel):
    appid: int
    name: str
    hours_played: float
```

```python
# schemas/recommendations.py
from pydantic import Field
from app.schemas.base import CamelModel
from app.schemas.steam import OwnedGame

class RecommendationsRequest(CamelModel):
    steam_url: str
    top_k: int = Field(default=10, ge=1, le=50)

class Profile(CamelModel):
    games_total: int
    games_matched: int
    top_games: list[OwnedGame]

class Movie(CamelModel):
    id: str
    title: str
    year: int | None
    genres: list[str]
    rating: float | None
    poster_url: str | None
    score: float
    because: list[str] = []

class Game(CamelModel):
    appid: int
    name: str
    genres: list[str]
    header_image_url: str | None
    score: float
    because: list[str] = []

class RecommendationsResponse(CamelModel):
    profile: Profile
    movies: list[Movie]
    games: list[Game]
```

**Rotas**

```python
# routes/recommendations.py
from fastapi import APIRouter, Request
from app.schemas.recommendations import RecommendationsRequest, RecommendationsResponse

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("", response_model=RecommendationsResponse)
async def create_recommendations(body: RecommendationsRequest, request: Request) -> RecommendationsResponse:
    catalog = request.app.state.catalog      # carregado no startup (main.py)
    ...                                      # steam.py → recommender.py → resposta
```

```python
# main.py
from app.routes import health, recommendations

app.include_router(health.router, prefix="/api/v1")
app.include_router(recommendations.router, prefix="/api/v1")
```

**Regras**

1. Domínio novo = um arquivo em `routes/`, um com o mesmo nome em `schemas/` (se houver dados) e um `include_router` no `main.py`.
2. Cada pasta tem um `__init__.py` (pode ser vazio). Imports absolutos: `from app.schemas.steam import OwnedGame`.
3. Todo schema herda de `CamelModel`.
4. Um schema pode importar de outro domínio (`recommendations` usa `OwnedGame` de `steam`), mas sem import circular.
5. Rotas não importam outras rotas.

### 4.3 Fluxo de `POST /api/v1/recommendations`

1. `steam.py` extrai o SteamID64 da URL. Se for `/id/<nome>`, resolve com `ResolveVanityURL`.
2. `steam.py` chama `GetOwnedGames` com `include_appinfo=1` e devolve a lista de jogos com horas. A Steam retorna `playtime_forever` em **minutos**, converta para horas.
3. Cruza os `appid` com o catálogo. Jogos fora do catálogo são ignorados. Se nenhum casar, erro `EMPTY_PROFILE`.
4. `recommender.py` calcula o perfil e o ranking de filmes e o de jogos (duas chamadas, listas separadas).
5. A rota monta a resposta e retorna.

### 4.4 Núcleo do recomendador

```python
# recommender.py
import numpy as np

def build_profile(embeddings: np.ndarray, hours: np.ndarray, weighting: str = "log") -> np.ndarray:
    w = np.log1p(hours) if weighting == "log" else np.ones_like(hours)
    v = (w[:, None] * embeddings).sum(axis=0)
    return v / np.linalg.norm(v)

def rank(profile: np.ndarray, matrix: np.ndarray, mask: np.ndarray, k: int) -> list[tuple[int, float]]:
    scores = matrix @ profile          # embeddings já normalizados → cosseno
    scores[~mask] = -np.inf            # filtros e jogos já possuídos
    top = np.argsort(-scores)[:k]
    return [(int(i), float(scores[i])) for i in top]
```

- Embeddings em `float32`, normalizados (L2) quando gerados.
- Filmes: filtrar por `votes >= 1000` e `rating >= 6` (via `mask`).
- Jogos: excluir os que o usuário já tem (via `mask`).
- `recommender.py` não importa FastAPI. Assim o `ml/experiments` consegue reutilizá-lo (`PYTHONPATH=../backend`).

### 4.5 Catálogo

`catalog.py` carrega os arquivos de `ml/artifacts/` uma vez, no startup do FastAPI. Verificações na carga:

- A linha `i` do parquet corresponde à linha `i` do `.npy` (mesmo número de linhas).
- Existe um dicionário `appid → índice` para o cruzamento com a biblioteca.

### 4.6 Regras do backend

- Todo dado que entra ou sai da API, ou vem da Steam, é um **modelo Pydantic** (`schemas/`).
- Rotas são curtas: chamam funções de `steam.py` e `recommender.py`, sem regra de negócio dentro.
- Funções públicas com _type hints_.
- Erros esperados viram `HTTPException` com `detail={"code": "...", "message": "..."}` (seção 6.3).
- Chamadas à Steam com `httpx.AsyncClient` e timeout definido.
- A chave `STEAM_API_KEY` fica só no backend. Nunca logar nem commitar.
- Dependências: `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `httpx`, `numpy`, `pandas`, `pyarrow`.

---

## 5. Frontend (React + TypeScript + CSS Modules)

### 5.1 Organização

- Um componente = um arquivo `.tsx` + um `.module.css` com o mesmo nome, lado a lado.
- Chamadas ao backend ficam **só** em `services/api.ts`. Componentes não usam `fetch`.
- `hooks/useRecommendations.ts` guarda o estado da requisição (carregando, erro, dados).
- Todos os tipos do contrato ficam em `types.ts`.

### 5.2 CSS Modules

```tsx
import styles from "./MovieCard.module.css";

export function MovieCard({ movie }: { movie: Movie }) {
  return <article className={styles.card}>{movie.title}</article>;
}
```

- Classes em `camelCase` (`.card`, `.posterImage`), para usar como `styles.posterImage`.
- Estilo de cada componente fica no seu `.module.css`. O `index.css` só tem reset e variáveis globais (cores, espaçamentos).

### 5.3 TypeScript: padrões

TypeScript puro, sem biblioteca de validação.

1. `"strict": true` no `tsconfig`.
2. Evitar `any`. O único lugar aceitável é o retorno de `res.json()` em `api.ts`, convertido para o tipo certo na hora.
3. Usar `type` para modelar o contrato. Sem `enum`: usar união de textos literais.
4. Campo ausente vem como `null` (igual ao backend), não `undefined`.
5. Os tipos de `types.ts` **espelham** os modelos de `schemas/` (mesmos nomes e campos). Mudou um, muda o outro no mesmo PR.
6. Formatação para exibição (ex.: `score` → "74%", `year` nulo → "—") fica em funções utilitárias, não espalhada nos componentes.

**`types.ts`**

```ts
export type OwnedGame = { appid: number; name: string; hoursPlayed: number };

export type Profile = {
  gamesTotal: number;
  gamesMatched: number;
  topGames: OwnedGame[];
};

export type Movie = {
  id: string; // IMDb ID, ex.: "tt0133093"
  title: string;
  year: number | null;
  genres: string[];
  rating: number | null;
  posterUrl: string | null;
  score: number; // 0 a 1
  because: string[]; // opcional no MVP, pode vir vazio
};

export type Game = {
  appid: number;
  name: string;
  genres: string[];
  headerImageUrl: string | null;
  score: number;
  because: string[];
};

export type RecommendationsRequest = { steamUrl: string; topK?: number };

export type RecommendationsResponse = {
  profile: Profile;
  movies: Movie[];
  games: Game[];
};

export type ApiErrorCode =
  | "INVALID_STEAM_URL"
  | "PROFILE_NOT_FOUND"
  | "LIBRARY_PRIVATE"
  | "EMPTY_PROFILE"
  | "STEAM_UNAVAILABLE"
  | "INTERNAL_ERROR"
  | "NETWORK_ERROR";
```

**`services/api.ts`**

```ts
import type {
  ApiErrorCode,
  RecommendationsRequest,
  RecommendationsResponse,
} from "../types";

const API_URL = import.meta.env.VITE_API_URL;

export class ApiError extends Error {
  constructor(
    public code: ApiErrorCode,
    message = "",
  ) {
    super(message);
  }
}

export async function getRecommendations(
  req: RecommendationsRequest,
): Promise<RecommendationsResponse> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}/recommendations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
  } catch {
    throw new ApiError("NETWORK_ERROR");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(
      body?.detail?.code ?? "INTERNAL_ERROR",
      body?.detail?.message,
    );
  }
  return res.json();
}
```

**`hooks/useRecommendations.ts`**

```ts
type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: RecommendationsResponse }
  | { status: "error"; error: ApiError };

export function useRecommendations() {
  const [state, setState] = useState<State>({ status: "idle" });

  async function search(steamUrl: string) {
    setState({ status: "loading" });
    try {
      const data = await getRecommendations({ steamUrl });
      setState({ status: "success", data });
    } catch (e) {
      setState({ status: "error", error: e as ApiError });
    }
  }

  return { state, search };
}
```

**Mensagens de erro** (um texto por código; o `Record` faz o compilador avisar se faltar algum):

```ts
export const errorMessages: Record<ApiErrorCode, string> = {
  INVALID_STEAM_URL: "O link não parece ser um perfil da Steam.",
  PROFILE_NOT_FOUND: "Não encontramos esse perfil.",
  LIBRARY_PRIVATE:
    "A biblioteca é privada. Deixe “Detalhes do jogo” como público no perfil.",
  EMPTY_PROFILE: "Nenhum dos seus jogos está na nossa base ainda.",
  STEAM_UNAVAILABLE: "A Steam não respondeu. Tente de novo em instantes.",
  INTERNAL_ERROR: "Algo deu errado do nosso lado.",
  NETWORK_ERROR: "Sem conexão com o servidor.",
};
```

### 5.4 Estados da tela

A tela precisa tratar: **inicial**, **carregando**, **erro** (texto por código), **sucesso** e **sucesso sem resultados**.

---

## 6. Contrato da API

### 6.1 Convenções

- Prefixo `/api/v1`.
- JSON em `camelCase`. No backend, uma classe base resolve isso para todos os schemas:

```python
# schemas/base.py
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
```

- Campo ausente é enviado como `null`.
- `score` vai de 0 a 1.

### 6.2 Endpoints

| Método | Rota                      | Descrição                                    |
| ------ | ------------------------- | -------------------------------------------- |
| `POST` | `/api/v1/recommendations` | Gera recomendações a partir da URL do perfil |
| `GET`  | `/api/v1/health`          | Confere se o backend está de pé              |

**Requisição**

```json
{ "steamUrl": "https://steamcommunity.com/id/fulano", "topK": 10 }
```

`topK`: de 1 a 50, padrão 10.

**Resposta 200**

```json
{
  "profile": {
    "gamesTotal": 120,
    "gamesMatched": 96,
    "topGames": [{ "appid": 1145360, "name": "Hades", "hoursPlayed": 85.5 }]
  },
  "movies": [
    {
      "id": "tt0133093",
      "title": "The Matrix",
      "year": 1999,
      "genres": ["Action", "Sci-Fi"],
      "rating": 8.7,
      "posterUrl": "https://image.tmdb.org/t/p/w342/xxxx.jpg",
      "score": 0.74,
      "because": ["Deus Ex"]
    }
  ],
  "games": [
    {
      "appid": 123,
      "name": "Example Game",
      "genres": ["RPG"],
      "headerImageUrl": "https://cdn.cloudflare.steamstatic.com/steam/apps/123/header.jpg",
      "score": 0.81,
      "because": ["Hades"]
    }
  ]
}
```

### 6.3 Erros

O backend usa `HTTPException` e o FastAPI devolve:

```json
{
  "detail": {
    "code": "LIBRARY_PRIVATE",
    "message": "A biblioteca deste perfil é privada."
  }
}
```

| `code`              | HTTP | Quando                                                                           |
| ------------------- | ---- | -------------------------------------------------------------------------------- |
| `INVALID_STEAM_URL` | 400  | URL fora do formato aceito                                                       |
| `PROFILE_NOT_FOUND` | 404  | Vanity inexistente ou perfil não encontrado                                      |
| `LIBRARY_PRIVATE`   | 403  | "Detalhes do jogo" não é público (a Steam devolve resposta sem a lista de jogos) |
| `EMPTY_PROFILE`     | 422  | Nenhum jogo da biblioteca existe no catálogo                                     |
| `STEAM_UNAVAILABLE` | 502  | Timeout ou erro da Steam                                                         |

---

## 7. ML: pipeline e experimentos

### 7.1 Pipeline (executado em ordem)

```
data/ (brutos)
  ├─ build_movies.py      → artifacts/movies.parquet
  ├─ build_games.py       → artifacts/games.parquet
  └─ build_embeddings.py  → artifacts/movies_emb.npy, games_emb.npy, manifest.json
```

**Filmes.** Juntar IMDb e The Movies Dataset por `imdb_id`. Sinopse e keywords vêm do TMDB, nota e votos do IMDb. Remover filmes sem sinopse e com poucos votos.

**Jogos.** Dataset de jogos da Steam com descrição, gêneros e tags (a escolher: ver seção 9). Manter apenas jogos com descrição, e considerar limitar o catálogo aos mais relevantes (por número de avaliações) para reduzir o tamanho.

**Texto por item.** Função única `build_item_text()` em `ml/pipeline/text.py`, usada para filmes e jogos.

**Embeddings.** `sentence-transformers` com `all-MiniLM-L6-v2` (384 dimensões, roda em CPU). Salvar `float32`, normalizados. Custo de armazenamento: cerca de 1,5 KB por item.

**Colunas mínimas dos parquet**

| `movies.parquet`                                                  | `games.parquet`           |
| ----------------------------------------------------------------- | ------------------------- |
| `id`, `title`, `year`, `genres`, `rating`, `votes`, `poster_path` | `appid`, `name`, `genres` |

A **ordem das linhas é o vínculo com o `.npy`**. Nunca reordenar ou filtrar um arquivo sem regenerar o outro.

### 7.2 Experimentos

Um arquivo YAML por experimento em `ml/experiments/configs/`, executado por `evaluate.py`. Parâmetros a comparar:

| Parâmetro                  | Variantes                                   |
| -------------------------- | ------------------------------------------- |
| Representação do texto     | TF-IDF (baseline) vs. embeddings MiniLM     |
| Peso por horas             | uniforme vs. `log(1 + h)`                   |
| Campos do texto (opcional) | só descrição vs. descrição + gêneros + tags |

**Avaliação**

- **Jogos:** esconder 20% dos jogos mais jogados de cada biblioteca, recomendar com o resto e medir **Recall@K / Hit Rate@K**. Comparar com a baseline de popularidade.
- **Filmes:** cada integrante recebe o top 10 da própria biblioteca e marca "faz sentido" ou não, gerando **Precision@10**.

Resultados e conclusões vão em um arquivo no repositório (tabela + um parágrafo por experimento), para alimentar o relatório da disciplina.

---

## 8. Convenções e trabalho em equipe

### 8.1 Código

|            | Backend (Python 3.11+)                                    | Frontend (TypeScript)                                                |
| ---------- | --------------------------------------------------------- | -------------------------------------------------------------------- |
| Nomes      | `snake_case` (funções, variáveis), `PascalCase` (classes) | `camelCase` (variáveis, funções), `PascalCase` (componentes e tipos) |
| Arquivos   | `snake_case.py`                                           | Componentes `PascalCase.tsx`, demais `camelCase.ts`                  |
| Formatação | `ruff format` (ou `black`)                                | Prettier                                                             |
| Lint       | `ruff check`                                              | ESLint (já vem no template do Vite)                                  |

Código, comentários e commits em **inglês**. Textos da interface em português.

### 8.2 Vocabulário comum

| Termo       | Significado                                            |
| ----------- | ------------------------------------------------------ |
| **Library** | Biblioteca do usuário (lista de jogos com horas)       |
| **Catalog** | Itens (filmes e jogos) que possuem embedding           |
| **Profile** | Vetor de gosto do usuário (média ponderada)            |
| **Score**   | Similaridade de cosseno entre o perfil e um item       |
| **Matched** | Jogos da biblioteca que existem no catálogo            |
| **Because** | Jogos da biblioteca que mais explicam uma recomendação |

### 8.3 Git

- `main` sempre funcionando. Sem push direto, alterações entram por Pull Request.
- Branches curtas: `feat/<assunto>`, `fix/<assunto>`.
- Mensagens de commit claras, no imperativo (`add steam url parser`).
- Todo PR é revisado por pelo menos **1 outra pessoa** do grupo.
- Mudou o contrato da API? Atualize no mesmo PR: `schemas/`, `types.ts` e a seção 6 deste documento.

---

## 9. Execução local

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # preencher STEAM_API_KEY
uvicorn app.main:app --reload     # http://localhost:8000/docs

# Frontend (criado com: npm create vite@latest frontend -- --template react-ts)
cd frontend
npm install
cp .env.example .env              # VITE_API_URL=http://localhost:8000/api/v1
npm run dev                       # http://localhost:5173

# Pipeline de ML (uma vez, ou quando os dados mudarem)
cd ml
pip install -r requirements.txt
python -m pipeline.build_movies
python -m pipeline.build_games
python -m pipeline.build_embeddings
```

---

## 10. Responsabilidades e pendências

| Pessoa | Frente      | Entregas principais                                              |
| ------ | ----------- | ---------------------------------------------------------------- |
| 1      | Frontend    | Componentes, hook, `api.ts`, `types.ts`, estados de tela         |
| 2      | Steam + API | `steam.py`, `routes/`, `schemas/`, tratamento de erros           |
| 3      | Dados       | `build_movies.py`, `build_games.py`, esquema dos parquet         |
| 4      | Modelo      | `build_embeddings.py`, `recommender.py`, experimentos e métricas |

**Ordem para destravar todo mundo**

1. Pessoa 2 publica a API com resposta **mockada** seguindo o contrato. A Pessoa 1 já trabalha em cima dela.
2. Pessoa 3 entrega uma primeira versão pequena dos parquet (algumas centenas de itens bastam).
3. Pessoa 4 gera os embeddings dessa amostra e implementa o recomendador.
4. Pessoa 2 troca o mock pelo recomendador real. O resto é escalar o catálogo e rodar os experimentos.

**Pendências**

- Escolher o dataset de jogos da Steam (precisa de `appid`, descrição, gêneros e tags). Responsável: Pessoa 3.
- Definir o tamanho do catálogo. Responsáveis: Pessoas 3 e 4.
- Definir onde hospedar os artefatos (Drive ou release do GitHub). Responsável: grupo.
