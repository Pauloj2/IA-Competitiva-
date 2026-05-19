"""
ai.py — Agente inteligente para o jogo Isolation.

Implementa dois algoritmos de busca adversarial:
  - Minimax com profundidade limitada (Etapa 1)
  - Minimax com Poda Alfa-Beta (Etapa 2)

Heurística combinada (Etapa 2):
  1. Diferença de mobilidade  : movimentos(IA) − movimentos(adversário)
  2. Proximidade ao centro    : distância de Chebyshev ao centro (IA perto = mais opções de fuga)
  3. Penalização de isolamento: vizinhos bloqueados reduzem a liberdade futura
"""

import math
import time
from collections import deque

from game import GameState, PLAYER1, PLAYER2, BLOCKED, EMPTY

WIN_SCORE  =  10_000   # IA ganha (adversário preso)
LOSE_SCORE = -10_000   # IA perde (IA presa)

BUDGET_SEGUNDOS = 2.0  # tempo máximo por jogada (qualquer dificuldade)


class _Timeout(Exception):
    """Lançada internamente quando o deadline da busca é ultrapassado."""


class AI:
    """
    Parâmetros
    ----------
    player       : peça controlada pela IA (padrão = PLAYER2)
    depth        : profundidade máxima da busca (ply)
    use_alphabeta: True → Alfa-Beta  |  False → Minimax puro
    """

    def __init__(self, player: int = PLAYER2, depth: int = 3,
                 use_alphabeta: bool = True):
        self.player        = player
        self.opponent      = PLAYER1 if player == PLAYER2 else PLAYER2
        self.depth         = depth
        self.use_alphabeta = use_alphabeta

        self.nodes_evaluated = 0
        self.time_taken      = 0.0
        self._deadline: float | None = None

    # ── Interface pública ────────────────────────────────────────────────────

    def get_best_move(self, state: GameState):
        """
        Retorna a melhor ação (move_pos, block_pos).

        Usa aprofundamento iterativo com deadline fixo (BUDGET_SEGUNDOS).
        Busca de depth=1 até self.depth, parando se o tempo esgotar.
        Sempre retorna o melhor resultado do último depth que completou.
        Nunca bloqueia a UI por mais de ~2 segundos.
        """
        self.nodes_evaluated = 0
        t0                   = time.perf_counter()
        self._deadline       = t0 + BUDGET_SEGUNDOS
        best_action          = None

        for d in range(1, self.depth + 1):
            try:
                if self.use_alphabeta:
                    action, _ = self._alphabeta(state, d, -math.inf, math.inf, True)
                else:
                    action, _ = self._minimax(state, d, True)
                if action is not None:
                    best_action = action
            except _Timeout:
                break                      # usa o melhor resultado do depth anterior

        # Fallback: se nenhum depth completou, pega a primeira ação disponível
        if best_action is None:
            actions = self._get_actions(state, state.current_player)
            if actions:
                best_action = actions[0]

        self._deadline  = None
        self.time_taken = time.perf_counter() - t0
        return best_action

    # ── Geração de ações combinadas ──────────────────────────────────────────

    def _get_actions(self, state: GameState, player: int) -> list:
        """
        Gera todos os pares (movimento, bloqueio) válidos para o jogador
        sem clonar o estado.

        Filtro estratégico: só considera bloqueios dentro do raio de Chebyshev 2
        do oponente ou raio 1 do próprio jogador. Tiles fora desse raio têm
        valor estratégico próximo de zero no curto prazo e explodir o fator de
        ramificação de ~360 para ~24, viabilizando depth=4 em 7×7.
        """
        opponent          = PLAYER1 if player == PLAYER2 else PLAYER2
        r,    c           = state.pos[player]
        opp_r, opp_c      = state.pos[opponent]
        is_start          = ((r, c) == state.start_pos[player])

        base_blocks = set(state.get_valid_blocks())
        if not is_start:
            base_blocks.add((r, c))

        # Filtro: bloqueios perto do oponente (raio 2) ou perto do próprio jogador (raio 1)
        strategic = {
            (br, bc) for (br, bc) in base_blocks
            if max(abs(br - opp_r), abs(bc - opp_c)) <= 2
            or max(abs(br - r),     abs(bc - c))     <= 1
        }
        if not strategic:
            strategic = base_blocks   # fallback: todas as casas se filtro zerar

        actions = []
        for move in state.get_valid_moves(player):
            for block in strategic:
                if block != move:
                    actions.append((move, block))
        return actions

    # ── Minimax puro ─────────────────────────────────────────────────────────

    def _minimax(self, state: GameState, depth: int, maximizing: bool):
        """
        Minimax com profundidade limitada.

        Retorna (melhor_ação, valor_heurístico).
        Cada ação é um par (move_pos, block_pos) — um turno completo.
        maximizing=True  → turno da IA  (maximiza o valor)
        maximizing=False → turno do humano (minimiza o valor)
        """
        self.nodes_evaluated += 1
        if self.nodes_evaluated % 200 == 0 and self._deadline is not None:
            if time.perf_counter() > self._deadline:
                raise _Timeout()

        # ── Casos base ────────────────────────────────────────
        if state.is_terminal():
            if state.current_player == self.player:
                return None, LOSE_SCORE
            else:
                return None, WIN_SCORE

        if depth == 0:
            return None, self._heuristic(state)

        # ── Expansão dos filhos ────────────────────────────────
        current     = state.current_player
        best_action = None

        if maximizing:
            best_val = -math.inf
            for action in self._get_actions(state, current):
                move, block = action
                ns = state.clone()
                ns.make_move(current, move)
                ns.block_tile(block[0], block[1])
                _, val = self._minimax(ns, depth - 1, False)
                if val > best_val:
                    best_val    = val
                    best_action = action
        else:
            best_val = math.inf
            for action in self._get_actions(state, current):
                move, block = action
                ns = state.clone()
                ns.make_move(current, move)
                ns.block_tile(block[0], block[1])
                _, val = self._minimax(ns, depth - 1, True)
                if val < best_val:
                    best_val    = val
                    best_action = action

        return best_action, best_val

    # ── Minimax com Poda Alfa-Beta ────────────────────────────────────────────

    def _alphabeta(self, state: GameState, depth: int,
                   alpha: float, beta: float, maximizing: bool):
        """
        Minimax com poda Alfa-Beta.

        Cada ação é um par (move_pos, block_pos) — um turno completo.
        alpha : melhor valor já garantido para o maximizador
        beta  : melhor valor já garantido para o minimizador
        Poda β: ramo descartado quando beta <= alpha (no maximizador)
        Poda α: ramo descartado quando beta <= alpha (no minimizador)
        """
        self.nodes_evaluated += 1
        if self.nodes_evaluated % 200 == 0 and self._deadline is not None:
            if time.perf_counter() > self._deadline:
                raise _Timeout()

        # ── Casos base ────────────────────────────────────────
        if state.is_terminal():
            if state.current_player == self.player:
                return None, LOSE_SCORE
            else:
                return None, WIN_SCORE

        if depth == 0:
            return None, self._heuristic(state)

        # ── Expansão com poda ─────────────────────────────────
        current     = state.current_player
        best_action = None

        if maximizing:
            best_val = -math.inf
            for action in self._get_actions(state, current):
                move, block = action
                ns = state.clone()
                ns.make_move(current, move)
                ns.block_tile(block[0], block[1])
                _, val = self._alphabeta(ns, depth - 1, alpha, beta, False)
                if val > best_val:
                    best_val    = val
                    best_action = action
                alpha = max(alpha, best_val)
                if beta <= alpha:
                    break
        else:
            best_val = math.inf
            for action in self._get_actions(state, current):
                move, block = action
                ns = state.clone()
                ns.make_move(current, move)
                ns.block_tile(block[0], block[1])
                _, val = self._alphabeta(ns, depth - 1, alpha, beta, True)
                if val < best_val:
                    best_val    = val
                    best_action = action
                beta = min(beta, best_val)
                if beta <= alpha:
                    break

        return best_action, best_val

    # ── Território (BFS) ────────────────────────────────────────────────────

    def _territory(self, state: GameState, r: int, c: int) -> int:
        """
        BFS a partir de (r, c): conta todas as casas EMPTY alcançáveis.
        Representa o espaço de liberdade futura do jogador — quando esse valor
        é pequeno, o isolamento é iminente.
        """
        visited = {(r, c)}
        queue   = deque([(r, c)])
        while queue:
            cr, cc = queue.popleft()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),
                           (-1,-1),(-1,1),(1,-1),(1,1)]:
                nr, nc = cr + dr, cc + dc
                if ((nr, nc) not in visited
                        and 0 <= nr < state.size
                        and 0 <= nc < state.size
                        and state.board[nr][nc] == EMPTY):
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return len(visited) - 1  # desconta a casa inicial (ocupada pelo próprio jogador)

    # ── Função Heurística ────────────────────────────────────────────────────

    def _heuristic(self, state: GameState) -> float:
        """
        Avalia o estado do ponto de vista da IA (valores positivos = bom para IA).

        Componentes:
          mobility  : movimentos imediatos disponíveis — sobrevivência de curto prazo (peso 4)
          territory : casas alcançáveis via BFS — penaliza isolamento iminente    (peso 3)
          position  : proximidade ao centro (Chebyshev) — posição estratégica     (peso 2)
          isolation : vizinhos bloqueados/borda imediatos — pressão local         (peso 1)
        """
        ai_moves  = len(state.get_valid_moves(self.player))
        hum_moves = len(state.get_valid_moves(self.opponent))

        ai_r,  ai_c  = state.pos[self.player]
        hum_r, hum_c = state.pos[self.opponent]

        # 1. Mobilidade imediata
        mobility = ai_moves - hum_moves

        # 2. Território (BFS) — isolamento iminente: região pequena = perigo
        ai_terr  = self._territory(state, ai_r,  ai_c)
        hum_terr = self._territory(state, hum_r, hum_c)
        territory = ai_terr - hum_terr

        # 3. Posição estratégica: proximidade ao centro (distância de Chebyshev)
        center   = state.size // 2
        ai_dist  = max(abs(ai_r - center), abs(ai_c - center))
        hum_dist = max(abs(hum_r - center), abs(hum_c - center))
        position = hum_dist - ai_dist   # IA mais perto do centro → positivo

        # 4. Isolamento local: vizinhos imediatos bloqueados ou fora do tabuleiro
        def blocked_neighbors(r: int, c: int) -> int:
            cnt = 0
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),
                           (-1,-1),(-1,1),(1,-1),(1,1)]:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < state.size and 0 <= nc < state.size):
                    cnt += 1
                elif state.board[nr][nc] == BLOCKED:
                    cnt += 1
            return cnt

        ai_iso  = blocked_neighbors(ai_r,  ai_c)
        hum_iso = blocked_neighbors(hum_r, hum_c)
        isolation = hum_iso - ai_iso

        return mobility * 4 + territory * 3 + position * 2 + isolation
