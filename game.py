"""
game.py — Lógica central do jogo Isolation.

Regras:
  - Tabuleiro NxN (configurável).
  - Dois jogadores: PLAYER1 (humano) e PLAYER2 (IA).
  - Movimentação: qualquer direção (horizontal, vertical e diagonal), apenas UMA casa por vez (como rei do xadrez).
  - Após mover, o jogador escolhe QUALQUER casa vazia do tabuleiro para bloquear permanentemente.
  - A casa anterior NÃO é bloqueada automaticamente.
  - O jogador que não tiver movimentos disponíveis perde.
"""


# ── Constantes ──────────────────────────────────────────────────────────────
BOARD_SIZE = 5   # tamanho padrão (mantido para compatibilidade)
EMPTY      = 0
PLAYER1    = 1   # Humano
PLAYER2    = 2   # IA
BLOCKED    = -1

# Oito direções: N, S, W, E, NW, NE, SW, SE
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1)]


class GameState:
    """Representa o estado completo de uma partida de Isolation."""

    def __init__(self, size: int = BOARD_SIZE):
        self.size  = size
        self.board = [[EMPTY] * size for _ in range(size)]

        # Peças iniciais na coluna central, linhas opostas
        mid = size // 2
        self.pos = {
            PLAYER1: (0, mid),
            PLAYER2: (size - 1, mid),
        }
        self.board[0][mid]        = PLAYER1
        self.board[size - 1][mid] = PLAYER2

        self.current_player = PLAYER1
        self.phase     = "move"   # "move" | "block"
        self.start_pos = {PLAYER1: (0, mid), PLAYER2: (size - 1, mid)}

    # ── Movimentação ────────────────────────────────────────────────────────

    def get_valid_moves(self, player: int) -> list:
        """Retorna as casas adjacentes alcançáveis (1 casa por direção, 8 direções)."""
        r, c  = self.pos[player]
        moves = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                if self.board[nr][nc] == EMPTY:
                    moves.append((nr, nc))
        return moves

    def make_move(self, player: int, new_pos: tuple) -> None:
        """Move a peça. Casa inicial fica BLOQUEADA; demais ficam VAZIAS. Fase passa para 'block'."""
        or_, oc = self.pos[player]
        nr, nc  = new_pos
        if (or_, oc) == self.start_pos[player]:
            self.board[or_][oc] = BLOCKED
        else:
            self.board[or_][oc] = EMPTY
        self.board[nr][nc]  = player
        self.pos[player]    = new_pos
        self.phase          = "block"

    def block_tile(self, r: int, c: int) -> None:
        """Bloqueia a casa escolhida pelo jogador. Fase volta para 'move' e troca de jogador."""
        self.board[r][c]    = BLOCKED
        self.phase          = "move"
        self.current_player = PLAYER2 if self.current_player == PLAYER1 else PLAYER1

    def get_valid_blocks(self) -> list:
        """Todas as casas EMPTY do tabuleiro (qualquer casa não ocupada)."""
        blocks = []
        for r in range(self.size):
            for c in range(self.size):
                if self.board[r][c] == EMPTY:
                    blocks.append((r, c))
        return blocks

    # ── Estado terminal ─────────────────────────────────────────────────────

    def is_terminal(self) -> bool:
        if self.phase != "move":
            return False
        return len(self.get_valid_moves(self.current_player)) == 0

    # ── Cópia rápida ────────────────────────────────────────────────────────

    def clone(self) -> "GameState":
        new                = object.__new__(GameState)
        new.size           = self.size
        new.board          = [row[:] for row in self.board]
        new.pos            = self.pos.copy()
        new.current_player = self.current_player
        new.phase          = self.phase
        new.start_pos      = self.start_pos   # imutável durante o jogo
        return new

    # ── Representação textual (debug) ────────────────────────────────────────

    def __str__(self) -> str:
        symbols = {EMPTY: ".", PLAYER1: "P", PLAYER2: "I", BLOCKED: "#"}
        lines   = ["  " + " ".join(str(c) for c in range(self.size))]
        for r in range(self.size):
            row = " ".join(symbols[self.board[r][c]] for c in range(self.size))
            lines.append(f"{r} {row}")
        return "\n".join(lines)
