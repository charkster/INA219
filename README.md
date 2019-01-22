INA219 Log Battery Voltage and Charge Current to file

These 3 python files will allow you to use a INA219 board (like the ones on adafruit and amazon) to log voltage and current to both the screen and a file once every second.
I use this to monitor my batteries as they charge.

INA219.py          <- this is the python class to communicate with the INA219 board
rpi_i2c_new.py     <- this is the raspberry pi I2C that adds additional debugging and has bit field operations
ina219_example2.py <- this is the top-level script that initializes the INA219 board and defines the file to log to

I replace the sense resistor on my INA219 boards with a 10milli ohm resistor as to not have a large voltage drop when charge currents reach 2-3amps.
To obtain the needed calibration value (see the cal_device routine) I use a 40 Ohm 2W resistor and use a 5V power supply. I modify the calibration code until I see the proper 125milli amp result.
Manual calibration allows you to get the best calibration code for your specific sample resistor.

To stop the logging just press control-c. 

For measuring charge current for a phone I cut a usb c type cable to put the VBUS wires through the INA219 terminal. A connection to GND is needed for the voltage measurement.
