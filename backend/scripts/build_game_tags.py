"""Script legado (DEPRECIADO).

O sistema agora utiliza o catálogo global steam_tratado.parquet (102.868 jogos)
hospedado no GitHub Releases e carregado automaticamente pelo backend.

Para baixar o catálogo manualmente, utilize:
    python -m scripts.download_catalog
"""

import sys


def main() -> None:
    print(
        "AVISO: O script 'build_game_tags' foi depreciado.\n"
        "O backend agora utiliza o catálogo global 'steam_tratado.parquet' (~102k jogos).\n"
        "O download ocorre automaticamente na primeira execução do servidor, ou via:\n"
        "    python -m scripts.download_catalog",
        file=sys.stderr,
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
