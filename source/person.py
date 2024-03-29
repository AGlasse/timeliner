#!/usr/bin/python
import numpy as np
from shift_plan import ShiftPlan


class Person:

    arrival_buffer = 0      # Arrive in Baltimore n days before task
    departure_buffer = 0    # Leave at least n days after
    role_console = 'm'      # Supporting one of the three shifts on this day
    role_sme_console = 'M'
    role_free = '.'         # Not schedulable
    blackout = 'X'          # Person is not available in Baltimore
    greyout = 'x'           # Person not required on shift (set by Alistair)
    role_analyst = 'a'      # In Baltimore but not on shift (Analysis or support role)
    role_sme_analyst = 'A'  # Analyst for a CAR running on this day
    role_kdp = 'K'          # Supporting a KDP on this day
    role_remote_analyst = 'R'

    def __init__(self, idents, availabilty):
        self.initial, self.forename, self.surname, self.email, self.organisation, self.bar_colour = idents
        self.is_reserve, max_nweeks, max_nweeks_block, self.blackout_days, self.greyout_days, schedule_days, analysis_days = availabilty
        self.fg_colour = 'blue'
        if self.organisation in ['ESA', 'STScI', 'GSFC']:
            self.fg_colour = 'black'
        self.max_allocation = 7 * max_nweeks
        self.max_contiguous_allocation = 7 * max_nweeks_block
        self.contiguously_allocated = 0
        self.timetable = np.full(ShiftPlan.n_days, Person.role_free)
        for day in schedule_days:                   # Set on console by Alistair
            if 0 <= day < ShiftPlan.n_days - 1:
                self.timetable[day] = Person.role_console
        for day in analysis_days:
            if 0 <= day < ShiftPlan.n_days - 1:
                self.timetable[day] = Person.role_analyst
        for day in self.greyout_days:               # Set unavailable by Alistair (overwrites his on console settings)
            if 0 <= day < ShiftPlan.n_days - 1:
                self.timetable[day] = Person.greyout
        for day in self.blackout_days:              # Personally specified as unavailable (top priority)
            if 0 <= day < ShiftPlan.n_days - 1:
                self.timetable[day] = Person.blackout
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
        is_free = status == Person.role_free
        is_available = is_free and not is_blackout
        return is_available

    def _remove_from_rota(self, rota, col):
        rota_column = rota[:, col]
        for row, slot in enumerate(rota_column):
            if slot != None and slot.initial == self.initial:
                rota[row, col] = None
                return rota
        return rota

    def _get_allocated(self):
        """ Find the number of days currently allocated to this person to be available
        on console.
        """
        tt = self.timetable
        n_console = len(np.where(tt == self.role_console)[0])
        n_sme_console = len(np.where(tt == self.role_sme_console)[0])
        n_allocated = n_sme_console + n_console
        return n_allocated

    def _find_free_slot(self, rota, col, n_slots):
        """ Find the the first free row (slot) in a column (day) of the rota.  Returns None if n_slots are
        already filled.
        """
        free_slots = []
        count_filled = 0
        for slot, person in enumerate(rota[:, col]):
            if person == self:
                return slot
            if person == None:
                free_slots.append(slot)
            else:
                count_filled += 1
        if count_filled >= n_slots:
            return None
        return free_slots[0]

    def schedule_tasks(self, rota, task_type):
        """ Allocate this person to support all tasks in their sme list of a specific type
        (task_type = 'CAR', 'CAP' etc.).
        """
        for task, role in self.sme_tasks:
            if task.type == task_type:
                rota = self._schedule_task(rota, task, role)
        return rota

    def _schedule_task(self, rota, task, requested_role):
        """ Schedule this person in the rota.  The start day of any allocation block is set to be a Tuesday
        or Friday to help with badging and travel.
        """
        daily_slots = ShiftPlan.daily_slot_quota
        task_day = int(task.t_start + ShiftPlan.launchhour/24.0)
        task_col = task_day - ShiftPlan.start_md
        start_col = task_col - self.arrival_buffer            # start_md - ShiftPlan.start_day
        end_col = int(task_col + task.t_dur)                         #self.departure_buffer
        if task.type == 'KDP':
            start_col, end_col = task_col, task_col

        for col in range(start_col, end_col + 1):
            n_slots = daily_slots[col]
            current_role = self.timetable[col]
            is_blackout = current_role == Person.blackout       # Person says they're unavailable
            is_greyout = current_role == Person.greyout         # Alistair says they're not needed
            is_moc = current_role == Person.role_console
            is_sme_moc = current_role == Person.role_sme_console

            is_unavailable = is_blackout or is_greyout
            if is_unavailable:
                md = col + ShiftPlan.start_md
                if requested_role == 'R':
                    fmt = "{:s} analysing {:s} ({:s}) remotely on L+{:d}"
                else:
                    fmt = "Unable to schedule {:s} for {:s} ({:s}) on L+{:d}"
                err_msg = fmt.format(self.surname, task.idt_id, task.label, md)
                print(err_msg)

            else:
                role = current_role                             # Default is current role
                n_allocated = self._get_allocated()             # Allocated full allowance?
                ok_total = n_allocated < self.max_allocation
                if ok_total:
                    if task.type == 'CAP' or task.type == 'KDP':    # Requested task for this day
                        if is_moc or is_sme_moc:                # Currently scheduled to be on console. Flag discrepancy
                            if task.type == 'KDP':              # Prioritise over MOC activities.
                                role = Person.role_kdp
                            else:
                                if col == task_col:
                                    role = Person.role_sme_analyst
                                else:
                                    role = Person.role_analyst
                            rota = self._remove_from_rota(rota, col)
                        else:
                            if task.type == 'KDP':
                                role = Person.role_kdp
                            else:
                                role = Person.role_analyst      # Add to timetable (not rota)
                    else:   # Its a CAR. May support as an SME analyst (not in rota)
                        if requested_role == 'A':
                            role = Person.role_analyst
                            if col == task_col:
                                role = Person.role_sme_analyst
                            if is_moc or is_sme_moc:            # Currently assigned to be in MOC
                                rota = self._remove_from_rota(rota, col)
                        else:   # Requested role is in MOC
                            if is_moc or is_sme_moc:            # Already allocated in MOC
                                role = Person.role_sme_console if col == task_col else Person.role_console
                            else:
                                role = Person.role_console      # Default role for CARs
                                row = self._find_free_slot(rota, col, n_slots)  # Find free slot in rota
                                if row is not None:
                                    if col == task_col:
                                        role = Person.role_sme_console
                                    rota[row, col] = self       # Allocate CARs on rota.
                self.timetable[col] = role                      # Allocate all tasks in personal timetable
        return rota

    def schedule_forced(self, rota):
        """ Allocate this person into the rota on the days when they are prescheduled to be
        on shift in their timetable. """
        daily_slots = ShiftPlan.daily_slot_quota
        n_rows, n_days = rota.shape
        start_col, end_col, car_col = 0, n_days, -1         # Default - schedule all of commissioning
        for col in range(start_col, end_col):
            n_slots = daily_slots[col]
            if self.timetable[col] == Person.role_console:
                row = self._find_free_slot(rota, col, n_slots)  # Find free slot in rota
                if row is not None:
                    rota[row, col] = self
        return rota

    def schedule_remaining(self, rota):
        """ Schedule remaining allocation for this person to be on console rota """
        daily_slots = ShiftPlan.daily_slot_quota
        n_rows, n_days = rota.shape
        start_col, end_col, car_col = 0, n_days, -1                     # Default - schedule all of commissioning

        for col in range(start_col, end_col):
            n_slots = daily_slots[col]
            current_role = self.timetable[col]
            is_free = current_role == Person.role_free
            if is_free:
                n_allocated = self._get_allocated()                     # Allocated full allowance?
                ok_total = n_allocated < self.max_allocation
                if ok_total:
                    row = self._find_free_slot(rota, col, n_slots)      # Find free slot in rota
                    if row is not None:
                        rota[row, col] = self
                        self.timetable[col] = Person.role_console
        return rota

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
        day = ShiftPlan.start_md       # + days_week       # Label is at start of week
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
        day = ShiftPlan.start_md
        dow = 0
        for code in self.timetable:
            str += code
            day += 1
            dow += 1
            if dow == 7 and to_csv:
                str += ','
                dow = 0
        return str
