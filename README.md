# MIRI Timeliner

Author: Alistair Glasse, UKATC. 

## Summary
Scheduling and dataflow planning software for JWST/MIRI commissioning.  Timeliner reads in the commissioning timeline as recorded by the CAWG (Lauren Wheate) in the published spreadsheet and generates a dataflow diagram which links the CARs selected in file 'car_obs_table.csv' with the Commissioning Analysis Projects listed in 'caps.csv' and Key Delivery Milestones listed in 'kdps.csv'.  The duration of APT/OSS driven CARs are read from file 'apt_decoder_data.csv' which is in turn generated from the archived APT files by program 'apt_decoder'.  Dataflow diagrams are generated for each KDP, up to and including the final 'End of Commissioning' science readiness review. 

Next, the staffing calendar is generated, using the team's availability information and CAR subject matter expertise as specified in file 'staff.csv'.  The calendar is output in both spreadsheet (shift_plan_basis.csv) and image (staff_schedule.png and rota.png) form, where the aim is to provide the basis for generating the shift by shift MOC schedule.   




## Installation

## Operation
Currently the code is intended to be run by executing Python programme 'timeliner.py'.  