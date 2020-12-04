import numpy as np
import matplotlib.pyplot as plt
from printind.printind_function import printiv
from data_loader import load_data_with_timestamps
import datetime_utils


class IMU_data(object):
    def __init__(self, data, array_time_since_reference, column_offset=1, header_timestamp=None, footer_timestamp=None, verbose=0):
        """A function to load some VN100 IMU data in the output format including
        Karman information used for the waves in ice sensors.

        - data: the numpy data of the IMU
        - column_offset: an offset. For example, if UTC timestamp at the beginning
            of each column (1 column), then 1 column offset."""

        self.data = data
        self.array_time_since_reference = array_time_since_reference
        self.data_length = data.shape[0]
        self.column_offset = column_offset
        self.header_timestamp = header_timestamp
        self.footer_timestamp = footer_timestamp
        self.verbose = verbose

        self.column_acceleration_N = 26 + column_offset
        self.column_acceleration_E = 27 + column_offset
        self.column_acceleration_D = 28 + column_offset
        self.column_yaw = 11 + column_offset
        self.column_pitch = 12 + column_offset
        self.column_roll = 13 + column_offset

        self.logging_frequency = 10.0
        self.time_vector_seconds = np.arange(0, self.data.shape[0] / self.logging_frequency, 1.0 / self.logging_frequency)

        self.acceleration_to_elevation()

        # self.duration_data = datetime_utils.DurationAnalyzer(self, verbose=verbose)

        # print(self.data.shape)
        # print(self.time_vector_seconds.shape)

    @property
    def acc_N(self):
        return(self.data[:, self.column_acceleration_N])

    @property
    def acc_E(self):
        return(self.data[:, self.column_acceleration_E])

    @property
    def acc_D(self):
        return(self.data[:, self.column_acceleration_D])

    @property
    def yaw(self):
        return(self.data[:, self.column_yaw])

    @property
    def pitch(self):
        return(self.data[:, self.column_pitch])

    @property
    def roll(self):
        return(self.data[:, self.column_roll])

    def plot(self):
        plt.figure()
        plt.plot(self.time_vector_seconds, self.data[:, self.column_acceleration_N], label="acceleration N (Karman filter)")
        plt.plot(self.time_vector_seconds, self.data[:, self.column_acceleration_E], label="acceleration E (Karman filter)")
        plt.plot(self.time_vector_seconds, self.data[:, self.column_acceleration_D], label="acceleration D (Karman filter)")
        plt.xlabel("time since start (s)")
        plt.ylabel("[m/s$^2$]")
        plt.legend()
        if self.header_timestamp is not None:
            plt.title("start time: {}".format(self.header_timestamp))

        plt.figure()
        plt.plot(self.time_vector_seconds, self.data[:, self.column_yaw], label="yaw")
        plt.plot(self.time_vector_seconds, self.data[:, self.column_pitch], label="pitch")
        plt.plot(self.time_vector_seconds, self.data[:, self.column_roll], label="roll")
        plt.xlabel("time since start (s)")
        plt.ylabel("degrees")
        plt.legend()
        if self.header_timestamp is not None:
            plt.title("start time: {}".format(self.header_timestamp))

        plt.figure()
        plt.plot(self.time_vector_seconds, self.elev, label="double integrated add Down auto timestamp")
        plt.plot(self.array_time_since_reference - self.array_time_since_reference[0], self.elev, label="double integrated acc Down computer timestamp")
        plt.xlabel("time since start (s)")
        plt.ylabel("[m]")
        plt.legend()
        if self.header_timestamp is not None:
            plt.title("start time: {}".format(self.header_timestamp))

        # plt.show()

    def acceleration_to_elevation(self):
        '''integrate twice using fft and ifft'''

        # calculate fft, filter, and then ifft to get heights

        # suppress divide by 0 warning
        np.seterr(divide='ignore')

        Y = np.fft.fft(self.acc_D)

        # calculate weights before applying ifft
        freq = np.fft.fftfreq(self.acc_D.size, d=1.0 / self.logging_frequency)
        weights = -1.0 / ((2 * np.pi * freq)**2)
        # need to do some filtering for low frequency (from Kohout)
        f1 = 0.03
        f2 = 0.04
        Yf = np.zeros_like(Y)
        ind = np.argwhere(np.logical_and(freq >= f1, freq <= f2))
        Yf[ind] = Y[ind] * 0.5 * (1 - np.cos(np.pi * (freq[ind] - f1) / (f2 - f1))) * weights[ind]
        Yf[freq > f2] = Y[freq > f2] * weights[freq > f2]

        # apply ifft to get height
        self.elev = np.real(np.fft.ifft(2 * Yf))


if __name__ == "__main__":
    # options
    verbose = 2
    path_to_data = '/media/jrlab/Data/data_nansen_UG/2018-09-13-14:08:12_VN100.csv'
    # path_to_data = '/media/jrlab/Data/data_nansen_UG/2018-09-13-13:45:32_VN100.csv'

    data, array_time_since_reference, header_timestamp, footer_timestamp = load_data_with_timestamps(path_to_data=path_to_data, verbose=verbose)

    imu_data_object = IMU_data(data, array_time_since_reference, header_timestamp=header_timestamp, footer_timestamp=footer_timestamp, verbose=verbose)

    # example of how to get some specific data
    # print(imu_data_object.acc_D)

    imu_data_object.plot()
    plt.show()
