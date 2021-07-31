#!/usr/bin/python
import numpy as np
from shift_plan import ShiftPlan


class Person:

    arrival_buffer = 3      # Arrive in Baltimore at least 3 days before task
    departure_buffer = 1    # Leave at least 1 day after
    on_console = 'o'        # Supporting one of the three shifts on this day
    resting = 'r'           # In Baltimore but not schedulable for >7 days contiguously
    free = '.'              # Not schedulable
    blackout = 'x'          # Person is not available in Baltimore
    greyout = '+'           # Person not required on shift (set by Alistair)
    sme_role = '!'          # Scheduled to be present on console for a specific CAR execution

    def __init__(self, idents, availabilty):
        self.initial, self.forename, self.surname, self.email, self.organisation = idents
        self.is_reserve, max_nweeks, max_nweeks_block, self.blackout_days, self.greyout_days, schedule_days = availabilty
        self.fg_colour = 'black'
        self.max_allocation = 7 * max_nweeks
        self.max_contiguous_allocation = 7 * max_nweeks_block
        self.contiguously_allocated = 0
        self.timetable = np.full(ShiftPlan.n_days, Person.free)
        for day in self.blackout_days:
            if 0 <= day < ShiftPlan.n_days - 1:      # Clip days outside commissioning period
                self.timetable[day] = Person.blackout
        for day in self.greyout_days:
            if 0 <= day < ShiftPlan.n_days - 1:
                self.timetable[day] = Person.greyout
        for day in schedule_days:
            if 0 <= day < ShiftPlan.n_days - 1:
                self.timetable[day] = Person.on_console
        self.sme_tasks = []
        return

    def __str__(self):
        return self.surname

    def get_allocation_text(self):
        text = "{:s}{:4d}/{:d}".format(self.surname, self._get_allocated(), self.max_allocation)
        return text

    def is_available(self, day):
        """ Check if this person is available for MOC a shift on a specific day """
        status = self.timetable[day]
        is_blackout = status == Person.blackout
        is_free = status == Person.free
        is_available = is_free and not is_blackout
        return is_available

    def _get_allocated(self):
        """ Find the number of days currently allocated to this person to be available
        in Baltimore. This includes rest days, but excludes blackout days.
        """
        tt = self.timetable
        n_total = len(tt)
        n_free = len(np.where(tt == self.free)[0])
        n_blackout = len(np.where(tt == self.blackout)[0])
        n_allocated = n_total - n_free - n_blackout
        return n_allocated

    def _find_free_row(self, rota_column, n_slots):
        """ Find the free row (slot) in a column of the rota.
        """
        for row in range(0, n_slots):
            slot = rota_column[row]
            if slot == None or slot == self:  # Free or this person already scheduled
                return row
        return -1

    def _schedule(self, rota, **kwargs):
        """ Schedule this person in the rota.  The start day of any allocation block is set to be a Tuesday
        or Friday to help with badging and travel.
        """
        task = kwargs.get('task', None)
        forced = kwargs.get('forced', False)

        daily_slots = ShiftPlan.daily_slots
        n_rows, n_days = rota.shape
        start_col, end_col, car_col = 0, n_days, -1     # Default - schedule all of commissioning
        if task != None:
            car_day = int(task.t_start)
            car_col = car_day - ShiftPlan.start_day
            start_day = car_day - self.arrival_buffer
            start_md = ShiftPlan.getLastDow(mission_day=start_day,
                                            dows=[1, 4])   # Force start on Tuesday or Friday
            start_col = start_md - ShiftPlan.start_day
            end_col = car_col + self.departure_buffer + 1

        self.contiguously_allocated = 0
        for col in range(start_col, end_col):
            n_slots = daily_slots[col]
            current_role = self.timetable[col]
            is_forced = current_role == Person.on_console   # Force scheduled busy or not
            is_resting = current_role == Person.resting
            is_blackout = current_role == Person.blackout   # Person says they're unavailable
            is_greyout = current_role == Person.greyout     # Alistair says they're not needed
            is_unavailable = is_blackout or is_greyout
            is_sme = current_role == Person.sme_role
            is_busy = is_resting or is_unavailable or is_sme

            if (not forced and not is_busy) or (forced and is_forced):
                need_rest = self.contiguously_allocated >= self.max_contiguous_allocation
                if need_rest:
                    rest_days = 0
                    n_allocated = self._get_allocated()
                    if n_allocated + rest_days < self.max_allocation:    # maybe go home..
                        self.timetable[col:col + rest_days] = Person.resting
                        self.contiguously_allocated = 0
                else:
                    n_allocated = self._get_allocated()
                    ok_total = n_allocated < self.max_allocation
                    if ok_total:
                        row = self._find_free_row(rota[:, col], n_slots)  # Find (any) free slot on day of CAR
                        if row != -1:
                            role = Person.sme_role if col == car_col else Person.on_console
                            rota[row, col] = self
                            self.timetable[col] = role
                            self.contiguously_allocated += 1
        return rota

    def schedule_smes(self, rota):
        """ Allocate this person to support a specific task.
        """
        for task in self.sme_tasks:
            rota = self._schedule(rota, task=task)
        return rota

    def schedule_forced(self, rota):
        """ Schedule 'forced' (scheduled) dates """
        rota = self._schedule(rota, forced=True)
        return rota

    def schedule_remaining(self, rota):
        """ Schedule remaining allocation to rota """
        rota = self._schedule(rota)
        return rota

    def is_allocatable(self, n_days):
        """ Return True if the number of days is less than the remaining budget """
        n_allocated = self._get_allocated()
        is_allocatable = n_allocated + n_days < self.max_allocation
        return is_allocatable

    @staticmethod
    def get_header_string(**kwargs):
        to_csv = kwargs.get('to_csv', False)
        is_blank = kwargs.get('is_blank', False)
        fmt = "  {:<5s}{:<13s}{:<20s}{:>40s}{:>10s}{:>12s}{:>15s}"
        if to_csv:
            fmt = "  {:<5s},{:<13s},{:<20s},{:>40s},{:>10s},{:>12s},{:>15s},"
        str = fmt.format('ID', 'Forename', 'Surname', 'e-mail', 'Institute', 'Commit./days', 'Max_stay/days')
        if is_blank:
            str = fmt.format('', '', '', '', '', '', '')
        return str

    def get_string(self, **kwargs):
        to_csv = kwargs.get('to_csv', False)
        fmt = "  {:<5s}{:<13s}{:<20s}{:>40s}{:>10s}{:>12.0f}{:>15.0f}"
        if to_csv:
            fmt = "  {:<5s},{:<13s},{:<20s},{:>40s},{:>10s},{:>12.0f},{:>15.0f},"
        init, fname, sname, email, org = self.initial, self.forename, self.surname, self.email, self.organisation
        ma, mca = self.max_allocation, self.max_contiguous_allocation
        str = fmt.format(init, fname, sname, email, org, ma, mca)
        return str

    @staticmethod
    def get_attendance_header_string(**kwargs):
        to_csv = kwargs.get('to_csv', False)

        str = "{:>6s}".format("L + |")
        days_week = 7
        day = ShiftPlan.start_day       # + days_week       # Label is at start of week
        width = days_week
        fmt = '{:<' + "{:d}".format(width) + '}'
        if to_csv:
            fmt = ',' + fmt
        while day < ShiftPlan.n_days:
            tag = fmt.format(day)
            str += tag
            day += days_week
        return str

    def get_attendance_string(self, **kwargs):
        to_csv = kwargs.get('to_csv', False)

        str = "{:>6s}".format("|")
        if to_csv:
            str = str + ','
        day = ShiftPlan.start_day
        dow = 0
        for code in self.timetable:
            str += code
            day += 1
            dow += 1
            if dow == 7 and to_csv:
                str += ','
                dow = 0
        return str
