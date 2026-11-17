import React from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { ERROR_MESSAGES } from "../../types";
import type { ApiError } from "../../services/api";
import styles from "./ErrorState.module.css";

interface ErrorStateProps {
  error: ApiError;
  onRetry: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry }) => {
  const message = ERROR_MESSAGES[error.code];

  return (
    <div className={styles.wrapper}>
      <div className={styles.iconWrapper}>
        <AlertTriangle size={32} className={styles.icon} />
      </div>
      <h2 className={styles.title}>{message.title}</h2>
      <p className={styles.description}>{message.description}</p>
      {error.message && <p className={styles.detail}>{error.message}</p>}
      <button type="button" className={styles.retryBtn} onClick={onRetry}>
        <RotateCcw size={16} />
        <span>Tentar novamente</span>
      </button>
    </div>
  );
};
