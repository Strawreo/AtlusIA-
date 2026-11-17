import type {
  ApiErrorCode,
  RecommendationsRequest,
  RecommendationsResponse,
} from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  code: ApiErrorCode;

  constructor(code: ApiErrorCode, message = "") {
    super(message);
    this.name = "ApiError";
    this.code = code;
  }
}

// Dados simulados para demonstração enquanto o backend não existe.
// Cada preset corresponde a um botão da tela ("bibliotecas prontas").
export const MOCK_PRESETS: Record<string, RecommendationsResponse> = {
  souls: {
    profile: {
      gamesTotal: 45,
      gamesMatched: 38,
      topGames: [
        { appid: 1245620, name: "ELDEN RING", hoursPlayed: 180.5 },
        { appid: 374320, name: "DARK SOULS III", hoursPlayed: 125.0 },
        { appid: 292030, name: "The Witcher 3: Wild Hunt", hoursPlayed: 95.2 },
      ],
    },
    movies: [
      {
        id: "tt0082766",
        title: "Conan the Barbarian",
        year: 1982,
        genres: ["Action", "Adventure", "Fantasy"],
        rating: 6.9,
        posterUrl: null,
        score: 0.89,
        because: ["dark fantasy", "sword and sorcery", "knight"],
      },
      {
        id: "tt0104652",
        title: "Army of Darkness",
        year: 1992,
        genres: ["Action", "Comedy", "Fantasy", "Horror"],
        rating: 7.4,
        posterUrl: null,
        score: 0.84,
        because: ["demon", "medieval", "survival"],
      },
      {
        id: "tt0116136",
        title: "DragonHeart",
        year: 1996,
        genres: ["Action", "Adventure", "Fantasy"],
        rating: 6.5,
        posterUrl: null,
        score: 0.81,
        because: ["dragon", "medieval", "knight"],
      },
      {
        id: "tt0085444",
        title: "Krull",
        year: 1983,
        genres: ["Action", "Adventure", "Fantasy", "Sci-Fi"],
        rating: 6.1,
        posterUrl: null,
        score: 0.78,
        because: ["dark fantasy", "sword", "quest"],
      },
    ],
    albums: [
      {
        id: "mock-souls-1",
        name: "Nightfall in Middle-Earth",
        artist: "Blind Guardian",
        year: 1998,
        coverUrl: null,
        genres: ["Power Metal", "Fantasy"],
        score: 0.88,
        because: ["ELDEN RING", "dark fantasy"],
      },
      {
        id: "mock-souls-2",
        name: "Jomsviking",
        artist: "Amon Amarth",
        year: 2016,
        coverUrl: null,
        genres: ["Melodic Death Metal"],
        score: 0.83,
        because: ["DARK SOULS III", "medieval"],
      },
      {
        id: "mock-souls-3",
        name: "The Mantle",
        artist: "Agalloch",
        year: 2002,
        coverUrl: null,
        genres: ["Dark Folk", "Atmospheric"],
        score: 0.79,
        because: ["ELDEN RING", "melancholy"],
      },
    ],
    games: [
      {
        appid: 1091500,
        name: "Cyberpunk 2077",
        genres: ["RPG", "Action"],
        headerImageUrl: null,
        score: 0.92,
        because: ["ELDEN RING", "The Witcher 3: Wild Hunt"],
      },
      {
        appid: 1145360,
        name: "Hades",
        genres: ["Action", "Indie", "RPG"],
        headerImageUrl: null,
        score: 0.88,
        because: ["DARK SOULS III"],
      },
    ],
  },
  cozy: {
    profile: {
      gamesTotal: 62,
      gamesMatched: 54,
      topGames: [
        { appid: 413150, name: "Stardew Valley", hoursPlayed: 210.0 },
        { appid: 105600, name: "Terraria", hoursPlayed: 140.8 },
        { appid: 431960, name: "Wallpaper Engine", hoursPlayed: 88.0 },
      ],
    },
    movies: [
      {
        id: "tt4016454",
        title: "Over the Garden Wall",
        year: 2014,
        genres: ["Animation", "Adventure", "Family"],
        rating: 8.8,
        posterUrl: null,
        score: 0.91,
        because: ["friendship", "family", "cozy"],
      },
      {
        id: "tt0119822",
        title: "My Neighbor Totoro",
        year: 1988,
        genres: ["Animation", "Family", "Fantasy"],
        rating: 8.2,
        posterUrl: null,
        score: 0.87,
        because: ["nature", "friendship", "magic"],
      },
      {
        id: "tt1160419",
        title: "Dune",
        year: 2021,
        genres: ["Sci-Fi", "Adventure"],
        rating: 8.0,
        posterUrl: null,
        score: 0.75,
        because: ["world building", "adventure"],
      },
    ],
    albums: [
      {
        id: "mock-cozy-1",
        name: "Punisher",
        artist: "Phoebe Bridgers",
        year: 2020,
        coverUrl: null,
        genres: ["Indie Folk"],
        score: 0.9,
        because: ["Stardew Valley", "cozy"],
      },
      {
        id: "mock-cozy-2",
        name: "For Emma, Forever Ago",
        artist: "Bon Iver",
        year: 2007,
        coverUrl: null,
        genres: ["Indie Folk"],
        score: 0.85,
        because: ["Stardew Valley", "introspective"],
      },
      {
        id: "mock-cozy-3",
        name: "Fleet Foxes",
        artist: "Fleet Foxes",
        year: 2008,
        coverUrl: null,
        genres: ["Indie Folk", "Baroque Pop"],
        score: 0.8,
        because: ["Terraria", "nature"],
      },
    ],
    games: [
      {
        appid: 1147550,
        name: "Slime Rancher 2",
        genres: ["Action", "Adventure", "Casual", "Indie"],
        headerImageUrl: null,
        score: 0.95,
        because: ["Stardew Valley"],
      },
      {
        appid: 1677740,
        name: "Stray",
        genres: ["Action", "Adventure", "Indie"],
        headerImageUrl: null,
        score: 0.89,
        because: ["Terraria"],
      },
    ],
  },
  fps: {
    profile: {
      gamesTotal: 80,
      gamesMatched: 72,
      topGames: [
        { appid: 730, name: "Counter-Strike 2", hoursPlayed: 650.0 },
        { appid: 271590, name: "Grand Theft Auto V", hoursPlayed: 310.4 },
        { appid: 1172470, name: "Apex Legends", hoursPlayed: 190.2 },
      ],
    },
    movies: [
      {
        id: "tt0277327",
        title: "We Were Soldiers",
        year: 2002,
        genres: ["Action", "History", "War"],
        rating: 7.2,
        posterUrl: null,
        score: 0.9,
        because: ["soldier", "war", "battle"],
      },
      {
        id: "tt0120863",
        title: "Black Hawk Down",
        year: 2001,
        genres: ["Action", "History", "War"],
        rating: 7.7,
        posterUrl: null,
        score: 0.86,
        because: ["military", "squad", "tactical"],
      },
    ],
    albums: [
      {
        id: "mock-fps-1",
        name: "Toxicity",
        artist: "System of a Down",
        year: 2001,
        coverUrl: null,
        genres: ["Nu Metal", "Alternative Metal"],
        score: 0.87,
        because: ["Counter-Strike 2", "aggression"],
      },
      {
        id: "mock-fps-2",
        name: "The Downward Spiral",
        artist: "Nine Inch Nails",
        year: 1994,
        coverUrl: null,
        genres: ["Industrial Rock"],
        score: 0.82,
        because: ["Apex Legends", "industrial"],
      },
      {
        id: "mock-fps-3",
        name: "Rage Against the Machine",
        artist: "Rage Against the Machine",
        year: 1992,
        coverUrl: null,
        genres: ["Rap Metal", "Funk Metal"],
        score: 0.79,
        because: ["Grand Theft Auto V", "rebellion"],
      },
    ],
    games: [
      {
        appid: 582660,
        name: "Black Desert",
        genres: ["MMORPG", "Action"],
        headerImageUrl: null,
        score: 0.82,
        because: ["Counter-Strike 2"],
      },
    ],
  },
};

