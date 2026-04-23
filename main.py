import pygame
import sys

# Window
WINDOW_WIDTH  = 780
WINDOW_HEIGHT = 900

# 8x8 board grid
GRID_COLS = 8
GRID_ROWS = 8
CELL_SIZE = 56
CELL_GAP  = 5
GRID_OFFSET_X = (WINDOW_WIDTH - (GRID_COLS * (CELL_SIZE + CELL_GAP) - CELL_GAP)) // 2
GRID_OFFSET_Y = 90

# 5x5 piece editor
PIECE_COLS = 5
PIECE_ROWS = 5
PIECE_CELL = 36
PIECE_GAP  = 4
PIECE_EDITOR_X = 55

# Mini piece display
MINI_CELL = 18
MINI_GAP  = 2

MAX_PIECES = 3

# Derived layout
_grid_h        = GRID_ROWS * (CELL_SIZE + CELL_GAP) - CELL_GAP   # 483
PIECE_AREA_TOP = GRID_OFFSET_Y + _grid_h + 40                     # 613
PIECE_EDITOR_Y = PIECE_AREA_TOP + 15

_editor_w  = PIECE_COLS * (PIECE_CELL + PIECE_GAP) - PIECE_GAP   # 196
DIVIDER_X  = PIECE_EDITOR_X + _editor_w + 42                     # 293
MINI_START_X = DIVIDER_X + 22                                     # 315

