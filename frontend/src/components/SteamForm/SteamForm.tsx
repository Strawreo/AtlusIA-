import React, { useState } from "react";
import { Search, Sparkles, Gamepad2, HeartHandshake, Crosshair } from "lucide-react";
import styles from "./SteamForm.module.css";

interface SteamFormProps {
  onSearch: (steamUrl: string) => void;
  isLoading: boolean;
}

export const SteamForm: React.FC<SteamFormProps> = ({ onSearch, isLoading }) => {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onSearch(url.trim());
    }
  };

  const handlePreset = (presetKey: string) => {
    const presetUrl = `https://steamcommunity.com/id/preset-${presetKey}`;
    setUrl(presetUrl);
    onSearch(presetUrl);
  };

  return (
    <div className={styles.wrapper}>
      <div className={styles.headerBox}>
        <h2 className={styles.headline}>
          Descubra filmes e jogos baseados no seu gosto da <span className={styles.steamText}>Steam</span>
        </h2>
        <p className={styles.subtext}>
          Insira o link do seu perfil público da Steam. Nossa Inteligência Artificial analisa seus jogos mais jogados
          e calcula afinidades temáticas e colaborativas.
        </p>
      </div>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.inputContainer}>
          <Search className={styles.searchIcon} size={20} />
          <input
            type="text"
            className={styles.input}
            placeholder="https://steamcommunity.com/id/seu_perfil ou SteamID64"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className={styles.submitBtn} disabled={isLoading || !url.trim()}>
            {isLoading ? (
              <span className={styles.loader}></span>
            ) : (
              <>
                <Sparkles size={18} />
                <span>Recomendar</span>
              </>
            )}
          </button>
        </div>
      </form>

      <div className={styles.presetsArea}>
        <span className={styles.presetsLabel}>Ou experimente com bibliotecas prontas:</span>
        <div className={styles.presetButtons}>
          <button
            type="button"
            className={styles.presetBtn}
            onClick={() => handlePreset("souls")}
            disabled={isLoading}
          >
            <Gamepad2 size={16} className={styles.presetIconSouls} />
            Souls-like / RPG
          </button>
          <button
            type="button"
            className={styles.presetBtn}
            onClick={() => handlePreset("cozy")}
            disabled={isLoading}
          >
            <HeartHandshake size={16} className={styles.presetIconCozy} />
            Cozy / Relax
          </button>
          <button
            type="button"
            className={styles.presetBtn}
            onClick={() => handlePreset("fps")}
            disabled={isLoading}
          >
            <Crosshair size={16} className={styles.presetIconFps} />
            FPS / Guerra
          </button>
        </div>
      </div>
    </div>
  );
};
