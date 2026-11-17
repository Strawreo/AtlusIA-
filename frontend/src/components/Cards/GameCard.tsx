import React from "react";
import { Gamepad2, Sparkles, ExternalLink } from "lucide-react";
import type { Game } from "../../types";
import styles from "./GameCard.module.css";

interface GameCardProps {
  game: Game;
}

export const GameCard: React.FC<GameCardProps> = ({ game }) => {
  const matchPercentage = Math.round(game.score * 100);
  const steamStoreUrl = `https://store.steampowered.com/app/${game.appid}`;

  return (
    <div className={styles.card}>
      <div className={styles.imageContainer}>
        {game.headerImageUrl ? (
          <img
            src={game.headerImageUrl}
            alt={game.name}
            className={styles.image}
            loading="lazy"
            onError={(e) => {
              (e.target as HTMLElement).style.display = "none";
            }}
          />
        ) : null}
        <div className={styles.imageFallback}>
          <Gamepad2 size={40} className={styles.fallbackIcon} />
        </div>

        <div className={styles.scoreBadge}>
          <Sparkles size={13} />
          <span>{matchPercentage}% Match</span>
        </div>
      </div>

      <div className={styles.content}>
        <div className={styles.header}>
          <h3 className={styles.title} title={game.name}>
            {game.name}
          </h3>
          <a
            href={steamStoreUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.steamLink}
            title="Ver na Loja da Steam"
          >
            <ExternalLink size={15} />
          </a>
        </div>

        {game.genres && game.genres.length > 0 && (
          <div className={styles.genresRow}>
            {game.genres.slice(0, 3).map((g, idx) => (
              <span key={idx} className={styles.genreTag}>
                {g}
              </span>
            ))}
          </div>
        )}

        {game.because && game.because.length > 0 && (
          <div className={styles.becauseBox}>
            <span className={styles.becauseLabel}>Com base em:</span>
            <div className={styles.becauseTags}>
              {game.because.map((item, i) => (
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
