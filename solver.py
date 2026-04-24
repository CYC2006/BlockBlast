from itertools import permutations

BOARD_SIZE = 8


def normalize_piece(piece):
    """Convert a 5x5 boolean grid into a list of (row, col) offsets, origin at (0,0)."""
    cells = [(r, c) for r in range(5) for c in range(5) if piece[r][c]]
    if not cells:
        return []
    min_r = min(r for r, c in cells)
    min_c = min(c for r, c in cells)
    return [(r - min_r, c - min_c) for r, c in cells]


def can_place(board, cells, ar, ac):
    for pr, pc in cells:
        br, bc = ar + pr, ac + pc
        if not (0 <= br < BOARD_SIZE and 0 <= bc < BOARD_SIZE):
            return False
        if board[br][bc]:
            return False
    return True


def place_and_clear(board, cells, ar, ac):
    b = [row[:] for row in board]
    for pr, pc in cells:
        b[ar + pr][ac + pc] = True
    # Clear complete rows
    for r in range(BOARD_SIZE):
        if all(b[r]):
            b[r] = [False] * BOARD_SIZE
    # Clear complete columns
    for c in range(BOARD_SIZE):
        if all(b[r][c] for r in range(BOARD_SIZE)):
            for r in range(BOARD_SIZE):
                b[r][c] = False
    return b


def _try_place(board, pieces_cells):
    """Recursively try to place each piece in order. Returns True if all succeed."""
    if not pieces_cells:
        return True
    cells = pieces_cells[0]
    max_r = max(r for r, c in cells)
    max_c = max(c for r, c in cells)
    for ar in range(BOARD_SIZE - max_r):
        for ac in range(BOARD_SIZE - max_c):
            if can_place(board, cells, ar, ac):
                new_board = place_and_clear(board, cells, ar, ac)
                if _try_place(new_board, pieces_cells[1:]):
                    return True
    return False


def solve(board, pieces):
    """Return True if all pieces can be placed on the board in some order."""
    normalized = [normalize_piece(p) for p in pieces]
    normalized = [c for c in normalized if c]   # skip empty pieces
    if not normalized:
        return True
    for perm in permutations(normalized):
        if _try_place(board, list(perm)):
            return True
    return False
