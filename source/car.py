#!/usr/bin/python
from task import Task
from loom import Loom

class Car(Task):

    smes = None       # Subject matter expert persons for this CAR
    cell_rectangle = None
    inset_w, inset_h = 0.0, 45.0
    type = 'CAR'
    type_code = 'o'

    def __init__(self, cawg_row, idt_id, label, title, ng_id, pid_id, apt_obs, **kwargs):
        Task.__init__(self, idt_id, label, 'black')

        self.cawg_row = cawg_row
        self.idt_id = idt_id #if idt_id is not '' else 'NG-' + ng_id)
        self.t_start = kwargs.get("tstart", -1.0)
        self.t_dur_cawg = kwargs.get("tdur_hr", 1.0)
        self.t_dur = self.t_dur_cawg / 24.0
        self.t_sci_apt, self.t_dur_apt, t_dur_cawg = -1.0, -1.0, -1.0   # Calculated from apt_decoder data
        self.col_offset = kwargs.get("col_offset", 0)
        self.next_inplug = 0.
        self.next_outplug = 0.
        self.ng_id = ng_id
        self.pid_id = pid_id
        self.apt_obs = apt_obs
        self.pid_tdur = 0.0
        self.title = title
        self.caplinks = []
        self.x = 0.0
        self.y = 0.0
        self.loom = Loom(self, colour='black', ls='-')
        return

    def plot_box(self, ax, **kwargs):
        self._set_box_layout()
        self._plot_box(ax, **kwargs)
        return

    def is_milestone(self):
        is_milestone = self.idt_id[0:2] == 'M-'
        return is_milestone

    def print(self):
        """ Print the key CAR parameters, with the dependent and provider CAPs
        marked.
        """
        fmt = "  {:<10s}{:<12s}{:<8s}{:60s}{:10.2f}{:10.2f}{:16.2f}"
        line = fmt.format(self.ng_id, self.idt_id, self.pid_id, self.title[0:60],
                          self.t_start, self.t_dur, self.pid_tdur)
        tab = 9
        for caplink in self.caplinks:
            fmt = "{:>" + "{:d}".format(tab) + "s}"
            sup = fmt.format(caplink[1])
            line = line + sup
            tab = 5
        print(line)

    def print_header(self):
        """ Print a CAR title row
        """
        fmt = "  {:<10s}{:<12s}{:<8s}{:60s}{:>10s}{:>10s}{:>16s}{:>5s}"
        line = fmt.format('CAR ID', 'IDT ID', 'PID', 'Title', 'L + dy', 'Dur./hr', 'PID_Dur./hr', 'CAP')
        tab = 3
        for caplink in self.caplinks:
            fmt = "{:>" + "{:d}".format(tab) + "s}"
            sup = fmt.format("-" + caplink[0].idt_id)
            line = line + sup
            tab = 5
        print(line)

    def plot_car_link(self, ax):
        """ Plot link arrow from single source CAR to this one.
        """
        from conduit import Conduit

        mitre, style, lc, fc = self.plot_settings
        box_w, box_h = Task.box_w, Task.box_h
        if len(self.sources) == 0:       # First CAR has no sources
            return
        source = self.sources[0]
        xf = source.box_x + box_w
        yf = source.box_y + box_h / 2.0
        xt = self.box_x
        yt = self.box_y + box_h / 2.0
        ls = '-'
        lw = 2.0
        if xt > xf:
            ax.plot([xf, xt], [yf, yt], linestyle=ls, linewidth=lw, color=lc)
        else:                   # Draw arrow in segments
            xa = 0.3 * box_w    # Distance of arrow turn from box
            x2 = xf + xa
            y2 = yt + 0.4 * (yf - yt)
            x3 = xt - xa
            xs = [xf, x2, x2, x3, x3, xt]
            ys = [yf, yf, y2, y2, yt, yt]
            ax.plot(xs, ys, clip_on=True, linestyle=ls, linewidth=lw, color=lc)
        self.loom.plot_arrow(ax, xt, yt, 'l')
        return
