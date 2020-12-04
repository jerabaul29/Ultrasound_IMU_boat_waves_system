from __future__ import print_function
import serial
from datetime import datetime
from printind.printind_function import printiv, printi
import time
from binascii import hexlify, unhexlify
from crcmod import mkCrcFun
import numpy as np
from struct import unpack
import matplotlib.pyplot as plt

crc16 = mkCrcFun(0x11021, 0x0000, False, 0x0000)

# length of one binary dataframe
length_binary_frame = 124
# number of 4 bits floating points in one frame
number_of_VN100_fields = 29


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


def checksum_vn100(binary_data):
    """
    checksum binary_data
    """

    crc1 = np.int('0x' + binary_data[-4:], 16)
    crc2 = crc16(unhexlify(binary_data[2:-4]))
    if crc1 == crc2:
        return True
    else:
        return False


def display_binary_data(binary_data):
    """
    Display some binary data in hex format
    """

    print("Print binary data")

    length_data = len(binary_data)
    print("Length of binary data as ASCII: " + str(length_data))

    str_print = ""

    for ind in range(int(length_data / 2)):
        str_print += binary_data[2 * ind:2 * ind + 2]
        str_print += " "

    print(str_print)


def parse_frame_vn100(data_frame, verbose=0):
    """
    parse one VN100 checksummed frame
    """

    output = np.zeros((number_of_VN100_fields,))

    for ind_data in range(number_of_VN100_fields):
        ind_float_start = 8 + 4 + 4 * 2 * ind_data
        ind_float_final = ind_float_start + 4 * 2
        current_binary_bytes = data_frame[ind_float_start:ind_float_final]

        if verbose > 5:
            print("Parsing bytes:")
            display_binary_data(current_binary_bytes)

        current_value = np.float(unpack('<f', unhexlify(current_binary_bytes))[0])
        output[ind_data] = current_value

    if verbose > 5:
        print("Parsed VN100 data frame")
        print(output)

    return output


def print_parsed_frame_vn100(output):
    """
    user friendly print of VN100 parsed data
    """

    # Mag
    print(output[0:3])
    # Accel
    print(output[3:6])
    # Gyro
    print(output[6:9])
    # Temp
    print(output[9])
    # Pres
    print(output[10])
    # YawPitchRoll
    print(output[11:14])
    # DCM
    print(output[14:23].reshape((3, 3)))
    # MagNed
    print(output[23:26])
    # AccNed
    print(output[26:29])


class PatternFinder(object):
    def __init__(self, header_list=None):
        self.header_list = header_list
        self.length_header = len(self.header_list)
        self.current_position = 0

    def reset(self):
        self.current_position = 0

    def process_one_char(self, crrt_char):
        if self.header_list[self.current_position] == crrt_char:
            self.current_position += 1
        else:
            self.current_position = 0

        if self.current_position == self.length_header:
            self.reset()

            return(True)
        else:
            return(False)



class IMU_Logger(object):
    def __init__(self, serial_port_name="/dev/USB0", file_path=None, header=["\xfa", "\x14", "\x3e", "\x00", "\x3a", "\x00"], current_filename=None):
        self.serial_port_name = serial_port_name
        self.file_path = file_path
        self.current_filename = current_filename

        self.header = header

        self.header_finder = PatternFinder(self.header)

        # open the serial port
        self.serial_port = serial.Serial(self.serial_port_name, baudrate=57600)
        self.serial_port.flushInput()
        self.serial_port.flushOutput()
        printiv(self.serial_port_name)

        time.sleep(5)

    def get_current_file_name(self):
        # take care of file paths
        if self.file_path is None:
            self.file_path = "~/"
        printiv(self.file_path)

        if self.current_filename is None:
            self.time_start = datetime.utcnow()
            self.file_name = self.time_start.strftime("%Y-%m-%d-%H:%M:%S") + "_VN100.csv"
        else:
            self.file_name = self.current_filename

        printiv(self.file_name)

        # full file name
        self.full_file_name = self.file_path + "/" + self.file_name
        printiv(self.full_file_name)

    def reset_until_header(self):
        while True:
            if self.serial_port.in_waiting > 0:
                crrt_char = self.serial_port.read()
                found_header = self.header_finder.process_one_char(crrt_char)

                if found_header:
                    break

    def perform_one_measurement(self):
        crrt_frame = self.header[:]

        while True:
            crrt_char = self.serial_port.read()

            crrt_frame.append(crrt_char)

            found_header = self.header_finder.process_one_char(crrt_char)

            if found_header:
                crrt_frame = crrt_frame[0: 124]

                validity_checksum = checksum_vn100(hexlify("".join(crrt_frame)))

                if not validity_checksum:
                    printi("Unvalid checksum!")
                    printi("catch one more measurement")
                    return(self.perform_one_measurement())


                output = parse_frame_vn100(hexlify("".join(crrt_frame)))

                crrt_frame = self.header[:]

                return(output)

    def log_for_duration(self, duration_logging_seconds=1800, plot=True, nbr_points_plot=10*10):
        printi("start logging for {} seconds".format(duration_logging_seconds))

        number_of_measurements = 0

        time_start = time.time()

        utc_time_start = datetime.utcnow()
        printiv(utc_time_start)

        self.get_current_file_name()

        if plot:
            plt.ion()
            fig, ax = plt.subplots(1)
            ax.set_xlim([0, nbr_points_plot])
            ax.set_ylim([0, 1024])

            averaged_fps = 3
            last_draw_utc = datetime.utcnow()

            ring_buffer_measurements_accD = RingBuffer(nbr_points_plot)

        with open(self.full_file_name, 'w') as fh:
            utc_time_start = datetime.utcnow()

            fh.write("computer utc start ")
            fh.write(utc_time_start.strftime("%Y-%m-%d-%H:%M:%S.%f"))
            fh.write("\n")
            fh.write("MagX, MagY, MagZ, AccX, AccY, AccZ, GyroX, GyroY, GyroZ, Temp, Pres, Yaw, Pitch, Roll, DCM1, DCM2, DCM3, DCM4, DCM5, DCM6, DCM7, DCM8, DCM9, MagNED1, MagNED2, MagNED3, AccNED1, AccNED2, ACCNED3 \n")

            self.serial_port.flushInput()
            self.serial_port.flushOutput()
            self.reset_until_header()


            while time.time() - time_start < duration_logging_seconds:
                while self.serial_port.in_waiting > 248:
                    output = self.perform_one_measurement()

                    number_of_measurements += 1

                    for crrt_value in output:
                        fh.write(str(crrt_value))
                        fh.write(" ")
                    fh.write("\n")

                    if plot:
                        ring_buffer_measurements_accD.extend(np.array(output[28]))

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
                    plt.plot(np.arange(0, 10.0, 1/10.0), ring_buffer_measurements_accD.get())
                    ax.set_xlim([0, nbr_points_plot / 10.0])
                    plt.xlabel("t [s]")
                    plt.ylabel("ACC Down [m/s$^2$]")
                    # ax.set_ylim([0, 1024])
                    plt.title(title_string)
                    plt.draw()
                    plt.pause(0.05)

            utc_time_end = datetime.utcnow()
            printiv(utc_time_end)

            fh.write("computer utc end ")
            fh.write(utc_time_end.strftime("%Y-%m-%d-%H:%M:%S.%f"))
            fh.write(" ")

        printiv(number_of_measurements)

        expected_number_of_measurements = duration_logging_seconds * 10
        printiv(expected_number_of_measurements)

        effective_logging_frequency = number_of_measurements / (utc_time_end - utc_time_start).total_seconds()

        printiv(effective_logging_frequency)


