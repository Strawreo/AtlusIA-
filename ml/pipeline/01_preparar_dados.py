"""Pipeline de Preparação e Limpeza de Dados (Steam Games + IMDb Movies).

Modularizado a partir das seções 1.1 e 1.2 do notebook ModeloProjeto.ipynb.

Fontes dos dados:
- Steam: Hugging Face (FronkonGames/steam-games-dataset) ou arquivo local
- Filmes: Kaggle (raedaddala/top-500-600-movies-of-each-year-from-1960-to-2024)
"""

import argparse
import ast
import html
from pathlib import Path
import re
import sys

import numpy as np
import pandas as pd

_ITEM = re.compile(r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"")


def parse_list(v):
    """Converte repr de numpy, lista stringificada ou iterável em list[str]."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return []
    if isinstance(v, (list, tuple, np.ndarray)):
        return [str(x).strip() for x in v if str(x).strip()]
    return [(a or b).strip() for a, b in _ITEM.findall(str(v)) if (a or b).strip()]


def parse_tags(v):
    """Converte dict {tag: votos}, lista ou texto em list[str] ordenada por votos."""
    if isinstance(v, dict):
        return [str(k) for k, _ in sorted(v.items(), key=lambda kv: -(kv[1] or 0))]
    if isinstance(v, str) and v.strip().startswith("{"):
        try:
            return parse_tags(ast.literal_eval(v))
        except (ValueError, SyntaxError):
            pass
    return parse_list(v)


def clean_text(v):
    if not isinstance(v, str):
        return np.nan
    v = html.unescape(re.sub(r"<[^>]+>", " ", v))
    return re.sub(r"\s+", " ", v).strip() or np.nan


def parse_votes(v):
    """'2.5K' -> 2500, '1.2M' -> 1200000, '114' -> 114."""
    if pd.isna(v):
        return np.nan
    if isinstance(v, (int, float)):
        return float(v)
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([KMB]?)", str(v).strip().upper().replace(",", ""))
    if not m:
        return np.nan
    num, suf = m.groups()
    return round(float(num) * {"": 1, "K": 1e3, "M": 1e6, "B": 1e9}[suf])


def parse_duration(v):
    """'1h 16m' / '1h16min' -> 76, '2h' -> 120, '45m' -> 45."""
    if pd.isna(v):
        return np.nan
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).lower()
    h = re.search(r"(\d+)\s*h", s)
    m = re.search(r"(\d+)\s*m", s)
    if not (h or m):
        return np.nan
    return (int(h.group(1)) if h else 0) * 60 + (int(m.group(1)) if m else 0)


def preparar_steam(caminho_entrada: Path, caminho_saida: Path) -> pd.DataFrame:
    """Aplica o fluxo de limpeza e tratamento dos dados da Steam."""
    print(f"Lendo base Steam de {caminho_entrada}...")
    df = pd.read_parquet(caminho_entrada) if str(caminho_entrada).endswith(".parquet") else pd.read_csv(caminho_entrada)
    print(f"Linhas brutas: {len(df):,}")

    # Remove duplicados por appID
    df = df.drop_duplicates(subset=["appID"]).reset_index(drop=True)

    # Limpeza de texto e colunas
    if "texto_modelo" not in df.columns:
        desc = df["about_the_game"].fillna(df["short_description"]).fillna("")
        df["texto_modelo"] = desc.map(clean_text).fillna("")

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(caminho_saida, index=False)
    print(f"Base Steam tratada salva em {caminho_saida} ({len(df):,} jogos).")
    return df


def preparar_filmes(caminho_entrada: Path, caminho_saida: Path) -> pd.DataFrame:
    """Aplica o fluxo de limpeza e conversão do dataset de filmes do IMDb."""
    print(f"Lendo base de filmes de {caminho_entrada}...")
    df = pd.read_csv(caminho_entrada, low_memory=False)
    print(f"Linhas brutas: {len(df):,}")

    cols_drop = [
        "opening_weekend_gross", "gross_us_canada", "filming_locations",
        "gross_worldwide", "budget", "awards_content"
    ]
    df.drop(columns=cols_drop, inplace=True, errors="ignore")
    df = df.dropna(subset=["id"]).drop_duplicates(subset=["id"]).reset_index(drop=True)

    df["votes"] = df["votes"].map(parse_votes)
    if "duration" in df.columns:
        df["duration"] = df["duration"].map(parse_duration)

    df["genres"] = df["genres"].map(parse_list)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(caminho_saida, index=False)
    print(f"Base de filmes tratada salva em {caminho_saida} ({len(df):,} filmes).")
    return df


def main():
    parser = argparse.ArgumentParser(description="Prepara datasets da Steam e do IMDb.")
    parser.add_argument("--steam-in", default="ml/artifacts/steam_tratado.parquet")
    parser.add_argument("--steam-out", default="ml/artifacts/steam_tratado.parquet")
    parser.add_argument("--filmes-in", default=None)
    parser.add_argument("--filmes-out", default="ml/artifacts/filmes_tratado.parquet")
    args = parser.parse_args()

    if Path(args.steam_in).is_file():
        preparar_steam(Path(args.steam_in), Path(args.steam_out))

    if args.filmes_in and Path(args.filmes_in).is_file():
        preparar_filmes(Path(args.filmes_in), Path(args.filmes_out))


if __name__ == "__main__":
    main()
