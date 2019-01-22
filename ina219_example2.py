#!/usr/bin/python
from __future__ import print_function
from INA219 import INA219
import time
from datetime import datetime

def main():
	ina219 = INA219(address=0x41,debug=False);
	ina219.reset_chip()
	time.sleep(1)
	ina219.config_device()
	ina219.cal_device(device=1)

	log = open('/home/pi/iphone8_2nd_closed_wireless_samsung_charger_profile.txt','w')
	print("Time,Bus Voltage (Volts),Charge Current (mA)")
	print("Time,Bus Voltage (Volts),Charge Current (mA)", file = log)
	try:
		while True:
			bus_voltage = ina219.getBusVoltage_V()
			charge_current = ina219.getCurrent_mA()
			curtime = datetime.now().strftime("%b %d %Y %H:%M:%S")
			print("%s,%02f,%02f" % (curtime,bus_voltage,charge_current))
			print("%s,%02f,%02f" % (curtime,bus_voltage,charge_current), file = log)
			dt = datetime.now()
			time_to_sleep = 1.0 - (dt.microsecond * 0.000001)
			time.sleep(time_to_sleep)
	except KeyboardInterrupt:
		log.close()
	
if __name__ == '__main__':  
   main()
