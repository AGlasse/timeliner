#!/usr/bin/python
import numpy as np

class Conduit:
    """ Conduit class manages connections between tasks.
    """
    n_tracks = 13                           # Number of connections per row
    n_shafts = 12                           # Number of connections per column
    wire_pitch = [1.5, 1.5]                 # Pitch of wires (row, col)
    n_rows, n_cols = -1, -1
    cell_occupation, cell_rectangles = None, None
    xy_origin = None                        # (rows increase with decreasing y)
    row_pitch = 2.8                         # Row pitch for all Tasks
    col_pitch = (1.3, 2.0, 2.0)             # CAR, CAP, KDP column widths (fraction of box width)

    def __init__(self, xy_origin, n_rows, n_cols_list):
        from loom import Loom

        Conduit.xy_origin = xy_origin
        Conduit.n_cols_list = n_cols_list
        n_car_cols, n_cap_cols, n_kdp_cols = n_cols_list
        n_cols = n_car_cols + n_cap_cols + n_kdp_cols
        Conduit.n_rows = n_rows
        Conduit.n_cols = n_cols

        Conduit.cell_occupation = np.full((n_rows, n_cols), False)              # Boolean table True = Cell in plot is occupied by a CAP
        n_tracks = Conduit.n_tracks
        n_channels = 4
        n_rowcols = n_cols if n_cols > n_rows else n_rows
        Conduit.wire_usage = np.full((n_channels, n_rowcols, n_tracks), Loom.free_uid)
        Conduit.xcols = np.zeros(n_cols)        # x coordinates of cell left edge
        return

    @staticmethod
    def plot_grid(ax):
        for r in range(0, Conduit.n_rows):
            xywh = Conduit.cell_rectangles[r, 0]
            x1, y1, w1, h1 = xywh[0], xywh[1], xywh[2], xywh[3]
            xywh = Conduit.cell_rectangles[r, Conduit.n_cols-1]
            x2, y2, w2, h2 = xywh[0], xywh[1], xywh[2], xywh[3]
            xs = [x1, x2]
            ys = [y1, y2]
            ax.plot(xs, ys, linestyle='dotted', linewidth=1.0, color='green')
        for c in range(0, Conduit.n_cols):
            xywh = Conduit.cell_rectangles[0, c]
            x1, y1, w1, h1 = xywh[0], xywh[1], xywh[2], xywh[3]
            xywh = Conduit.cell_rectangles[Conduit.n_rows-1, c]
            x2, y2, w2, h2 = xywh[0], xywh[1], xywh[2], xywh[3]
            xs = [x1, x2]
            ys = [y1, y2]
            ax.plot(xs, ys, linestyle='dotted', linewidth=1.0, color='green')
        return

    @staticmethod
    def build_cells():
        from task import Task

        n_rows = Conduit.n_rows
        n_cols = Conduit.n_cols
        cell_rectangles = np.zeros((n_rows, n_cols, 4))

        h = Conduit.row_pitch * Task.box_h
        start_col = 0
        x_origin = Conduit.xy_origin[0]
        x_block_origin = x_origin
        for b in range(0, 3):
            x = x_block_origin
            n_cols = Conduit.n_cols_list[b]
            for c in range(start_col, start_col+n_cols):

                w = Conduit.col_pitch[b] * Task.box_w
                y = Conduit.xy_origin[1]
                for r in range(0, Conduit.n_rows):
                    cell_rectangles[r, c, :] = [x, y, w, h]
                    y = y - h
                x = x + w
            x_block_origin = x
            start_col += n_cols

        Conduit.cell_rectangles = cell_rectangles
        return

    @staticmethod
    def get_bounds():
        x1, y1, w1, h1 = Conduit.get_cell_rectangle(0, 0)
        xmin = x1 - h1
        ymax = y1 + 1 * h1
        x2, y2, w2, h2 = Conduit.get_cell_rectangle(Conduit.n_rows-1, Conduit.n_cols-1)
        xmax = x2 + 0 * w2
        ymin = y2 - h2
        return xmin, xmax, ymin, ymax

    @staticmethod
    def get_cell_rectangle(row, col):
        rectangle = Conduit.cell_rectangles[row, col]
        return rectangle

    @staticmethod
    def get_wire(task, loom, **kwargs):
        """ Find the x or y coordinate of a track which is either in use by this
        loom or unused. """
        from task import Task

        channel = kwargs.get('channel', 'hl')
        channel_dict = {'hl': 0, 'hr': 1, 'v1': 2, 'v2': 3}
        channel_index = channel_dict[channel]
        xy_frac = [0.40, 0.40, 0.05, 0.90]

        row, col = task.row, task.col
        rowcol = row if channel_index < 2 else col

        xc, yc, wc, hc = Conduit.get_cell_rectangle(task.row, task.col)

        j_free = -1         # Index of first free track
        j_ass = -1          # Index of track pre-assigned to this loom
        for j in range(0, Conduit.n_tracks):
            wire = Conduit.wire_usage[channel_index, rowcol, j]
            is_first_free = wire == Task.free_uid and j_free == -1
            j_free = j if is_first_free else j_free
            is_pre_ass = wire == loom.uid
            j_ass = j if is_pre_ass else j_ass
        j = j_ass if j_ass != -1 else j_free
        Conduit.wire_usage[channel_index, rowcol, j] = loom.uid
        is_vertical = channel_index > 1
        uc = xc if is_vertical else yc              # Cell corner
        usize = wc if is_vertical else hc           # Cell size
        upitch = Conduit.wire_pitch[0] if is_vertical else Conduit.wire_pitch[1]
        u = uc + xy_frac[channel_index] * usize + j * upitch
        return u

    @staticmethod
    def get_free_col(tgt_row, start_col):#

        col = start_col
        occ = Conduit.cell_occupation
        nr, nc = occ.shape
        while occ[tgt_row, col] and col < nc - 1:
            col += 1
        Conduit.cell_occupation[tgt_row, col] = True
        return col