// Cada preset é identificado por uma palavra-chave na URL informada,
// por exemplo: https://steamcommunity.com/id/preset-souls
const PRESET_KEYWORDS: Array<{ match: string; preset: keyof typeof MOCK_PRESETS }> = [
  { match: "souls", preset: "souls" },
  { match: "cozy", preset: "cozy" },
  { match: "fps", preset: "fps" },
];

const MOCK_DELAY_MS = 600;

function mockFromUrl(steamUrl: string): RecommendationsResponse | null {
  const lower = steamUrl.toLowerCase();
  const found = PRESET_KEYWORDS.find((p) => lower.includes(p.match));
  return found ? MOCK_PRESETS[found.preset] : null;
}

export async function getRecommendations(
  req: RecommendationsRequest,
): Promise<RecommendationsResponse> {
  const steamUrl = req.steamUrl.trim();

  // 1. Bibliotecas demonstrativas: o botão da tela gera uma URL com "preset-<nome>".
  const preset = mockFromUrl(steamUrl);
  if (preset) {
    await new Promise((resolve) => setTimeout(resolve, MOCK_DELAY_MS));
    return preset;
  }

  // 2. Valida o formato antes de tentar rede (feedback imediato sem backend).
  if (!/^https?:\/\/(www\.)?steamcommunity\.com\//.test(steamUrl) && !/^\d{17}$/.test(steamUrl)) {
    throw new ApiError("INVALID_STEAM_URL");
  }

  // 3. Backend real (ainda não existe no MVP). Sem servidor no ar, cai no mock
  //    padrão para a demonstração continuar funcionando.
  try {
    const res = await fetch(`${API_URL}/recommendations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ steamUrl, topK: req.topK }),
    });

    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new ApiError(
        body?.detail?.code ?? "INTERNAL_ERROR",
        body?.detail?.message,
      );
    }

    return (await res.json()) as RecommendationsResponse;
  } catch (e) {
    if (e instanceof ApiError) throw e;

    // Backend offline: propagamos o erro para a tela mostrar ErrorState,
    // em vez de exibir silenciosamente dados simulados de um URL real.
    throw new ApiError("NETWORK_ERROR", (e as Error)?.message ?? "Não foi possível conectar ao servidor.");
  }
}
