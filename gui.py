"""
gui.py — Interface estilo arcade / anos 80 para o jogo Isolation.
"""

import sys
import math
import pygame

from game import GameState, PLAYER1, PLAYER2, BLOCKED, EMPTY
from ai   import AI

# ── Layout ────────────────────────────────────────────────────────────────────
BRD_AREA = 420          # área fixa do tabuleiro (independe do tamanho)
WIN_W    = 920
WIN_H    = 660
TOP_H    = 138          # altura do painel superior
BRD_X    = (WIN_W - BRD_AREA) // 2   # 250 — board centralizado
BRD_Y    = TOP_H + 22                # 160
CRTR_CX  = BRD_X // 2                # 125 — centro horizontal das criaturas
CRTR_CX2 = BRD_X + BRD_AREA + BRD_X // 2  # 795

# ── Paleta Pixel Art Suave ────────────────────────────────────────────────────
C_BG      = ( 13,  13,  20)   # fundo principal
C_SURF    = ( 22,  22,  34)   # superfície de cards/painel
C_BORDER  = ( 48,  48,  70)   # bordas sutis
C_DIM     = ( 82,  82, 108)   # texto secundário
C_TEXT    = (208, 204, 192)   # texto principal (creme)
C_P1      = (108, 196, 154)   # P1 — verde menta
C_P2      = (216, 116,  96)   # P2 — coral
C_GOLD    = (196, 168,  80)   # destaque / seleção
C_GREEN   = (132, 192,  96)   # positivo
C_RED_S   = (192,  76,  72)   # bloqueado / erro
C_BLKFILL = ( 26,  14,  14)   # célula bloqueada


