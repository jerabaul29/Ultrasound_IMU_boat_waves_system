# Ultrasound_IMU_boat_waves_system

Code for assembling an Ultrasonic Gauge + Inertial Motion Unit system for measurements of waves from boats.

The IMU used for ship motion correction is the VN100 from Vectornav. It is logged directly by the computer using the code in the **VN100** folder.

The Ultrasonic sensor used for measuring the wave height is the QT50ULBQ from Banner Engineering. It is logged by an Arduino, which then provides the measurements to the logging computer through USB. The code for the Arduino and computer logger modules is in the **QT50ULBQ6** folder.

Logging of both the IMU and UG is performed by the code in the **all_logging_simultaneous** folder.

Code for extracting the waves properties from the UG and IMU readings is available in the **DataAnalysis** folder.

For any question, open an issue directly on this repo.

If you find this material useful, and / or use it in your reseach, please consider citing our paper:

```
Løken, T. K., Rabault, J., Jensen, A., Sutherland, G., Christensen, K. H., & Müller, M. (2020).
Wave measurements from ship mounted sensors in the Arctic marginal ice zone.
Cold Regions Science and Technology, 103207.
```

Publisher version: https://www.sciencedirect.com/science/article/pii/S0165232X20304547 .

Preprint: https://www.researchgate.net/publication/337324692_Wave_measurements_from_ship_mounted_sensors_in_the_Arctic_marginal_ice_zone .
