import pygame
import sys
from solver import solve, get_clearing, precompute_states

# ------------------------------------------------------------------ Window
WINDOW_WIDTH  = 780
WINDOW_HEIGHT = 800

# ------------------------------------------------------------------ 8x8 board
GRID_COLS = 8
GRID_ROWS = 8
CELL_SIZE = 56
CELL_GAP  = 5
GRID_OFFSET_X = (WINDOW_WIDTH - (GRID_COLS * (CELL_SIZE + CELL_GAP) - CELL_GAP)) // 2
GRID_OFFSET_Y = 20

# ------------------------------------------------------------------ 5x5 piece editor
PIECE_COLS = 5
PIECE_ROWS = 5
PIECE_CELL = 36
PIECE_GAP  = 4
PIECE_EDITOR_X = 55

# ------------------------------------------------------------------ Mini piece display
MINI_CELL = 24
MINI_GAP  = 2

MAX_PIECES   = 3
MAX_SOLUTIONS = 20

# ------------------------------------------------------------------ Derived layout
_grid_h        = GRID_ROWS * (CELL_SIZE + CELL_GAP) - CELL_GAP   # 483
PIECE_AREA_TOP = GRID_OFFSET_Y + _grid_h + 20                     # 523
PIECE_EDITOR_Y = PIECE_AREA_TOP + 12

_editor_w    = PIECE_COLS * (PIECE_CELL + PIECE_GAP) - PIECE_GAP  # 196
DIVIDER_X    = PIECE_EDITOR_X + _editor_w + 18                    # 269
MINI_START_X = DIVIDER_X + 18                                      # 287

# ------------------------------------------------------------------ Colors
C_BG          = (14,  14,  14)
C_PANEL       = (26,  26,  26)
C_EMPTY       = (50,  50,  50)
C_FILLED      = (210, 210, 210)
C_FILLED_HIGH = (255, 255, 255)
C_EMPTY_HIGH  = (78,  78,  78)
C_TEXT        = (255, 255, 255)
C_SUBTEXT     = (145, 145, 145)
C_BTN         = (62,  62,  62)
C_BTN_HOVER   = (92,  92,  92)
C_BTN_TEXT    = (255, 255, 255)
C_BTN_DIM     = (32,  32,  32)
C_BTN_DIM_TXT = (70,  70,  70)
C_MINI_EMPTY  = (40,  40,  40)
C_DIVIDER     = (55,  55,  55)
C_SOLVE       = (75,  75,  75)
C_SOLVE_HOVER = (110, 110, 110)

