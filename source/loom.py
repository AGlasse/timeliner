#!/usr/bin/python
from conduit import Conduit

class Loom:
    uid_counter = 0
    free_uid = 'UID-tbd'
    n_tracks = 6        # Number of connections per row
    n_shafts = 8        # Number of connections per column
    track_pitch = 1.0
    mast_pitch = 2.5


    def __init__(self, task, **kwargs):
        Loom.uid_counter += 1                               # Increment global loom counter
        self.uid = "LOO{:04d}".format(Loom.uid_counter)     # ..and assign to this instance
        self.task = task                                    # Task this loom connects to
        self.colour1 = kwargs.get('colour1', 'black')
        self.colour2 = kwargs.get('colour2', 'red')
        self.ls = kwargs.get('ls', '-')
        self.lw = kwargs.get('lw', 1.5)
        self.spars, self.stubs, self.arrows, self.plugs = [], [], [], []
        return

    def construct(self):
        """ Construct the loom, connecting this task to its sources
        """
        from car import Car
        from cap import Cap

        this_task = self.task
        face, channel = 'l', 'v1'
        # All looms have a vertical 'mast' to the left of the target CAP or KDP
        x_socket, y_socket = this_task.get_socket(self.uid, face=face)  # CAP or KDP
        x_mast = Conduit.get_wire(this_task, self, channel=channel)
        mast = [[x_mast, x_mast], [y_socket, y_socket]]
        # Initialise array of spars running from input tasks to the mast
        spars = []
        for row in range(0, Conduit.n_rows):
            spars.append([[x_mast, x_mast], [y_socket, y_socket]])
        # Initialise plot arrays
        arrows = []
        arrows.append([x_socket, y_socket, face])              # Arrow at output socket
        stubs = []
        stubs.append([[x_socket, x_mast], [y_socket, y_socket]])    # Stub from socket to mast
        plugs = []
        for source in this_task.sources:
            row, col = source.row, source.col
            type = source.type
            y_wire = Conduit.get_wire(source, self, channel='hl')
            spar = spars[row]
            spar[1][0], spar[1][1] = y_wire, y_wire
            if type == 'CAR':
                x_socket, y_socket = source.get_socket(self.uid, face='b')
                stubs.append([[x_socket, x_socket], [y_socket, y_wire]])
                plugs.append([x_socket, y_socket, 'b'])  # Plug at input
                x_spar = x_socket
            else:
                x_socket, y_socket = source.get_socket(self.uid, face='r')
                x_wire = Conduit.get_wire(source, self, channel='v2')
                stubs.append([[x_socket, x_wire, x_wire], [y_socket, y_socket, y_wire]])
                plugs.append([x_socket, y_socket, 'r'])  # Plug at input
                x_spar = x_wire
            y_mast = y_wire
            y_mast_min, y_mast_max = mast[1][0], mast[1][1]
            y_mast_min = y_mast_min if y_mast_min < y_mast else y_mast
            y_mast_max = y_mast_max if y_mast_max > y_mast else y_mast
            mast[1][0], mast[1][1] = y_mast_min, y_mast_max

            x_spar_min, x_spar_max = spar[0][0], spar[0][1]
            x_spar_min = x_spar_min if x_spar_min < x_spar else x_spar
            x_spar_max = x_spar_max if x_spar_max > x_spar else x_spar
            spar[0][0], spar[0][1] = x_spar_min, x_spar_max
        self.stubs = stubs
        self.spars = spars
        self.plugs = plugs
        self.arrows = arrows
        self.mast = mast
        return

    def plot(self, ax):
        from task import Task

        for stub in self.stubs:
            x, y = stub[0], stub[1]
            Loom._plot_line(ax, x, y, self.colour1, self.colour2)
        for spar in self.spars:
            x, y = spar[0], spar[1]
            Loom._plot_line(ax, x, y, self.colour1, self.colour2)
        x, y = self.mast[0], self.mast[1]
        Loom._plot_line(ax, x, y, self.colour1, self.colour2)
        wid = Task.socket_pitch / 2.0
        for plug in self.plugs:
            Loom._plot_socket(ax, plug[0], plug[1], plug[2],
                              shape='plug', wid=wid, colour=self.colour2)
        for arrow in self.arrows:
            Loom._plot_socket(ax, arrow[0], arrow[1], arrow[2],
                              shape='arrow', wid=wid, colour=self.colour2)
        return

    @staticmethod
    def _plot_line(ax, x, y, colour1, colour2):
        ax.plot(x, y, ls='-', color=colour1)
        ax.plot(x, y, ls='--', color=colour2)
        return

    @staticmethod
    def plot_arrow(ax, x, y, lrbt, **kwargs):
        Loom._plot_socket(ax, x, y, lrbt, **kwargs)

    @staticmethod
    def _plot_socket(ax, x, y, lrbt, **kwargs):
        """ Plot a socket symbol (arrow or plug) centred on x, y.  The arrow
        points towards the edge specified in lrud, and the plug is drawn
        inside the box, and and lying with its long edge alibg lrud.
        """
        import numpy as np

        colour = kwargs.get('colour', 'black')
        shape = kwargs.get('shape', 'arrow')
        wid = kwargs.get('wid', 3.0)
        len = 2.0 * wid
        lw = 0.5    # Small offset to make shape cross box boundary
        n, u, v = 3, [+len, -lw, +len], [-wid, -lw, +wid]
        if shape != 'arrow':
            n, u, v = 4, [+wid, -lw, -lw, +wid], [-wid, -wid, +wid, +wid]
        xs, ys = np.full(n, x), np.full(n, y)
        if lrbt == 'l':
            xs, ys = np.subtract(xs, u), np.add(ys, v)
        if lrbt == 'r':
            xs, ys = np.add(xs, u), np.add(ys, v)
        if lrbt == 't':
            xs, ys = np.subtract(xs, v), np.subtract(ys, u)
        if lrbt == 'b':
            xs, ys = np.add(xs, v), np.subtract(ys, u)
        ax.fill(xs, ys, color=colour)
        return
