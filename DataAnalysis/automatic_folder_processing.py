from __future__ import print_function
from printind.printind_function import printiv
import os
import fnmatch
from aggregate_IMU_UG import aggregate_UG_VN_data
import pickle
from look_at_spectra import welch_spectrum
import tqdm
import datetime
import matplotlib.dates as mdates
import time
import numpy as np
from dateutil import parser
from look_at_spectra import compute_SWH
import matplotlib.pyplot as plt
from load_boat_data_v2 import load_boat_data

print("Put in UTC")
os.environ['TZ'] = 'UTC'
time.tzset()

# load all the UG and VN100 data --------------------------------------------------
# FIXME: this should as well be a couple of functions

verbose = 3

frequency_common_time_base = 10.0
minimum_duration_for_valid_data_minutes = 20
minimum_number_points_valid_data = int(20 * 60.0 * frequency_common_time_base)

plot = 0
min_frq = 0.04
max_frq = 2.0

# path_to_data = "/media/jrlab/Data/data_nansen_UG/"
path_to_data = "/media/jrlab/SAMSUNG/Data_USB_Key/Data/data_nansen_UG_processed/"

list_all_files = os.listdir(path_to_data)
list_file_timestamps = []

for crrt_file in list_all_files:
    if verbose > 3:
        printiv(crrt_file)

    if fnmatch.fnmatch(crrt_file, '*_gauge.csv'):
        list_file_timestamps.append(crrt_file[0:-10])
        if verbose > 2:
            printiv(crrt_file[0:-10])

# order the list of timestamps
list_file_timestamps = sorted(list_file_timestamps)

# choose the range of times
cp_list_file_timestamps = list_file_timestamps[:]
list_file_timestamps = []

# time_min = datetime.datetime(2018, 9, 14)
# time_max = datetime.datetime(2018, 9, 19)

time_min = "2018-09-14"
time_max = "2018-09-19"

for crrt_time in cp_list_file_timestamps:
    if (crrt_time > time_min) and (crrt_time < time_max):
        list_file_timestamps.append(crrt_time)

if verbose > 2:
    printiv(list_file_timestamps)

dict_all_wave_data = {}
dict_all_wave_data["list_all_timestamps"] = []

if verbose > 0:
    print("Found {} valid log files from the UG sensor".format(len(list_file_timestamps)))

for current_file_timestamp in tqdm.tqdm(list_file_timestamps):

    dict_all_wave_data["list_all_timestamps"].append(current_file_timestamp)

    if verbose > 1:
        printiv(current_file_timestamp)

    current_pickle_file = path_to_data + current_file_timestamp + ".pkl"

    # check if the file has already been pre-processed before; if not, need to pre-process
    if not os.path.exists(current_pickle_file):

        print("need to pre process...")

        # the dict with the data to save
        dict_wave_data = {}

        # load the data
        common_time_base, interpolated_pitch_elevation_effect, interpolated_2integrated_acc_down, interpolated_dist_ug, wave_elevation = aggregate_UG_VN_data(path_to_data, current_file_timestamp, plot=0, verbose=0)

        data_length = common_time_base.shape[0] + 1

        # compute SWH
        SWH = compute_SWH(wave_elevation, verbose=0)
        dict_wave_data["SWH"] = SWH

        # check the saturation
        saturation_absolute_threshold = 0.46

        where_saturated_high = interpolated_dist_ug > saturation_absolute_threshold
        number_saturated_high = np.sum(where_saturated_high)
        proportion_saturated_high = 1.0 * number_saturated_high / data_length
        dict_wave_data["proportion_saturated_high"] = proportion_saturated_high

        where_saturated_low = interpolated_dist_ug < -saturation_absolute_threshold
        number_saturated_low = np.sum(where_saturated_low)
        proportion_saturated_low = 1.0 * number_saturated_low / data_length
        dict_wave_data["proportion_saturated_low"] = proportion_saturated_low

        dict_wave_data["timestamp"] = current_file_timestamp
        dict_wave_data["valid_data_number_points"] = data_length > minimum_number_points_valid_data

        if verbose > 0:
            printiv(dict_wave_data["valid_data_number_points"])

        if dict_wave_data["valid_data_number_points"]:

            # get the spectrum
            f_elev, Pxx_elev = welch_spectrum(wave_elevation, frequency_common_time_base, min_frq, max_frq, plot=plot, label="wave elevation")
            _, Pxx_2integrated_acc_down = welch_spectrum(interpolated_2integrated_acc_down, frequency_common_time_base, min_frq, max_frq, plot=plot, label="boat vertical acceleration")
            _, Pxx_dist_ug = welch_spectrum(interpolated_dist_ug, frequency_common_time_base, min_frq, max_frq, plot=plot, label="u gauge reading")
            _, Pxx_dist_pitch = welch_spectrum(interpolated_pitch_elevation_effect, frequency_common_time_base, min_frq, max_frq, plot=plot, label="pitch effect")

            dict_wave_data["common_f_base"] = f_elev
            dict_wave_data["Pxx_elev"] = Pxx_elev
            dict_wave_data["Pxx_2integrated_acc_down"] = Pxx_2integrated_acc_down
            dict_wave_data["Pxx_dist_ug"] = Pxx_dist_ug
            dict_wave_data["Pxx_dist_pitch"] = Pxx_dist_pitch

            if verbose > 1:
                print("size of the spectrum: {}".format(f_elev.shape[0]))

        if verbose > 1:
            print("dump the pickle")

        # dump the pickle file
        with open(current_pickle_file, 'w') as crrt_file:
            pickle.dump(dict_wave_data, crrt_file, pickle.HIGHEST_PROTOCOL)

        if verbose > 1:
            print("done dumping the pickle")

    else:
        print("already pre processed; load the pickle file")
        # load the pickle file
        with open(current_pickle_file, 'r') as crrt_file:
            dict_wave_data = pickle.load(crrt_file)

    dict_all_wave_data[current_file_timestamp] = dict_wave_data

