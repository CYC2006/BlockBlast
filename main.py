import pygame
import sys

# Window
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 900

# 8x8 grid
GRID_COLS = 8
GRID_ROWS = 8
CELL_SIZE = 56
CELL_GAP = 5
GRID_OFFSET_X = (WINDOW_WIDTH - (GRID_COLS * (CELL_SIZE + CELL_GAP) - CELL_GAP)) // 2
GRID_OFFSET_Y = 90

# Colors
C_BG          = (28,  56,  45)
C_PANEL       = (20,  45,  35)
C_EMPTY       = (38,  80,  58)
C_FILLED      = (220, 170,  55)
C_FILLED_HIGH = (240, 195,  85)   # hover highlight when filled
C_EMPTY_HIGH  = (55, 105,  75)    # hover highlight when empty
C_TEXT        = (230, 230, 230)
C_SUBTEXT     = (140, 180, 155)
C_BTN         = (50,  110,  75)
C_BTN_HOVER   = (65,  140,  95)
C_BTN_TEXT    = (255, 255, 255)


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("BlockBlast Helper")
        self.clock = pygame.time.Clock()

        self.font_title  = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_label  = pygame.font.SysFont("Arial", 14)
        self.font_btn    = pygame.font.SysFont("Arial", 15, bold=True)

        self.grid = [[False] * GRID_COLS for _ in range(GRID_ROWS)]

        # drag state
        self.dragging   = False
        self.drag_paint = True   # True = paint filled, False = erase

        # clear button rect (defined in draw, used in events)
        self.btn_clear_rect = pygame.Rect(0, 0, 0, 0)

    # ------------------------------------------------------------------ helpers

    def pos_to_cell(self, mx, my):
        """Return (row, col) if (mx, my) is inside the 8x8 grid, else None."""
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_OFFSET_X + col * (CELL_SIZE + CELL_GAP)
                y = GRID_OFFSET_Y + row * (CELL_SIZE + CELL_GAP)
                if x <= mx < x + CELL_SIZE and y <= my < y + CELL_SIZE:
                    return row, col
        return None

    def grid_pixel_rect(self):
        """Return the bounding Rect of the full 8x8 grid."""
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
                # Clear button
                if self.btn_clear_rect.collidepoint(mx, my):
                    self.grid = [[False] * GRID_COLS for _ in range(GRID_ROWS)]
                    continue

                # Grid cells
                cell = self.pos_to_cell(mx, my)
                if cell:
                    r, c = cell
                    self.drag_paint = not self.grid[r][c]
                    self.grid[r][c] = self.drag_paint
                    self.dragging = True

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    cell = self.pos_to_cell(mx, my)
                    if cell:
                        r, c = cell
                        self.grid[r][c] = self.drag_paint

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False

    # ------------------------------------------------------------------ drawing

    def draw_grid(self, mx, my):
        # Panel background
        gr = self.grid_pixel_rect()
        panel = gr.inflate(18, 18)
        pygame.draw.rect(self.screen, C_PANEL, panel, border_radius=14)

        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = GRID_OFFSET_X + col * (CELL_SIZE + CELL_GAP)
                y = GRID_OFFSET_Y + row * (CELL_SIZE + CELL_GAP)
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

                filled  = self.grid[row][col]
                hovered = rect.collidepoint(mx, my)

                if filled:
                    color = C_FILLED_HIGH if hovered else C_FILLED
                else:
                    color = C_EMPTY_HIGH  if hovered else C_EMPTY

                pygame.draw.rect(self.screen, color, rect, border_radius=7)

    def draw_button(self, label, rect, mx, my):
        hovered = rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, C_BTN_HOVER if hovered else C_BTN, rect, border_radius=8)
        surf = self.font_btn.render(label, True, C_BTN_TEXT)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def draw_placeholder(self):
        """Reserved area for the three 5x5 piece grids (not yet implemented)."""
        gr = self.grid_pixel_rect()
        top = gr.bottom + 40
        w   = WINDOW_WIDTH - 60
        h   = WINDOW_HEIGHT - top - 20
        if h <= 0:
            return
        area = pygame.Rect(30, top, w, h)
        pygame.draw.rect(self.screen, C_PANEL, area, border_radius=14)
        lbl = self.font_label.render("Piece area — coming soon", True, C_SUBTEXT)
        self.screen.blit(lbl, lbl.get_rect(center=area.center))

    def draw(self):
        mx, my = pygame.mouse.get_pos()
        self.screen.fill(C_BG)

        # Title
        title = self.font_title.render("BlockBlast AI Solver", True, C_TEXT)
        self.screen.blit(title, title.get_rect(centerx=WINDOW_WIDTH // 2, y=22))

        self.draw_grid(mx, my)

        # Clear button — top-right of grid
        gr = self.grid_pixel_rect()
        self.btn_clear_rect = pygame.Rect(gr.right - 80, gr.top - 36, 80, 26)
        self.draw_button("Clear", self.btn_clear_rect, mx, my)

        self.draw_placeholder()

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
