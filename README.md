# RM3100-Magnetic-Sensor

rm3100_timed_measurements.py contains the code stored on the Beaglebone, which is used to take timed single measurements.

rm3100_continuous_measurements.py contains the code stored on the Beaglebone, which is used to take continuous
measurements at a set sampling rate.

rm3100_adev.ipynb contains the analysis of data taken using both timed and continuous measurements. This is a work in
progress, and will be updated regularly.

mag_data_short.txt is the data file for timed measurements.
mag_data.txt is the data file for a continuous measurement.

The columns of these two data files are:
magX | magY | magZ | magn | time | Δt


error_log.txt is the data file containing timing errors for mag_data.txt. It contains the timestamps at which the DRDY
pin was high for consecutive measurement reads, indicating that it may have missed a data point.
