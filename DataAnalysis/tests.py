import numpy as np
import matplotlib.pyplot as plt


def acceleration_to_elevation(acc_D, logging_frequency):
    '''integrate twice using fft and ifft'''

    # calculate fft, filter, and then ifft to get heights

    # suppress divide by 0 warning
    np.seterr(divide='ignore')

    Y = np.fft.fft(acc_D)

    # calculate weights before applying ifft
    freq = np.fft.fftfreq(acc_D.size, d=1.0 / logging_frequency)
    weights = -1.0 / ((2 * np.pi * freq)**2)
    # need to do some filtering for low frequency (from Kohout)
    f1 = 0.03
    f2 = 0.04
    Yf = np.zeros_like(Y)
    ind = np.argwhere(np.logical_and(freq >= f1, freq <= f2))
    Yf[ind] = Y[ind] * 0.5 * (1 - np.cos(np.pi * (freq[ind] - f1) / (f2 - f1))) * weights[ind]
    Yf[freq > f2] = Y[freq > f2] * weights[freq > f2]

    # apply ifft to get height
    elev = -np.real(np.fft.ifft(2 * Yf))

    return(elev)


logging_frequency = 10.0
wave_amplitude = 0.5
wave_frequency = 0.2
duration_signal = 300
omega = 2 * np.pi * wave_frequency

time_array = np.arange(0, duration_signal, 1.0/logging_frequency)
wave_elevation = wave_amplitude * np.cos(omega * time_array)
wave_acceleration = - wave_amplitude * omega**2 * np.cos(omega * time_array)

integrated_acceleration = acceleration_to_elevation(wave_acceleration, logging_frequency)

plt.figure()
plt.plot(wave_elevation)
plt.plot(integrated_acceleration)
plt.show()
