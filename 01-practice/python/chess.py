

import re
import os
import sys
import time
import pickle
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from itertools import count
from collections import namedtuple
import numpy as np
from functools import partial

print = partial(print, flush=True)

version = 'sunfish nnue'

# Neural network dimensions
L0, L1, L2 = 10, 10, 10

# Load model from argument or default path
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(script_dir, 'nnue/models/tanh.pickle')
try:
    model = pickle.load(open(model_path, 'rb'))
except Exception as exc:
    print(f'Error loading model: {exc}', file=sys.stderr)
    print('Usage: changed.py [model_path]', file=sys.stderr)
    sys.exit(1)
# pos_emb, comb, piece_val, comb_col layers0-1
arrays = [np.frombuffer(arr, dtype=np.int8) / 127.0 for arr in model['ars']]
layer1, layer2 = arrays[4].reshape(L2, 2 * L1 - 2), arrays[5].reshape(1, L2)

# pad embedding to 10x12 board
pad = np.pad(arrays[0].reshape(8, 8, 6)[::-1], ((2, 2), (1, 1), (0, 0))).reshape(120, 6)
pos_table = np.einsum('sd,odp->pso', pad, arrays[1].reshape(L0, 6, 6))
pos_table = np.einsum('psd,odc->cpso', pos_table, arrays[3].reshape(L0, L0, 2))
pst = dict(zip('PNBRQKpnbrqk', pos_table.reshape(12, 120, L0)))
pst['.'] = [[0] * L0] * 120

MATE = 100000
pst['K'][:, 0] += MATE // 2
pst['k'][:, 0] -= MATE // 2
MATE_LOWER = MATE // 2
MATE_UPPER = MATE * 3 // 2

# Board constants
A1, H1, A8, H8 = 91, 98, 21, 28
initial_board = (
    '         \n'
    '         \n'
    ' rnbqkbnr\n'
    ' pppppppp\n'
    ' ........\n'
    ' ........\n'
    ' ........\n'
    ' ........\n'
    ' PPPPPPPP\n'
    ' RNBQKBNR\n'
    '         \n'
    '         \n'
)

N, E, S, W = -10, 1, 10, -1
piece_dirs = {
    'P': (N, N + N, N + W, N + E),
    'N': (N + N + E, E + N + E, E + S + E, S + S + E, S + S + W, W + S + W, W + N + W, N + N + W),
    'B': (N + E, S + E, S + W, N + W),
    'R': (N, E, S, W),
    'Q': (N, E, S, W, N + E, S + E, S + W, N + W),
    'K': (N, E, S, W, N + E, S + E, S + W, N + W),
}

EVAL_ROUGHNESS = 13
Move = namedtuple('Move', 'frm to promo')


