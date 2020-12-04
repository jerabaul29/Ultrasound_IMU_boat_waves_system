from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
from printind.printind_function import printiv
from data_loader import load_data_with_timestamps
from load_UG_data import UG_data
from load_VN100_data import IMU_data
from datetime_utils import DurationAnalyzer


def aggregate_UG_VN_data(path_to_data, current_file_timestamp, lever_X_direction=2.5, lever_Z_direction=6.0, plot=1, verbose=1):
    # extensions
    extension_vn = "_VN100.csv"
    extension_ug = "_gauge.csv"

    # lever: the distance from the IMU to the pole, projected on the X direction
    lever_X_direction = lever_X_direction

    # load VN100
    path_VN100 = path_to_data + current_file_timestamp + extension_vn
    data, array_time_since_reference, header_timestamp, footer_timestamp = load_data_with_timestamps(path_VN100)
    imu_data_instance = IMU_data(data, array_time_since_reference, header_timestamp=header_timestamp, footer_timestamp=footer_timestamp, verbose=verbose)
    DurationAnalyzer(imu_data_instance, verbose=verbose)
    if plot > 1:
        imu_data_instance.plot()

    # load IMU
    path_gauge = path_to_data + current_file_timestamp + extension_ug
    data, array_time_since_reference, header_timestamp, footer_timestamp = load_data_with_timestamps(path_gauge)
    ug_data_instance = UG_data(data, array_time_since_reference, header_timestamp=header_timestamp, footer_timestamp=footer_timestamp)
    DurationAnalyzer(ug_data_instance, verbose=verbose)
    if plot > 1:
        ug_data_instance.plot()

    # generate the common time base
    min_time_base = int(max(imu_data_instance.array_time_since_reference[0], ug_data_instance.array_time_since_reference[0])) + 1.0
    max_time_base = int(min(imu_data_instance.array_time_since_reference[-1], ug_data_instance.array_time_since_reference[-1]))
    frequency_common_time_base = 10.0

    common_time_base = np.arange(min_time_base, max_time_base, 1.0 / frequency_common_time_base)

    # printiv(min_time_base)
    # printiv(max_time_base)

    # interpolate the IMU and VN signal
    interpolated_2integrated_acc_down = np.interp(common_time_base, imu_data_instance.array_time_since_reference, imu_data_instance.elev)
    interpolated_dist_ug = np.interp(common_time_base, ug_data_instance.array_time_since_reference, ug_data_instance.data_vertical_distance_self_calibration)
    interpolated_pitch = np.interp(common_time_base, imu_data_instance.array_time_since_reference, imu_data_instance.pitch)
    interpolated_roll = np.interp(common_time_base, imu_data_instance.array_time_since_reference, imu_data_instance.roll)

    """
    interpolated_2integrated_acc_down = interpolated_2integrated_acc_down - np.mean(interpolated_2integrated_acc_down)
    interpolated_dist_ug = interpolated_dist_ug - np.mean(interpolated_dist_ug)
    interpolated_pitch  = interpolated_pitch - np.mean(interpolated_pitch)
    interpolated_roll = interpolated_roll - np.mean(interpolated_roll)
    """

    # [gauge measurement] = [heigth reference] + [integrated acc up] - [elevation]
    #                     = [average heigth reference] + sin(pitch) * [lever] - [integrated acc down] - [elevation]
    # ie: [elevation] = - [integrated acc down] - [distance UGauge] + sin(pitch) * [lever]
    interpolated_pitch_elevation_effect = np.sin(np.pi / 180.0 * interpolated_pitch) * lever_X_direction
    interpolated_roll_elevation_effect = (1 - np.cos(np.pi / 180.0 * interpolated_roll)) * lever_Z_direction
    wave_elevation = - interpolated_2integrated_acc_down - interpolated_dist_ug - interpolated_pitch_elevation_effect
    # wave_elevation = wave_elevation - np.mean(wave_elevation)

    if plot > 0:
        # look at water elevation
        plt.figure()
        plt.plot(common_time_base, interpolated_2integrated_acc_down, label="interpolated 2integrated acc down", marker="*")
        # plt.plot(common_time_base, interpolated_2integrated_acc_down, label="interpolated 2integrated acc down")
        plt.plot(common_time_base, interpolated_dist_ug, label="interpolated ug distance", marker="*")
        # plt.plot(common_time_base, interpolated_dist_ug, label="interpolated ug distance")
        plt.plot(common_time_base, interpolated_pitch_elevation_effect, label="interpolated lever x sin(pitch)", marker="*")
        plt.plot(common_time_base, interpolated_roll_elevation_effect, label="interpolated lever x cos(roll)", marker="*")
        plt.plot(common_time_base, wave_elevation, label="wave elevation", marker="*")
        plt.xlabel("Time [s]")
        plt.ylabel("distance [m]")
        plt.legend()

    return(common_time_base, interpolated_pitch_elevation_effect, interpolated_2integrated_acc_down, interpolated_dist_ug, wave_elevation)


if __name__ == "__main__":

    path_to_data = "/media/jrlab/Data/data_nansen_UG/"

    # file time stamp
    # current_file_timestamp = "2018-09-14-12:26:09"
    current_file_timestamp = "2018-09-15-08:05:24"

    aggregate_UG_VN_data(path_to_data, current_file_timestamp, plot=2)
    plt.show()
