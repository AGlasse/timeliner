import astropy
import requests
import json
import os
import subprocess

class AptUtils:

    aptexe_path = '/home/achg/Applications/APT_2020.2/bin/apt'        # Local copy of APT
    apt_folder = '/home/achg/PycharmProjects/timeliner/apt_scripts/'
    # MIRI APT PIDs
    pid_list = ['1012']
#        , 1011, 1012, 1022, 1023, 1024, 1027, 1028, 1029,
#               1030, 1031, 1032, 1033, 1034,
#               1037, 1038, 1039, 1040, 1042, 1043,
#               1045, 1046, 1047, 1049, 1050, 1051, 1052, 1053, 1054,
#               1172,
#               1259, 1261, 1406, 1445, 1448, 1449]

    def __init__(self):
        return

    def process(self):
        redownload = False
        if redownload:
            AptUtils.download_apt_aptx()
        for pid in AptUtils.pid_list:
            AptUtils.unzip(pid)

            AptUtils.export_json_times(pid)
            timedata = AptUtils.read_json_times(pid)
            science_time = timedata['science_time']
            charged_time = timedata['charged_time']
            efficiency = science_time / charged_time
            print("{:5s}{:10.2f}{:10.2f}{:10.2f}".format(pid, science_time, charged_time, efficiency))
        return

    @staticmethod
    def unzip(pid):
        import zipfile
        apt_path = AptUtils.apt_folder + pid + '.aptx'
        zip_folder = AptUtils.apt_folder + pid
        with zipfile.ZipFile(apt_path, 'r') as zip_ref:
            zip_ref.extractall(zip_folder)
        return

    @staticmethod
    def download_apt_aptx():
        """ Download and save the APT files
        """
        for pid in AptUtils.pid_list:
            outname = "{:d}.aptx".format(pid)
            outpath = AptUtils.apt_folder + outname
            if not os.path.exists(outname):
                tgt = 'http://www.stsci.edu/jwst/phase2-public/{:d}.aptx'.format(pid)
                print('Downloading ' + tgt)
                r = requests.get(tgt)
                open(outpath, "wb").write(r.content)
                print(outname + ' downloaded')
            else:
                print(outname + ' - file already present')
            return

    @staticmethod
    def export_json_times(pid):
        pid_file = AptUtils.apt_folder + '1012.aptx'
        subprocess.run([AptUtils.aptexe_path, '-mode', 'STScI', \
                        '--nogui', '-export', 'timing.json', '-nobackups', pid_file])
        subprocess.run([AptUtils.aptexe_path, '-mode', 'STScI', \
                        '--nogui', '-export', 'timing.json,sql', '-nobackups', pid_file])
        return

    @staticmethod
    def read_json_times(pid):
        json_file = pid + '.' + 'timing.json'
        json_path = AptUtils.apt_folder + json_file
        with open(json_path) as file:
            timedata = json.load(file)
        return timedata

    def export_times(self, pid):
        """ Invoke APT command line to export timing report.
        Thanks to Andrew Myers on APT team for instruction
        """
        outname = "{:d}.aptx".format(pid)
        json_path = "{:d}.timing.json".format(pid)
        print(json_path)
        if not os.path.exists(json_path):
            print("Exporting timing summary for {:d}".format(pid))
            subprocess.run([self.aptexe_path, "-export", "times", "--nogui", outname])
        return

    @staticmethod
    def get_timing_summary(pid):
        # Read info from the APT exported pid.times files and display summary
        path = "{:d}.times".format(pid)
        with open(path) as file:
            text = file.read()

        tgt_str = 'Duration    Charged'

        lines = text.split('\n')
        n_lines = len(lines)
        ct_sum = 0.0
        lno = 0
        for i in range(0, n_lines):  # Hunt for charged time for each observation
            line = lines[i]
            if tgt_str in line:
                exp_title = lines[i - 2]
                ct_line = lines[i + 1]
                tokens = ct_line.split()
                ct = float(tokens[1])
                ct_sum += ct
        ct_hrs = ct_sum / 3600.0
        print('Total charged in APT for program {:d} = {:6.2f} hours'.format(pid, ct_hrs))
        return pid, ct_hrs
