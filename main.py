"""
main.py — Ponto de entrada do jogo Isolation.

Como executar:
    python main.py

Dependências:
    pip install pygame
"""

import sys


def main():
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("=" * 50)
        print("ERRO: pygame nao encontrado.")
        print("Instale com: pip install pygame")
        print("=" * 50)
        sys.exit(1)

    from gui import IsolationGUI
    app = IsolationGUI()
    app.run()


if __name__ == "__main__":
    main()
