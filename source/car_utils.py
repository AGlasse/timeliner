from source.car import Car
import numpy as np
from task import Task


class CarUtils:

    cars = []
    ng_id_final = '838'

    def __init__(self):
        return

    @staticmethod
    def read_miri_car_ids():
        """ Read in the identifiers for all CARs of interest to MIRI
        :return: miri_car_identifiers
        """
        path = './inputs/car_obs_table.csv'
        print('Reading identifiers for MIRI related CARs from ' + path)
        with open(path, 'r') as file:
            text_block = file.read()
        line_list = text_block.split('\n')
        miri_car_ids = []
        for line in line_list[1:]:
            tokens = line.split(',')
            if len(tokens) > 3:
                ng_id, idt_id, pid, obs_list, tag, title = (token.strip() for token in tokens[0:6])
                miri_car_ids.append([ng_id, idt_id, pid, obs_list, tag, title])
        return np.asarray(miri_car_ids)

    @staticmethod
    def read_timeline(path):
        from tools import Tools
        import re

        tools = Tools()

        raw_car_list = []
        miri_car_ids = CarUtils.read_miri_car_ids()

        with open(path, 'r') as file:
            text_block = file.read()
        line_list = text_block.split('\n')
        n_header_lines = 3                      # Was 4 for June 2020
        cawg_row = 4
        for line in line_list[n_header_lines + 1:-1]:
            cawg_row += 1
            line = tools.filter_strcom(line)    # Remove commas in strings
            token_list = line.split(',')
            cawg_ng_id = token_list[0]          # Index =1 for June 2020

            # Look for a matching miri CAR identifier, including wild card characters
            for miri_car_id in miri_car_ids:
                miri_ng_id = miri_car_id[0]
                is_miri_car = miri_ng_id == cawg_ng_id
                if miri_ng_id.find('?') != -1:
                    re_string = miri_ng_id.replace('?', '.')    # Check for single character wildcard
                    is_in_string = re.search(re_string, cawg_ng_id) is not None
                    is_same_length = len(re_string) == len(cawg_ng_id)
                    is_miri_car = is_in_string and is_same_length
                if is_miri_car:
                    idt_id = miri_car_id[1]
                    # Replace any wild card character
                    miri_ng_id_wc_idx = miri_ng_id.find('?')
                    if miri_ng_id_wc_idx != -1:
                        wc = cawg_ng_id[miri_ng_id_wc_idx]
                        miri_ng_id = miri_ng_id.replace('?', wc)
                        idt_id = idt_id.replace('?', wc)
                    pid_id = miri_car_id[2]
                    apt_obs = miri_car_id[3]
                    label = miri_car_id[4]
                    title = token_list[2]
                    tstart = CarUtils._decode_time(token_list[3:5], 'day')
                    tdur_hr = CarUtils._decode_time(token_list[5:7], 'hr')
                    car = Car(cawg_row, idt_id, label, title, miri_ng_id,
                              pid_id, apt_obs,
                              tstart=tstart, tdur_hr=tdur_hr)
                    raw_car_list.append(car)
                    break
        return raw_car_list

    @staticmethod
    def patch_cars(raw_car_list):
        """ Filter Car list to those with matched NGST CAR id number and
        perform specific edits to aid later processing.
        Note: NG-74.4 appears twice in the March2020 timeline, at rows 667
        and 713.  The instance at row 667 is renumbered to 74.6 and the IDT
        renamed MIRI-005.4 to MIR-005.6.  The instance at row 713 is skipped
        For June 2020, the skipped row is now 720.
        :return:
        """
        skip_rows = []          # eg [720] to skip row 720
        ng_renames = {}         # eg {'74.4': '74.6'}
        idt_renames = {'217.1': 'MIR-058.1', '217.2': 'MIR-058.2'}        # eg {'88': 'MIR-011.1', '88.01': 'MIR-011.2'}
        removes = ['882.2', '76.2',
                   '774.1', '774.2', '774.4',                       # Non-MIRI parts of FGS-017
                  ]

        durations = []          # eg [('MIR-005.1', 5.0)]
        add_afters = [] #(Car(-1, 'MIR-011.1', 'Phot zero pts.', 'Photometric zero points',
                        #   '88.1', '1027', 'All',
                        #   tstart=-1.0, tdur=1.0), 'MIR-076')
                      #]
        add_befores = []  # eg [(Car(-1, 'MIR-005.8', 'Anneal 8', 'Anneal before MIR-061', '74.8', '1023')]

        combines = [('MIR-082',                     # Combined CAR name
                     'MIR-082.1', 'MIR-082.2', 'MIR-082.3', 'MIR-082.4', 'MIR-082.5'),  # ..included
                    ('MIR-065',
                     'MIR-065.1', 'MIR-065.2'),
                    ('MIR-ERO',
                     'ERO-1.2', 'ERO-2.2', 'ERO-3.2', 'ERO-4.2', 'ERO-5.2', 'ERO-6.2')
                    ]
        eros = [("ERO-1.1", "ERO 1 - MIR")]
        patch_names = {'270.2': 'SIAF update conf.',
                       '812.1': 'Sky bgd, hot', '812.2': 'Sky bgd, cold'}
        print('')
        print('Note that the following edits are performed on the CAWG timeline')
        fmt = ",{:<10s},{:<12s},{:<20s},{:<s}"
        fmt_hdr = " {:<6s}" + fmt
        fmt_rec = " {:<6d}" + fmt
        print(fmt_hdr.format('Row', 'Priority', 'CAR ID', 'CAR Label', 'Change'))

        cawg_crs = []       # List of CAWG change requests
        out_cars = []
        for car in raw_car_list:
            cr_text = None
            skip_ga = 'analysis' in car.title.lower()   # Reject all analysis
            skip_cam = 'CAM' in car.title               # Match case for rejecting CAM meetings.
            skip = skip_ga or skip_cam
            if skip:      # Remove all analysis CARs
                text = 'Ground analysis or CAM may use duplicate NG CAR number'
                cr_text = fmt_rec.format(car.cawg_row, 'Low', car.idt_id, car.label, text)
                cawg_crs.append(cr_text)
            else:
                if car.ng_id in ng_renames:
                    new_ng_id = ng_renames[car.ng_id]
                    text = "Renamed NG CAR id from {:s} to {:s}"
                    cr_text = fmt_rec.format(car.cawg_row, 'Low', car.idt_id, car.ng_id, new_ng_id)
                    cawg_crs.append(cr_text)
                    car.ng_id = new_ng_id
                if car.ng_id in idt_renames:
                    new_idt_id = idt_renames[car.ng_id]
                    text = "Renamed to {:s}".format(new_idt_id)
                    cr_text = fmt_rec.format(car.cawg_row, 'Low', car.idt_id, new_idt_id, text)
                    cawg_crs.append(cr_text)
                    car.idt_id = new_idt_id
                if 'MIR' in car.idt_id:     # Enforce MIR-XXX.Y syntax
                    tags = car.idt_id.split('.')
                    mir_xxx = tags[0]
                    xxx = mir_xxx.split('-')[1]
                    while len(xxx) < 3:
                        xxx = '0' + xxx
                    dec = '.' + tags[1] if len(tags) > 1 else ''
                    new_idt_id = 'MIR-' + xxx + dec
                    fmt = "{:>6d},{:>10s},Rename IDT {:s} to {:s}"
                    cr_text = fmt.format(car.cawg_row, 'Low', car.idt_id, new_idt_id)
                    cawg_crs.append(cr_text)
                    car.idt_id = new_idt_id
                for ero in eros:
                    if car.ng_id in ero[0]:       # Filter out NRC ERO CARs with identical ng_id
                        if car.title in ero[1]:
                            out_cars.append(car)
                if car.ng_id in patch_names:
                    new_label = patch_names[car.ng_id]
                    fmt = "{:>6d},{:>10s},Non-CAWG change.  In {:s}, change label from {:s} -> {:s}"
                    cr_text = fmt.format(car.cawg_row, 'Low', car.idt_id, car.label, new_label)
                    cawg_crs.append(cr_text)
                    car.label = new_label
                if car.ng_id not in removes:
                    out_cars.append(car)
                for add_after in add_afters:
                    pre_car_idt = add_after[1]
                    if car.idt_id == pre_car_idt:
                        new_car = add_after[0]
                        new_car.add_source(car)
                        t_start = car.get_t_end()
                        new_car.t_start = t_start
                        out_cars.append(new_car)
                        fmt = "{:>6d},{:>10s},Insert new CAR {:s} immediately after and linked to {:s}"
                        cr_text = fmt.format(car.cawg_row, 'High', new_car.idt_id, car.idt_id)
                        cawg_crs.append(cr_text)
                for add_before in add_befores:
                    post_car_idt = add_before[1]
                    if car.idt_id == post_car_idt:
                        new_car = add_before[0]
                        car.add_source(new_car)
                        t_start = car.t_start - new_car.t_dur
                        new_car.t_start = t_start
                        out_cars.insert(-1, new_car)
                        fmt = "{:>6d},{:>10s},Insert new CAR {:s} immediately before and linked to {:s}"
                        cr_text = fmt.format(car.cawg_row, 'High', new_car.idt_id, car.idt_id)
                        cawg_crs.append(cr_text)
            if cr_text is not None:
                print(cr_text)

        # Update durations.
        for car in out_cars:
            cr_text = None
            for duration in durations:        # Use primary/new CAR
                if car.idt_id == duration[0]:
                    old_t_dur_cawg = car.t_dur_cawg
                    new_t_dur_cawg = duration[1]
                    car.t_dur_cawg = new_t_dur_cawg
                    fmt = "{:6d},{:>10s},CAR {:s}, change duration from {:10.2f} to {:10.2f} (hours)"
                    cr_text = fmt.format(car.cawg_row, 'High', car.idt_id, old_t_dur_cawg, new_t_dur_cawg)
                    cawg_crs.append(cr_text)
            if cr_text is not None:
                print(cr_text)

        # Combine (cooler assisted anneals) into a single CAR.
        for car in out_cars:
            for combine in combines:        # Use primary/new CAR
                if car.idt_id == combine[1]:
                    print('Combining CARs {:s} etc. into {:s}'.format(combine[1], combine[0]))
                    new_idt_id = combine[0]
                    prime_car, err_msg = CarUtils.get_car(combine[1], car_list=out_cars)
                    for sec_idt_id in combine[2:]:
                        sec_car, err_msg = CarUtils.get_car(sec_idt_id, car_list=out_cars)
                        prime_car.t_dur += sec_car.t_dur
                        out_cars.remove(sec_car)
                    prime_car.idt_id = new_idt_id

        # Link all CARs (except the first) to their predecessor
        for i in range(1, len(out_cars)):
            out_cars[i].add_source(out_cars[i-1])
        CarUtils.cars = out_cars

        # Write CAWG change requests to a file
        cr_file = open('./outputs/miri_cawg_crs', 'w')
        fmt = "{:>6s},{:>10s},{:s}"
        hdr = fmt.format('Row', 'Priority', 'Change')
        cr_file.write(hdr + "\n")
        for cr_text in cawg_crs:
            cr_file.write(cr_text + "\n")
        cr_file.close()
        return

    @staticmethod
    def get_car(idt_id, **kwargs):
        task_list = kwargs.get('car_list', CarUtils.cars)
        return Task._get_task(idt_id, task_list)

    @staticmethod
    def print():
        cars = CarUtils.cars
        cars[0].print_header()
        for car in cars:
            car.print()
        return

    @staticmethod
    def select_cars(cars, day, shift):
        """ Select CARs which start on a specific day/shift.
        """
        car_list = []
        for car in cars:
            car_day = int(car.tstart)
            if car_day == day:
                car_shift = int(3.0 * (car.tstart - car_day))
                if car_shift == shift:
                    car_list.append(car)
        return car_list

    @staticmethod
    def _decode_time(time, op_unit):
        tscale = {'min': 1, 'hr': 60.0, 'day': 60.0 * 24.0}
        val = float(time[0])
        in_scale = tscale[time[1]]
        out_scale = tscale[op_unit]
        t = val * in_scale / out_scale
        return t

    @staticmethod
    def add_apt_times_to_cars(cars, car_obs_file, apt_data_file):

        with open(car_obs_file, 'r') as file:
            text_block = file.read()
        line_list = text_block.split('\n')
        n_header_lines = 1
        cpos_table = []
        for line in line_list[n_header_lines:-1]:
            tokens = line.split(',')
            car_instance = tokens[1].strip()
            pid = tokens[2].strip()
            if pid != 'RTC' and pid != 'TBD':
                obs_text = tokens[3]
                ots = obs_text.split('.')
                obs_list = []
                for ot in ots:
                    obs_list.append(ot)
                cpos_table.append((car_instance, pid, obs_list))

        with open(apt_data_file, 'r') as file:
            text_block = file.read()
        line_list = text_block.split('\n')
        n_header_lines = 1
        apt_obs_table = []
        for line in line_list[n_header_lines:-1]:
            tokens = line.split(',')
            apt_car_id = tokens[0].strip()
            apt_pid = tokens[1].strip()
            apt_obs = tokens[6].strip()
            apt_obs_t_sci = float(tokens[32]) / 3600.0
            apt_obs_t_dur = float(tokens[33]) / 3600.0
            apt_obs_table.append((apt_car_id, apt_pid, apt_obs, apt_obs_t_sci, apt_obs_t_dur))

        car_times_file = './outputs/car_times.csv'
        csv_file = open(car_times_file, 'w')

        t_sci_apt_tot, t_dur_apt_tot, t_dur_cawg_tot = 0.0, 0.0, 0.0
        fmt1 = "{:12s},{:8s},{:30s},{:>14s},{:>14s},{:>14s},  {:30s}"
        fmt2 = "{:12s},{:8s},{:30s},{:14.2f},{:14.2f},{:14.2f},  {:30s}"
        line = fmt1.format("CAR", "PID", "Observations",
                           "t_sci_apt/hr", "t_dur_apt/hr",
                           "t_dur_cawg/hr", "CAR label")
        print(line)
        csv_file.write(line + '\n')
        for cpos in cpos_table:
            cpos_car_inst, cpos_pid, cpos_obs_list = cpos
            car, err_msg = CarUtils.get_car(cpos_car_inst)
            if car is None:
                print('Failed to find' + cpos_car_inst)
                nob = 1
            car.obs_list = []
            car.t_sci_apt, car.t_dur_apt = 0.0, 0.0
            handled_obs_list = []
            obs_text = ''
            for apt in apt_obs_table:
                apt_car_id, apt_pid, apt_obs, apt_obs_t_sci, apt_obs_t_dur = apt
                tokens = cpos_car_inst.split('.')
                cpos_car_id = tokens[0]
                is_car = apt_car_id == cpos_car_id
                if is_car:
                    obs_text = ''
                    for cpos_obs in cpos_obs_list:
                        obs_text = obs_text + cpos_obs + '-'
                        is_all = True if cpos_obs == 'All' else False
                        is_obs = False
                        if not is_all:
                            is_obs = True if apt_obs == cpos_obs else False
                        if is_all or is_obs:
                            is_handled = False
                            for handled_obs in handled_obs_list:
                                if handled_obs == apt_obs:
                                    is_handled = True
                            if not is_handled:
                                car.t_sci_apt += apt_obs_t_sci
                                car.t_dur_apt += apt_obs_t_dur
                                car.obs_list.append((apt_obs, apt_obs_t_dur))
                                handled_obs_list.append(apt_obs)
            t_sci_apt_tot += car.t_sci_apt
            t_dur_apt_tot += car.t_dur_apt
            t_dur_cawg_tot += car.t_dur_cawg
            line = fmt2.format(cpos_car_inst, cpos_pid, obs_text[0:-1], car.t_sci_apt, car.t_dur_apt, car.t_dur_cawg, car.label)
            print(line)
            csv_file.write(line + '\n')
        line = fmt2.format(" ", " ", "Total = ", t_sci_apt_tot, t_dur_apt_tot, t_dur_cawg_tot, " ")
        print(line)
        csv_file.write(line + '\n')
        print()
        csv_file.close()
        return cars

    @staticmethod
    def add_caps_to_cars(cars, caps):
        for car in cars:
            idt_id = car.idt_id
            for cap in caps:
                link = (cap, '.')    # Default is no link
                for source in cap.sources:
                    is_consumer = source.idt_id == idt_id
                    if is_consumer:
                        link = (cap, 'In')
                car.caplinks.append(link)
        return cars

    @staticmethod
    def set_positions(cars):
        for car in cars:
            car.set_position()
        return

    @staticmethod
    def layout_cars(cars, n_car_cols, **kwargs):

        car_start_col = 0

        nominal_car_breaks = ['MIR-004', 'MIR-007', 'MIR-018']
        car_breaks = kwargs.get('car_breaks', nominal_car_breaks)

        row, col = 0, 0
        for car in cars:
            car.row, car.col = row, col
            col += 1
            for car_break in car_breaks:
                if car.idt_id == car_break:
                    col = n_car_cols
            if col == n_car_cols:
                col = car_start_col
                row = row + 1
        return row + 1
