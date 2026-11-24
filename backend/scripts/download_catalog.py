"""Script para baixar o catálogo global de jogos da Steam a partir da Release do GitHub."""

import argparse
import sys
from pathlib import Path

from app.config import settings
from app.game_catalog import download_catalog


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baixa o arquivo steam_tratado.parquet publicado no GitHub Releases."
    )
    parser.add_argument(
        "--url",
        default=settings.steam_catalog_url,
        help="URL direta do arquivo parquet no GitHub Releases.",
    )
    parser.add_argument(
        "--dest",
        default=str(settings.game_catalog_path),
        help="Caminho local de destino para o arquivo.",
    )
    args = parser.parse_args()

    dest_path = Path(args.dest)
    print(f"Baixando catálogo de:\n  {args.url}")
    print(f"Para:\n  {dest_path}")

    try:
        download_catalog(args.url, dest_path)
        print("Download concluído e validado com sucesso!")
    except Exception as exc:
        print(f"Erro ao baixar o catálogo: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
