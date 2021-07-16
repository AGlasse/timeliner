import numpy as np
from loom import Loom

class Task:
    """ Task contains the parameters for a single CAP, CAR or KDP (milestone).
    """
    # Define class globals
    n_inputs, n_outputs = 8, 8              # Number of connector i/o sites
    uid_counter = 0
    free_uid = 'UID-tbd'
    box_w, box_h = 50.0, 25.0               # Box width, height
    inset_w, inset_h = 8.0, 20.0
    socket_pitch = 4.0
    task = 'TBD'

    def __init__(self, idt_id, label, colour):
        self.uid = "TSK{:04d}".format(Task.uid_counter)
        Task.uid_counter += 1
        self.idt_id = idt_id
        self.label = label
        self.colour = colour
        self.t_start, self.t_dur = 0.0, 3.0
        self.row, self.col = -1, -1
        self.box_x, self.box_y = 0.0, 0.0   # Lower left corner x, y
        self.y_box_offset = 0.0             # Box offset (for CAPs and KDPs)
        self.sources = []                   # Tasks which feed into this task
        self.wires = []                     # Connectors from source tasks
        self.setup_sockets()
        self.ysmes = []                      # Plot y coordinates for ShiftPlan.plot_rota
        return

    def __str__(self):
        return "{:s}".format(self.idt_id)

    def assign_sme(self, person):
        self.smes.append(person)
        return

    @staticmethod
    def _get_task(idt_id, task_list):
        for task in task_list:
            if task.idt_id == idt_id:
                return task, None
        err_msg = '{:s} not found !!'.format(idt_id)
        return None, err_msg

    def setup_sockets(self):
        """ Add sockets, 1 on left and right face and n on the bottom socket
        format is 'face', 'loom_uid', dx, dy, where dx, dy are offsets from the
        bottom left of the box.
        """
        w, h = Task.box_w, Task.box_h
        p = Task.socket_pitch
        faces = ['l', 'b', 'tl', 'tr', 'r']
        n_sockets_face = [5, 10, 5, 5, 8]
        x_orgs = [0.0, 0.1*w, 0.1*w, 0.9*w, w]
        y_orgs = [0.5*h, 0.0, h, h, 0.9*h]
        x_pitches = [0.0, p, p, -p, 0.0]
        y_pitches = [p, 0.0, 0.0, 0.0, -p]
        n_faces = len(faces)
        sockets = []
        for i in range(0, n_faces):
            face = faces[i]
            x_org, y_org = x_orgs[i], y_orgs[i]
            x_pitch, y_pitch = x_pitches[i], y_pitches[i]
            n_sockets = n_sockets_face[i]
            for j in range(0, n_sockets):
                x = x_org + j * x_pitch
                y = y_org + j * y_pitch
                sockets.append([face, Task.free_uid, x, y])
        self.sockets = sockets
        return

    def get_socket(self, loom_uid, **kwargs):
        """ Get a free output connector for a connecting loom
        """
        from conduit import Conduit

        face = kwargs.get('face', 'b')      # (b)ottom, (l)eft, (r)ight (t)op
        i_free = -1                         # Index of first free socket
        i_ass = -1                          # Index of socket pre-assigned to this loom
        n_sockets = len(self.sockets)
        for i in range(0, n_sockets):       # Check all sockets on selected face for this loom
            socket = self.sockets[i]
            if socket[0] == face:
                is_first_free = socket[1] == Loom.free_uid and i_free == -1
                i_free = i if is_first_free else i_free
                is_pre_ass = socket[1] == loom_uid
                i_ass = i if is_pre_ass else i_ass
        i = i_ass if i_ass != -1 else i_free
        x, y = 0., 0.
        if i_free != -1:
            socket = self.sockets[i]
            x = self.box_x + socket[2]
            y = self.box_y + socket[3]
            self.sockets[i][1] = loom_uid
        else:
            print('t.get_socket - Socket {:s} not found !!'.format(face))
        return x, y

    def _set_box_layout(self, **kwargs):
        """ Default box layout is a white filled rectangle with square corners
        """
        from conduit import Conduit

        k_mitre = kwargs.get('k_mitre', 0.0)
        style_format = kwargs.get('style_format', "square,pad={:3.1f}")
        lc = kwargs.get('lc', 'black')
        fc = kwargs.get('fc', 'white')
        mitre = k_mitre * Task.box_w
        style = style_format.format(mitre)
        self.plot_settings = mitre, style, lc, fc
        return

    def get_days(self):
        """ Get start and end day of task. """
        start_day = int(self.t_start)
        end_day = int(self.get_t_end())
        return start_day, end_day

    def get_t_end(self):
        t_end = self.t_start + self.t_dur
        return t_end

    def add_source(self, task):
        self.sources.append(task)
        return

    def set_linked_tasks(self, sources, sinks):
        self.sources = sources
        self.sinks = sinks
        return

    def set_position(self):
        from conduit import Conduit

        x, y, w, h = Conduit.get_cell_rectangle(self.row, self.col)
        box_x = x + self.inset_w
        box_y = y + self.inset_h
        self.box_x, self.box_y = box_x, box_y
        return

    def _plot_box(self, ax, **kwargs):
        import matplotlib.transforms as mtransforms
        from matplotlib.patches import FancyBboxPatch
        from conduit import Conduit
        from car import Car
        from cap import Cap

        tl_text = kwargs.get('tl_text', '')
        xbl = kwargs.get('xbl', self.box_x)
        ybl = kwargs.get('xbl', self.box_y)

        mitre, style, lc, fc = self.plot_settings
        xw, yh = Task.box_w, Task.box_h
        xtr, ytr = xbl + xw, ybl + yh

        bb = mtransforms.Bbox([[xbl, ybl], [xtr, ytr]])   # Bounding box
        box = FancyBboxPatch((bb.xmin+mitre, bb.ymin+mitre),
                             abs(bb.width)-2.0*mitre, abs(bb.height)-2.0*mitre,
                             boxstyle=style, lw=2.0, fc=fc, ec=lc)
        # Plot box with labels
        ax.add_patch(box)
        ax.text(xbl + 0.03 * xw, ybl + 0.9 * yh, tl_text, color='blue', va='top', ha='left')
        ax.text(xbl + 0.97 * xw, ybl + 0.9 * yh, self.idt_id, color='black', va='top', ha='right')
        ts_text = "L+{:6.1f}".format(self.t_start)
        ax.text(xbl + 0.95 * xw, ybl + 0.05 * yh, ts_text, color='red', va='bottom', ha='right')
        if self.type == 'CAR':
            ax.text(xbl + 0.03 * xw, ybl + 0.05 * yh, self.pid_id,
                    color='green', va='bottom', ha='left')
        text = (str(self.label)).replace('\\n', '\n')
        ax.text(xbl + 0.50 * xw, ybl + 0.50 * yh, text,
                color='black', va='center', ha='center')
        return
