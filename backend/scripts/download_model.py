"""Script para baixar e extrair o pacote modelo_final.zip do GitHub Releases."""

import argparse
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

import httpx

from app.config import PROJECT_ROOT, settings


def download_and_extract_model(
    url: str,
    dest_dir: Path,
    client: httpx.Client | None = None,
) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)

    http_client = client or httpx.Client(timeout=300.0, follow_redirects=True)
    should_close = client is None

    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_file:
            tmp_zip = Path(tmp_file.name)

        print(f"Baixando modelo de:\n  {url}")
        with http_client.stream("GET", url) as response:
            if response.status_code != 200:
                raise ValueError(
                    f"Falha ao baixar o modelo. HTTP Status: {response.status_code}"
                )
            with open(tmp_zip, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=65536):
                    f.write(chunk)

        print(f"Extraindo em:\n  {dest_dir}")
        with zipfile.ZipFile(tmp_zip, "r") as zf:
            zf.extractall(dest_dir)

        tmp_zip.unlink(missing_ok=True)
        print("Modelo extraído com sucesso!")
    finally:
        if should_close:
            http_client.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Baixa e extrai modelo_final.zip do GitHub Releases."
    )
    parser.add_argument(
        "--url",
        default=settings.model_artifacts_url,
        help="URL direta do arquivo modelo_final.zip no GitHub Releases.",
    )
    parser.add_argument(
        "--dest",
        default=str(settings.model_dir_path),
        help="Diretório de destino para os artefatos.",
    )
    args = parser.parse_args()

    if not args.url:
        print("Erro: Nenhuma URL configurada ou informada via --url.", file=sys.stderr)
        sys.exit(1)

    try:
        download_and_extract_model(args.url, Path(args.dest))
    except Exception as exc:
        print(f"Erro ao baixar modelo: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
