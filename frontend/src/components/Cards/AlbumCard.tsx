import React from "react";
import { Sparkles, Music, Disc3 } from "lucide-react";
import type { Album } from "../../types";
import styles from "./AlbumCard.module.css";

interface AlbumCardProps {
  album: Album;
}

export const AlbumCard: React.FC<AlbumCardProps> = ({ album }) => {
  const matchPercentage = Math.round(album.score * 100);

  return (
    <div className={styles.card}>
      <div className={styles.coverContainer}>
        {album.coverUrl ? (
          <img
            src={album.coverUrl}
            alt={album.name}
            className={styles.cover}
            loading="lazy"
            onError={(e) => {
              (e.target as HTMLElement).style.display = "none";
            }}
          />
        ) : null}
        <div className={styles.coverFallback}>
          <Music size={40} className={styles.fallbackIcon} />
        </div>

        <div className={styles.scoreBadge}>
          <Sparkles size={13} />
          <span>{matchPercentage}% Match</span>
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.header}>
          <h3 className={styles.title} title={album.name}>
            {album.name}
          </h3>
          {album.year && <span className={styles.year}>{album.year}</span>}
        </div>

        <div className={styles.artistRow}>
          <Disc3 size={14} className={styles.artistIcon} />
          <span className={styles.artist}>{album.artist}</span>
        </div>

        {album.genres && album.genres.length > 0 && (
          <div className={styles.genresRow}>
            {album.genres.slice(0, 3).map((g, idx) => (
              <span key={idx} className={styles.genreTag}>
                {g}
              </span>
            ))}
          </div>
        )}

        {album.because && album.because.length > 0 && (
          <div className={styles.becauseBox}>
            <span className={styles.becauseLabel}>Com base em:</span>
            <div className={styles.becauseTags}>
              {album.because.map((item, i) => (
                <span key={i} className={styles.becauseTag}>
                  {item}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
