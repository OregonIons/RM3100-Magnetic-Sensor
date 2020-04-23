import Adafruit_BBIO.SPI as SPI
from Adafruit_BBIO.SPI import SPI
import time
import struct
import numpy as np
import os
class RM3100_timed():

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
		spi.writebytes([0x04, 0x03, 0x20, 0x03, 0x20, 0x03, 0x20]) # 800 cycle counts
		time.sleep(.01)
		resolution = 3.3 # nT/LSB; corresponding to 800 cycle counts
		# set sampling rate, in hertz
		rate = 32
		# display device settings
		cycleX = spi.xfer2([0x84, 0x00, 0x00])
		cycleY = spi.xfer2([0x86, 0x00, 0x00])
		cycleZ = spi.xfer2([0x88, 0x00, 0x00])
		sensor_settings1 = 'Cycle count [x, y, z]: [' + str(int(hex(cycleX[1]) + hex(cycleX[2])[2:], 16)) + ', '  + str(int(hex(cycleY[1]) + hex(cycleY[2])[2:], 16)) + ', ' + str(int(hex(cycleZ[1]) + hex(cycleZ[2])[2:], 16)) + ']'
		sensor_settings2 = 'Measurement rate: ' + str(rate) + ' Hz'
		print(sensor_settings1)
		print(sensor_settings2)

		# list of timestamps for each measurement read
		timestamp = []
		# list to store raw data
		raw = []
		# set the total measuring time, in seconds
		run_time = 30
		print('Total measuring time: ' + str(run_time) + ' seconds')
		t_end = time.time() + run_time

		# main loop
		trigger = time.time()
		while time.time() < t_end:
			timestamp.append(time.time())
			target = (len(raw) + 1) * (1/rate) + trigger
			# initiate single measurement
			spi.writebytes([0x00, 0x70])
			condition = True
			# loop to keep checking until measurement is completed
			while condition:
				# if DRDY is high (measurement is completed)
				if format(spi.xfer2([0xB4, 0x00])[1], '#010b')[2] == '1':
					# read measurement results
					raw.append(spi.xfer2([0xA4, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
					condition = False
			# if there is time remaining before next measurement
			if time.time() < target:
				# wait until appropriate time
				time.sleep(target - time.time())
			else:
				print('Timing error.')
				return

		spi.close()
		magX = []
		magY = []
		magZ = []
		magn = []
		for i in range(len(raw)):
			results = []
			for j in range(0,9,3):
				data = float(self.recast24to32(raw[i][j+1],raw[i][j+2],raw[i][j+3])) * resolution
				status = float
				results.append(data)
			magX.append(results[0])
			magY.append(results[1])
			magZ.append(results[2])
			magn.append(np.sqrt(results[0]**2 + results[1]**2 + results[2]**2))
		start_time = timestamp[0]
		time_diff = [0]
		for k in range(len(timestamp)):
			timestamp[k] = timestamp[k] - start_time
			if k > 0:
				time_diff.append(timestamp[k] - timestamp[k-1])
		mag_data = np.transpose(np.array([magX, magY, magZ, magn, timestamp, time_diff]))
		np.savetxt('mag_data_short_32Hz.txt', mag_data, header=sensor_settings1+' ; '+sensor_settings2)
		print('Successful measurement.')
		return

magf = RM3100_timed()
magf.spi()
