from __future__ import print_function
from printind.printind_function import printiv
from scipy import integrate
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from aggregate_IMU_UG import aggregate_UG_VN_data


def find_min_gt_index_in_ordered_array(array, value_test):
    for i, value in enumerate(array):
        if value > value_test:
            return(i)
    return(None)


def welch_spectrum(data_in, sampling_rate, min_frq, max_frq, plot=0, overlap_proportion=0.9, segment_duration_seconds=600, label="", smooth=True):
    nperseg = int(segment_duration_seconds * sampling_rate)
    noverlap = int(overlap_proportion * nperseg)

    f, Pxx_den = signal.welch(data_in, sampling_rate, nperseg=nperseg, noverlap=noverlap)

    if smooth:
        Pxx_den = signal.savgol_filter(Pxx_den, window_length=21, polyorder=2)

    min_ind = find_min_gt_index_in_ordered_array(f, min_frq)
    max_ind = find_min_gt_index_in_ordered_array(f, max_frq)

    if plot > 0:
        plt.plot(f[min_ind: max_ind], Pxx_den[min_ind: max_ind], label=label)

    return(f[min_ind: max_ind], Pxx_den[min_ind: max_ind])


def compute_SWH(elevation, verbose=2):
        """Compute SWH using double integration of vertical acceleration."""

        # SWH
        SWH = 4.0 * np.std(elevation)

        if verbose > 1:
            print("SWH = {} m".format(SWH))

        return(SWH)


def compute_wave_spectrum_moments(wave_spectrum, list_frequencies, verbose=2):
    """Compute the moments of the wave spectrum."""

    omega = 2 * np.pi * list_frequencies
    # note: integrate only on the 'valid' part of the spectrum

    M0 = integrate.trapz(wave_spectrum, x=omega)
    M1 = integrate.trapz(wave_spectrum * (omega), x=omega)
    M2 = integrate.trapz(wave_spectrum * (omega**2), x=omega)
    M3 = integrate.trapz(wave_spectrum * (omega**3), x=omega)
    M4 = integrate.trapz(wave_spectrum * (omega**4), x=omega)
    MM1 = integrate.trapz(wave_spectrum * (omega**(-1)), x=omega)
    MM2 = integrate.trapz(wave_spectrum * (omega**(-2)), x=omega)

    if verbose > 2:
        print('min, max of freq is {}, {}'.format(list_frequencies.min(), list_frequencies.max()))
        print('f shape is {}'.format(list_frequencies.shape))

    return(M0, M1, M2, M3, M4, MM1, MM2)


def compute_spectral_properties(M0, M2, M4, wave_spectrum, list_frequencies, verbose=2):
    """Compute SWH and the peak period, both zero up-crossing and peak-to-peak,
    from spectral moments."""

    Hs = np.sqrt(M0) * 4.0 / np.sqrt(2 * np.pi)
    T_z = 2.0 * np.pi * np.sqrt(M0 / M2)
    T_c = 2.0 * np.pi * np.sqrt(M2 / M4)
    T_p = 1.0 / list_frequencies[np.argmax(wave_spectrum)]

    if verbose > 1:
        print('Hs (from M0) = {} m'.format(Hs))
        print('T_z = {} s | {} Hz'.format(T_z, 1.0 / T_z))
        # print('T_c = {} s | {} Hz'.format(T_c, 1.0 / T_c))
        print('T_p = {} s | {} Hz'.format(T_p, 1.0 / T_p))

    return(Hs, T_z, T_c, T_p)


if __name__ == "__main__":
    path_to_data = "/media/jrlab/Data/data_nansen_UG/"

    # file time stamp
    # current_file_timestamp = "2018-09-14-12:26:09"
    # current_file_timestamp = "2018-09-14-12:51:19"
    # current_file_timestamp = "2018-09-14-14:53:40"  # A nice example at sea, when boat at rest: no saturation in this set.
    current_file_timestamp = "2018-09-15-08:05:24"

    printiv(current_file_timestamp)

    common_time_base, interpolated_pitch_elevation_effect, interpolated_2integrated_acc_down, interpolated_dist_ug, wave_elevation = aggregate_UG_VN_data(path_to_data, current_file_timestamp, plot=1, verbose=0)

    plot = 1
    sampling_rate = 10.0
    min_frq = 0.04
    max_frq = 2.0

    plt.figure()
    f_elev, Pxx_elev = welch_spectrum(wave_elevation, sampling_rate, min_frq, max_frq, plot=plot, label="wave elevation")
    welch_spectrum(interpolated_2integrated_acc_down, sampling_rate, min_frq, max_frq, plot=plot, label="boat vertical acceleration")
    welch_spectrum(interpolated_dist_ug, sampling_rate, min_frq, max_frq, plot=plot, label="u gauge reading")
    welch_spectrum(interpolated_pitch_elevation_effect, sampling_rate, min_frq, max_frq, plot=plot, label="pitch effect")
    plt.xlabel("f [Hz]")
    plt.ylabel("PSD$_{\eta}$ [kg m$^2$ s$^{-1}$]")
    plt.legend()
    plt.title("Wave spectrum at {}".format(current_file_timestamp[:-3]))

    # a few statistics
    compute_SWH(wave_elevation)
    M0, M1, M2, M3, M4, MM1, MM2 = compute_wave_spectrum_moments(Pxx_elev, f_elev)
    compute_spectral_properties(M0, M2, M4, Pxx_elev, f_elev)

    plt.show()
