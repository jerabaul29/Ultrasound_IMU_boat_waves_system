from __future__ import print_function
import datetime
from dateutil import parser
from printind.printind_function import printiv


def timestamp_from_filename(filename, verbose=0):
    # filename_modified = filename.replace("_", " ")[0:-4]
    datetime_object = parser.parse(filename, ignoretz=True)

    if verbose > 1:
        print("filename: {}".format(filename))
        print("timestamp: {}".format(datetime_object))

    return(datetime_object)


def seconds_between_datetimes(datetime_start, datetime_end):
    return((datetime_end - datetime_start).total_seconds())


class DurationAnalyzer(object):
    def __init__(self, data_object, verbose=0):
        self.data_object = data_object

        self.timestamp_start = timestamp_from_filename(data_object.header_timestamp, verbose=verbose)
        self.timestamp_end = timestamp_from_filename(data_object.footer_timestamp)

        self.duration_seconds = seconds_between_datetimes(self.timestamp_start, self.timestamp_end)
        self.empirical_logging_frequency = 1.0 * data_object.data_length / self.duration_seconds

        self.empirical_logging_frequency_error = (self.empirical_logging_frequency - data_object.logging_frequency) / data_object.logging_frequency

        self.expected_duration = data_object.data_length * 1.0 / data_object.logging_frequency
        self.empirical_logging_time_error_seconds = (self.expected_duration - self.duration_seconds)
        self.empirical_logging_time_error_samples = self.empirical_logging_time_error_seconds * data_object.logging_frequency

        if verbose > 1:
            printiv(self.empirical_logging_frequency)
            printiv(self.empirical_logging_frequency_error)
            printiv(self.empirical_logging_time_error_seconds)
            printiv(self.empirical_logging_time_error_samples)

if __name__ == "__main__":
    test_string_timestamp = "2018-09-13-14:14:29.297802"
    timestamp_1 = timestamp_from_filename(test_string_timestamp, verbose=2)
    test_string_timestamp = "2018-09-13-15:14:29.297802"
    timestamp_2 = timestamp_from_filename(test_string_timestamp, verbose=2)
    duration = seconds_between_datetimes(timestamp_1, timestamp_2)
    print(duration)
