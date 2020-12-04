from __future__ import print_function
import numpy as np
from dateutil import parser
from printind.printind_function import printiv
import pytz
import datetime

now_utc = datetime.datetime.now(pytz.utc)
today_utc = now_utc.date()


def load_data_with_timestamps(path_to_data, verbose=1):
    """Load some data and timestamps.

    The data is with with header and footer timestamps, and UTC timestamp at the
    beginning of each line."""

    # obtain a reference time from the name of the file
    reference_timestamp = path_to_data[-29:-10]
    datetime_reference_timestamp = parser.parse(reference_timestamp, ignoretz=True)
    list_measurements_timestamps = []
    list_time_since_reference = []

    if verbose > 1:
        printiv(reference_timestamp)

    # load the data
    # get the timestamp from the header
    with open(path_to_data, 'r') as fh:
        line_1 = fh.readline()

        if verbose > 3:
            printiv(line_1)

        header_timestamp = line_1[19:38]
        if verbose > 3:
            printiv(header_timestamp)

        if verbose > 1:
            printiv(header_timestamp)

    # get the data
    data = np.genfromtxt(fname=path_to_data,
                         skip_header=2, skip_footer=1, delimiter=" ")

    # get the timestamps and the
    # timestamp from the footer
    crrt_last_line = "no_data"
    with open(path_to_data, 'r') as fh:
        # read the two lines of the header
        fh.readline()
        fh.readline()

        while True:
            crrt_line = fh.readline()
            if verbose > 3:
                printiv(crrt_line)
            if len(crrt_line) is not 0:
                crrt_last_line = crrt_line

                # check if this is a 'normal' line
                if crrt_line[4] == '-':
                    # extract the timestamp and add it
                    crrt_timestamp = crrt_line[0:26]
                    # print(crrt_timestamp)
                    crrt_datetime_timestamp = parser.parse(crrt_timestamp, ignoretz=True)
                    list_measurements_timestamps.append(crrt_datetime_timestamp)
                    crrt_time_since_reference = (crrt_datetime_timestamp - datetime_reference_timestamp).total_seconds()
                    list_time_since_reference.append(crrt_time_since_reference)

            else:
                break

        if verbose > 3:
            printiv(crrt_last_line)

        if not crrt_last_line[0:8] == "computer":
            print("Warning! it seems that the logging was interrupted!")
            footer_timestamp = crrt_last_line[0:26]
            flag_interrupted_logging = True

        else:
            footer_timestamp = crrt_last_line[17:36]
            flag_interrupted_logging = False

        if verbose > 1:
            printiv(footer_timestamp)

        if flag_interrupted_logging:
            list_time_since_reference.pop()

        array_time_since_reference = np.array(list_time_since_reference)

    return(data, array_time_since_reference, header_timestamp, footer_timestamp)