class Position(namedtuple('Position', 'board score wf bf wc bc ep kp')):
    def gen_moves(self):
        for i, piece in enumerate(self.board):
            if not piece.isupper():
                continue
            for direction in piece_dirs[piece]:
                for j in count(i + direction, direction):
                    target = self.board[j]
                    if target.isspace() or target.isupper():
                        break
                    if piece == 'P':
                        if direction in (N, N + N) and target != '.':
                            break
                        if direction == N + N and (i < A1 + N or self.board[i + N] != '.'):
                            break
                        if direction in (N + W, N + E) and target == '.' and j not in (self.ep, self.kp, self.kp - 1, self.kp + 1):
                            break
                        if A8 <= j <= H8:
                            yield from (Move(i, j, prom) for prom in 'NBRQ')
                            break
                    yield Move(i, j, '')
                    if piece in 'PNK' or target.islower():
                        break
                    if i == A1 and self.board[j + E] == 'K' and self.wc[0]:
                        yield Move(j + E, j + W, '')
                    if i == H1 and self.board[j + W] == 'K' and self.wc[1]:
                        yield Move(j + W, j + E, '')

    def rotate(self, nullmove=False):
        rotated = Position(
            self.board[::-1].swapcase(),
            0,
            self.bf,
            self.wf,
            self.bc,
            self.wc,
            0 if nullmove or not self.ep else 119 - self.ep,
            0 if nullmove or not self.kp else 119 - self.kp,
        )
        return rotated._replace(score=rotated.compute_value())

    def put_piece(self, pos, index, piece):
        return pos._replace(
            board=pos.board[:index] + piece + pos.board[index + 1 :],
            wf=pos.wf + pst[piece][index] - pst[pos.board[index]][index],
            bf=pos.bf + pst[piece.swapcase()][119 - index] - pst[pos.board[index].swapcase()][119 - index],
        )

    def move(self, move):
        frm, to, promo = move
        piece = self.board[frm]
        new_pos = self._replace(ep=0, kp=0)
        new_pos = self.put_piece(new_pos, to, piece)
        new_pos = self.put_piece(new_pos, frm, '.')
        if frm == A1:
            new_pos = new_pos._replace(wc=(False, new_pos.wc[1]))
        if frm == H1:
            new_pos = new_pos._replace(wc=(new_pos.wc[0], False))
        if to == A8:
            new_pos = new_pos._replace(bc=(new_pos.bc[0], False))
        if to == H8:
            new_pos = new_pos._replace(bc=(False, new_pos.bc[1]))
        if abs(to - self.kp) < 2:
            new_pos = self.put_piece(new_pos, self.kp, 'K')
        if piece == 'K':
            new_pos = new_pos._replace(wc=(False, False))
            if abs(to - frm) == 2:
                new_pos = new_pos._replace(kp=(frm + to) // 2)
                new_pos = self.put_piece(new_pos, A1 if to < frm else H1, '.')
                new_pos = self.put_piece(new_pos, (frm + to) // 2, 'R')
        if piece == 'P':
            if A8 <= to <= H8:
                new_pos = self.put_piece(new_pos, to, promo)
            if to - frm == 2 * N:
                new_pos = new_pos._replace(ep=frm + N)
            if to == self.ep:
                new_pos = self.put_piece(new_pos, to + S, '.')
        return new_pos.rotate()

    def is_capture(self, move):
        return self.board[move.to] != '.' or abs(move.to - self.kp) < 2 or move.promo

    def compute_value(self):
        act = np.tanh
        wf, bf = self.wf, self.bf
        hidden = (layer1[:, :9] @ act(wf[1:])) + (layer1[:, 9:] @ act(bf[1:]))
        score = layer2 @ act(hidden)
        return int(((score + model['scale'] * (wf[0] - bf[0])) * 360).item())

    def hash(self):
        return hash((self.board, self.wc, self.bc, self.ep, self.kp))


Entry = namedtuple('Entry', 'lower upper')

class Searcher:
    def __init__(self):
        self.tt_score = {}
        self.tt_move = {}
        self.history = set()
        self.nodes = 0

    def bound(self, pos, gamma, depth, root=True):
        self.nodes += 1
        depth = max(depth, 0)
        if pos.score <= -MATE_LOWER:
            return -MATE_UPPER
        entry = self.tt_score.get((pos.hash(), depth, root), Entry(-MATE_UPPER, MATE_UPPER))
        if entry.lower >= gamma:
            return entry.lower
        if entry.upper < gamma:
            return entry.upper
        if not root and pos.hash() in self.history:
            return 0

        def move_order(move):
            if abs(move.to - pos.kp) < 2:
                return -MATE
            frm, to = move.frm, move.to
            piece = pos.board[frm]
            target = pos.board[to]
            promo_piece = move.promo or piece
            score = pst[target][to][0] - (pst[promo_piece][to][0] - pst[piece][frm][0])
            score -= pst[target.swapcase()][119 - to][0] - (pst[promo_piece.swapcase()][119 - to][0] - pst[piece.swapcase()][119 - frm][0])
            return score

        def moves():
            if depth > 2 and not root and any(c in pos.board for c in 'NBRQ'):
                yield None, -self.bound(pos.rotate(nullmove=True), 1 - gamma, depth - 3, False)
            if depth == 0:
                yield None, pos.score
            killer = self.tt_move.get(pos.hash())
            if killer and (depth > 0 or pos.is_capture(killer)):
                yield killer, -self.bound(pos.move(killer), 1 - gamma, depth - 1, False)
            for move in sorted(pos.gen_moves(), key=move_order):
                if depth > 0 or pos.is_capture(move):
                    yield move, -self.bound(pos.move(move), 1 - gamma, depth - 1, False)

        best = -MATE_UPPER
        for move, score in moves():
            best = max(best, score)
            if best >= gamma:
                if move is not None:
                    self.tt_move[pos.hash()] = move
                break

        if depth > 0 and best == -MATE_UPPER:
            flipped = pos.rotate(nullmove=True)
            in_check = self.bound(flipped, MATE_UPPER, 0) == MATE_UPPER
            best = -MATE_LOWER if in_check else 0

        self.tt_score[pos.hash(), depth, root] = Entry(best, entry.upper) if best >= gamma else Entry(entry.lower, best)
        return best

    def search(self, history):
        self.nodes = 0
        pos = history[-1]
        self.history = {p.hash() for p in history}
        self.tt_score.clear()
        gamma = 0
        for depth in range(1, 1000):
            lower, upper = -MATE_UPPER, MATE_UPPER
            while lower < upper - EVAL_ROUGHNESS:
                score = self.bound(pos, gamma, depth)
                if score >= gamma:
                    lower = score
                else:
                    upper = score
                yield depth, gamma, score, self.tt_move.get(pos.hash())
                gamma = (lower + upper + 1) // 2


def board_features(board):
    wf = sum(pst[p][i] for i, p in enumerate(board) if p.isalpha())
    bf = sum(pst[p.swapcase()][119 - i] for i, p in enumerate(board) if p.isalpha())
    return wf, bf


def parse_square(text):
    file = ord(text[0]) - ord('a')
    rank = int(text[1]) - 1
    return A1 + file - 10 * rank


def render_square(index):
    rank, file = divmod(index - A1, 10)
    return chr(file + ord('a')) + str(-rank + 1)


def parse_move(text, white_turn):
    frm = parse_square(text[:2])
    to = parse_square(text[2:4])
    promo = text[4:].upper() if len(text) > 4 else ''
    if not white_turn:
        frm, to = 119 - frm, 119 - to
    return Move(frm, to, promo)


def parse_fen(fen, turn, castle, ep, halfmove, fullmove):
    board = re.sub(r'\d', lambda m: '.' * int(m.group(0)), fen)
    board = list(21 * ' ' + '  '.join(board.split('/')) + 21 * ' ')
    board[9::10] = ['\n'] * 12
    board = ''.join(board)
    wc = ('Q' in castle, 'K' in castle)
    bc = ('k' in castle, 'q' in castle)
    ep_sq = parse_square(ep) if ep != '-' else 0
    wf, bf = board_features(board)
    pos = Position(board, 0, wf, bf, wc, bc, ep_sq, 0)
    pos = pos._replace(score=pos.compute_value())
    return pos if turn == 'w' else pos.rotate()


def board_color(pos):
    return 1 if pos.board.startswith('\n') else 0


# Unicode chess pieces
UNICODE_PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    '.': ''
}

# GUI Colors
COLOR_BG = '#2c2c2c'
COLOR_LIGHT = '#e8d5b7'
COLOR_DARK = '#b48860'
COLOR_HIGHLIGHT = '#aad751'
COLOR_LEGAL = '#829769'
COLOR_SELECTED = '#f5f57a'
COLOR_LAST_MOVE = '#cdd26a'
COLOR_TEXT = '#ffffff'
COLOR_ACCENT = '#4a90d9'
COLOR_PANEL = '#3a3a3a'

SQ_SIZE = 72
BOARD_SIZE = SQ_SIZE * 8
PANEL_WIDTH = 260


def board_to_display(index):
    """Convert 120-char board index to (row, col) 0-7 from white's perspective."""
    row = (index // 10) - 2
    col = (index % 10) - 1
    return row, col


def display_to_board(row, col):
    """Convert (row, col) 0-7 from white's perspective to 120-char board index."""
    return (2 + row) * 10 + 1 + col


def get_white_piece(pos, row, col):
    """Get piece at display (row, col) from white's perspective."""
    if board_color(pos) == 0:
        return pos.board[display_to_board(row, col)]
    else:
        idx = 119 - display_to_board(row, col)
        return pos.board[idx].swapcase()


def recommend_moves(pos, top_n=5):
    """Return top N recommended moves with static evaluation scores."""
    moves = list(pos.gen_moves())
    if not moves:
        return []
    scored = []
    for m in moves:
        try:
            val = -pos.move(m).score
        except Exception:
            val = -MATE_UPPER
        scored.append((m, val))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]


def game_result(pos):
    """Return game result string, or None if game is ongoing."""
    # Sunfish is a king-capture engine: if a king is missing, the game is over.
    # Check from the current side-to-move's perspective.
    if 'K' not in pos.board:
        return 'White wins!' if board_color(pos) == 1 else 'Black wins!'
    if 'k' not in pos.board:
        return 'White wins!' if board_color(pos) == 0 else 'Black wins!'

    moves = list(pos.gen_moves())
    if not moves:
        flipped = pos.rotate(nullmove=True)
        in_check = any(flipped.board[m.to] == 'k' for m in flipped.gen_moves())
        if in_check:
            return 'White wins!' if board_color(pos) == 1 else 'Black wins!'
        return 'Stalemate!'
    return None


class EngineThread(threading.Thread):
    """Runs engine search in a background thread."""

    def __init__(self, history, think_time=1.0):
        super().__init__(daemon=True)
        self.history = history
        self.think_time = think_time
        self.best_move = None
        self.best_score = 0
        self.depth = 0
        self.nodes = 0
        self.running = True
        self._progress = None

    def set_progress_callback(self, cb):
        self._progress = cb

    def run(self):
        searcher = Searcher()
        start = time.time()
        try:
            for d, gamma, score, move in searcher.search(self.history):
                if not self.running:
                    return
                if score >= gamma and move is not None:
                    self.best_move = move
                    self.best_score = score
                    self.depth = d
                    self.nodes = searcher.nodes
                    if self._progress:
                        self._progress(d, score, move, searcher.nodes)
                if self.best_move and time.time() - start > self.think_time:
                    break
        except Exception:
            pass

    def stop(self):
        self.running = False


class PromotionDialog(tk.Toplevel):
    """Dialog for choosing a promotion piece."""

    def __init__(self, parent, is_white):
        super().__init__(parent)
        self.result = None
        self.title('Promotion')
        self.configure(bg=COLOR_BG)
        self.resizable(False, False)

        pieces = 'QRBN' if is_white else 'qrbn'
        symbols = [UNICODE_PIECES[p] for p in pieces]

        tk.Label(self, text='Choose promotion:', font=('Segoe UI', 12),
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(pady=10)

        frame = tk.Frame(self, bg=COLOR_BG)
        frame.pack(pady=5)

        for i, (p, s) in enumerate(zip(pieces, symbols)):
            btn = tk.Button(frame, text=s, font=('Segoe UI', 28),
                            width=3, height=1, bg=COLOR_PANEL, fg=COLOR_TEXT,
                            activebackground=COLOR_ACCENT,
                            command=lambda piece=p: self._choose(piece))
            btn.pack(side=tk.LEFT, padx=5)

        self.transient(parent)
        self.grab_set()
        self.geometry('+%d+%d' % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 200))
        self.wait_window()

    def _choose(self, piece):
        self.result = piece
        self.destroy()


class ChessGUI:
    """Main Chess GUI application."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Sunfish NNUE — Chess')
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        # Game state
        pos = Position(initial_board, 0, *board_features(initial_board),
                       (True, True), (True, True), 0, 0)
        pos = pos._replace(score=pos.compute_value())
        self.history = [pos]
        self.selected_sq = None      # (row, col) of selected piece
        self.legal_dests = set()     # set of (row, col) legal destinations
        self.last_move = None        # (from_idx, to_idx) in white-perspective
        self.engine_thinking = False
        self.game_over = False
        self.engine_thread = None
        self.move_history_text = []

        self._build_ui()
        self._update_display()
        self._update_recommendations()
        self.root.mainloop()

    def _build_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=COLOR_BG)
        main_frame.pack(padx=15, pady=15)

        # Board frame
        board_frame = tk.Frame(main_frame, bg=COLOR_BG, highlightthickness=2,
                               highlightbackground=COLOR_ACCENT)
        board_frame.pack(side=tk.LEFT, padx=(0, 15))

        self.canvas = tk.Canvas(board_frame, width=BOARD_SIZE, height=BOARD_SIZE,
                                bg=COLOR_BG, highlightthickness=0)
        self.canvas.pack()

        # Rank/file labels
        label_frame = tk.Frame(board_frame, bg=COLOR_BG)
        label_frame.pack(fill=tk.X)
        files = 'abcdefgh'
        for f in range(8):
            tk.Label(label_frame, text=files[f], font=('Segoe UI', 9),
                     bg=COLOR_BG, fg=COLOR_TEXT,
                     width=9).grid(row=0, column=f)

        # Right panel
        panel = tk.Frame(main_frame, bg=COLOR_PANEL, width=PANEL_WIDTH,
                         highlightthickness=1, highlightbackground='#555')
        panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        panel.pack_propagate(False)

        # Status
        self.status_label = tk.Label(panel, text='Your turn', font=('Segoe UI', 16, 'bold'),
                                     bg=COLOR_PANEL, fg=COLOR_ACCENT)
        self.status_label.pack(pady=(15, 5))

        # Score
        self.score_label = tk.Label(panel, text='Score: —', font=('Segoe UI', 22, 'bold'),
                                    bg=COLOR_PANEL, fg=COLOR_TEXT)
        self.score_label.pack(pady=(0, 15))

        # Separator
        ttk.Separator(panel, orient='horizontal').pack(fill=tk.X, padx=20)

        # Recommendations
        tk.Label(panel, text='Recommendations', font=('Segoe UI', 11, 'bold'),
                 bg=COLOR_PANEL, fg='#888').pack(pady=(12, 5))
        self.rec_frame = tk.Frame(panel, bg=COLOR_PANEL)
        self.rec_frame.pack(fill=tk.X, padx=15)
        self.rec_labels = []
        for i in range(5):
            lbl = tk.Label(self.rec_frame, text='', font=('Segoe UI', 11),
                           bg=COLOR_PANEL, fg=COLOR_TEXT, anchor='w')
            lbl.pack(fill=tk.X, pady=1)
            self.rec_labels.append(lbl)

        # Separator
        ttk.Separator(panel, orient='horizontal').pack(fill=tk.X, padx=20, pady=(15, 0))

        # Move history
        tk.Label(panel, text='Move History', font=('Segoe UI', 11, 'bold'),
                 bg=COLOR_PANEL, fg='#888').pack(pady=(12, 5))
        self.move_list = tk.Text(panel, font=('Consolas', 10), bg='#2a2a2a',
                                 fg=COLOR_TEXT, height=14, width=28, state=tk.DISABLED,
                                 relief=tk.FLAT, borderwidth=4, padx=8, pady=5)
        self.move_list.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 5))

        # Buttons
        btn_frame = tk.Frame(panel, bg=COLOR_PANEL)
        btn_frame.pack(fill=tk.X, padx=15, pady=(5, 15))
        tk.Button(btn_frame, text='New Game', font=('Segoe UI', 10),
                  bg=COLOR_ACCENT, fg='white', relief=tk.FLAT,
                  activebackground='#5ba0e9', padx=15, pady=4,
                  command=self._new_game).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(btn_frame, text='Quit', font=('Segoe UI', 10),
                  bg='#555', fg='white', relief=tk.FLAT,
                  activebackground='#777', padx=15, pady=4,
                  command=self.root.quit).pack(side=tk.LEFT)

        # Canvas click binding
        self.canvas.bind('<Button-1>', self._on_board_click)

    # ---- Display ----

    def _update_display(self):
        """Redraw the entire board."""
        self.canvas.delete('all')
        pos = self.history[-1]

        # Draw squares
        for r in range(8):
            for c in range(8):
                x1, y1 = c * SQ_SIZE, r * SQ_SIZE
                x2, y2 = x1 + SQ_SIZE, y1 + SQ_SIZE

                # Determine square color
                is_light = (r + c) % 2 == 1
                if self.selected_sq == (r, c):
                    color = COLOR_SELECTED
                elif self.last_move and self._is_last_move_sq(r, c):
                    color = COLOR_LAST_MOVE
                elif (r, c) in self.legal_dests:
                    color = COLOR_LEGAL
                elif is_light:
                    color = COLOR_LIGHT
                else:
                    color = COLOR_DARK

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color,
                                             outline=color, width=0)

        # Draw grid lines
        for i in range(9):
            self.canvas.create_line(i * SQ_SIZE, 0, i * SQ_SIZE, BOARD_SIZE,
                                    fill='#555', width=1)
            self.canvas.create_line(0, i * SQ_SIZE, BOARD_SIZE, i * SQ_SIZE,
                                    fill='#555', width=1)

        # Draw pieces
        for r in range(8):
            for c in range(8):
                piece = get_white_piece(pos, r, c)
                if piece != '.':
                    symbol = UNICODE_PIECES.get(piece, '')
                    x, y = c * SQ_SIZE + SQ_SIZE // 2, r * SQ_SIZE + SQ_SIZE // 2
                    self.canvas.create_text(x, y, text=symbol,
                                            font=('Segoe UI Symbol', SQ_SIZE - 18),
                                            fill='#1a1a1a' if piece.isupper() else '#222')

        # Rank labels on left
        for r in range(8):
            self.canvas.create_text(6, r * SQ_SIZE + 12, text=str(8 - r),
                                    font=('Segoe UI', 9), fill=COLOR_TEXT, anchor='nw')

    def _is_last_move_sq(self, r, c):
        """Check if (r, c) matches the last move's from or to square."""
        if not self.last_move:
            return False
        idx = display_to_board(r, c)
        return idx == self.last_move[0] or idx == self.last_move[1]

    def _update_recommendations(self):
        """Update the recommendations panel."""
        if self.engine_thinking or self.game_over:
            for lbl in self.rec_labels:
                lbl.config(text='')
            return
        pos = self.history[-1]
        recs = recommend_moves(pos, top_n=5)
        for i, lbl in enumerate(self.rec_labels):
            if i < len(recs):
                m, val = recs[i]
                move_str = render_square(m.frm) + render_square(m.to) + m.promo.lower()
                prefix = '★ ' if i == 0 else '   '
                lbl.config(text=f'{prefix}{move_str}  ({val:+d})',
                           fg='#aad751' if i == 0 else COLOR_TEXT)
            else:
                lbl.config(text='')

    def _set_status(self, text, color=None):
        self.status_label.config(text=text, fg=color or COLOR_ACCENT)

    def _add_move_to_history(self, move_num, white_move, black_move=None):
        """Add a move pair to the move history text widget."""
        self.move_list.config(state=tk.NORMAL)
        if white_move:
            line = f'{move_num:3d}. {white_move:<8s}'
            if black_move:
                line += f'{black_move:<8s}'
            self.move_list.insert(tk.END, line + '\n')
        self.move_list.see(tk.END)
        self.move_list.config(state=tk.DISABLED)

    # ---- Board Interaction ----

    def _on_board_click(self, event):
        if self.engine_thinking or self.game_over:
            return
        col = event.x // SQ_SIZE
        row = event.y // SQ_SIZE
        if not (0 <= row < 8 and 0 <= col < 8):
            return

        pos = self.history[-1]
        piece = get_white_piece(pos, row, col)

        if self.selected_sq is None:
            # Select a piece
            if piece.isupper():  # Human's pieces are uppercase
                self.selected_sq = (row, col)
                self.legal_dests = self._get_legal_dests(pos, row, col)
                self._update_display()
        elif self.selected_sq == (row, col):
            # Deselect
            self.selected_sq = None
            self.legal_dests.clear()
            self._update_display()
        elif (row, col) in self.legal_dests:
            # Make the move
            self._make_human_move(row, col)
        elif piece.isupper():
            # Select a different piece
            self.selected_sq = (row, col)
            self.legal_dests = self._get_legal_dests(pos, row, col)
            self._update_display()
        else:
            # Clicked on empty or enemy square (not a legal destination)
            self.selected_sq = None
            self.legal_dests.clear()
            self._update_display()

    def _get_legal_dests(self, pos, row, col):
        """Get all legal destination squares for the piece at (row, col)."""
        idx = display_to_board(row, col)
        dests = set()
        for m in pos.gen_moves():
            if m.frm == idx:
                dr, dc = board_to_display(m.to)
                if 0 <= dr < 8 and 0 <= dc < 8:
                    dests.add((dr, dc))
        return dests

    def _make_human_move(self, row, col):
        """Execute a human move from selected square to (row, col)."""
        pos = self.history[-1]
        from_idx = display_to_board(*self.selected_sq)
        to_idx = display_to_board(row, col)
        piece = pos.board[from_idx]

        # Check for promotion
        promo = ''
        if piece == 'P' and 21 <= to_idx <= 28:
            dlg = PromotionDialog(self.root, is_white=True)
            promo = dlg.result or 'Q'

        # Find the matching move
        target_move = None
        for m in pos.gen_moves():
            if m.frm == from_idx and m.to == to_idx:
                if piece == 'P' and 21 <= to_idx <= 28:
                    if m.promo == promo:
                        target_move = m
                        break
                else:
                    target_move = m
                    break

        if target_move is None:
            self.selected_sq = None
            self.legal_dests.clear()
            self._update_display()
            return

        # Apply the move
        self.selected_sq = None
        self.legal_dests.clear()
        self.last_move = (from_idx, to_idx)

        move_str = render_square(from_idx) + render_square(to_idx) + target_move.promo.lower()
        move_num = (len(self.history) + 1) // 2
        self._add_move_to_history(move_num, move_str, None)

        new_pos = pos.move(target_move)
        self.history.append(new_pos)
        self._update_display()

        # Check game over
        result = game_result(self.history[-1])
        if result:
            self.game_over = True
            self._set_status(result, '#f5a623')
            self.score_label.config(text=f'Result: {result}')
            return

        # Start engine thinking
        self._engine_think()

    def _engine_think(self):
        """Start engine computation in background thread."""
        self.engine_thinking = True
        self._set_status('Engine thinking...', '#f5a623')
        self.score_label.config(text='Thinking...')
        for lbl in self.rec_labels:
            lbl.config(text='')

        self.engine_thread = EngineThread(self.history, think_time=0.8)
        thread_obj = self.engine_thread
        last_depth = [0]

        def progress(depth, score, move, nodes):
            if depth != last_depth[0]:
                last_depth[0] = depth
                efrm, eto = move.frm, move.to
                dfrm, dto = 119 - efrm, 119 - eto
                pv = render_square(dfrm) + render_square(dto) + move.promo.lower()
                self.score_label.config(text=f'd{depth}  {pv}  {score:+d}')

        self.engine_thread.set_progress_callback(progress)

        def on_done():
            if self.engine_thread is not thread_obj:
                return  # Stale callback from a previous game
            self.engine_thinking = False
            move = self.engine_thread.best_move
            score = self.engine_thread.best_score

            if move is None:
                self._set_status('Engine has no moves!', '#f5a623')
                return

            # Convert engine move to display coordinates
            efrm, eto = move.frm, move.to
            dfrm, dto = 119 - efrm, 119 - eto

            # Apply engine move
            move_str = render_square(dfrm) + render_square(dto) + move.promo.lower()
            move_num = len(self.history) // 2
            self._add_move_to_history(move_num, None, move_str)

            new_pos = self.history[-1].move(move)
            self.history.append(new_pos)
            self.last_move = (dfrm, dto)
            self.score_label.config(text=f'Score: {score:+d}')
            self._update_display()

            # Check game over
            result = game_result(self.history[-1])
            if result:
                self.game_over = True
                self._set_status(result, '#f5a623')
                return

            self._set_status('Your turn')
            self._update_recommendations()

        # Poll for completion
        def check_thread():
            if self.engine_thread.is_alive():
                self.root.after(50, check_thread)
            else:
                on_done()

        self.engine_thread.start()
        self.root.after(50, check_thread)

    def _new_game(self):
        """Reset to a new game."""
        if self.engine_thread and self.engine_thread.is_alive():
            self.engine_thread.stop()
        pos = Position(initial_board, 0, *board_features(initial_board),
                       (True, True), (True, True), 0, 0)
        pos = pos._replace(score=pos.compute_value())
        self.history = [pos]
        self.selected_sq = None
        self.legal_dests.clear()
        self.last_move = None
        self.engine_thinking = False
        self.game_over = False
        self.move_history_text.clear()
        self.move_list.config(state=tk.NORMAL)
        self.move_list.delete('1.0', tk.END)
        self.move_list.config(state=tk.DISABLED)
        self._set_status('Your turn')
        self.score_label.config(text='Score: —')
        self._update_display()
        self._update_recommendations()


def main():
    ChessGUI()


if __name__ == '__main__':
    main()
