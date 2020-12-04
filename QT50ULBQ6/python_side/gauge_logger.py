from printind.printind_function import printi, printiv
import serial
import os
from datetime import datetime
import time
import matplotlib.pyplot as plt
import numpy as np
import struct


class RingBuffer():
    "A 1D ring buffer using numpy arrays"
    def __init__(self, length):
        self.data = np.zeros(length, dtype='f')
        self.index = 0

    def extend(self, x):
        "adds array x to ring buffer"
        x_index = (self.index + np.arange(x.size)) % self.data.size
        self.data[x_index] = x
        self.index = x_index[-1] + 1

    def get(self):
        "Returns the first-in-first-out data in the ring buffer"
        idx = (self.index + np.arange(self.data.size)) % self.data.size
        return self.data[idx]


class GaugeLogger(object):
    def __init__(self, serial_port_name="/dev/ttyACM1", file_path=None, current_filename=None):
        self.SIZE_STRUCT = 10

        self.current_filename = current_filename

        self.serial_port_name = serial_port_name
        self.file_path = file_path

        # open the serial port
        self.serial_port = serial.Serial(self.serial_port_name, baudrate=57600)
        self.serial_port.flushInput()
        self.serial_port.flushOutput()
        printiv(self.serial_port_name)

        time.sleep(5)

        self.wait_for_ready()

    def wait_for_ready(self):
        while True:
            if self.serial_port.in_waiting > 0:
                crrt_char = self.serial_port.read()
                
                if crrt_char == 'S':
                    break

    def tare_gauge(self):
        printi("start taring...")
        self.serial_port.write("T")

        time.sleep(0.5)

        self.serial_port.flushInput()
        self.serial_port.flushOutput()

        self.wait_for_ready()
        
        printi("done taring...")

    def get_current_file_name(self):
        # take care of file paths
        if self.file_path is None:
            self.file_path = "~/"
        printiv(self.file_path)

        if self.current_filename is None:
            self.time_start = datetime.utcnow()
            self.file_name = self.time_start.strftime("%Y-%m-%d-%H:%M:%S") + "_gauge.csv"
        else:
            self.file_name = self.current_filename

        printiv(self.file_name)

        # full file name
        self.full_file_name = self.file_path + "/" + self.file_name
        printiv(self.full_file_name)

    def perform_one_measurement(self):
        logging_level = 0

        while True:
            if self.serial_port.in_waiting > 2 * self.SIZE_STRUCT:
                crrt_char = self.serial_port.read()

                # printiv(crrt_char)

                if crrt_char == 'L':
                    printi("WARNING: a late reading!")

                if logging_level == 0:
                    # waiting for a 'S
                    if crrt_char == 'S':
                        logging_level = 1

                if logging_level == 1:
                    # reading the measurement
                    data = self.serial_port.read(self.SIZE_STRUCT)
                    latest_values = list(struct.unpack('<LHL', data))
                    
                    next_char = self.serial_port.read()
                    if not next_char == 'E':
                        printi("Problem with end byte")
                        logging_level = 0
                    else:
                        break

        return (latest_values)

    def log_for_duration(self, duration_logging_seconds=1800, plot=True, nbr_points_plot=50*10):
        printi("start logging for {} seconds".format(duration_logging_seconds))

        number_of_measurements = 0

        time_start = time.time()

        utc_time_start = datetime.utcnow()
        printiv(utc_time_start)

        self.get_current_file_name()

        previous_latest_value_number = 0

        if plot:
            plt.ion()
            fig, ax = plt.subplots(1)
            ax.set_xlim([0, nbr_points_plot / 50.0])
            ax.set_ylim([0, 1024])

            averaged_fps = 3
            last_draw_utc = datetime.utcnow()

            ring_buffer_measurements = RingBuffer(nbr_points_plot)

        with open(self.full_file_name, 'w') as fh:
            self.serial_port.flushInput()
            self.serial_port.flushOutput()

            utc_time_start = datetime.utcnow()

            fh.write("computer utc start ")
            fh.write(utc_time_start.strftime("%Y-%m-%d-%H:%M:%S.%f"))
            fh.write("\n")
            fh.write("meas_number_computer | arduino_time_since_boot_ms | gauge_reading | arduino_measurement_nubmer\n")

            while time.time() - time_start < duration_logging_seconds:
                while self.serial_port.in_waiting > 2 * self.SIZE_STRUCT:
                    latest_values = self.perform_one_measurement()
                    # printiv(string_received)

                    fh.write(datetime.utcnow().strftime("%Y-%m-%d-%H:%M:%S.%f"))
                    fh.write(" ")
                    fh.write(str(number_of_measurements))
                    fh.write(" ")
                    fh.write(str(latest_values[0]))
                    fh.write(" ")
                    fh.write(str(latest_values[1]))
                    fh.write(" ")
                    fh.write(str(latest_values[2]))
                    fh.write("\n")

                    if previous_latest_value_number > 0 and (latest_values[2] - previous_latest_value_number) > 1:
                        printi("WARNING: missed a measurement")

                    previous_latest_value_number = latest_values[2]

                    number_of_measurements += 1

                    if plot:
                        ring_buffer_measurements.extend(np.array(latest_values[1]))

                # perform a plot with updating
                if plot:
                    title_string = ""
                    crrt_utc = datetime.utcnow()
                    averaged_fps = 0.8 * averaged_fps + 0.2 * 1.0 / (crrt_utc - last_draw_utc).total_seconds()
                    title_string += str(averaged_fps)[0: 3]
                    title_string += " averaged fps"
                    last_draw_utc = crrt_utc
                    crrt_time_elapsed_S = (crrt_utc - utc_time_start).total_seconds()
                    title_string += " | logging time "
                    title_string += str(crrt_time_elapsed_S)[0: -4]
                    title_string += " s"
                    title_string += " of {} s".format(duration_logging_seconds)

                    fig.clear()
                    plt.plot(np.arange(0, 10.0, 1/50.0), (ring_buffer_measurements.get() - 512) * 1.0 / 1024)
                    ax.set_xlim([0, nbr_points_plot])
                    ax.set_ylim([0, 1024])
                    plt.xlabel("t [s]")
                    plt.ylabel("$\eta$ [m]")
                    plt.title(title_string)
                    plt.draw()
                    plt.pause(0.05)


            utc_time_end = datetime.utcnow()
            printiv(utc_time_end)
            
            fh.write("computer utc end ")
            fh.write(utc_time_end.strftime("%Y-%m-%d-%H:%M:%S.%f"))
            fh.write(" ")

        printiv(number_of_measurements)

        expected_number_of_measurements = duration_logging_seconds * 50
        printiv(expected_number_of_measurements)

        effective_logging_frequency = number_of_measurements / (utc_time_end - utc_time_start).total_seconds()

        printiv(effective_logging_frequency)






        

        
    
