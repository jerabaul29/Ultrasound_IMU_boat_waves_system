import sys
import os
import multiprocessing
from datetime import datetime

pwd = os.getcwd()

sys.path.append(pwd + "/../VN100/")
from logging_VN100 import IMU_Logger

sys.path.append(pwd + "/../QT50ULBQ6/python_side/")
import gauge_logger

# some parameters
duration_logging_s = 120
tare_ugauge = True

# get file name
crrt_time = datetime.utcnow()
file_name = crrt_time.strftime("%Y-%m-%d-%H:%M:%S")

# prepare u gauge
gauge_logger_instance = gauge_logger.GaugeLogger(serial_port_name="/dev/ttyACM1",
                                                 file_path="/home/jrlab/Desktop/Current/UGauge",
                                                 current_filename=file_name + "_gauge.csv")
if tare_ugauge:
    gauge_logger_instance.tare_gauge()

# prepare VN100
imu_logger = IMU_Logger(serial_port_name="/dev/ttyUSB0",
                        file_path="/home/jrlab/Desktop/Current/UGauge",
                        current_filename=file_name + "_VN100.csv",
                        header=["\xfa", "\x14", "\x3e", "\x00", "\x3a", "\x00"])

def thrd_VN100():
    imu_logger.log_for_duration(duration_logging_s)

def thrd_UG():
    gauge_logger_instance.log_for_duration(duration_logging_s)

thread_VN100 = multiprocessing.Process(target=thrd_VN100)
thread_UG = multiprocessing.Process(target=thrd_UG)

thread_VN100.start()
thread_UG.start()

thread_VN100.join()
thread_UG.join()