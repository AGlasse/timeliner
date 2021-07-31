#!/usr/bin/python
#from person import Person
from car_utils import CarUtils
from cap_utils import CapUtils
from kdp_utils import KdpUtils
from tools import Tools
import numpy as np


class ShiftPlan:
    """ The shift plan object manages an array (rota) with one row per shift slot
    (6 per day) and one column per day of commissioning.  The slots are filled
    person by person using the following rules,
    1.  For all CARs, find SMEs and schedule them for week starting 1 day before
        the CAR (2 days before SMEs 1st CAR).
    2.
    """
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'Jul', 'Aug', 'Sep', 'Oct', 'November', 'December']
    launchyear, launchmonth, launchdate, launchtime = 2021, 11, 25, 11.00
    launchdate_last_monday = 22
    start_day, end_day = -5, 200
    n_days = end_day - start_day + 1
    console_rota = []
    n_slots_max = 15            # Maximum number of personnel scheduled per day
    n_slots_min = 10        # Minimum number for 4.2 shifts per person per week
    free = None

    def __init__(self, **kwargs):
        import numpy as np

        comm_start_day = kwargs.get('start_day', ShiftPlan.start_day)
        comm_end_day = kwargs.get('end_day', ShiftPlan.end_day)
        n_days = comm_end_day - comm_start_day + 1
        ShiftPlan.start_day, ShiftPlan.end_day, ShiftPlan.n_days = comm_start_day, comm_end_day, n_days
        ld_lm = ShiftPlan.launchdate_last_monday
        ShiftPlan.launchdoy_last_monday = ShiftPlan._ymd_to_doy(2021, 11, ld_lm)
        ly, lm, ld = ShiftPlan.launchyear, ShiftPlan.launchmonth, ShiftPlan.launchdate
        ShiftPlan.launchdoy = ShiftPlan._ymd_to_doy(ly, lm, ld)
        ShiftPlan.staff = self.read_staff()
        return

    @staticmethod
    def create_rota():
        """ Create the rota array which holds Person objects for all daily slots, and
        a daily_slots array which contains the number of people required each day (this
        can be greater/less than the baseline 10 in periods of peak/low activity).
        """
        n_days = ShiftPlan.n_days
        n_slots_min = ShiftPlan.n_slots_min
        n_slots_max = ShiftPlan.n_slots_max
        rota = np.full((n_slots_max, n_days), None)         # Create empty rota
        daily_slots = np.full((n_days), n_slots_min)  # Count of slots on each day
        peak_days = [[90, 100], [152, 165]]
        for days in peak_days:
            col1 = days[0] - ShiftPlan.start_day
            col2 = days[1] - ShiftPlan.start_day
            daily_slots[col1:col2+1] = n_slots_max
        ShiftPlan.daily_slots = daily_slots
        return rota

    @staticmethod
    def _decode_period_token(token):
        """ Create an array containing the index (column number) of the day in the rota
        object from a period date token (format 'yyyymmdd:yyyymmdd').
        :param token: Date token.  eg '20211220:20220109'
        :return:  Array of day indices in rota objects
        """
        days = []
        if token != '':
            tokens = token.split(';')
            for t in tokens:
                if t[0] == 'L':
                    md_start = int(t[1:5])
                    md_end = int(t[7:11])
                else:
                    md_start = ShiftPlan._ymd_to_md(2000 + int(t[0:2]), int(t[2:4]), int(t[4:6]))
                    md_end = ShiftPlan._ymd_to_md(2000 + int(t[7:9]), int(t[9:11]), int(t[11:13]))
                for md in np.arange(md_start, md_end + 1):
                    day_idx = md - ShiftPlan.start_day
                    days.append(day_idx)
        return days

    def read_staff(self):
        from cap_utils import CapUtils
        from person import Person

        path = './inputs/staff.csv'
        with open(path, 'r') as file:
            text_block = file.read()
        line_list = text_block.split('\n')
        n_lines = len(line_list)
        staff = []
        is_reserve = False
        for row in range(1, n_lines):
            tokens = line_list[row].split(',')
            if tokens[0] == 'End':
                break
            else:
                if tokens[0] == 'Reserve':
                    is_reserve = True
                    row += 1
                else:
                    initial, forename, surname, email, organisation = (token.strip() for token in tokens[0:5])
                    ident = initial, forename, surname, email, organisation
                    max_nweeks, max_nweeks_block  = (int(token.strip()) for token in tokens[5:7])
                    blackout_days = ShiftPlan._decode_period_token(tokens[7])
                    greyout_days = ShiftPlan._decode_period_token(tokens[8])
                    scheduled_days = ShiftPlan._decode_period_token(tokens[9])
                    availability = is_reserve, max_nweeks, max_nweeks_block, blackout_days, greyout_days, scheduled_days
                    person = Person(ident, availability)
                    for token in tokens[10:]:
                        idt_id = token.strip()
                        if len(idt_id) > 2:
                            task, err_msg = CapUtils.get_cap(idt_id)
                            if task == None:
                                task, err_msg = CarUtils.get_car(idt_id)
                                if task == None:
                                    task, err_msg = KdpUtils.get_kdp(idt_id)
                            if task == None:
                                print("Shift plan unable to find task {:s}".format(idt_id))
                            else:
                                person.sme_tasks.append(task)
                    staff.append(person)
        n_staff = len(staff)
        colours = Tools.get_colour_list(n_staff)
        for i, person in enumerate(staff):
            colour = colours[i]
            person.bar_colour = colour
        return staff

    @staticmethod
    def get_task_header_string(label, **kwargs):
        is_csv = kwargs.get('to_csv', False)
        fmt = "  {:>88s}"
        if is_csv:
            fmt = "  {:>88s},"
        str = fmt.format('CARs')
        return str

    @staticmethod
    def print(**kwargs):
        """ Print the shift plan. If parameter to_csv=True, the plan is written
        in csv format to file 'outputs\shift_plan_basis.csv'
        """
        import numpy as np
        from person import Person

        to_csv = kwargs.get('to_csv', False)
        if to_csv:
            csv_file = "./outputs/shift_plan_basis.csv"
            csv = open(csv_file, 'w')
        att_hdr = Person.get_attendance_header_string(**kwargs)
        header_str = Person.get_header_string(**kwargs) + att_hdr
        if to_csv:
            csv.write(header_str + '\n')
        print(header_str)
        staff = ShiftPlan.staff
        for person in staff:
            person_str = person.get_string(**kwargs)
            attendance_str = person.get_attendance_string(**kwargs)
            str = person_str + attendance_str
            if to_csv:
                csv.write(str + '\n')
            print(str)

        # Repeat header text for readability
        if to_csv:
            csv.write(header_str + '\n')
        print(header_str)
        tasks = CarUtils.cars
        n_car_rows = 25
        car_texts = []
        row_idxs = []
        blank_staff_str = Person.get_header_string(is_blank=True, **kwargs)
        for i in range(0, n_car_rows):
            car_text = blank_staff_str
            car_text += "{:>6s}".format('|')
            car_texts.append(car_text)
            row_idxs.append(0)
        t_soc = ShiftPlan.start_day     # Start of commissioning
        row = 0
        for task in tasks:
            car_text, row_idx = car_texts[row], row_idxs[row]
            idx = row_idxs[row]
            idx_start = int(task.t_start - t_soc)
            if to_csv:
                week_start = int(idx_start / 7)
                idx_start = 7 * week_start
            while idx < idx_start-1:
                dow = idx % 7
                if dow == 0:
                    car_text += ', '
                else:
                    car_text += ' '
                idx += 1
            token = task.idt_id
            n_chars = len(token)
            if to_csv:
                post = int((n_chars-1) / 7)
                token = ' ,' + token + post*','
                idx += 1
            car_text += token
            idx += n_chars
            car_texts[row], row_idxs[row] = car_text, idx
            row += 1
            if row == n_car_rows:
                row = 0
        for car_text in car_texts:
            print(car_text)
            if to_csv:
                csv.write(car_text + '\n')
        if to_csv:
            csv.close()
        return

    @staticmethod
    def allocate_smes(rota):
        from person import Person

        staff = ShiftPlan.staff
        for person in staff:        # Combine personal timetables into a rota
            rota = person.schedule_smes(rota)
        return rota

    @staticmethod
    def allocate_scheduled(rota):
        staff = ShiftPlan.staff
        for person in staff:
            rota = person.schedule_forced(rota)
        return rota

    @staticmethod
    def allocate_non_smes(rota):
        staff = ShiftPlan.staff
        for person in staff:
            rota = person.schedule_remaining(rota)
        return rota

    @staticmethod
    def remove_singles(rota):
        n_rows, n_days = rota.shape
        daily_slots = ShiftPlan.daily_slots
        for row in range(0, n_rows):
            yesterday = rota[row, 0]
            count = 1
            for col in range(1, n_days - 1):
                n_slots = daily_slots[col]
                today = rota[row, col]
                if today == yesterday:
                    count += 1
                else:
                    tomorrow = rota[row, col+1]
                    if tomorrow is not None:
                        if tomorrow != today:
                            if tomorrow in rota[0:n_slots, col]:
                                print('{:s} already scheduled on day {:d}'.format(tomorrow.surname, col))
                            else:
                                rota[row, col] = tomorrow
                                tomorrow.timetable[col] = tomorrow.on_console
                                tomorrow.contiguously_allocated += 1
                        count = 1
                yesterday = today
        return rota

    @staticmethod
    def tidy_rota(rota):
        """ Tidy up rota by placing each person's allocated days on a single row """
        n_rows, n_days = rota.shape
        for day in range(0, n_days-1):
            for row in range(0, n_rows):
                person = rota[row, day]
                for tom_row in range(0, n_rows):
                    tom_person = rota[tom_row, day + 1]
                    if tom_person == person:    # Person also on tomorrow, swap rows tomorrow
                        rota[tom_row, day+1] = rota[row, day+1]
                        rota[row, day+1] = person
        return rota

    @staticmethod
    def get_allocated(rota):
        """ Get the list of unique persons from the rota array who can be
        allocated rota days. """
        person_list = []
        rota_flat = rota.flatten()
        for person in rota_flat:
            if person != None:
                if person not in person_list:
                    person_list.append(person)
        return person_list

    @staticmethod
    def get_available_person(excluded, n_days):
        """ Get the next available person in the staff list. """
        staff = ShiftPlan.staff
        for person in staff:
            if person.is_allocatable(n_days):
                if person not in excluded:      # and person.is_allocatable():
                    return person
        return None

    @staticmethod
    def _plot_calendar_grid(n_panes, xrange, yrange, **kwargs):
        from plot_utils import Plot
        import calendar
        import datetime

        plotpad = kwargs.get('plotpad', 8.0)
        launch_phase = ShiftPlan.launchtime / 24.0        # Fraction of day
        plot = Plot()
        fig, axs = plot.set_plot_area('MIRI Shift Schedule',
                                      ncols=1, nrows=n_panes, fontsize=16,
                                      plotpad=plotpad)

        y_pitch = (0.008, 0.012, 0.016)[n_panes-1] * yrange
        xorg = ShiftPlan.start_day
        xlm = ShiftPlan.launchdoy_last_monday - ShiftPlan.launchdoy
        for pane in range(0, n_panes):
            ax = axs[pane, 0]
            xmin = xorg + xrange * pane
            xmax = xmin + xrange

            xlim = [xmin, xmax]
            ylim = [0, yrange]
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

            # Plot daily grid lines, thicker at DOW = Monday at 0000 UT
            for x in range(xmin, xmax):
                ax.plot([x, x], [ylim[0], ylim[1]], color='grey', lw=0.5)

            while xlm < xmax:
                ax.plot([xlm, xlm], [ylim[0], ylim[1]], color='grey', lw=1.5)
                year, doy = ShiftPlan._md_to_doy(xlm)
                doy_text = '{:d}'.format(doy)
                ax.text(xlm+0.001*xrange, yrange - 2.0*y_pitch, doy_text, color='grey')
                year, month, dom = ShiftPlan._doy_to_ymd(year, doy)
                ax.text(xlm+0.001*xrange, yrange - y_pitch, 'Mon', color='grey')
                if dom > 4:
                    dom_text = '{:d}'.format(dom)
                    ax.text(xlm+0.001*xrange, yrange + 0.1*y_pitch, dom_text, color='blue')
                xlm += 7
            xl = launch_phase
            ax.plot([xl, xl], [ylim[0], 1.01*yrange], color='blue', lw=1.5, ls='--')
            lyr, lmo = ShiftPlan.launchyear, ShiftPlan.launchmonth
            lda, lti = ShiftPlan.launchdate, ShiftPlan.launchtime
            fmt = 'Launch on {:d}/{:d}/{:d}\nat {:5.2f} UT'
            launch_text = fmt.format(lyr, lmo, lda, lti)
            ax.text(xl+0.001*xrange, yrange + y_pitch, launch_text, color='blue')
            year = ShiftPlan.launchyear
            month = ShiftPlan.launchmonth + 1
            is_more = True
            while is_more:
                xdom = ShiftPlan._ymd_to_md(year, month, 1)
                if xdom > 10:
                    text = "{:s}".format(ShiftPlan.month_names[month-1])
                    ax.text(xdom + 0.001*xrange, yrange + 0.1*y_pitch, text, color='blue')
                ax.plot([xdom, xdom], [ylim[0], ylim[1] + 5.0 * yrange], color='blue', lw=1.5, ls='-')

                month += 1
                if month > 12:
                    year += 1
                    month = 1
                is_more = xdom < ShiftPlan.n_days
        return fig, axs

    @staticmethod
    def plot_rota(rota, filename):
        from plot_utils import Plot
        import matplotlib.transforms as mtransforms
        from matplotlib.patches import Polygon, Rectangle, Circle
        from car import Car
        import calendar

        n_panes, xrange, yrange = 3, 70, 105         # Calendar; 3 panes, 105 rows, 70 days/plot
        fig, axs = ShiftPlan._plot_calendar_grid(n_panes, xrange, yrange)

        free = ShiftPlan.free
        n_slots, n_days = rota.shape
        xorg = ShiftPlan.start_day
        yorg = 32                                   # Plot CARs above midline and rota below
        ybarheight = 2.0
        launch_phase = ShiftPlan.launchtime / 24.0  # Fraction of day

        for pane in range(0, n_panes):
            ax = axs[pane, 0]
            xmin = xorg + xrange * pane
            xmax = xmin + xrange

            xlim = [xmin, xmax]
            ylim = [0, yrange]
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

            for slot in range(0, n_slots):          # Draw slot bars
                on_yesterday = free
                ybar = yorg - ybarheight * (1 + slot)        # Bottom left of bar y coord.
                for day in range(0, n_days):
                    x = day + xorg
                    on_today = rota[slot, day]
                    if on_today != on_yesterday:    # Change of shift for this slot
                        if on_yesterday != free:    # Close out last person
                            bar_colour = on_yesterday.bar_colour
                            if x >= xmin:
                                xoff = x if x < xmax else xmax
                                xon = xon if x > xmin else xmin
                                xw = xoff - xon
                                if xw > 0:
                                    bar_args = {'angle':0.0, 'fill':True, 'fc':bar_colour, 'edgecolor':'white'}
                                    bar = Rectangle((xon, ybar), xw, 0.9 * ybarheight, **bar_args)
                                    ax.add_patch(bar)
                                    bartext = on_yesterday.surname
                                    is_dark = Tools.is_dark(bar_colour)
                                    text_colour = 'black'   #if is_dark else 'black'
                                    ax.text(xon, ybar, bartext,
                                            ha='left', va='bottom', color=text_colour)
                                    sme_tasks = on_yesterday.sme_tasks     # Plot SME tasks on timeline
                                    for task in sme_tasks:
                                        xstart = task.t_start + launch_phase
                                        ybarmid = ybar + 0.5 * ybarheight
                                        if xstart > xon and xstart < xoff:
                                            task.ysmes.append(ybarmid)
                                            ax.plot([xstart], [ybarmid],
                                                    marker='o', ms=5.0, mfc='red', fillstyle='full')
                        if on_today != free:        # New person on shift
                            xon = x
                    on_yesterday = on_today

            n_task_slots = 26
            ytaskheight = 2.5
            slot = 0
            cars = CarUtils.cars
            caps = CapUtils.caps
            kdps = KdpUtils.kdps
            tasks = ShiftPlan.merge_tasks(cars, caps)
            tasks = ShiftPlan.merge_tasks(tasks, kdps)
            for task in tasks:
                xstart = task.t_start + launch_phase
                xend = task.get_t_end() + launch_phase
                ytask = yorg + ytaskheight * (slot + 1)
                label = ShiftPlan.strip_line_feeds(task.label)
                text = task.idt_id + ', ' + label
                colour = 'green' if task.type == 'CAP' else 'black'
                ax.text(xstart, ytask, text, color=colour)
                ax.plot([xstart, xend], [ytask-0.2, ytask-0.2], color='red')
                ylo = ylim[1]

                if len(task.ysmes) > 0:
                    for y in task.ysmes:
                        ylo = y if y < ylo else ylo
                        ax.plot([xstart], [ytask],
                                marker='o', ms=5.0, mfc='red', mec='black', fillstyle='full')
                    ax.plot([xstart, xstart], [ylo, ytask], color='red', lw=1.0, ls='dotted')
                slot += 1
                if slot == n_task_slots:
                    slot = 0

        filepath = './outputs/' + filename + '.png'
        fig.savefig(filepath)
        return

    @staticmethod
    def strip_line_feeds(text):
        tokens = text.split('\n')
        text = ''
        for token in tokens:
            text += token
        return text

    @staticmethod
    def merge_tasks(tasks1, tasks2):
        """ Merge multiple time ordered task lists into a single time ordered list.
        """
        tasks = []
        for task1 in tasks1:     # Copy first list into new list
            tasks.append(task1)
        for task2 in tasks2:
            t2 = task2.t_start
            for i, task in enumerate(tasks):
                t = task.t_start
                if t2 < t:
                    tasks.insert(i, task2)
                    break
        if task2 not in tasks:
            tasks.append(task2)
        return tasks

    @staticmethod
    def plot_staff_schedules(**kwargs):
        from matplotlib.patches import Polygon, Rectangle, Circle

        name = kwargs.get('name', 'staff_schedule.png')

        n_panes, xrange, yrange = 2, 105, 120
        fig, axs = ShiftPlan._plot_calendar_grid(n_panes, xrange, yrange, plotpad=15.0)
        xorg = ShiftPlan.start_day

        staff = ShiftPlan.staff
        ybarheight = 2.0

        for pane in range(0, n_panes):
            ax = axs[pane, 0]
            xmin = xorg + xrange * pane
            xmax = xmin + xrange
            n_colours = len(Tools.colours)
            xlim = [xmin, xmax]
            ylim = [0, yrange]
            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
            ax.get_yaxis().set_ticks([])
            nbars_group = 5                                 # Split into groups for readability
            ibar = -1
            ybar = yrange - 2.0 * ybarheight
            for i, person in enumerate(staff):              # Combine personal timetables into a rota
                ybar -= ybarheight                          # Bottom left of bar y coord.
                ibar += 1
                if ibar == nbars_group:
                    ibar = 0
                    yg = ybar + 0.7 * ybarheight
                    ax.plot([xlim[0], xlim[1]], [yg, yg], color='grey', lw=2.5)
                    ybar -= 0.5 * ybarheight
                role_yesterday = ''
                xon = xmin
                for day, role_today in enumerate(person.timetable):
                    x = day + xorg
                    if role_today != role_yesterday or x == xmax:        # Draw the 'old' bar and start a new one
                        if x >= xmin:
                            xoff = x if x < xmax else xmax
                            xw = xoff - xon
                            if xw > 0 and role_yesterday != person.free:
                                icol = i % n_colours            # Default bar colour
                                colour = Tools.colours[icol]
                                if role_yesterday == person.blackout:
                                    colour = 'black'
                                if role_yesterday == person.greyout:
                                    colour = 'grey'
                                if role_yesterday == person.sme_role:
                                    colour = 'pink'
                                if role_yesterday == person.on_console:
                                    colour = 'green'
                                bar_args = {'angle': 0.0, 'fill': True, 'fc': colour, 'edgecolor': 'white'}
                                bar = Rectangle((xon, ybar), xw, 0.9 * ybarheight, **bar_args)
                                ax.add_patch(bar)
                        xon = x
                    role_yesterday = role_today
                text = person.get_allocation_text()
                ax.text(xmin-1.0, ybar, text, ha='right', va='bottom', color='black')
                bar = Rectangle((xmin-1.0, ybar), 1.0, 0.9 * ybarheight, fc=person.bar_colour, fill=True)
                ax.add_patch(bar)
        filepath = './outputs/' + name
        fig.savefig(filepath)
        return

    @staticmethod
    def getLastDow(**kwargs):
        md = kwargs.get('mission_day', None)          # Mission day
        dows = kwargs.get('dows', [1, 4])             # Good start days of week (Tues/Fri)

        md_monday = ShiftPlan.launchdoy_last_monday - ShiftPlan.launchdoy
        dow = (md - md_monday) % 7
        d = dow
        while d > dow - 7:
            is_valid = d in dows
            if is_valid:
                return md
            md -= 1
            d -= 1
            d = d if d >= 0 else 6
        return None

    @staticmethod
    def _ymd_to_doy(year, month, dom):
        doms = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if year % 400 == 0:     # Trap leap years
            doms[2] = 29
        doy = 0
        for mm in range(0, month):
            doy += doms[mm]
        return doy + dom

    @staticmethod
    def _doy_to_ymd(year, doy):

        doms = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if year % 400 == 0:     # Trap leap years
            doms[2] = 29
        day = doy
        for month, dom in enumerate(doms):
            if day <= dom:
                return year, month, day
            day -= dom
        return None

    @staticmethod
    def _ymd_to_md(year, month, day):
        """ Calculate the number of days after launch
        :param year:
        :param month:
        :param day:
        :return: mission day (L + md)
        """
        doy = ShiftPlan._ymd_to_doy(year, month, day)
        if year > 2021:
            endof2021 = ShiftPlan._ymd_to_doy(2021, 12, 31)
            doy += endof2021
        mission_day = doy - ShiftPlan.launchdoy
        return mission_day

    @staticmethod
    def _md_to_ymd(mission_day):
        """ Calculate the number of days after launch
        :param mission day (L + md)
        :return: year, month, day:
        """
        doy = mission_day + ShiftPlan.launchdoy
        endof2021 = ShiftPlan._ymd_to_doy(2021, 12, 31)
        year = 2021
        if doy > endof2021:
            doy -= endof2021
            year = 2022
        ymd = ShiftPlan._doy_to_ymd(year, doy)
        return ymd

    @staticmethod
    def _md_to_doy(md):
        """ Mission day to day of year """
        ldoy = ShiftPlan.launchdoy
        doy = ldoy + md
        year = ShiftPlan.launchyear
        doy_eoy = ShiftPlan._ymd_to_doy(year, 12, 31)
        if doy > doy_eoy:
            doy -= doy_eoy
            year += 1
        doy = doy if doy < doy_eoy else doy - doy_eoy
        return year, doy

    @staticmethod
    def _md_to_dom(md):
        """ Mission day to day of month """
        ldoy = ShiftPlan.launchdoy
        doy = ldoy + md
        doy_eoy = ShiftPlan._ymd_to_doy(ShiftPlan.launchyear, 12, 31)
        doy = doy if doy < doy_eoy else doy - doy_eoy
        return doy
