from source.kdp import Kdp
from car_utils import CarUtils
from task import Task


class KdpUtils:
    """
    """
    def __init__(self):
        """ Create kdps from parameters in file 'kdps.csv', with lists of input
        and output CARs linked from the passed list 'cars'.
        """
        KdpUtils.kdps = self._read_kdps()
        return

    @staticmethod
    def get_kdp(idt_id, **kwargs):
        task_list = kwargs.get('kdp_list', KdpUtils.kdps)
        return Task._get_task(idt_id, task_list)

    def _read_kdps(self):
        from cap_utils import CapUtils

        path = '../inputs/kdps.csv'

        with open(path, 'r') as file:
            text_block = file.read()
        line_list = text_block.split('\n')
        n_lines = len(line_list)
        kdps = []
        for row in range(2, n_lines, 2):
            kdp_tokens = self._parse_line(line_list[row])
            if len(kdp_tokens) > 3:
                idt_id, label, ng_id, title, colour = (token for token in kdp_tokens[0:5])
                source_tokens = self._parse_line(line_list[row + 1])
                sources = []
                for token in source_tokens[1:]:
                    cap, err_msg = CapUtils.get_cap(token)
                    if cap is not None:
                        sources.append(cap)
                kdp = Kdp(idt_id, label, colour, sources)
                kdps.append(kdp)
        return kdps

    @staticmethod
    def connect_kdps(kdps):
        """ Connect CAPs to their sources by generating a plottable 'loom'
        object.
        """
        from conduit import Conduit
        from loom import Loom

        for kdp in kdps:
            kdp.loom.construct()
        return

    @staticmethod
    def schedule_kdps():
        for kdp in KdpUtils.kdps:
            kdp_row = KdpUtils.schedule_kdp(kdp)
        return

    @staticmethod
    def schedule_kdp(kdp):
        # Find last input to this cap
        last_task = None
        t_start_min = -999.0         # earliest start time (L + day)
        for task in kdp.sources:
            t_end = task.get_t_end()
            if t_end > t_start_min:
                t_start_min = t_end
                last_task = task
            else:
                t_start_min
        kdp.add_source(last_task)
        kdp.t_start = t_start_min
        kdp_row = last_task.row         # Used by method layout_kdps
        return kdp_row

    @staticmethod
    def layout_kdps(kdps):
        from conduit import Conduit

        for kdp in kdps:
            # Find last input to this cap
#            last_task = None
#            t_start_min = -999.0         # earliest start time (L + day)
#            for task in kdp.sources:
#                t_end = task.get_t_end()
#                if t_end > t_start_min:
#                    t_start_min = t_end
#                    last_task = task
#                else:
#                    t_start_min
#            kdp.add_source(last_task)
#            kdp.t_start = t_start_min
#            kdp_row = last_task.row
            kdp_row = KdpUtils.schedule_kdp(kdp)

            start_col = Conduit.n_cols_list[0] + Conduit.n_cols_list[1]
            kdp_col = Conduit.get_free_col(kdp_row, start_col)
            kdp.row, kdp.col = kdp_row, kdp_col
            kdp.set_position()
        return

    def _parse_line(self, line):
        """ Parse a line of comma delimited text into a token list, with
        trailing empty tokens removed.
        """
        in_tokens = line.split(',')
        out_tokens = []
        for token in in_tokens:
            if len(token) > 0:
                out_tokens.append(token)
        return out_tokens
