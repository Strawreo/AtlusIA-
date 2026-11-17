import { useState } from "react";
import { ApiError, getRecommendations } from "../services/api";
import type { RecommendationsResponse } from "../types";

export type SearchState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: RecommendationsResponse }
  | { status: "error"; error: ApiError };

export function useRecommendations() {
  const [state, setState] = useState<SearchState>({ status: "idle" });

  async function search(steamUrl: string) {
    if (!steamUrl.trim()) {
      setState({
        status: "error",
        error: new ApiError("INVALID_STEAM_URL", "Por favor, insira o link do perfil."),
      });
      return;
    }

    setState({ status: "loading" });
    try {
      const data = await getRecommendations({ steamUrl });
      setState({ status: "success", data });
    } catch (e) {
      if (e instanceof ApiError) {
        setState({ status: "error", error: e });
      } else {
        setState({
          status: "error",
          error: new ApiError("INTERNAL_ERROR", (e as Error)?.message),
        });
      }
    }
  }

  function reset() {
    setState({ status: "idle" });
  }

  return { state, search, reset };
}
