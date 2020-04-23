import Adafruit_BBIO.SPI as SPI
from Adafruit_BBIO.SPI import SPI
import time
import struct
import numpy as np
import os
class RM3100_cont():

	def __init__(self):
		self.mode = 0
	def recast24to32(self,byte0,byte1,byte2):
		# pack 24 bits (3 bytes) into 32 bits byte-type
		b24 = struct.pack('xBBB',byte0,byte1,byte2)

		# unpack to unsigned long integer
		uL = struct.unpack('>L',b24)[0]

		# this is for 2's complement signed numbers - if negative assign sign bits for 32 bit case
		if (uL & 0x00800000):
			uL = uL | 0xFF000000

		# repack as 32 bit unsigned long byte-type
		packed = struct.pack('>L', uL)
		# unpack as 32 bit signed long integer
		unpacked = struct.unpack('>l', packed)[0]

		return unpacked
	def spi(self):
		spi = SPI(1,0)
		spi.mode = self.mode
		spi.cshigh = False
		spi.msh = 1000000
		spi.bpw = 8
		spi.lsbfirst = False
		spi.open(1,0)

		# set cycle counts
		spi.writebytes([0x04, 0x03, 0xE8, 0x03, 0xE8, 0x03, 0xE8]) # 1000 cycle counts
		time.sleep(.01)
		# set continuous measurement mode
		spi.writebytes([0x01, 0x79])
		time.sleep(.01)
		# set measurement rate
		spi.writebytes([0x0B, 0x95])
		time.sleep(.01)
		resolution = 2.7 # nT/LSB; corresponding to 800 cycle counts
		# display device settings
		cycleX = spi.xfer2([0x84, 0x00, 0x00])
		cycleY = spi.xfer2([0x86, 0x00, 0x00])
		cycleZ = spi.xfer2([0x88, 0x00, 0x00])
		sensor_settings1 = 'Cycle count [x, y, z]: [' + str(int(hex(cycleX[1]) + hex(cycleX[2])[2:], 16)) + ', '  + str(int(hex(cycleY[1]) + hex(cycleY[2])[2:], 16)) + ', ' + str(int(hex(cycleZ[1]) + hex(cycleZ[2])[2:], 16)) + ']'
		sensor_settings2 = 'Measurement rate: ' + hex(spi.xfer2([0x8B, 0x00])[1])
		print(sensor_settings1)
		print(sensor_settings2)

		# list of timestamps for each measurement read
		timestamp = []
		# list to check for rate errors: use this list to display an error if there are consecutive measurements where DRDY (status) is high.
		error_check = []
		# list to store the time values corresponding to each error
		error_log = []
		# list to store export data
		mag_data = []
		# set the total measuring time, in seconds
		run_time = 10
		print('Total measuring time: ' + str(run_time) + ' seconds')
		t_end = time.time() + run_time

		# Main loop
		while time.time() < t_end:
			# if the DRDY (status) pin is high
			if format(spi.xfer2([0xB4, 0x00])[1], '#010b')[2] == '1':
				# append appropriate values to lists
				timestamp.append(time.time())
				error_check.append(1)
				# read measurement results
				raw = spi.xfer2([0xA4, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
				results = []
				for i in range(0,9,3):
					data = float(self.recast24to32(raw[i+1],raw[i+2],raw[i+3]))*resolution
					status = float
					results.append(data)
				magXYZ = results
				magn = np.sqrt(magXYZ[0]**2 + magXYZ[1]**2 + magXYZ[2]**2)
				# if mag_data already contains some data
				if len(mag_data) > 0:
					# if DRDY was high two times in a row
					if error_check[-2] == 1:
						# store and display the error
						error_log.append(timestamp[-1]-timestamp[0])
						print('Error at t = '+ str(error_log[-1])  +': Consecutive iterations with DRDY high.')
					# append results to mag_data
					mag_data = np.vstack((mag_data, np.array([magXYZ[0], magXYZ[1], magXYZ[2], magn, timestamp[-1]-timestamp[0], timestamp[-1]-timestamp[-2]])))
				# if mag_data contains nothing
				else:
					# create first line in mag_data
					mag_data = np.array([magXYZ[0], magXYZ[1], magXYZ[2], magn, 0, 0])
			# if the DRDY pin was NOT high
			else:
				# store appropriate value in error_check
				error_check.append(0)

		spi.close()

		# if mag_data is empty, display error
		if len(mag_data) == 0:
			print('Error: DRDY never went high.')
			return

		# save data as txt file
		np.savetxt('mag_data_short.txt', mag_data, header=sensor_settings1+' ; '+sensor_settings2, comments='')
		# if there was a rate error -> save an additional txt file containing the corresponding time values
		if len(error_log) > 0:
			error_log = np.array(error_log)
			np.savetxt('error_log_short.txt', error_log, header='Time values for which DRDY was high for consecutive measurements')
			print('Successful measurement, with DRDY errors.')
			return
		print('Successful measurement.')
		return

magf = RM3100_cont()
magf.spi()
