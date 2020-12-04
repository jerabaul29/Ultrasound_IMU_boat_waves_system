from __future__ import print_function
import serial
import time
from logging_VN100 import display_binary_data, PatternFinder, parse_frame_vn100, print_parsed_frame_vn100, checksum_vn100
from binascii import hexlify, unhexlify
from printind.printind_function import printiv

# read from the VN100 and show in hex
serial_port = serial.Serial("/dev/ttyUSB0", baudrate=57600)

time_start = time.time()

list_binary_data = []

header_list = ["\xfa", "\x14", "\x3e", "\x00", "\x3a", "\x00"]

header_finder = PatternFinder(header_list=header_list)

crrt_frame = header_list[:]

number_of_bytes = 0

while True:
    if serial_port.in_waiting > 0:
        crrt_char = serial_port.read()
        found_header = header_finder.process_one_char(crrt_char)
        
        if found_header:
            break

while (time.time() - time_start < 1):
    if serial_port.in_waiting > 0:
        crrt_char = serial_port.read()
        number_of_bytes += 1

        crrt_frame.append(crrt_char)
        list_binary_data.append(crrt_char)

        found_header = header_finder.process_one_char(crrt_char)

        if found_header:
            printiv(number_of_bytes)
            print("found header")

            crrt_frame = crrt_frame[0: 124]

            validity_checksum = checksum_vn100(hexlify("".join(crrt_frame)))
            printiv(validity_checksum)

            display_binary_data(hexlify("".join(crrt_frame)))
            output = parse_frame_vn100(hexlify("".join(crrt_frame)))

            print_parsed_frame_vn100(output)

            crrt_frame = header_list[:]
            number_of_bytes = 0



# display_binary_data(hexlify("".join(list_binary_data)))

# find the header