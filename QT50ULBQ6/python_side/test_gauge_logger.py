import gauge_logger

gauge_logger_instance = gauge_logger.GaugeLogger(file_path="/home/jrlab/Desktop/Current/UGauge")
gauge_logger_instance.tare_gauge()
gauge_logger_instance.log_for_duration(duration_logging_seconds=25)