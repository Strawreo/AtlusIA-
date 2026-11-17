import React from "react";
import { AlertTriangle, RotateCcw } from "lucide-react";
import { ERROR_MESSAGES, type ApiErrorCode } from "../../types";
import type { ApiError } from "../../services/api";
import styles from "./ErrorState.module.css";

interface ErrorBoundaryState {
  error: ApiError | null;
}

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    const apiError =
      error instanceof ApiError
        ? error
        : new ApiError("INTERNAL_ERROR", error.message ?? "Erro inesperado durante a renderização.");
    return { error: apiError };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Erro capturado pelo ErrorBoundary:", error, errorInfo);
  }

  render() {
    if (this.state.error) {
      return <ErrorState error={this.state.error} onRetry={() => this.setState({ error: null })} />;
    }
    return this.props.children;
  }
}

interface ErrorStateProps {
  error: ApiError;
  onRetry: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry }) => {
  const code: ApiErrorCode = (error.code as ApiErrorCode) ?? "INTERNAL_ERROR";
  const message = ERROR_MESSAGES[code] ?? ERROR_MESSAGES.INTERNAL_ERROR;

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
