import React from "react";
import { SearchX } from "lucide-react";
import styles from "./EmptyState.module.css";

interface EmptyStateProps {
  onRetry: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ onRetry }) => {
  return (
    <div className={styles.wrapper}>
      <div className={styles.iconWrapper}>
        <SearchX size={32} className={styles.icon} />
      </div>
      <h2 className={styles.title}>Nada por aqui ainda</h2>
      <p className={styles.description}>
        Não encontramos recomendações para este perfil. Tente outra biblioteca.
      </p>
      <button type="button" className={styles.retryBtn} onClick={onRetry}>
        Buscar outro perfil
      </button>
    </div>
  );
};