# Step accent colors: (normal, hover/bright, dim for clearing rows)
STEP_COLORS = [
    ((60,  120, 220), (100, 155, 255), (30,  65,  140)),   # Step 0 — blue
    ((200, 130,  40), (235, 165,  75), (125,  80,  20)),   # Step 1 — amber
    ((55,  175,  95), (90,  210, 130), (28,  110,  55)),   # Step 2 — green
]


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("BlockBlast Helper")
        self.clock = pygame.time.Clock()

        bold = "Arial Black"
        self.font_label  = pygame.font.SysFont(bold, 14)
        self.font_btn    = pygame.font.SysFont(bold, 15)
        self.font_piece  = pygame.font.SysFont(bold, 15)
        self.font_hint   = pygame.font.SysFont(bold, 11)
        self.font_step   = pygame.font.SysFont(bold, 22)   # large step number
        self.font_info   = pygame.font.SysFont(bold, 13)

        # ---- Board state
        self.grid       = [[False] * GRID_COLS for _ in range(GRID_ROWS)]
        self.dragging   = False
        self.drag_paint = True

        # ---- Piece editor state
        self.piece_grid     = [[False] * PIECE_COLS for _ in range(PIECE_ROWS)]
        self.pieces         = []
        self.piece_dragging = False
        self.piece_paint    = True

        # ---- Mode: "edit" | "view"
        self.mode = "edit"

        # ---- View-mode state
        self.solutions   = []
        self.sol_capped  = False
        self.cur_sol     = 0
        self.cur_step    = 0
        self.board_states   = []   # board before each step (+ after last)
        self.clearing_info  = []   # (rows, cols) cleared at each step

        # ---- Button rects (set during draw)
        self.btn_clear_rect       = pygame.Rect(0, 0, 0, 0)
        self.btn_confirm_rect     = pygame.Rect(0, 0, 0, 0)
        self.btn_piece_clear_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_solve_rect       = pygame.Rect(0, 0, 0, 0)
        self.mini_piece_rects     = []

        # view-mode buttons
        self.btn_back_rect     = pygame.Rect(0, 0, 0, 0)
        self.btn_prev_sol_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_next_sol_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_step_rects    = [pygame.Rect(0, 0, 0, 0)] * 3

    # ====================================================== helpers

    def pos_to_cell(self, mx, my):
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_OFFSET_X + col * (CELL_SIZE + CELL_GAP)
                y = GRID_OFFSET_Y + row * (CELL_SIZE + CELL_GAP)
                if x <= mx < x + CELL_SIZE and y <= my < y + CELL_SIZE:
                    return row, col
        return None

    def pos_to_piece_cell(self, mx, my):
        for row in range(PIECE_ROWS):
            for col in range(PIECE_COLS):
                x = PIECE_EDITOR_X + col * (PIECE_CELL + PIECE_GAP)
                y = PIECE_EDITOR_Y + row * (PIECE_CELL + PIECE_GAP)
                if x <= mx < x + PIECE_CELL and y <= my < y + PIECE_CELL:
                    return row, col
        return None

    def grid_pixel_rect(self):
        w = GRID_COLS * (CELL_SIZE + CELL_GAP) - CELL_GAP
        h = GRID_ROWS * (CELL_SIZE + CELL_GAP) - CELL_GAP
        return pygame.Rect(GRID_OFFSET_X, GRID_OFFSET_Y, w, h)

    def _load_solution(self, idx):
        sol = self.solutions[idx]
        self.board_states  = precompute_states(self.grid, sol)
        self.clearing_info = [get_clearing(self.board_states[i], cells, ar, ac)
                              for i, (_, cells, ar, ac) in enumerate(sol)]

    def _enter_view_mode(self, solutions, capped):
        self.mode       = "view"
        self.solutions  = solutions
        self.sol_capped = capped
        self.cur_sol    = 0
        self.cur_step   = 0
        self._load_solution(0)

    # ====================================================== events

    def handle_events(self):
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.mode == "edit":
                    self._handle_edit_click(mx, my)
                else:
                    self._handle_view_click(mx, my)

            elif event.type == pygame.MOUSEMOTION:
                if self.mode == "edit":
                    if self.dragging:
                        cell = self.pos_to_cell(mx, my)
                        if cell:
                            self.grid[cell[0]][cell[1]] = self.drag_paint
                    if self.piece_dragging:
                        cell = self.pos_to_piece_cell(mx, my)
                        if cell:
                            self.piece_grid[cell[0]][cell[1]] = self.piece_paint

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
                self.piece_dragging = False

    def _handle_edit_click(self, mx, my):
        if self.btn_clear_rect.collidepoint(mx, my):
            self.grid = [[False] * GRID_COLS for _ in range(GRID_ROWS)]
            return

        if self.btn_confirm_rect.collidepoint(mx, my):
            has_cells = any(self.piece_grid[r][c]
                            for r in range(PIECE_ROWS) for c in range(PIECE_COLS))
            if has_cells and len(self.pieces) < MAX_PIECES:
                self.pieces.append([row[:] for row in self.piece_grid])
                self.piece_grid = [[False] * PIECE_COLS for _ in range(PIECE_ROWS)]
            return

        if self.btn_piece_clear_rect.collidepoint(mx, my):
            self.piece_grid = [[False] * PIECE_COLS for _ in range(PIECE_ROWS)]
            return

        if self.btn_solve_rect.collidepoint(mx, my):
            solutions, capped = solve(self.grid, self.pieces)
            count_str = f"{MAX_SOLUTIONS}+" if capped else str(len(solutions))
            if solutions:
                print(f"True {count_str}")
                self._enter_view_mode(solutions, capped)
            else:
                print("False")
            return

        # click confirmed mini piece to remove
        for i, rect in enumerate(self.mini_piece_rects):
            if rect.collidepoint(mx, my):
                self.pieces.pop(i)
                return

        cell = self.pos_to_cell(mx, my)
        if cell:
            r, c = cell
            self.drag_paint = not self.grid[r][c]
            self.grid[r][c] = self.drag_paint
            self.dragging = True
            return

        cell = self.pos_to_piece_cell(mx, my)
        if cell:
            r, c = cell
            self.piece_paint = not self.piece_grid[r][c]
            self.piece_grid[r][c] = self.piece_paint
            self.piece_dragging = True

    def _handle_view_click(self, mx, my):
        if self.btn_back_rect.collidepoint(mx, my):
            self.mode = "edit"
            return

        if self.btn_prev_sol_rect.collidepoint(mx, my) and self.cur_sol > 0:
            self.cur_sol -= 1
            self.cur_step = 0
            self._load_solution(self.cur_sol)
            return

        if self.btn_next_sol_rect.collidepoint(mx, my) and self.cur_sol < len(self.solutions) - 1:
            self.cur_sol += 1
            self.cur_step = 0
            self._load_solution(self.cur_sol)
            return

        for i, rect in enumerate(self.btn_step_rects):
            if rect.collidepoint(mx, my):
                self.cur_step = i
                return

    # ====================================================== drawing helpers

    def draw_button(self, label, rect, mx, my,
                    c_bg=None, c_bg_hover=None, c_txt=None):
        c_bg       = c_bg       or C_BTN
        c_bg_hover = c_bg_hover or C_BTN_HOVER
        c_txt      = c_txt      or C_BTN_TEXT
        hov = rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, c_bg_hover if hov else c_bg, rect, border_radius=8)
        surf = self.font_btn.render(label, True, c_txt)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    # ====================================================== edit-mode drawing

    def draw_grid_edit(self, mx, my):
        gr = self.grid_pixel_rect()
        pygame.draw.rect(self.screen, C_PANEL, gr.inflate(18, 18), border_radius=14)
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_OFFSET_X + col * (CELL_SIZE + CELL_GAP)
                y = GRID_OFFSET_Y + row * (CELL_SIZE + CELL_GAP)
                rect   = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                filled = self.grid[row][col]
                hov    = rect.collidepoint(mx, my)
                color  = (C_FILLED_HIGH if hov else C_FILLED) if filled else \
                         (C_EMPTY_HIGH  if hov else C_EMPTY)
                pygame.draw.rect(self.screen, color, rect, border_radius=7)

    def draw_piece_editor(self, mx, my):
        area_h = WINDOW_HEIGHT - 20 - PIECE_AREA_TOP
        area   = pygame.Rect(30, PIECE_AREA_TOP, WINDOW_WIDTH - 60, area_h)
        pygame.draw.rect(self.screen, C_PANEL, area, border_radius=14)

        # 5×5 editor grid
        for row in range(PIECE_ROWS):
            for col in range(PIECE_COLS):
                x    = PIECE_EDITOR_X + col * (PIECE_CELL + PIECE_GAP)
                y    = PIECE_EDITOR_Y + row * (PIECE_CELL + PIECE_GAP)
                rect = pygame.Rect(x, y, PIECE_CELL, PIECE_CELL)
                f    = self.piece_grid[row][col]
                hov  = rect.collidepoint(mx, my)
                color = (C_FILLED_HIGH if hov else C_FILLED) if f else \
                        (C_EMPTY_HIGH  if hov else C_EMPTY)
                pygame.draw.rect(self.screen, color, rect, border_radius=5)

        # Confirm / Clear buttons
        editor_grid_h = PIECE_ROWS * (PIECE_CELL + PIECE_GAP) - PIECE_GAP
        btn_y  = PIECE_EDITOR_Y + editor_grid_h + 12
        btn_w, btn_h = 92, 30

        self.btn_confirm_rect     = pygame.Rect(PIECE_EDITOR_X, btn_y, btn_w, btn_h)
        self.btn_piece_clear_rect = pygame.Rect(PIECE_EDITOR_X + btn_w + 8, btn_y, btn_w, btn_h)

        can_confirm = (len(self.pieces) < MAX_PIECES and
                       any(self.piece_grid[r][c]
                           for r in range(PIECE_ROWS) for c in range(PIECE_COLS)))
        self.draw_button("Confirm", self.btn_confirm_rect, mx, my,
                         c_bg=C_BTN if can_confirm else C_BTN_DIM,
                         c_bg_hover=C_BTN_HOVER if can_confirm else C_BTN_DIM,
                         c_txt=C_BTN_TEXT if can_confirm else C_BTN_DIM_TXT)
        self.draw_button("Clear", self.btn_piece_clear_rect, mx, my)

        # Vertical divider
        pygame.draw.line(self.screen, C_DIVIDER,
                         (DIVIDER_X, area.top + 14), (DIVIDER_X, area.bottom - 14), 1)

        # Mini confirmed pieces (right section)
        self._draw_mini_pieces(mx, my, area, highlight_step=None)

        # Solve button
        solve_w, solve_h = 120, 34
        self.btn_solve_rect = pygame.Rect(area.right - solve_w - 14,
                                          area.bottom - solve_h - 14,
                                          solve_w, solve_h)
        self.draw_button("Solve", self.btn_solve_rect, mx, my,
                         c_bg=C_SOLVE, c_bg_hover=C_SOLVE_HOVER)

    def _draw_mini_pieces(self, mx, my, area, highlight_step):
        """Draw the mini confirmed pieces in the right section.
        highlight_step: int (0/1/2) to tint that piece, or None for normal display."""
        mini_size    = PIECE_COLS * (MINI_CELL + MINI_GAP) - MINI_GAP
        mini_gap_btw = 22
        right_cx     = (MINI_START_X + area.right) // 2
        right_cy     = area.top + (area.height - 30) // 2

        self.mini_piece_rects = []

        if not self.pieces:
            msg = self.font_label.render("No pieces yet", True, C_SUBTEXT)
            self.screen.blit(msg, msg.get_rect(centerx=right_cx, centery=right_cy))
            return

        total_w = len(self.pieces) * mini_size + (len(self.pieces) - 1) * mini_gap_btw
        start_x = right_cx - total_w // 2
        mini_y  = right_cy - mini_size // 2

        for i, piece in enumerate(self.pieces):
            px         = start_x + i * (mini_size + mini_gap_btw)
            piece_rect = pygame.Rect(px, mini_y, mini_size, mini_size)
            self.mini_piece_rects.append(piece_rect)

            is_active = (highlight_step is not None and i == highlight_step)
            hov       = piece_rect.collidepoint(mx, my) and highlight_step is None

            step_c = STEP_COLORS[i][0] if is_active else None

            # Label
            lbl_text = f"Step {i}" if highlight_step is not None else f"Piece {i + 1}"
            lbl_color = STEP_COLORS[i][1] if is_active else (C_TEXT if hov else C_SUBTEXT)
            lbl = self.font_piece.render(lbl_text, True, lbl_color)
            self.screen.blit(lbl, lbl.get_rect(centerx=px + mini_size // 2,
                                                bottom=mini_y - 6))

            for row in range(PIECE_ROWS):
                for col in range(PIECE_COLS):
                    x    = px + col * (MINI_CELL + MINI_GAP)
                    y    = mini_y + row * (MINI_CELL + MINI_GAP)
                    rect = pygame.Rect(x, y, MINI_CELL, MINI_CELL)
                    if piece[row][col]:
                        if is_active:
                            color = STEP_COLORS[i][1]
                        elif hov:
                            color = C_FILLED_HIGH
                        else:
                            color = C_FILLED
                    else:
                        color = C_MINI_EMPTY
                    pygame.draw.rect(self.screen, color, rect, border_radius=3)

            if hov and highlight_step is None:
                hint = self.font_hint.render("click to remove", True, C_SUBTEXT)
                self.screen.blit(hint, hint.get_rect(
                    centerx=px + mini_size // 2, top=mini_y + mini_size + 5))

    # ====================================================== view-mode drawing

    def draw_grid_view(self, mx, my):
        sol  = self.solutions[self.cur_sol]
        step = self.cur_step
        board         = self.board_states[step]
        _, cells, ar, ac = sol[step]
        rows_clr, cols_clr = self.clearing_info[step]

        c_normal, c_bright, c_dim = STEP_COLORS[step]

        piece_set = {(ar + pr, ac + pc) for pr, pc in cells}
        clear_set = set()
        for r in rows_clr:
            for c in range(GRID_COLS):
                clear_set.add((r, c))
        for c in cols_clr:
            for r in range(GRID_ROWS):
                clear_set.add((r, c))

        gr = self.grid_pixel_rect()
        pygame.draw.rect(self.screen, C_PANEL, gr.inflate(18, 18), border_radius=14)

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x    = GRID_OFFSET_X + col * (CELL_SIZE + CELL_GAP)
                y    = GRID_OFFSET_Y + row * (CELL_SIZE + CELL_GAP)
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                in_piece = (row, col) in piece_set
                in_clear = (row, col) in clear_set
                filled   = board[row][col]

                if in_piece and in_clear:
                    color = c_dim       # piece lands in clearing zone → dimmed (will vanish)
                elif in_piece:
                    color = c_bright    # piece placed normally → bright step color
                elif in_clear and filled:
                    color = (105, 105, 105)  # existing cell about to be cleared → mid gray
                elif filled:
                    color = C_FILLED
                else:
                    color = C_EMPTY

                pygame.draw.rect(self.screen, color, rect, border_radius=7)

    def draw_view_panel(self, mx, my):
        area_h = WINDOW_HEIGHT - 20 - PIECE_AREA_TOP
        area   = pygame.Rect(30, PIECE_AREA_TOP, WINDOW_WIDTH - 60, area_h)
        pygame.draw.rect(self.screen, C_PANEL, area, border_radius=14)

        # ---- Left: step buttons [0] [1] [2]
        n_steps   = len(self.solutions[self.cur_sol])
        btn_w, btn_h = 64, 48
        gap       = 12
        total_btn_w = n_steps * btn_w + (n_steps - 1) * gap
        left_cx   = (30 + DIVIDER_X) // 2
        btn_start_x = left_cx - total_btn_w // 2
        btn_y     = area.centery - btn_h // 2 - 10

        self.btn_step_rects = []
        for i in range(n_steps):
            bx   = btn_start_x + i * (btn_w + gap)
            rect = pygame.Rect(bx, btn_y, btn_w, btn_h)
            self.btn_step_rects.append(rect)

            active = (i == self.cur_step)
            c_norm, c_brt, _ = STEP_COLORS[i]
            bg = c_brt if active else (C_BTN_HOVER if rect.collidepoint(mx, my) else C_BTN)
            pygame.draw.rect(self.screen, bg, rect, border_radius=10)

            num_surf = self.font_step.render(str(i), True, C_TEXT)
            self.screen.blit(num_surf, num_surf.get_rect(center=rect.center))

        # active indicator dot
        act_rect = self.btn_step_rects[self.cur_step]
        dot_y = btn_y + btn_h + 8
        pygame.draw.circle(self.screen, STEP_COLORS[self.cur_step][0],
                           (act_rect.centerx, dot_y), 4)

        # Piece label below buttons
        sol  = self.solutions[self.cur_sol]
        pidx = sol[self.cur_step][0]
        info = self.font_info.render(f"Placing Piece {pidx + 1}", True, C_SUBTEXT)
        self.screen.blit(info, info.get_rect(centerx=left_cx, top=dot_y + 14))

        # ---- Vertical divider
        pygame.draw.line(self.screen, C_DIVIDER,
                         (DIVIDER_X, area.top + 14), (DIVIDER_X, area.bottom - 14), 1)

        # ---- Right: mini pieces with current step highlighted
        # Determine which piece_idx corresponds to each step
        step_piece_order = [s[0] for s in sol]   # e.g. [1, 0, 2]
        # highlight_step tells _draw_mini_pieces which piece index to colour
        # We highlight piece[step_piece_order[cur_step]]
        self._draw_mini_pieces(mx, my, area,
                               highlight_step=step_piece_order[self.cur_step])

        # ---- Solution navigation (bottom of right section)
        total = len(self.solutions)
        label = f"Sol {self.cur_sol + 1} / {'20+' if self.sol_capped else total}"
        sol_lbl = self.font_info.render(label, True, C_SUBTEXT)

        nav_cx = (MINI_START_X + area.right) // 2
        nav_y  = area.bottom - 38

        arr_w, arr_h = 32, 26
        self.btn_prev_sol_rect = pygame.Rect(nav_cx - 80, nav_y, arr_w, arr_h)
        self.btn_next_sol_rect = pygame.Rect(nav_cx + 48, nav_y, arr_w, arr_h)

        can_prev = self.cur_sol > 0
        can_next = self.cur_sol < len(self.solutions) - 1
        self.draw_button("←", self.btn_prev_sol_rect, mx, my,
                         c_bg=C_BTN if can_prev else C_BTN_DIM,
                         c_bg_hover=C_BTN_HOVER if can_prev else C_BTN_DIM)
        self.draw_button("→", self.btn_next_sol_rect, mx, my,
                         c_bg=C_BTN if can_next else C_BTN_DIM,
                         c_bg_hover=C_BTN_HOVER if can_next else C_BTN_DIM)
        self.screen.blit(sol_lbl, sol_lbl.get_rect(centerx=nav_cx, centery=nav_y + arr_h // 2))

    # ====================================================== main draw

    def draw(self):
        mx, my = pygame.mouse.get_pos()
        self.screen.fill(C_BG)

        if self.mode == "edit":
            self.draw_grid_edit(mx, my)

            gr = self.grid_pixel_rect()
            self.btn_clear_rect = pygame.Rect(gr.right + 12, gr.top, 82, 30)
            self.draw_button("Clear", self.btn_clear_rect, mx, my)

            self.draw_piece_editor(mx, my)

        else:  # view mode
            self.draw_grid_view(mx, my)

            gr = self.grid_pixel_rect()
            self.btn_back_rect = pygame.Rect(gr.right + 12, gr.top, 110, 30)
            self.draw_button("← Edit", self.btn_back_rect, mx, my)

            self.draw_view_panel(mx, my)

        pygame.display.flip()

    # ====================================================== loop

    def run(self):
        while True:
            self.handle_events()
            self.draw()
            self.clock.tick(60)


if __name__ == "__main__":
    app = App()
    app.run()
