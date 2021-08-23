""" Programme to read in '.csv' formatted copies of the commissioning timeline
and MIRI shift plan and generate schedules to include the timing of CARs and
CAPs with staff availability.
"""
from car_utils import CarUtils
from cap_utils import CapUtils
from person import Person
from shift_plan import ShiftPlan
from plot_utils import Plot
from kdp_utils import KdpUtils
from dataflow import DataFlow
from tools import Tools

cawg_path = "./inputs/"
cawg_date = "2021_07"
#timeline_file = "2021June_Working_Commissioning_Timeline.csv"
timeline_file = "2021July_MIR005_3_update.csv"
staff_file = "staff.csv"
apt_data_file = "./inputs/apt_decoder_data.csv"
car_obs_file = "./inputs/car_obs_table.csv"

tools = Tools()
car_utils = CarUtils()

timeline_path = cawg_path + timeline_file
print('Reading CAWG timeline from {:s}'.format(timeline_path))
raw_cars = CarUtils.read_timeline(timeline_path)
CarUtils.patch_cars(raw_cars)

cars = CarUtils.cars
cap_utils = CapUtils()
caps = CapUtils.caps

CarUtils.add_caps_to_cars(cars, caps)
CarUtils.add_apt_times_to_cars(cars, car_obs_file, apt_data_file)
CarUtils.print()

kdp_utils = KdpUtils()
KdpUtils.schedule_kdps()
kdps = KdpUtils.kdps

print()
dataflow = True        # True = Replot dataflow diagrams
if dataflow:
    dataflow = DataFlow()
    dc_keys = DataFlow.col_dict.keys()
    for dc_key in dc_keys:      #['M-1']:
        print('Plotting ' + dc_key)
        dataflow.plot_dataflow(cars, caps, kdps, cawg_date, kdp_id=dc_key)  # kdp_id=dc_key (or any non-KDP) to plot all

print("Building shift plan")
plan = ShiftPlan()
rota = ShiftPlan.create_rota()
#ShiftPlan.plot_staff_schedules(name='s1.png')
#ShiftPlan.plot_rota(rota, 'r1')
rota = ShiftPlan.allocate_prescheduled(rota)
#ShiftPlan.plot_staff_schedules(name='s2.png')
#ShiftPlan.plot_rota(rota, 'r2')
rota = ShiftPlan.allocate_tasks(rota, 'CAP')
rota = ShiftPlan.allocate_tasks(rota, 'KDP')
rota = ShiftPlan.allocate_tasks(rota, 'CAR')
#ShiftPlan.plot_staff_schedules(name='s3.png')
#ShiftPlan.plot_rota(rota, 'r3')
rota = ShiftPlan.allocate_remaining(rota)
#ShiftPlan.plot_staff_schedules(name='s4.png')
#ShiftPlan.plot_rota(rota, 'r4')
rota = ShiftPlan.tidy_rota(rota)
#ShiftPlan.plot_staff_schedules(name='s5.png')
#ShiftPlan.plot_rota(rota, 'r5')
rota = ShiftPlan.remove_singles(rota)
ShiftPlan.test_rota(rota)
ShiftPlan.plot_staff_schedules(name='staff_schedule.png')
ShiftPlan.plot_rota(rota, 'rota')
ShiftPlan.print(to_csv=True)

print('timeliner - finished')
