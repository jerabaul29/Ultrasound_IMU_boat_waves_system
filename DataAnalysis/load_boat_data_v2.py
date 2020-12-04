from __future__ import print_function
import matplotlib.pyplot as plt
import numpy as np
from printind.printind_function import printiv
from datetime import datetime, tzinfo, timedelta
import time
import os
import pickle
from dateutil import parser

print("Put in UTC")
os.environ['TZ'] = 'UTC'
time.tzset()

def load_boat_data(folder_boat_data, filename_boat_data, plot=False, print_header_format=False, verbose=0):

    path_to_boat_data = folder_boat_data + filename_boat_data

    time_boat_to_time_UTC = timedelta(hours=+0)

    # load the data: either read or pickle
    current_pickle_boat_data_filename = folder_boat_data + filename_boat_data[:-4] + ".pkl"
    printiv(current_pickle_boat_data_filename)

    # print the header format
    if print_header_format:
        with open(path_to_boat_data, 'r') as fh:
            # read the line of the header
            first_line = fh.readline()

        crrt_buffer = ""
        crrt_position = 0

        for crrt_char in first_line:
            if (crrt_char == " " or crrt_char == "\t") and (crrt_buffer is not ""):
                print("field {} is {}".format(crrt_position, crrt_buffer))
                crrt_position += 1
                crrt_buffer = ""

            elif (crrt_char == " " or crrt_char == "\t") and (crrt_buffer == ""):
                pass
                
            else:
                crrt_buffer += crrt_char

    if not os.path.exists(current_pickle_boat_data_filename):

        dict_AWS = {}

        # load the data
        print("Start loading the boat AWS data")
        data = np.genfromtxt(path_to_boat_data, skip_header=1)
        print("shape of the data: {}".format(data.shape))

        dict_AWS["data"] = data

        # read the timestamps
        list_timestamps = []

        with open(path_to_boat_data, 'r') as fh:
            # read the line of the header
            fh.readline()

            while True:
                crrt_line = fh.readline()

                if verbose > 3:
                    printiv(crrt_line)

                if len(crrt_line) is not 0:
                    # check if this is a 'normal' line
                    if crrt_line[4] == '-':
                        # extract the timestamp and add it
                        crrt_timestamp = crrt_line[0:19]
                        # print(crrt_timestamp)
                        crrt_datetime_timestamp = parser.parse(crrt_timestamp, ignoretz=True) + time_boat_to_time_UTC
                        list_timestamps.append(crrt_datetime_timestamp)

                else:
                    break

        dict_AWS["list_timestamps"] = list_timestamps

        # save the data
        with open(current_pickle_boat_data_filename, 'w') as crrt_file:
            pickle.dump(dict_AWS, crrt_file, pickle.HIGHEST_PROTOCOL)

    else:
        with open(current_pickle_boat_data_filename, 'r') as crrt_file:
            dict_AWS = pickle.load(crrt_file)
            data = dict_AWS["data"]
            list_timestamps = dict_AWS["list_timestamps"]

    if print_header_format:
        first_line_data = data[0, :]
        for i, crrt_data in enumerate(first_line_data):
            print("column {} data {}".format(i, crrt_data))

    # time is in 2 fields, not 1...
    shift_columns = 1

    # SOG: Speed Over Ground
    SOG = data[:, 37 + shift_columns]

    # SPEED: speed relatively to water
    SPEED = data[:, 38 + shift_columns]

    # WS: Wind Speed Real (without the motion of the ship)
    WS = data[:, 64 + shift_columns]

    # print(SPEED)

    if plot:
        plt.figure()
        plt.plot(list_timestamps, SOG)
        plt.ylabel("SOG [m/s]")

        """
        plt.figure()
        plt.plot(list_timestamps, SPEED)
        plt.ylabel("wind speed [m/s]")
        """

        plt.figure()
        plt.plot(list_timestamps, WS)
        plt.ylabel("WS [m/s]")
        plt.show()

    return(list_timestamps, SOG, WS)


if __name__ == "__main__":
    # NOTE: the file must be a 'Malte' file!!!
    folder_boat_data = "/media/jrlab/Data/Nansen_legacy_2018_KpHaakon_AWS/AWS_text_data/"
    filename_boat_data = "AWS430__SMSAWS__20180901.txt"

    load_boat_data(folder_boat_data, filename_boat_data, plot=True, print_header_format=True)