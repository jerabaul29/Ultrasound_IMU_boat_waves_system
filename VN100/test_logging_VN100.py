from logging_VN100 import IMU_Logger

imu_logger = IMU_Logger(serial_port_name="/dev/ttyUSB0", file_path="/home/jrlab/Desktop/Current/UGauge", header=["\xfa", "\x14", "\x3e", "\x00", "\x3a", "\x00"])
imu_logger.log_for_duration(60)