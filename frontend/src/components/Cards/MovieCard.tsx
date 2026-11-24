import React from "react";
import { Star, Film, Sparkles } from "lucide-react";
import type { Movie } from "../../types";
import styles from "./MovieCard.module.css";

interface MovieCardProps {
  movie: Movie;
}

export const MovieCard: React.FC<MovieCardProps> = ({ movie }) => {
  const matchPercentage = Math.round(movie.score * 100);

  return (
    <div className={styles.card}>
      <div className={styles.posterContainer}>
        {movie.posterUrl ? (
          <img
            src={movie.posterUrl}
            alt={movie.title}
            className={styles.poster}
            loading="lazy"
            onError={(e) => {
              // Image fallback if load fails
              (e.target as HTMLElement).style.display = "none";
            }}
          />
        ) : (
          <div className={styles.posterFallback}>
            <Film size={40} className={styles.fallbackIcon} />
          </div>
        )}

        <div className={styles.scoreBadge}>
          <Sparkles size={13} />
          <span>{matchPercentage}% Match</span>
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.header}>
          <h3 className={styles.title} title={movie.title}>
            {movie.title}
          </h3>
          {movie.year && <span className={styles.year}>{movie.year}</span>}
        </div>

        {movie.rating !== null && (
          <div className={styles.ratingRow}>
            <Star size={14} className={styles.starIcon} />
            <span className={styles.ratingValue}>{movie.rating.toFixed(1)}</span>
            <span className={styles.ratingMax}>/10</span>
          </div>
        )}

        {movie.genres && movie.genres.length > 0 && (
          <div className={styles.genresRow}>
            {movie.genres.slice(0, 3).map((g, idx) => (
              <span key={idx} className={styles.genreTag}>
                {g}
              </span>
            ))}
          </div>
        )}

        {movie.because && movie.because.length > 0 && (
          <div className={styles.becauseBox}>
            <span className={styles.becauseLabel}>Porque você jogou:</span>
            <div className={styles.becauseTags}>
              {movie.because.map((term, i) => (
                <span key={i} className={styles.becauseTag}>
                  {term}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
