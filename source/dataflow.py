class DataFlow:


    cols_list = [(6, 5, 3), (3, 2, 1), (3, 3, 2),
                 (2, 2, 1), (2, 3, 1), (4, 6, 2)]
    col_dict = {'All': 0, 'M-1': 2, 'M-2': 1, 'M-3': 1, 'M-4': 2,
                'M-5': 3, 'M-6': 3, 'M-7': 4}       #, 'M-EOC': 5}

    def __init__(self, **kwargs):
        return

    @staticmethod
    def plot_dataflow(cars, caps, kdps, cawg_date, **kwargs):
        from plot_utils import Plot
        from car_utils import CarUtils
        from cap_utils import CapUtils
        from kdp_utils import KdpUtils
        from task import Task
        from conduit import Conduit
        from key import Key

        plot = Plot()

        tgt_kdp_id = kwargs.get('kdp_id', 'All')

        xlim = [50, 1300]        # Fixed for 'All' case to keep font size looking ok,
        ylim = [300,  1700]
        xy_origin = [xlim[0] + 50, ylim[1] - 100]

        # End of row CARS for 'All' case
        car_breaks = ['MIR-007', 'MIR-050', 'MIR-064.1', 'MIR-058.2', 'MIR-077']

        idx = DataFlow.col_dict[tgt_kdp_id]
        cols = DataFlow.cols_list[idx]
        plot_key = True
        if tgt_kdp_id != 'All':
            plot_key = False
            tgt_kdp = None
            car_breaks = []
            for kdp in kdps:
                if kdp.idt_id == tgt_kdp_id and tgt_kdp == None:
                    tgt_kdp = kdp
            cars, caps = DataFlow._filter_tasks(tgt_kdp)
            kdps = [tgt_kdp]

        n_car_cols, n_cap_cols, n_kdp_cols = cols
        n_rows = CarUtils.layout_cars(cars, n_car_cols, car_breaks=car_breaks)
        Conduit(xy_origin, n_rows, (n_car_cols, n_cap_cols, n_kdp_cols))
        Conduit.build_cells()

        CarUtils.set_positions(cars)

        CapUtils.layout_caps(caps)
        CapUtils.connect_caps(caps)

        KdpUtils.layout_kdps(kdps)
        KdpUtils.connect_kdps(kdps)

        fig, axs = plot.set_plot_area('MIRI CAR/CAP Flow',
                                      xlim=xlim, ylim=ylim, aspect='equal',
                                      fontsize=10)
        ax = axs[0, 0]
        plot_grid = kwargs.get('plot_grid', False)
        if plot_grid:
            Conduit.plot_grid(ax)

        for car in cars:
            car.plot_box(ax, tl_text=car.ng_id)
            car.plot_car_link(ax)

        for cap in caps:
            cap.plot_box(ax, tl_text=cap.lead)
            cap.loom.plot(ax)

        for kdp in kdps:
            kdp.plot_box(ax)
            kdp.loom.plot(ax)

        if plot_key:
            key = Key()
            x_key = 0.5 * (xlim[0] + xlim[1])
            y_key = Conduit.xy_origin[1]

            key.plot(ax, x_key, y_key)
        fig.savefig('../outputs/dataflow_' + tgt_kdp_id + '.png')
        plot.clear()
        return

    @staticmethod
    def _get_source_cars(cap, cars, caps):
        """ Append cars in this CAPs source tree to the passed list. """
        for task in cap.sources:
            if task.type == 'CAR':
                cars.append(task)
            else:
                caps.append(task)
                cars, caps = DataFlow._get_source_cars(task, cars, caps)
        return cars, caps

    @staticmethod
    def _filter_tasks(tgt_kdp):
        """ Select the subset of CAPs and CARs which flow data to a specific KDP.
        Remove duplicate CARs and sort them by start time. """
        from cap_utils import CapUtils
        from car_utils import CarUtils
        import numpy as np

        cars, caps = [], []
        for tgt_cap in tgt_kdp.sources:
            caps.append(tgt_cap)
            cars, caps = DataFlow._get_source_cars(tgt_cap, cars, caps)

        # Remove duplicates
        cars = DataFlow._remove_duplicates(cars)
        caps = DataFlow._remove_duplicates(caps)

        # Sort by start time
        sor_cars = [cars[0]]
        for car in cars[1:]:
            i = 0
            for scar in sor_cars:
                if car.t_start < scar.t_start:
                    sor_cars.insert(i, car)
                    break
                i += 1
            if i == len(sor_cars):
                sor_cars.append(car)
        cars = sor_cars

        # Enforce CAR dependencies for filtered list and remove CAR row breaks
        cars[0].sources = []
        for i in range(1, len(cars)):
            cars[i].sources = [cars[i-1]]
        return cars, caps

    @staticmethod
    def _remove_duplicates(tasks):
        # Remove duplicate tasks
        uni_tasks = []
        for task in tasks:
            is_unique = True
            for c in uni_tasks:
                if task.idt_id == c.idt_id:
                    is_unique = False
                    break
            if is_unique:
                uni_tasks.append(task)
        return uni_tasks