class IsolationGUI:

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("ISOLATION  //  ARCADE  //  1984")
        self.clock  = pygame.time.Clock()
        self._load_fonts()

        self.screen_state = "menu"
        self.menu_ply     = 2
        self.menu_algo    = True
        self.menu_mode    = "humano"   # "humano" | "ia_ia"
        self.menu_size    = 5          # tamanho do tabuleiro
        self.cell         = BRD_AREA // self.menu_size

        self.gs              = None
        self.ai_agent        = None
        self.ai_agent_p1     = None
        self.ia_ia_last_move = 0
        self.selected     = None
        self.valid_moves  = []
        self.valid_blocks = []
        self.block_phase  = False
        self.game_over    = False
        self.winner       = None
        self.status_msg   = ""
        self.ai_pending   = False
        self.move_count   = {PLAYER1: 0, PLAYER2: 0}
        self.stats        = {"nodes": 0, "time": 0.0,
                             "total_nodes": 0, "total_time": 0.0, "moves": 0}
        self._restart_rect    = pygame.Rect(0, 0, 0, 0)
        self._gameover_btn    = pygame.Rect(0, 0, 0, 0)
        self._switch_algo_btn = pygame.Rect(0, 0, 0, 0)
        self._compare_btn     = pygame.Rect(0, 0, 0, 0)
        self._menu_from_cmp   = pygame.Rect(0, 0, 0, 0)

        # Controle do ciclo de comparação
        self.cycle      = 0     # 0 = jogo normal, 1 = aguardando 2º jogo
        self.saved_game = None  # stats do 1º jogo para comparação


    def _load_fonts(self):
        def f(names, size, bold=False):
            for n in names:
                try:
                    fnt = pygame.font.SysFont(n, size, bold=bold)
                    if fnt:
                        return fnt
                except Exception:
                    pass
            return pygame.font.Font(None, size)

        mono = ["Consolas", "Courier New", "Lucida Console"]
        self.fTTL  = f(mono, 58, True)
        self.fXL   = f(mono, 36, True)
        self.fLG   = f(mono, 22, True)
        self.fMD   = f(mono, 16, True)
        self.fSM   = f(mono, 13, True)
        self.fBTN  = f(mono, 15, True)

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def _t():
        return pygame.time.get_ticks()

    def _bc(self, font, text, color, center, shadow_col=None):
        if shadow_col:
            s = font.render(text, True, shadow_col)
            self.screen.blit(s, s.get_rect(center=(center[0]+3, center[1]+3)))
        s = font.render(text, True, color)
        self.screen.blit(s, s.get_rect(center=center))

    def _bl(self, font, text, color, xy, shadow_col=None):
        if shadow_col:
            s = font.render(text, True, shadow_col)
            self.screen.blit(s, (xy[0]+2, xy[1]+2))
        s = font.render(text, True, color)
        self.screen.blit(s, xy)

    def _box(self, rect, border_col, thick=2, fill=None):
        if fill is not None:
            pygame.draw.rect(self.screen, fill, rect)
        pygame.draw.rect(self.screen, border_col, rect, thick)

    def _corners(self, rect, col=None, sz=10):
        col = col or C_BORDER
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        for (ax, ay), (bx, by), (cx, cy) in [
            ((x, y+sz), (x, y), (x+sz, y)),
            ((x+w-sz, y), (x+w, y), (x+w, y+sz)),
            ((x, y+h-sz), (x, y+h), (x+sz, y+h)),
            ((x+w-sz, y+h), (x+w, y+h), (x+w, y+h-sz)),
        ]:
            pygame.draw.line(self.screen, col, (ax, ay), (bx, by), 1)
            pygame.draw.line(self.screen, col, (bx, by), (cx, cy), 1)

    def _scanlines(self):
        pass  # removido no design minimalista

    def _pixel_bg(self):
        self.screen.fill(C_BG)
        for gx in range(0, WIN_W, 16):
            for gy in range(0, WIN_H, 16):
                pygame.draw.rect(self.screen, C_SURF, (gx, gy, 2, 2))

    def _retrowave_bg(self):
        self._pixel_bg()

    def _game_bg(self):
        self._pixel_bg()

    # ── MENU ──────────────────────────────────────────────────────────────────

    def _draw_menu(self, events):
        self._retrowave_bg()

        t      = self._t()
        mx, my = pygame.mouse.get_pos()

        # Título
        self._bc(self.fTTL, "ISOLATION", C_TEXT, (WIN_W // 2, 76))
        self._bc(self.fSM, "MINIMAX  &  ALPHA-BETA", C_DIM, (WIN_W // 2, 128))

        pygame.draw.line(self.screen, C_BORDER, (40, 148), (WIN_W-40, 148), 1)

        # Criaturas nos lados do menu
        menu_cy = 162 + 472 // 2
        self._draw_creature(100,          menu_cy, PLAYER1, t)
        self._draw_creature(WIN_W - 100,  menu_cy, PLAYER2, t)

        # Caixa principal
        box = pygame.Rect(WIN_W // 2 - 260, 162, 520, 472)
        pygame.draw.rect(self.screen, C_SURF, box)
        pygame.draw.rect(self.screen, C_BORDER, box, 1)
        self._corners(box, C_P1)

        yy = 178

        def section(title):
            self._bc(self.fSM, title, C_DIM, (WIN_W//2, yy))

        def btn_row(items, rects_out, active_val, cx_start, cx_step, btn_w, btn_h=34):
            nonlocal yy
            yy += 22
            for i, (label, val, col) in enumerate(items):
                cx = cx_start + i * cx_step
                r  = pygame.Rect(cx - btn_w//2, yy, btn_w, btn_h)
                active = active_val == val
                hov    = r.collidepoint(mx, my)
                fill = (col[0]//6, col[1]//6, col[2]//6) if active else \
                       (col[0]//12, col[1]//12, col[2]//12) if hov else C_BG
                bw   = 2 if active else 1
                self._box(r, col if (active or hov) else C_BORDER, bw, fill=fill)
                self._bc(self.fMD, label, col if (active or hov) else C_DIM, r.center)
                rects_out.append((r, val))
            yy += btn_h + 14
            pygame.draw.line(self.screen, C_BORDER,
                             (box.x+14, yy), (box.right-14, yy)); yy += 12

        section("MODO"); mode_rects = []
        btn_row([("HUMANO vs IA","humano",C_P1),("IA  vs  IA","ia_ia",C_P2)],
                mode_rects, self.menu_mode, WIN_W//2-118, 236, 220)

        section("TABULEIRO"); size_rects = []
        btn_row([("5 x 5",5,C_GOLD),("7 x 7",7,C_GOLD)],
                size_rects, self.menu_size, WIN_W//2-108, 216, 190)

        section("DIFICULDADE"); diff_rects = []
        btn_row([("FACIL",1,C_GREEN),("MEDIO",2,C_GOLD),("DIFICIL",4,C_P2)],
                diff_rects, self.menu_ply, WIN_W//2-158, 158, 136)

        # Ajuste fino de PLY — botões compactos abaixo da dificuldade
        cx2      = WIN_W // 2
        ply_m    = pygame.Rect(cx2 - 58, yy - 6, 26, 20)
        ply_p    = pygame.Rect(cx2 + 32, yy - 6, 26, 20)
        hov_pm   = ply_m.collidepoint(mx, my)
        hov_pp   = ply_p.collidepoint(mx, my)
        self._box(ply_m, C_P1 if hov_pm else C_BORDER, 1, fill=C_BG)
        self._bc(self.fSM, "−", C_P1 if hov_pm else C_DIM, ply_m.center)
        self._bc(self.fSM, f"PLY {self.menu_ply}", C_GOLD, (cx2, yy + 4))
        self._box(ply_p, C_P2 if hov_pp else C_BORDER, 1, fill=C_BG)
        self._bc(self.fSM, "+", C_P2 if hov_pp else C_DIM, ply_p.center)
        yy += 20
        pygame.draw.line(self.screen, C_BORDER,
                         (box.x+14, yy), (box.right-14, yy)); yy += 12

        section("ALGORITMO"); algo_rects = []
        btn_row([("MINIMAX",False,C_P1),("ALPHA-BETA",True,C_P2)],
                algo_rects, self.menu_algo, WIN_W//2-108, 216, 190)

        # Botão INICIAR
        play_r = pygame.Rect(WIN_W//2-120, yy, 240, 44)
        hov_p  = play_r.collidepoint(mx, my)
        pc     = C_GREEN
        self._box(play_r, pc, 2,
                  fill=(pc[0]//5, pc[1]//5, pc[2]//5) if hov_p else C_BG)
        self._bc(self.fBTN, "INICIAR", pc, play_r.center)

        # Rodapé
        pygame.draw.line(self.screen, C_BORDER, (40, WIN_H-50), (WIN_W-40, WIN_H-50), 1)
        rules = [
            f"{self.menu_size}x{self.menu_size}  |  mover como rei  |  depois escolher casa para bloquear",
            "qualquer casa vazia pode ser bloqueada  |  sem movimentos = derrota",
        ]
        for i, line in enumerate(rules):
            self._bc(self.fSM, line, C_DIM, (WIN_W//2, WIN_H - 36 + i * 16))

        # Eventos
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                ex, ey = e.pos
                for r, val in mode_rects:
                    if r.collidepoint(ex, ey):
                        self.menu_mode = val
                for r, val in size_rects:
                    if r.collidepoint(ex, ey):
                        self.menu_size = val
                for r, val in diff_rects:
                    if r.collidepoint(ex, ey):
                        self.menu_ply = val
                if ply_m.collidepoint(ex, ey):
                    self.menu_ply = max(1, self.menu_ply - 1)
                if ply_p.collidepoint(ex, ey):
                    self.menu_ply = min(6, self.menu_ply + 1)
                for r, val in algo_rects:
                    if r.collidepoint(ex, ey):
                        self.menu_algo = val
                if play_r.collidepoint(ex, ey):
                    self._init_game()
                    self.screen_state = "game"

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init_game(self):
        self.cell        = BRD_AREA // self.menu_size
        self.gs          = GameState(size=self.menu_size)
        self.ai_agent    = AI(PLAYER2, self.menu_ply, self.menu_algo)
        self.selected    = None
        self.valid_moves = []
        self.valid_blocks = []
        self.block_phase  = False
        self.game_over   = False
        self.winner      = None
        self.move_count  = {PLAYER1: 0, PLAYER2: 0}
        self.stats       = {"nodes": 0, "time": 0.0,
                            "total_nodes": 0, "total_time": 0.0, "moves": 0}
        self.ia_ia_last_move = 0

        if self.menu_mode == "ia_ia":
            self.ai_agent_p1 = AI(PLAYER1, self.menu_ply, self.menu_algo)
            self.ai_pending  = True
            self.status_msg  = "IA(P1) CALCULANDO..."
        else:
            self.ai_agent_p1 = None
            self.ai_pending  = False
            self.status_msg  = "selecione sua peca  [P1]"

    # ── Score bar ─────────────────────────────────────────────────────────────

    # ── Sprites pixel-art (7 colunas × 12 linhas) ────────────────────────────
    #  '1'=corpo  '2'=olho/detalhe  '3'=highlight  '0'=vazio
    _SPR_P1 = ["0111110","1000001","1020201","1033301",
               "1000001","0111110","1111111","1011101",
               "1011101","1111111","0100010","0100010"]
    _SPR_P1_BLINK = ["0111110","1000001","1011101","1033301",
                     "1000001","0111110","1111111","1011101",
                     "1011101","1111111","0100010","0100010"]
    _SPR_P2 = ["1000001","0111110","1000001","1020201",
               "1011101","0111110","0111110","1111111",
               "1011101","0111110","1000001","0100010"]
    _SPR_P2_BLINK = ["1000001","0111110","1000001","1011101",
                     "1011101","0111110","0111110","1111111",
                     "1011101","0111110","1000001","0100010"]

    def _draw_creature(self, cx, cy, player, t):
        scale  = 13
        col    = C_P1 if player == PLAYER1 else C_P2
        blink  = (t % 3200) < 180
        phase  = 0 if player == PLAYER1 else math.pi
        bob    = int(math.sin(t / 480 + phase) * 6)

        if player == PLAYER1:
            sprite = self._SPR_P1_BLINK if blink else self._SPR_P1
        else:
            sprite = self._SPR_P2_BLINK if blink else self._SPR_P2

        rows = len(sprite)
        cols = len(sprite[0])
        ox   = cx - (cols * scale) // 2
        oy   = cy - (rows * scale) // 2 + bob

        hl  = (min(col[0]+75, 255), min(col[1]+75, 255), min(col[2]+75, 255))
        dk  = (col[0]//3,           col[1]//3,           col[2]//3)
        eye = C_BG

        for r, row in enumerate(sprite):
            for c, px in enumerate(row):
                if px == '0':
                    continue
                if px == '2':
                    pxc = eye
                elif px == '3':
                    pxc = hl
                elif r < 2:
                    pxc = hl
                elif r >= rows - 3:
                    pxc = dk
                else:
                    pxc = col
                pygame.draw.rect(self.screen, pxc,
                                 (ox + c*scale, oy + r*scale, scale, scale))

        # Plaquinha com nome
        lbl = "P1" if player == PLAYER1 else "P2"
        self._bc(self.fSM, lbl, col, (cx, oy + rows*scale + 10))

    # ── Painel superior ───────────────────────────────────────────────────────

    def _draw_top_panel(self):
        bar = pygame.Rect(0, 0, WIN_W, TOP_H)
        pygame.draw.rect(self.screen, C_SURF, bar)
        pygame.draw.line(self.screen, C_BORDER, (0, TOP_H-1), (WIN_W, TOP_H-1), 2)

        mid = WIN_W // 2

        # ── Faixa A: nomes + título ───────────────────────────
        p1_name = "IA-P1" if self.menu_mode == "ia_ia" else "JOGADOR"
        self._bl(self.fSM, p1_name, C_DIM,  (14, 7))
        self._bl(self.fXL, f"{self.move_count[PLAYER1]:03d}", C_P1, (14, 22))

        self._bc(self.fMD, "I S O L A T I O N", C_TEXT, (mid, 16))
        algo_s = "ALPHA-BETA" if self.menu_algo else "MINIMAX"
        self._bc(self.fSM, f"{algo_s}  {self.menu_size}x{self.menu_size}  PLY={self.menu_ply}",
                 C_DIM, (mid, 38))

        self._bl(self.fSM, "IA",    C_DIM,  (WIN_W - 80, 7))
        self._bl(self.fXL, f"{self.move_count[PLAYER2]:03d}", C_P2, (WIN_W - 80, 22))

        pygame.draw.line(self.screen, C_BORDER, (14, 54), (WIN_W-14, 54))

        # ── Faixa B: detalhes dos jogadores + turno ───────────
        if self.gs:
            cp     = self.gs.current_player
            m1     = len(self.gs.get_valid_moves(PLAYER1))
            m2     = len(self.gs.get_valid_moves(PLAYER2))
            c1     = C_P1 if (not self.game_over and cp == PLAYER1) else C_DIM
            c2     = C_P2 if (not self.game_over and cp == PLAYER2) else C_DIM

            self._bl(self.fSM, f"jog {self.move_count[PLAYER1]:02d}  opc {m1:02d}", c1, (14, 60))
            if not self.game_over:
                turn_lbl = "JOGADOR" if cp == PLAYER1 else "IA"
                turn_col = C_P1 if cp == PLAYER1 else C_P2
                self._bc(self.fMD, turn_lbl, turn_col, (mid, 66))
            p2info = self.fSM.render(f"jog {self.move_count[PLAYER2]:02d}  opc {m2:02d}", True, c2)
            self.screen.blit(p2info, (WIN_W - 14 - p2info.get_width(), 60))

        pygame.draw.line(self.screen, C_BORDER, (14, 82), (WIN_W-14, 82))

        # ── Faixa C: stats da IA + status ─────────────────────
        st = self.stats
        stats_txt = (f"nos {st['nodes']:,}  ms {st['time']*1000:.1f}"
                     f"  total {st['total_nodes']:,}  t {st['total_time']:.2f}s"
                     f"  mov {st['moves']}")
        self._bl(self.fSM, stats_txt, C_DIM, (14, 88))

        cursor = "_" if (self._t() // 500) % 2 == 0 else " "
        self._bc(self.fSM, self.status_msg + cursor, C_GREEN, (mid, 108))

        # Botão ESC
        btn = pygame.Rect(WIN_W - 106, 108, 92, 24)
        mx, my = pygame.mouse.get_pos()
        hov = btn.collidepoint(mx, my)
        self._box(btn, C_P1 if hov else C_BORDER, 1,
                  fill=(C_P1[0]//6, C_P1[1]//6, C_P1[2]//6) if hov else C_BG)
        self._bc(self.fSM, "ESC  MENU", C_P1 if hov else C_DIM, btn.center)
        self._restart_rect = btn

    # ── Board ─────────────────────────────────────────────────────────────────

    def _draw_board(self):
        t  = self._t()
        cy = TOP_H + (WIN_H - TOP_H) // 2

        self._draw_creature(CRTR_CX,  cy, PLAYER1, t)
        self._draw_creature(CRTR_CX2, cy, PLAYER2, t)

        sz = self.gs.size
        cl = self.cell
        cont = pygame.Rect(BRD_X - 8, BRD_Y - 4,
                           cl * sz + 16, cl * sz + 14)
        pygame.draw.rect(self.screen, C_BG, cont)
        pygame.draw.rect(self.screen, C_BORDER, cont, 1)
        self._corners(cont, C_P1)

        for c in range(sz):
            cx2 = BRD_X + c * cl + cl // 2
            self._bc(self.fSM, chr(65 + c), C_DIM, (cx2, BRD_Y - 16))
        for r in range(sz):
            cy2 = BRD_Y + r * cl + cl // 2
            self._bc(self.fSM, str(r + 1), C_DIM, (BRD_X - 16, cy2))

        for r in range(sz):
            for c in range(sz):
                self._draw_cell(r, c)

    def _draw_cell(self, r, c):
        cl   = self.cell
        x    = BRD_X + c * cl
        y    = BRD_Y + r * cl
        rect = pygame.Rect(x, y, cl, cl)
        val  = self.gs.board[r][c]
        pos  = (r, c)
        t    = self._t()

        # Xadrez suave
        bg = C_BG if (r + c) % 2 == 0 else C_SURF
        pygame.draw.rect(self.screen, bg, rect)

        if val == BLOCKED:
            pygame.draw.rect(self.screen, C_BLKFILL, rect)
            m = max(6, cl // 6)
            pygame.draw.line(self.screen, C_RED_S, (x+m, y+m), (x+cl-m, y+cl-m), 2)
            pygame.draw.line(self.screen, C_RED_S, (x+cl-m, y+m), (x+m, y+cl-m), 2)

        elif pos in self.valid_moves and val == EMPTY:
            if math.sin(t / 350) > 0:
                inner = rect.inflate(-cl//3, -cl//3)
                pygame.draw.rect(self.screen,
                                 (C_GOLD[0]//5, C_GOLD[1]//5, C_GOLD[2]//5), inner)
                pygame.draw.rect(self.screen, C_GOLD, inner, 1)

        elif self.block_phase and pos in self.valid_blocks and val == EMPTY:
            if math.sin(t / 350) > 0:
                inner = rect.inflate(-cl//3, -cl//3)
                pygame.draw.rect(self.screen,
                                 (C_RED_S[0]//5, C_RED_S[1]//5, C_RED_S[2]//5), inner)
                pygame.draw.rect(self.screen, C_RED_S, inner, 1)

        if pos == self.selected:
            pygame.draw.rect(self.screen, C_GOLD, rect, 2)

        if val == PLAYER1:
            self._draw_piece(x, y, PLAYER1)
        elif val == PLAYER2:
            self._draw_piece(x, y, PLAYER2)

        pygame.draw.rect(self.screen, C_BORDER, rect, 1)

    def _draw_piece(self, x, y, player):
        cl    = self.cell
        col   = C_P1 if player == PLAYER1 else C_P2
        label = "P1" if player == PLAYER1 else "P2"
        pad   = max(6, cl // 5)
        piece = pygame.Rect(x + pad, y + pad, cl - pad*2, cl - pad*2)

        # Pixel shadow
        pygame.draw.rect(self.screen,
                         (col[0]//6, col[1]//6, col[2]//6),
                         piece.move(2, 2))
        # Fill escuro + borda colorida
        pygame.draw.rect(self.screen,
                         (col[0]//5, col[1]//5, col[2]//5), piece)
        pygame.draw.rect(self.screen, col, piece, 2)
        # Highlight pixel (canto superior esquerdo — estilo pixel art)
        hl = (min(col[0]+80, 255), min(col[1]+80, 255), min(col[2]+80, 255))
        pygame.draw.rect(self.screen, hl, (piece.x+3, piece.y+3, 4, 2))
        pygame.draw.rect(self.screen, hl, (piece.x+3, piece.y+3, 2, 4))

        font = self.fMD if cl >= 70 else self.fSM
        self._bc(font, label, col, piece.center)


    # ── Game Over ─────────────────────────────────────────────────────────────

    def _draw_gameover(self):
        t      = self._t()
        mx, my = pygame.mouse.get_pos()

        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        self.screen.blit(ov, (0, 0))

        col = C_P1 if self.winner == PLAYER1 else C_P2
        if self.menu_mode == "ia_ia":
            name = "IA-P1  VENCEU" if self.winner == PLAYER1 else "IA-P2  VENCEU"
            sub  = "ia-p2 sem movimentos" if self.winner == PLAYER1 else "ia-p1 sem movimentos"
        else:
            name = "VOCE  VENCEU" if self.winner == PLAYER1 else "IA  VENCEU"
            sub  = "ia sem movimentos" if self.winner == PLAYER1 else "voce sem movimentos"

        bw, bh = 460, 280
        bx, by = WIN_W // 2 - bw // 2, WIN_H // 2 - bh // 2
        box    = pygame.Rect(bx, by, bw, bh)
        pygame.draw.rect(self.screen, C_SURF, box)
        pygame.draw.rect(self.screen, col, box, 2)
        self._corners(box, col)

        # Título
        if self.menu_mode == "ia_ia":
            self._bc(self.fLG, "FIM DE JOGO", C_GOLD, (WIN_W//2, by+34))
        elif self.winner == PLAYER1:
            self._bc(self.fLG, "VOCE VENCEU", C_P1,   (WIN_W//2, by+34))
        else:
            self._bc(self.fLG, "GAME OVER",   C_P2,   (WIN_W//2, by+34))

        self._bc(self.fXL, name, col,     (WIN_W//2, by+90))
        self._bc(self.fSM, sub,  C_DIM,   (WIN_W//2, by+136))

        pygame.draw.line(self.screen, C_BORDER,
                         (bx+20, by+158), (bx+bw-20, by+158))

        # Botão jogar novamente
        btn  = pygame.Rect(WIN_W//2 - 110, by+168, 220, 36)
        hov  = btn.collidepoint(mx, my)
        self._box(btn, C_GREEN if hov else C_BORDER, 1,
                  fill=(C_GREEN[0]//6, C_GREEN[1]//6, C_GREEN[2]//6) if hov else C_BG)
        self._bc(self.fSM, "JOGAR NOVAMENTE", C_GREEN if hov else C_DIM, btn.center)
        self._gameover_btn = btn

        # Botão secundário
        if self.cycle == 0:
            other  = "ALPHA-BETA" if not self.menu_algo else "MINIMAX"
            sw_col = C_P2 if not self.menu_algo else C_P1
            sw_btn = pygame.Rect(WIN_W//2 - 110, by+214, 220, 36)
            hov_sw = sw_btn.collidepoint(mx, my)
            self._box(sw_btn, sw_col if hov_sw else C_BORDER, 1,
                      fill=(sw_col[0]//6, sw_col[1]//6, sw_col[2]//6) if hov_sw else C_BG)
            self._bc(self.fSM, f"TROCAR  {other}", sw_col if hov_sw else C_DIM, sw_btn.center)
            self._switch_algo_btn = sw_btn
            self._compare_btn     = pygame.Rect(0, 0, 0, 0)
        else:
            cmp_btn = pygame.Rect(WIN_W//2 - 110, by+214, 220, 36)
            hov_c   = cmp_btn.collidepoint(mx, my)
            self._box(cmp_btn, C_GOLD if hov_c else C_BORDER, 1,
                      fill=(C_GOLD[0]//6, C_GOLD[1]//6, C_GOLD[2]//6) if hov_c else C_BG)
            self._bc(self.fSM, "VER COMPARACAO", C_GOLD if hov_c else C_DIM, cmp_btn.center)
            self._compare_btn     = cmp_btn
            self._switch_algo_btn = pygame.Rect(0, 0, 0, 0)

    # ── Tela de Comparação ────────────────────────────────────────────────────

    def _draw_comparison(self, events):
        self._retrowave_bg()
        mx, my = pygame.mouse.get_pos()

        g1 = self.saved_game          # jogo 1 (primeiro algoritmo)
        g2 = self._current_game_data() # jogo 2 (segundo algoritmo)

        # Caixa central
        bw, bh = 600, 420
        bx     = WIN_W // 2 - bw // 2
        by     = WIN_H // 2 - bh // 2
        box    = pygame.Rect(bx, by, bw, bh)
        pygame.draw.rect(self.screen, C_SURF, box)
        pygame.draw.rect(self.screen, C_BORDER, box, 1)
        self._corners(box, C_GOLD)

        cx = WIN_W // 2
        yy = by + 18

        self._bc(self.fLG, "COMPARACAO DE DESEMPENHO", C_TEXT, (cx, yy)); yy += 34

        pygame.draw.line(self.screen, C_BORDER, (bx+16, yy), (bx+bw-16, yy)); yy += 12

        c1 = bx + bw // 2 - 10
        c2 = bx + bw - 20
        self._bc(self.fMD, g1["algo"], C_P1, (c1 - 60, yy))
        self._bc(self.fMD, g2["algo"], C_P2, (c2 - 60, yy)); yy += 24

        pygame.draw.line(self.screen, C_BORDER, (bx+16, yy), (bx+bw-16, yy)); yy += 10

        def row(label, v1, v2, hi="low"):
            nonlocal yy
            try:
                better = 1 if float(str(v1).replace(",","")) <= float(str(v2).replace(",","")) else 2
            except Exception:
                better = 0
            if hi == "high":
                better = 3 - better if better else 0
            c1v = C_GREEN if better == 1 else C_TEXT
            c2v = C_GREEN if better == 2 else C_TEXT
            self._bl(self.fSM, label, C_DIM, (bx + 16, yy))
            s1 = self.fSM.render(str(v1), True, c1v)
            s2 = self.fSM.render(str(v2), True, c2v)
            self.screen.blit(s1, (c1 - s1.get_width(), yy))
            self.screen.blit(s2, (c2 - s2.get_width(), yy))
            yy += 22

        n1, n2 = g1["total_nodes"], g2["total_nodes"]
        t1, t2 = g1["total_time"],  g2["total_time"]
        m1, m2 = g1["moves"],       g2["moves"]

        row("nos avaliados  ", f"{n1:,}", f"{n2:,}")
        row("tempo total (s)", f"{t1:.3f}", f"{t2:.3f}")
        row("jogadas da ia  ", f"{m1}", f"{m2}", "high")
        row("nos por jogada ", f"{n1//max(m1,1):,}", f"{n2//max(m2,1):,}")

        def res_str(g):
            if g["mode"] != "humano":
                return "ia-p1 venceu" if g["winner"] == PLAYER1 else "ia-p2 venceu"
            return "jogador venceu" if g["winner"] == PLAYER1 else "ia venceu"
        row("resultado      ", res_str(g1), res_str(g2), "high")

        pygame.draw.line(self.screen, C_BORDER, (bx+16, yy), (bx+bw-16, yy)); yy += 10

        if n1 > 0 and n2 > 0:
            menor, maior = (n1, n2) if n1 < n2 else (n2, n1)
            a1    = g1["algo"] if n1 < n2 else g2["algo"]
            pct_n = (1 - menor / maior) * 100
            pt_n  = g1["total_time"] if n1 < n2 else g2["total_time"]
            pt_o  = g2["total_time"] if n1 < n2 else g1["total_time"]
            pct_t = (1 - pt_n / pt_o) * 100 if pt_o > 0 else 0
            self._bc(self.fSM, f"{a1}  avaliou {pct_n:.1f}% menos nos",
                     C_GREEN, (cx, yy)); yy += 18
            self._bc(self.fSM, f"{a1}  foi {pct_t:.1f}% mais rapido",
                     C_GREEN, (cx, yy)); yy += 18

        pygame.draw.line(self.screen, C_BORDER, (bx+16, yy), (bx+bw-16, yy)); yy += 10

        mb  = pygame.Rect(cx - 100, yy, 200, 36)
        hov = mb.collidepoint(mx, my)
        self._box(mb, C_P1 if hov else C_BORDER, 1,
                  fill=(C_P1[0]//6, C_P1[1]//6, C_P1[2]//6) if hov else C_BG)
        self._bc(self.fSM, "MENU PRINCIPAL", C_P1 if hov else C_DIM, mb.center)
        self._menu_from_cmp = mb

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self._menu_from_cmp.collidepoint(e.pos):
                    self.cycle      = 0
                    self.saved_game = None
                    self.screen_state = "menu"

    def _current_game_data(self) -> dict:
        return {
            "algo":        "ALPHA-BETA" if self.menu_algo else "MINIMAX",
            "total_nodes": self.stats["total_nodes"],
            "total_time":  self.stats["total_time"],
            "moves":       self.stats["moves"],
            "winner":      self.winner,
            "mode":        self.menu_mode,
        }

    # ── Click handling ────────────────────────────────────────────────────────

    def _handle_game_click(self, mx, my):
        if self.game_over or self.ai_pending or self.menu_mode == "ia_ia":
            return
        if self.gs.current_player != PLAYER1:
            return

        col = (mx - BRD_X) // self.cell
        row = (my - BRD_Y) // self.cell
        if not (0 <= row < self.gs.size and 0 <= col < self.gs.size):
            return

        pos      = (row, col)
        cell_val = self.gs.board[row][col]

        # ── Fase 2: escolher qual casa bloquear ───────────────
        if self.block_phase:
            if pos in self.valid_blocks:
                self.gs.block_tile(row, col)
                self.block_phase  = False
                self.valid_blocks = []
                self.selected     = None
                if self.gs.is_terminal():
                    self.game_over  = True
                    self.winner     = PLAYER1
                    self.status_msg = "IA SEM MOVIMENTOS !"
                else:
                    self.status_msg = "IA CALCULANDO..."
                    self.ai_pending = True
            return

        # ── Fase 1: escolher para onde mover ─────────────────
        if self.selected is None:
            if cell_val == PLAYER1:
                self.selected    = pos
                self.valid_moves = self.gs.get_valid_moves(PLAYER1)
                n = len(self.valid_moves)
                self.status_msg  = f"MOVER PARA ONDE? [ {n} OPCOES ]"
        else:
            if pos in self.valid_moves:
                self.gs.make_move(PLAYER1, pos)
                self.move_count[PLAYER1] += 1
                self.selected     = None
                self.valid_moves  = []
                self.block_phase  = True
                self.valid_blocks = set(self.gs.get_valid_blocks())
                n = len(self.valid_blocks)
                self.status_msg   = f"BLOQUEAR QUAL CASA? [ {n} OPCOES ]"
            elif cell_val == PLAYER1:
                self.selected    = pos
                self.valid_moves = self.gs.get_valid_moves(PLAYER1)
                n = len(self.valid_moves)
                self.status_msg  = f"MOVER PARA ONDE? [ {n} OPCOES ]"
            else:
                self.selected    = None
                self.valid_moves = []
                self.status_msg  = "selecione sua peca  [P1]"

    # ── AI turn ───────────────────────────────────────────────────────────────

    def _do_ai_turn(self):
        current = self.gs.current_player
        agent   = self.ai_agent if current == PLAYER2 else self.ai_agent_p1

        action = agent.get_best_move(self.gs)
        n      = agent.nodes_evaluated
        t_ai = agent.time_taken
        self.stats["nodes"]        = n
        self.stats["time"]         = t_ai
        self.stats["total_nodes"] += n
        self.stats["total_time"]  += t_ai
        self.stats["moves"]       += 1


        if action is None:
            self.game_over  = True
            self.winner     = PLAYER1 if current == PLAYER2 else PLAYER2
            name = "IA(P2)" if current == PLAYER2 else "IA(P1)"
            self.status_msg = f"{name} SEM MOVIMENTOS !"
            self.ai_pending = False
            return

        move, block = action
        self.gs.make_move(current, move)
        self.gs.block_tile(block[0], block[1])
        self.move_count[current] += 1
        self.ai_pending = False

        if self.gs.is_terminal():
            self.game_over = True
            self.winner    = current  # quem acabou de mover vence; oponente ficou sem jogadas
            if self.menu_mode == "ia_ia":
                loser = "IA(P1)" if current == PLAYER2 else "IA(P2)"
                self.status_msg = f"{loser} SEM MOVIMENTOS !"
            else:
                self.status_msg = "VOCE SEM MOVIMENTOS !"
        elif self.menu_mode == "ia_ia":
            next_p = self.gs.current_player
            name   = "IA(P1)" if next_p == PLAYER1 else "IA(P2)"
            self.status_msg = f"{name} CALCULANDO..."
            self.ai_pending = True
        else:
            self.status_msg = "SELECIONE A PECA CYAN  [P1]"

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            events = []
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if (e.type == pygame.KEYDOWN
                        and e.key == pygame.K_ESCAPE
                        and self.screen_state != "menu"):
                    self.cycle = 0
                    self.saved_game = None
                    self.screen_state = "menu"
                events.append(e)

            self.screen.fill(C_BG)

            if self.screen_state == "menu":
                self._draw_menu(events)

            elif self.screen_state == "comparison":
                self._draw_comparison(events)

            else:
                self._game_bg()
                self._draw_board()
                self._draw_top_panel()

                if self.screen_state == "gameover":
                    self._draw_gameover()

                for e in events:
                    if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                        ex, ey = e.pos
                        if self._restart_rect.collidepoint(ex, ey):
                            self.cycle = 0
                            self.saved_game = None
                            self.screen_state = "menu"
                            break
                        if (self.screen_state == "gameover"
                                and self._gameover_btn.collidepoint(ex, ey)):
                            self.cycle = 0
                            self.saved_game = None
                            self.screen_state = "menu"
                            break
                        if (self.screen_state == "gameover"
                                and self._switch_algo_btn.collidepoint(ex, ey)):
                            self.saved_game = self._current_game_data()
                            self.menu_algo  = not self.menu_algo
                            self.cycle      = 1
                            self._init_game()
                            self.screen_state = "game"
                            break
                        if (self.screen_state == "gameover"
                                and self._compare_btn.collidepoint(ex, ey)):
                            self.screen_state = "comparison"
                            break
                        if self.screen_state == "game":
                            self._handle_game_click(ex, ey)

                if self.game_over and self.screen_state == "game":
                    self.screen_state = "gameover"

                if (self.screen_state == "game"
                        and self.ai_pending
                        and not self.game_over):
                    if self.menu_mode == "ia_ia":
                        now = pygame.time.get_ticks()
                        if now - self.ia_ia_last_move >= 600:
                            pygame.display.flip()
                            self._do_ai_turn()
                            self.ia_ia_last_move = now
                            if self.game_over:
                                self.screen_state = "gameover"
                    else:
                        # Redesenha com o estado atual (bloqueio do jogador visível)
                        # antes de a IA começar a calcular
                        self.screen.fill(C_BG)
                        self._game_bg()
                        self._draw_board()
                        self._draw_top_panel()
                        pygame.display.flip()
                        self._do_ai_turn()
                        if self.game_over:
                            self.screen_state = "gameover"

            pygame.display.flip()
            self.clock.tick(60)