# Colors — black/gray/white
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


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("BlockBlast Helper")
        self.clock = pygame.time.Clock()

        bold = "Arial Black"
        self.font_title  = pygame.font.SysFont(bold, 28)
        self.font_label  = pygame.font.SysFont(bold, 14)
        self.font_btn    = pygame.font.SysFont(bold, 15)
        self.font_piece  = pygame.font.SysFont(bold, 15)   # Piece N labels
        self.font_hint   = pygame.font.SysFont(bold, 11)

        # Board state
        self.grid       = [[False] * GRID_COLS for _ in range(GRID_ROWS)]
        self.dragging   = False
        self.drag_paint = True

        # Piece editor state
        self.piece_grid     = [[False] * PIECE_COLS for _ in range(PIECE_ROWS)]
        self.pieces         = []
        self.piece_dragging = False
        self.piece_paint    = True

        # Button rects (set during draw)
        self.btn_clear_rect       = pygame.Rect(0, 0, 0, 0)
        self.btn_confirm_rect     = pygame.Rect(0, 0, 0, 0)
        self.btn_piece_clear_rect = pygame.Rect(0, 0, 0, 0)
        self.btn_solve_rect       = pygame.Rect(0, 0, 0, 0)
        self.mini_piece_rects     = []

    # ------------------------------------------------------------------ helpers

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

    # ------------------------------------------------------------------ events

    def handle_events(self):
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_clear_rect.collidepoint(mx, my):
                    self.grid = [[False] * GRID_COLS for _ in range(GRID_ROWS)]
                    continue

                if self.btn_confirm_rect.collidepoint(mx, my):
                    has_cells = any(self.piece_grid[r][c]
                                    for r in range(PIECE_ROWS) for c in range(PIECE_COLS))
                    if has_cells and len(self.pieces) < MAX_PIECES:
                        self.pieces.append([row[:] for row in self.piece_grid])
                        self.piece_grid = [[False] * PIECE_COLS for _ in range(PIECE_ROWS)]
                    continue

                if self.btn_piece_clear_rect.collidepoint(mx, my):
                    self.piece_grid = [[False] * PIECE_COLS for _ in range(PIECE_ROWS)]
                    continue

                if self.btn_solve_rect.collidepoint(mx, my):
                    continue   # placeholder — solver not yet implemented

                removed = False
                for i, rect in enumerate(self.mini_piece_rects):
                    if rect.collidepoint(mx, my):
                        self.pieces.pop(i)
                        removed = True
                        break
                if removed:
                    continue

                cell = self.pos_to_cell(mx, my)
                if cell:
                    r, c = cell
                    self.drag_paint = not self.grid[r][c]
                    self.grid[r][c] = self.drag_paint
                    self.dragging = True
                    continue

                cell = self.pos_to_piece_cell(mx, my)
                if cell:
                    r, c = cell
                    self.piece_paint = not self.piece_grid[r][c]
                    self.piece_grid[r][c] = self.piece_paint
                    self.piece_dragging = True

            elif event.type == pygame.MOUSEMOTION:
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

    # ------------------------------------------------------------------ drawing

    def draw_button(self, label, rect, mx, my,
                    c_bg=None, c_bg_hover=None, c_txt=None):
        c_bg       = c_bg       or C_BTN
        c_bg_hover = c_bg_hover or C_BTN_HOVER
        c_txt      = c_txt      or C_BTN_TEXT
        hov = rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, c_bg_hover if hov else c_bg, rect, border_radius=8)
        surf = self.font_btn.render(label, True, c_txt)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_grid(self, mx, my):
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

        # --- Left: 5×5 piece editor ---
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
        editor_grid_h = PIECE_ROWS * (PIECE_CELL + PIECE_GAP) - PIECE_GAP   # 196
        btn_y  = PIECE_EDITOR_Y + editor_grid_h + 12
        btn_w, btn_h = 92, 30

        self.btn_confirm_rect     = pygame.Rect(PIECE_EDITOR_X, btn_y, btn_w, btn_h)
        self.btn_piece_clear_rect = pygame.Rect(PIECE_EDITOR_X + btn_w + 8, btn_y, btn_w, btn_h)

        can_confirm = (len(self.pieces) < MAX_PIECES and
                       any(self.piece_grid[r][c]
                           for r in range(PIECE_ROWS) for c in range(PIECE_COLS)))

        if can_confirm:
            self.draw_button("Confirm", self.btn_confirm_rect, mx, my)
        else:
            self.draw_button("Confirm", self.btn_confirm_rect, mx, my,
                             c_bg=C_BTN_DIM, c_bg_hover=C_BTN_DIM, c_txt=C_BTN_DIM_TXT)

        self.draw_button("Clear", self.btn_piece_clear_rect, mx, my)

        # Vertical divider
        pygame.draw.line(self.screen, C_DIVIDER,
                         (DIVIDER_X, area.top + 14), (DIVIDER_X, area.bottom - 14), 1)

        # --- Right: confirmed pieces ---
        mini_size    = PIECE_COLS * (MINI_CELL + MINI_GAP) - MINI_GAP   # 98
        mini_gap_btw = 22
        right_cx     = (MINI_START_X + area.right) // 2
        right_cy     = area.top + (area_h - 30) // 2   # shift up slightly for Solve btn

        self.mini_piece_rects = []

        if not self.pieces:
            msg = self.font_label.render("No pieces yet", True, C_SUBTEXT)
            self.screen.blit(msg, msg.get_rect(centerx=right_cx, centery=right_cy))
        else:
            total_w = len(self.pieces) * mini_size + (len(self.pieces) - 1) * mini_gap_btw
            start_x = right_cx - total_w // 2
            mini_y  = right_cy - mini_size // 2

            for i, piece in enumerate(self.pieces):
                px         = start_x + i * (mini_size + mini_gap_btw)
                piece_rect = pygame.Rect(px, mini_y, mini_size, mini_size)
                self.mini_piece_rects.append(piece_rect)
                hov = piece_rect.collidepoint(mx, my)

                # "Piece N" label
                lbl = self.font_piece.render(f"Piece {i + 1}", True, C_TEXT)
                self.screen.blit(lbl, lbl.get_rect(centerx=px + mini_size // 2,
                                                    bottom=mini_y - 6))

                for row in range(PIECE_ROWS):
                    for col in range(PIECE_COLS):
                        x    = px + col * (MINI_CELL + MINI_GAP)
                        y    = mini_y + row * (MINI_CELL + MINI_GAP)
                        rect = pygame.Rect(x, y, MINI_CELL, MINI_CELL)
                        color = (C_FILLED_HIGH if hov else C_FILLED) if piece[row][col] \
                                else C_MINI_EMPTY
                        pygame.draw.rect(self.screen, color, rect, border_radius=3)

                if hov:
                    hint = self.font_hint.render("click to remove", True, C_SUBTEXT)
                    self.screen.blit(hint, hint.get_rect(
                        centerx=px + mini_size // 2, top=mini_y + mini_size + 5))

        # Solve button — bottom right of panel
        solve_w, solve_h = 120, 34
        self.btn_solve_rect = pygame.Rect(area.right - solve_w - 14,
                                          area.bottom - solve_h - 14,
                                          solve_w, solve_h)
        self.draw_button("Solve", self.btn_solve_rect, mx, my,
                         c_bg=C_SOLVE, c_bg_hover=C_SOLVE_HOVER)

    def draw(self):
        mx, my = pygame.mouse.get_pos()
        self.screen.fill(C_BG)

        title = self.font_title.render("BlockBlast Helper", True, C_TEXT)
        self.screen.blit(title, title.get_rect(centerx=WINDOW_WIDTH // 2, y=22))

        self.draw_grid(mx, my)

        gr = self.grid_pixel_rect()
        self.btn_clear_rect = pygame.Rect(gr.right - 82, gr.top - 38, 82, 28)
        self.draw_button("Clear", self.btn_clear_rect, mx, my)

        self.draw_piece_editor(mx, my)

        pygame.display.flip()

    # ------------------------------------------------------------------ loop

    def run(self):
        while True:
            self.handle_events()
            self.draw()
            self.clock.tick(60)


if __name__ == "__main__":
    app = App()
    app.run()
