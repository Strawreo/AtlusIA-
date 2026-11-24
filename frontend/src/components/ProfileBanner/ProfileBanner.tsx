import React from "react";
import { Gamepad2, Clock, CheckCircle2, Info, User } from "lucide-react";
import type { Profile } from "../../types";
import styles from "./ProfileBanner.module.css";

interface ProfileBannerProps {
  profile: Profile;
}

export const ProfileBanner: React.FC<ProfileBannerProps> = ({ profile }) => {
  return (
    <div className={styles.banner}>
      <div className={styles.avatarWrapper}>
        {profile.avatarUrl ? (
          <img
            src={profile.avatarUrl}
            alt={`Foto de perfil do usuário`}
            className={styles.avatar}
            loading="lazy"
          />
        ) : (
          <div className={styles.avatarFallback}>
            <User size={40} className={styles.fallbackIcon} />
          </div>
        )}
      </div>

      <div className={styles.statsRow}>
        <div className={styles.statBox}>
          <div className={styles.statIconWrapper}>
            <Gamepad2 size={22} className={styles.statIcon} />
          </div>
          <div>
            <div className={styles.statValue}>{profile.gamesTotal}</div>
            <div className={styles.statLabel}>Jogos na Biblioteca</div>
          </div>
        </div>

        <div className={styles.statBox}>
          <div className={styles.statIconWrapperSuccess}>
            <CheckCircle2 size={22} className={styles.statIconSuccess} />
          </div>
          <div>
            <div className={styles.statValue}>{profile.gamesMatched}</div>
            <div className={styles.statLabel}>Mapeados no Catálogo</div>
          </div>
        </div>

        <div className={styles.weightingPill}>
          <Info size={16} />
          <span>Ponderação: <code>log(1 + horas)</code></span>
        </div>
      </div>

      {profile.topGames && profile.topGames.length > 0 && (
        <div className={styles.topGamesSection}>
          <span className={styles.topGamesTitle}>Seus Jogos Mais Relevantes:</span>
          <div className={styles.gameTags}>
            {profile.topGames.map((game) => (
              <div key={game.appid} className={styles.gameTag}>
                <span className={styles.gameName}>{game.name}</span>
                <span className={styles.gameHours}>
                  <Clock size={12} />
                  {game.hoursPlayed.toFixed(1)}h
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
