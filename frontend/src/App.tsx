import { Film, Music, Gamepad2 } from "lucide-react";
import { useRecommendations } from "./hooks/useRecommendations";
import { Header } from "./components/Header/Header";
import { SteamForm } from "./components/SteamForm/SteamForm";
import { ProfileBanner } from "./components/ProfileBanner/ProfileBanner";
import { MovieCard } from "./components/Cards/MovieCard";
import { AlbumCard } from "./components/Cards/AlbumCard";
import { GameCard } from "./components/Cards/GameCard";
import { LoadingSkeleton } from "./components/States/LoadingSkeleton";
import { ErrorState } from "./components/States/ErrorState";
import { EmptyState } from "./components/States/EmptyState";
import styles from "./App.module.css";

function App() {
  const { state, search, reset } = useRecommendations();

  const isLoading = state.status === "loading";
  const data = state.status === "success" ? state.data : null;
  const semResultados =
    data !== null &&
    data.movies.length === 0 &&
    data.albums.length === 0 &&
    data.games.length === 0;

  return (
    <div className={styles.page}>
      <Header />

      <main className={styles.main}>
        {state.status !== "success" && (
          <SteamForm onSearch={search} isLoading={isLoading} />
        )}

        {isLoading && <LoadingSkeleton />}

        {state.status === "error" && (
          <ErrorState error={state.error} onRetry={reset} />
        )}

        {data !== null && (
          <>
            <ProfileBanner profile={data.profile} />

            {semResultados && <EmptyState onRetry={reset} />}

            {data.movies.length > 0 && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>
                  <Film size={22} className={styles.sectionIcon} />
                  Filmes recomendados
                </h2>
                <div className={styles.grid}>
                  {data.movies.map((movie) => (
                    <MovieCard key={movie.id} movie={movie} />
                  ))}
                </div>
              </section>
            )}

            {data.albums.length > 0 && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>
                  <Music size={22} className={styles.sectionIcon} />
                  Álbuns recomendados
                </h2>
                <div className={styles.grid}>
                  {data.albums.map((album) => (
                    <AlbumCard key={album.id} album={album} />
                  ))}
                </div>
              </section>
            )}

            {data.games.length > 0 && (
              <section className={styles.section}>
                <h2 className={styles.sectionTitle}>
                  <Gamepad2 size={22} className={styles.sectionIcon} />
                  Jogos recomendados
                </h2>
                <div className={styles.grid}>
                  {data.games.map((game) => (
                    <GameCard key={game.appid} game={game} />
                  ))}
                </div>
              </section>
            )}

            <div className={styles.actions}>
              <button type="button" className={styles.resetBtn} onClick={reset}>
                Buscar outro perfil
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default App;