# now all the wave data are well loaded

# collect the data from VN100 and UG for the plots ----------------------------------
list_timestamps_UG_VN = []
list_proportion_saturated_data_high = []
list_proportion_saturated_data_low = []
list_SWH = []
list_SWH_saturation_compensated = []
list_spectra = []

list_frequencies = dict_all_wave_data[list_file_timestamps[0]]["common_f_base"]

for current_file_timestamp in tqdm.tqdm(list_file_timestamps):
    crrt_wave_dict = dict_all_wave_data[current_file_timestamp]

    # if the file has enough points, use its data...
    if crrt_wave_dict["valid_data_number_points"]:

        current_datetime = parser.parse(current_file_timestamp, ignoretz=True)
        # current_matplotlib_datetime = mdates.date2num(current_datetime)
        # list_timestamps_UG_VN.append(current_matplotlib_datetime)
        list_timestamps_UG_VN.append(current_datetime)

        list_proportion_saturated_data_high.append(crrt_wave_dict["proportion_saturated_high"])
        list_proportion_saturated_data_low.append(crrt_wave_dict["proportion_saturated_low"])

        list_SWH.append(crrt_wave_dict["SWH"])
        SWH_saturation_compensated = crrt_wave_dict["SWH"] / (1 - crrt_wave_dict["proportion_saturated_high"]) / (1 - crrt_wave_dict["proportion_saturated_low"])
        list_SWH_saturation_compensated.append(SWH_saturation_compensated)

        list_spectra.append(crrt_wave_dict["Pxx_elev"])

# TODO: add the saturated background color warning (?)

# load the boat AWS data ---------------------------------------
# NOTE: the file must be a 'Malte' file!!!
"""
folder_boat_data = "/media/jrlab/Data/Nansen_legacy_2018_KpHaakon_AWS/"
filename_boat_data = "AWS430__SMSAWS__20180911-15.txt"

list_timestamps_boat, SOG, WS = load_boat_data(folder_boat_data, filename_boat_data, plot=False)
# SOG: speed over ground
# WS: wind speed real
"""

# folder_boat_data = "/media/jrlab/Data/Nansen_legacy_2018_KpHaakon_AWS/AWS_text_data/"
folder_boat_data = "/media/jrlab/SAMSUNG/Data_USB_Key/Data/Nansen_legacy_2018_KpHaakon_AWS/AWS_text_data/"

list_all_files = os.listdir(path_to_data)
list_valid_boat_files = []

for crrt_file in os.listdir(folder_boat_data):
    printiv(crrt_file)
    if fnmatch.fnmatch(crrt_file, "*.txt"):
        list_valid_boat_files.append(crrt_file)

list_valid_boat_files = sorted(list_valid_boat_files)
printiv(list_valid_boat_files)

list_timestamps_boat = []
list_SOG = []
list_WS = []

for crrt_file in tqdm.tqdm(list_valid_boat_files):
    (list_timestamps, SOG, WS) = load_boat_data(folder_boat_data, crrt_file, plot=False, print_header_format=False)
    list_timestamps_boat += list_timestamps
    list_SOG += list(SOG)
    list_WS += list(WS)

# make the plot ---------------------------------------------
print("start plotting")

plt.figure()
nbr_plot_lines = 5
nbr_plot_columns = 1

# saturation
plt.subplot(nbr_plot_lines, nbr_plot_columns, 1)
plt.plot(list_timestamps_UG_VN, list_proportion_saturated_data_low, label="saturation low")
plt.plot(list_timestamps_UG_VN, list_proportion_saturated_data_high, label="saturation high")
plt.ylabel("saturation proportion")
plt.ylim([0, 1])
plt.xlim([list_timestamps_UG_VN[0], list_timestamps_UG_VN[-1]])
plt.legend()

# SWH
plt.subplot(nbr_plot_lines, nbr_plot_columns, 2)
plt.plot(list_timestamps_UG_VN, list_SWH, label="4 std")
plt.plot(list_timestamps_UG_VN, list_SWH_saturation_compensated, label="4 std compensated")
plt.xlim([list_timestamps_UG_VN[0], list_timestamps_UG_VN[-1]])
plt.ylabel("SWH [m]")
plt.legend()

# spectra in 2D
plt.subplot(nbr_plot_lines, nbr_plot_columns, 3)
X, Y = np.meshgrid(list_timestamps_UG_VN, list_frequencies)
Z = np.array(list_spectra).T
plt.pcolor(X, Y, Z, label="S_{xx} [kg m^{2} s^{-1}]")
plt.xlim([list_timestamps_UG_VN[0], list_timestamps_UG_VN[-1]])
plt.ylim([0.05, 0.5])
plt.ylabel("f [Hz]")

plt.subplot(nbr_plot_lines, nbr_plot_columns, 4)
plt.plot(list_timestamps_boat, list_SOG)  # FIXME, this is ugly...
plt.ylabel("SOG [m/s]")
plt.xlim([list_timestamps_UG_VN[0], list_timestamps_UG_VN[-1]])

plt.subplot(nbr_plot_lines, nbr_plot_columns, 5)
plt.plot(list_timestamps_boat, list_WS)  # FIXME, this is ugly...
plt.ylabel("WS [m/s]")
plt.xlim([list_timestamps_UG_VN[0], list_timestamps_UG_VN[-1]])

plt.xlabel("UTC time")
plt.show()
