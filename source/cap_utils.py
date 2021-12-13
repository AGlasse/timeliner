from source.cap import Cap
from car_utils import CarUtils
from task import Task


class CapUtils:
    """
    """
    def __init__(self):
        """ Create CAPs from parameters in file 'caps.csv', with lists of input
        and output CARs linked from the passed list 'cars'.
        """
        CapUtils.caps = self._read_caps()
        return

    def _read_caps(self):
        path = '../inputs/caps.csv'
        with open(path, 'r') as file:
            text_block = file.read()
        line_list = text_block.split('\n')
        n_lines = len(line_list)
        caps = []
        for row in range(2, n_lines, 2):
            cap_tokens = self._parse_line(line_list[row])
            if len(cap_tokens) > 3:
                idt_id, label, lead, colour = (token.strip() for token in cap_tokens[0:4])
                source_tokens = self._parse_line(line_list[row + 1])
                sources = []
                for token in source_tokens[1:]:     # Add CARs and CAPs to source list
                    search_id = token.strip()
                    car, err_msg = CarUtils.get_car(search_id)
                    if car is None:
                        is_assigned = False
                        for pre_cap in caps:
                            if pre_cap.idt_id == token:
                                sources.append(pre_cap)
                                print('Cap_Utils._read_caps - Appending ' + pre_cap.__str__() + ' to ' + cap.__str__())
                                is_assigned = True
                        if not is_assigned:
                            print(err_msg)
                    else:
                        sources.append(car)

                cap = Cap(idt_id, label, colour, sources, lead)
                print(cap)
                caps.append(cap)
        return caps

    @staticmethod
    def get_cap(idt_id, **kwargs):
        task_list = kwargs.get('cap_list', CapUtils.caps)
        return Task._get_task(idt_id, task_list)

    @staticmethod
    def connect_caps(caps):
        """ Connect CAPs to their sources by generating a plottable 'loom'
        object.
        """
        from conduit import Conduit
        from loom import Loom

        for cap in caps:
            cap.loom.construct()        # New test routine
        return

    @staticmethod
    def layout_caps(caps):
        from car_utils import CarUtils
        from conduit import Conduit

        for cap in caps:
            # Find last input to this cap
            last_task = None
            t_start_min = -999.0         # earliest start time (L + day)
            for task in cap.sources:
                t_end = task.get_t_end()
                if t_end > t_start_min:
                    t_start_min = t_end
                    last_task = task
            cap.t_start = t_start_min
            cap_row = last_task.row
            start_col = Conduit.n_cols_list[0]

#            print('Trying to place {:s} at row {:d}'.format(cap.idt_id, cap_row))
            cap_col = Conduit.get_free_col(cap_row, start_col)
            cap.row, cap.col = cap_row, cap_col
            cap.set_position()
        return

    def _parse_line(self, line):
        """ Parse a line of comma delimited text into a token list, with
        trailing empty tokens removed.
        """
        in_tokens = line.split(',')
        out_tokens = []
        for token in in_tokens:
            if len(token) > 0:
                nibs = token.split('\\n')
                if len(nibs) > 1:
                    token = nibs[0] + '\n' + nibs[1]
                out_tokens.append(token)
        return out_tokens
