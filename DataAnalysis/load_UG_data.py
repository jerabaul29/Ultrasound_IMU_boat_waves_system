import numpy as np
import matplotlib.pyplot as plt
from printind.printind_function import printiv
from data_loader import load_data_with_timestamps
import datetime_utils


class UG_data(object):
    def __init__(self, data, array_time_since_reference, header_timestamp=None, footer_timestamp=None, verbose=0):
        self.data = data
        self.array_time_since_reference = array_time_since_reference
        self.verbose = verbose
        self.data_length = data.shape[0]
        self.header_timestamp = header_timestamp
        self.footer_timestamp = footer_timestamp

        self.column_gauge_reading = 3

        self.data_gauge_reading = data[:, self.column_gauge_reading]
        self.data_vertical_distance_self_calibration = (self.data_gauge_reading - 512.0) * 1.0 / 1024.0  # TODO: check that the self calibration gives a range +-0.5m ie 1m width total

        # the proportion of saturated measurements
        where_saturated_high = self.data_gauge_reading > 1013
        number_saturated_high = np.sum(where_saturated_high)
        self.proportion_saturated_high = 1.0 * number_saturated_high / self.data_length

        where_saturated_low = self.data_gauge_reading < 10
        number_saturated_low = np.sum(where_saturated_low)
        self.proportion_saturated_low = 1.0 * number_saturated_low / self.data_length

        printiv(self.proportion_saturated_low)
        printiv(self.proportion_saturated_high)

        self.logging_frequency = 50.0
        self.time_vector_seconds = np.arange(0, self.data.shape[0] / self.logging_frequency, 1.0 / self.logging_frequency)

        self.duration_data = datetime_utils.DurationAnalyzer(self, verbose=verbose)

    def plot(self):
        plt.figure()
        plt.plot(self.time_vector_seconds, self.data_vertical_distance_self_calibration, label="self calibration auto timestamp")
        plt.plot(self.array_time_since_reference - self.array_time_since_reference[0], self.data_vertical_distance_self_calibration, label="self calibration computer timestamp")
        plt.xlabel("time since start (s)")
        plt.ylabel("$\eta$ (m)")
        plt.legend()
        if self.header_timestamp is not None:
            plt.title("start time: {}".format(self.header_timestamp))

        # plt.show()


if __name__ == "__main__":
    # options
    verbose = 1
    path_to_data = '/media/jrlab/Data/data_nansen_UG/2018-09-13-14:08:12_gauge.csv'

    data, array_time_since_reference, header_timestamp, footer_timestamp = load_data_with_timestamps(path_to_data=path_to_data, verbose=verbose)

    ug_data_object = UG_data(data, array_time_since_reference, header_timestamp=header_timestamp, footer_timestamp=footer_timestamp, verbose=5)

    # example of how to get some specific data
    # print(imu_data_object.acc_D)

    ug_data_object.plot()
    plt.show()
