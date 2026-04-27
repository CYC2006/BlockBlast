from itertools import permutations

BOARD_SIZE = 8


def normalize_piece(piece):
    """Convert 5×5 boolean grid → list of (row, col) offsets with origin at (0,0)."""
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
    for r in range(BOARD_SIZE):
        if all(b[r]):
            b[r] = [False] * BOARD_SIZE
    for c in range(BOARD_SIZE):
        if all(b[r][c] for r in range(BOARD_SIZE)):
            for r in range(BOARD_SIZE):
                b[r][c] = False
    return b


def get_clearing(board, cells, ar, ac):
    """Return (rows, cols) that will be cleared when piece is placed at (ar, ac)."""
    b = [row[:] for row in board]
    for pr, pc in cells:
        b[ar + pr][ac + pc] = True
    rows = [r for r in range(BOARD_SIZE) if all(b[r])]
    cols = [c for c in range(BOARD_SIZE) if all(b[r][c] for r in range(BOARD_SIZE))]
    return rows, cols


def precompute_states(initial_board, solution):
    """Return board state before each step (length = n_steps + 1)."""
    states = [initial_board]
    board = initial_board
    for (_, cells, ar, ac) in solution:
        board = place_and_clear(board, cells, ar, ac)
        states.append(board)
    return states


def _find_solutions(board, remaining, current_steps, solutions, max_solutions):
    if len(solutions) >= max_solutions:
        return
    if not remaining:
        solutions.append(list(current_steps))
        return

    piece_idx, cells = remaining[0]
    if not cells:
        current_steps.append((piece_idx, cells, 0, 0))
        _find_solutions(board, remaining[1:], current_steps, solutions, max_solutions)
        current_steps.pop()
        return

    max_r = max(r for r, c in cells)
    max_c = max(c for r, c in cells)

    for ar in range(BOARD_SIZE - max_r):
        if len(solutions) >= max_solutions:
            return
        for ac in range(BOARD_SIZE - max_c):
            if len(solutions) >= max_solutions:
                return
            if can_place(board, cells, ar, ac):
                new_board = place_and_clear(board, cells, ar, ac)
                current_steps.append((piece_idx, cells, ar, ac))
                _find_solutions(new_board, remaining[1:], current_steps, solutions, max_solutions)
                current_steps.pop()


def solve(board, pieces, max_solutions=20):
    """Return (solutions, capped).
    Each solution = [(piece_idx, cells, anchor_row, anchor_col), ...]
    capped = True if ≥ max_solutions solutions exist.
    """
    indexed = [(i, normalize_piece(p)) for i, p in enumerate(pieces)]
    indexed = [(i, c) for i, c in indexed if c]
    if not indexed:
        return [], False

    solutions = []
    for perm in permutations(indexed):
        if len(solutions) >= max_solutions:
            break
        _find_solutions(board, list(perm), [], solutions, max_solutions)

    capped = len(solutions) >= max_solutions
    return solutions, capped
