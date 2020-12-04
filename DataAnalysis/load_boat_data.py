from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np
from printind.printind_function import printiv
from datetime import datetime, tzinfo, timedelta
import time
import os
import pickle

# first, obtain the CSV and clean it myself
# ods -> save as -> csv -> separator , -> space ,
# ctrl H -> 2018- -> 2018,
# ctrl H -> 09- -> 09,
# ctrl H ->   -> ,
# ctrl H -> : -> ,

print("Put in UTC")
os.environ['TZ'] = 'UTC'
time.tzset()


def load_boat_data(folder_boat_data, filename_boat_data, plot=False):

    path_to_boat_data = folder_boat_data + filename_boat_data

    time_boat_to_time_UTC = timedelta(hours=+0)

    # load the data: either read or pickle
    current_pickle_boat_data_filename = folder_boat_data + filename_boat_data[:-4] + ".pkl"
    printiv(current_pickle_boat_data_filename)

    if not os.path.exists(current_pickle_boat_data_filename):

        # load the data
        print("Start loading the boat AWS data")
        data = np.genfromtxt(path_to_boat_data, skip_header=2)
        print("shape of the data: {}".format(data.shape))

        # save the data
        with open(current_pickle_boat_data_filename, 'w') as crrt_file:
            pickle.dump(data, crrt_file, pickle.HIGHEST_PROTOCOL)

    else:
        with open(current_pickle_boat_data_filename, 'r') as crrt_file:
            data = pickle.load(crrt_file)

    # SOG: Speed Over Ground
    SOG = data[:, 43-1]

    # WS: Wind Speed Real (without the motion of the ship)
    WS = data[:, 70-1]

    # timestamps
    list_timestamps = []
    for crrt_line in range(data.shape[0]):
        crrt_line = data[crrt_line, :]
        year = int(crrt_line[0])
        month = int(crrt_line[1])
        day = int(crrt_line[2])
        hour = int(crrt_line[3])
        minute = int(crrt_line[4])
        second = int(crrt_line[5])

        current_time = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second, tzinfo=None) + time_boat_to_time_UTC
        list_timestamps.append(current_time)

    if plot:
        plt.figure()
        plt.plot(list_timestamps, SOG)
        plt.ylabel("SOG [m/s]")

        plt.figure()
        plt.plot(list_timestamps, WS)
        plt.ylabel("WS [m/s]")
        plt.show()

    return(list_timestamps, SOG, WS)


if __name__ == "__main__":
    # NOTE: the file must be a 'Malte' file!!!
    folder_boat_data = "/media/jrlab/Data/Nansen_legacy_2018_KpHaakon_AWS/"
    filename_boat_data = "AWS430__SMSAWS__20180911-15.txt"

    load_boat_data(folder_boat_data, filename_boat_data, plot=True)