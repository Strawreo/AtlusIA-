import React from "react";
import { Gamepad2, Film, Sparkles } from "lucide-react";
import styles from "./Header.module.css";

export const Header: React.FC = () => {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <div className={styles.logoGroup}>
          <div className={styles.logoIcon}>
            <Gamepad2 className={styles.iconSteam} size={24} />
            <Sparkles className={styles.iconSparkle} size={16} />
            <Film className={styles.iconFilm} size={20} />
          </div>
          <div>
            <h1 className={styles.title}>
              Atlus<span className={styles.highlight}>IA</span>
            </h1>
            <p className={styles.subtitle}>
              Recomendador Híbrido Steam ➔ Filmes & Jogos
            </p>
          </div>
        </div>

        <div className={styles.badgeGroup}>
          <span className={styles.badge}>TF-IDF + Fatoração de Matrizes</span>
        </div>
      </div>
    </header>
  );
};
