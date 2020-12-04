# Ultrasound_IMU_boat_waves_system

Code for assembling an Ultrasonic Gauge + Inertial Motion Unit system for measurements of waves from boats

The IMU used for ship motion correction is the VN100 from Vectornav. It is logged directly by the computer using the code in the **VN100** folder.

The Ultrasonic sensor used for measuring the wave height is the QT50ULBQ from Banner Engineering. It is logged by an Arduino, which then provides the measurements to the logging computer through USB. The code for the Arduino and computer logger modules is in the **QT50ULBQ6** folder.

Logging of both the IMU and UG is performed by the code in the **all_logging_simultaneous** folder.

Code for extracting the waves properties from the UG and IMU readings is available in the **DataAnalysis** folder.

For any question, open an issue directly on this repo.

