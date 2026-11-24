export type OwnedGame = {
  appid: number;
  name: string;
  hoursPlayed: number;
};

export type Profile = {
  gamesTotal: number;
  gamesMatched: number;
  avatarUrl: string | null;
  topGames: OwnedGame[];
};

export type Movie = {
  id: string;
  title: string;
  year: number | null;
  genres: string[];
  rating: number | null;
  posterUrl: string | null;
  score: number;
  because: string[];
};

export type Game = {
  appid: number;
  name: string;
  genres: string[];
  headerImageUrl: string | null;
  hoursPlayed: number;
  score: number;
  because: string[];
};

export type Album = {
  id: string;
  name: string;
  artist: string;
  year: number | null;
  coverUrl: string | null;
  genres: string[];
  score: number;
  because: string[];
};

export type RecommendationsRequest = {
  steamUrl: string;
  topK?: number;
};

export type RecommendationsResponse = {
  profile: Profile;
  movies: Movie[];
  albums: Album[];
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

export const ERROR_MESSAGES: Record<ApiErrorCode, { title: string; description: string }> = {
  INVALID_STEAM_URL: {
    title: "URL Inválida",
    description: "O link informado não parece ser um perfil válido da Steam. Exemplo: https://steamcommunity.com/id/seu_usuario",
  },
  PROFILE_NOT_FOUND: {
    title: "Perfil Não Encontrado",
    description: "Não conseguimos encontrar este perfil da Steam. Verifique se o link ou ID personalizado está correto.",
  },
  LIBRARY_PRIVATE: {
    title: "Biblioteca Privada",
    description: "A biblioteca deste perfil é privada. Acesse as configurações de privacidade da Steam e defina 'Detalhes do jogo' como público.",
  },
  EMPTY_PROFILE: {
    title: "Nenhum Jogo Mapeado",
    description: "Nenhum dos jogos da sua biblioteca foi encontrado no nosso catálogo de recomendações ainda.",
  },
  STEAM_UNAVAILABLE: {
    title: "Steam Indisponível",
    description: "A API da Steam demorou para responder ou está instável. Tente novamente em instantes.",
  },
  INTERNAL_ERROR: {
    title: "Erro Interno",
    description: "Ocorreu um erro no servidor ao processar suas recomendações.",
  },
  NETWORK_ERROR: {
    title: "Erro de Conexão",
    description: "Não foi possível se conectar ao servidor do AtlusIA. Verifique sua conexão ou tente mais tarde.",
  },
};
