#!/usr/bin/python
from task import Task
from loom import Loom


class Kdp(Task):

    cell_rectangle = None
    inset_w, inset_h = 25.0, -5.0
    type = 'KDP'
    type_code = '#'


    def __init__(self, idt_id, label, colour, sources, **kwargs):
        Task.__init__(self, idt_id, label, colour)
        self.sources = sources
        self.loom = Loom(self, colour1='powderblue', colour2=colour, ls='dotted')
        return

    def plot_box(self, ax, **kwargs):
        self._set_box_layout(kmitre=0.2, style_format="round,pad={:3.1f}",
                             fc='powderblue', lc=self.colour)
        self._plot_box(ax, **kwargs)
        return
