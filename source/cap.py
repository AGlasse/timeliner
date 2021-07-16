from task import Task
from loom import Loom

class Cap(Task):

    duration = 6.0      # Standard notional analysis time after last CAR.
    cell_rectangle = None
    inset_w, inset_h = 25.0, 0.0
    type = 'CAP'
    type_code = 'x'


    def __init__(self, idt_id, label, colour, sources, lead):
        Task.__init__(self, idt_id, label, colour)
        self.next_inplug = 0.       # Index of next plug for link to CAPs
        self.next_outplug = 0.
        self.colour = colour
        self.lead = lead
        self.sources = sources
        last_task = self.find_last_task(sources)
        self.t_start = last_task.get_t_end()
        self.last_task = last_task
        self.idx = 0
        self.loom = Loom(self, colour1='black', colour2=colour, ls='--')
        return

    def plot_box(self, ax, **kwargs):
        colour = self.colour
        self._set_box_layout(lc=colour)
        self._plot_box(ax, **kwargs)

    def find_last_task(self, sources):              # Find last input to this cap
        last_task = None
        t_start_min = -999.0                        # earliest start time (L + day)
        for task in sources:
            t_end = task.get_t_end()
            if t_end > t_start_min:
                t_start_min = t_end
                last_task = task
            else:
                t_start_min
        return last_task
