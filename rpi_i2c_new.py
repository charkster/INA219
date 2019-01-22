#!/usr/bin/python
import smbus, re

# ===========================================================================
# rpi_i2c Class
# ===========================================================================
bus = smbus.SMBus(1)
class rpi_i2c(object):

	@staticmethod
	def getPiRevision():
		"Gets the version number of the Raspberry Pi board"
		# Revision list available at: http://elinux.org/RPi_HardwareHistory#Board_Revision_History
		try:
			with open('/proc/cpuinfo', 'r') as infile:
				for line in infile:
					# Match a line of the form "Revision : 0002" while ignoring extra
					# info in front of the revsion (like 1000 when the Pi was over-volted).
					match = re.match('Revision\s+:\s+.*(\w{4})$', line)
					if match and match.group(1) in ['0000', '0002', '0003']:
						# Return revision 1 if revision ends with 0000, 0002 or 0003.
						return 1
					elif match:
						# Assume revision 2 if revision ends with any other 4 chars.
						return 2
						# Couldn't find the revision, assume revision 0 like older code for compatibility.
			return 0
		except:
			return 0

	@staticmethod
	def getPii2cBusNumber():
		# Gets the i2c bus number /dev/i2c#
		return 1 if rpi_i2c.getPiRevision() > 1 else 0

	def __init__(self, address, busnum=-1, debug=False, name="", quiet=0):
		self.address = address
		# By default, the correct i2c bus is auto-detected using /proc/cpuinfo
		# Alternatively, you can hard-code the bus version below:
		# self.bus = smbus.SMBus(0); # Force i2c0 (early 256MB Pi's)
		# self.bus = smbus.SMBus(1); # Force i2c1 (512MB Pi's)
		self.bus = smbus.SMBus(busnum if busnum >= 0 else rpi_i2c.getPii2cBusNumber())
		self.debug = debug
		self.name = name
		self.quiet = quiet

	def reverseByteOrder(self, data):
		"Reverses the byte order of an int (16-bit) or long (32-bit) value"
		# Courtesy Vishal Sapre
		byteCount = len(hex(data)[2:].replace('L','')[::2])
		val       = 0
		for i in range(byteCount):
			val    = (val << 8) | (data & 0xff)
			data >>= 8
		return val

	def errMsg(self):
		print "Error accessing 0x%02X: Check your i2c address" % self.address
		return -1

	def write8(self, reg, value):
		"Writes an 8-bit value to the specified register/address"
		try:
			self.bus.write_byte_data(self.address, reg, value)
			if self.debug:
				print "i2c: Wrote 0x%02X to register 0x%02X" % (value, reg)
		except IOError, err:
			return self.errMsg()

	def write_quick(self):
		"Writes an 8-bit value to the specified register/address"
		try:
			self.bus.write_quick(self.address)
			if self.debug:
				print "i2c: Wrote to device address 0x%02X" % (self.address)
		except IOError, err:
			return self.errMsg()

	def write16(self, reg, value):
		"Writes a 16-bit value to the specified register/address pair"
		try:
			self.bus.write_word_data(self.address, reg, value)
			if self.debug:
				print ("i2c: Wrote 0x%02X to register pair 0x%02X,0x%02X" % (value, reg, reg+1))
		except IOError, err:
			return self.errMsg()

	def writeRaw8(self, value):
		"Writes an 8-bit value on the bus"
		try:
			self.bus.write_byte(self.address, value)
			if self.debug:
				print "i2c: Wrote 0x%02X" % value
		except IOError, err:
			return self.errMsg()

	def writeList(self, reg, list):
		try:
			if self.debug:
				print "i2c: Writing list to register 0x%02X:" % reg
				print list
			self.bus.write_i2c_block_data(self.address, reg, list)
		except IOError, err:
			return self.errMsg()

	def readList(self, reg, length):
		"Read a list of bytes from the i2c device"
		if (length > 32):
			print "Length is greater than maximum 32 bytes"
			return []
		try:
			results = self.bus.read_i2c_block_data(self.address, reg, length)
			if self.debug:
				print ("i2c: Device 0x%02X returned the following from reg 0x%02X" % (self.address, reg))
				print results
			return results
		except IOError, err:
			return self.errMsg()

	def readU8(self, reg):
		"Read an unsigned byte from the i2c device"
		try:
			result = self.bus.read_byte_data(self.address, reg)
			if self.debug:
				print ("i2c: Device 0x%02X returned 0x%02X from reg 0x%02X" % (self.address, result & 0xFF, reg))
			return result
		except IOError, err:
			return self.errMsg()

	def readS8(self, reg):
		"Reads a signed byte from the i2c device"
		try:
			result = self.bus.read_byte_data(self.address, reg)
			if result > 127: result -= 256
			if self.debug:
				print ("i2c: Device 0x%02X returned 0x%02X from reg 0x%02X" % (self.address, result & 0xFF, reg))
			return result
		except IOError, err:
			return self.errMsg()

	def readU16(self, reg, little_endian=True):
		"Reads an unsigned 16-bit value from the i2c device"
		try:
			result = self.bus.read_word_data(self.address,reg)
			# Swap bytes if using big endian because read_word_data assumes little 
			# endian on ARM (little endian) systems.
			if not little_endian:
				result = ((result << 8) & 0xFF00) + (result >> 8)
			if (self.debug):
				print "i2c: Device 0x%02X returned 0x%04X from reg 0x%02X" % (self.address, result & 0xFFFF, reg)
			return result
		except IOError, err:
			return self.errMsg()

	def readS16(self, reg, little_endian=True):
		"Reads a signed 16-bit value from the i2c device"
		try:
			result = self.readU16(reg,little_endian)
			if result > 32767: result -= 65536
			return result
		except IOError, err:
			return self.errMsg()

	def read_addr16_byte(self, addr16):
		a1=addr16/256
		a0=addr16%256
		self.bus.write_i2c_block_data(self.address, a1, [a0])
		return self.bus.read_byte(self.address)

	def writeList16(self, addr16, list):
		"Writes an array of bytes using i2c format"
		try:
			a1=addr16/256
			a0=addr16%256
			if self.debug:
				print "i2c: Writing list to register 0x%04X:" % addr16
			print list
			list.insert(0,a0)
			self.bus.write_i2c_block_data(self.address, a1, list)
		except IOError, err:
			return self.errMsg()

#########################################################
# Prefered functions, renamed versions of the ones above
# with new reg_field and bit_field classes defined below
#########################################################

# Bit Field class, this can be a single bit or up to 8bits in width
#	class bf_type:
#		NAME = ""
#		ADDR = 0x00
#		OTPADDR = 0x00
#		RST_VAL = 0x0
#		BIT_MASK = 0b00000000
#		SIM_MASK = 0b00000000
#		CONFIG_MASK = 0b00000000
#		WIDTH = 0
#		OFFSET = 0
#		ACCESS = ""

# Register class, this is an 8bit value with a single unique address
#	class reg_type:
#		NAME = ""
#		ADDR = 0x00
#		OTPADDR = 0x00
#		RST_VAL = 0x0
#		OTP_DFLT = 0x0
#		BIT_MASK = 0b00000000
#		OTP_MASK = 0b00000000
#		SIM_MASK = 0b00000000
#		CONFIG_MASK = 0b00000000
  
	def i2c_write(self, reg_field, wdata):
		try:
			self.bus.write_byte_data(self.address, reg_field.ADDR, wdata)
			if (self.debug or self.quiet != 1):
				print "Writing %s Register %s, Address x%02x, Data x%02x" % (self.name, reg_field.NAME, reg_field.ADDR, wdata)
		except IOError, err:
			return self.errMsg()

	def i2c_read(self, reg_field):
		try:
			read_data = self.bus.read_byte_data(self.address, reg_field.ADDR)
			if (self.debug or self.quiet != 1):
				print "Read %s Register %s, Address x%02x, value is x%02x" % (self.name, reg_field.NAME, reg_field.ADDR, read_data)
			return read_data
		except IOError, err:
			return self.errMsg()
			
	def i2c_read_check(self, reg_field, exp_value):
		try:
			read_data = self.bus.read_byte_data(self.address, reg_field.ADDR)
			if (self.debug or self.quiet != 1):
				print "Read and Checked %s Register %s, Address x%02x, value is x%02x" % (self.name, reg_field.NAME, reg_field.ADDR, read_data)
			if (read_data != exp_value):
				print "FAIL!!! Expected value of 0x%02x does not match actual value of 0x%02x for Register %s" % (exp_value,read_data,reg_field.NAME)
			return read_data
		except IOError, err:
			return self.errMsg()
      
	def i2c_bf_read(self, bit_field):
		try:
			bf_read_data = ( self.bus.read_byte_data(self.address, bit_field.ADDR) & bit_field.BIT_MASK ) >> bit_field.OFFSET
			if (self.debug or self.quiet != 1):
				print "Read %s bit_field %s value is x%02x" % (self.name, bit_field.NAME, bf_read_data)
			return bf_read_data
		except IOError, err:
			return self.errMsg()
			
	def i2c_bf_read_check(self, bit_field, exp_value):
		try:
			bf_read_data = ( self.bus.read_byte_data(self.address, bit_field.ADDR) & bit_field.BIT_MASK ) >> bit_field.OFFSET
			if (self.debug or self.quiet != 1):
				print "Read and Checked %s bit_field %s value is x%02x" % (self.name, bit_field.NAME, bf_read_data)
			if (bf_read_data != exp_value):
				print "FAIL!!! Expected value of 0x%02x does not match actual value of 0x%02x for bit_field %s" % (exp_value,bf_read_data,bit_field.NAME)
			return bf_read_data
		except IOError, err:
			return self.errMsg()

	def i2c_bf_get(self, bit_field):
		try:
			bf_read_data = ( self.bus.read_byte_data(self.address, bit_field.ADDR) & bit_field.BIT_MASK ) >> bit_field.OFFSET
			if (self.debug):
				print "Read %s bit_field %s value is x%02x" % (self.name, bit_field.NAME, bf_read_data)
			return bf_read_data
		except IOError, err:
			return self.errMsg()

	def i2c_bf_write(self, bit_field, bf_wdata):
		try:
			wdata = (self.bus.read_byte_data(self.address, bit_field.ADDR) & ~bit_field.BIT_MASK) | ((bf_wdata << bit_field.OFFSET) & bit_field.BIT_MASK)
			self.bus.write_byte_data(self.address, bit_field.ADDR, wdata)
			if (self.debug or self.quiet != 1):
				print "Wrote %s bit_field %s data x%02x" % (self.name, bit_field.NAME, bf_wdata)
		except IOError, err:
			return self.errMsg()

	def i2c_bf_event_clear(self, bit_field):
		try:
			if ( (self.bus.read_byte_data(self.address, bit_field.ADDR) & bit_field.BIT_MASK ) >> bit_field.OFFSET ):
				wdata = (0x01 << bit_field.OFFSET) & bit_field.BIT_MASK
				self.bus.write_byte_data(self.address, bit_field.ADDR, wdata)
				print "Cleared %s event %s" % (self.name, bit_field.NAME)
			else:
				print "Asked to clear %s event %s, but it is not set" % (self.name, bit_field.NAME)
		except IOError, err:
			return self.errMsg()

	def i2c_scan_unlock(self):
		try:
			self.write_quick()
			if (self.debug or self.quiet != 1):
				print "\nWrite Quick sent with device address x%02x" % self.address
		except IOError, err:
			return self.errMsg()
		
	def i2c_raw_write(self, wadd, wdata):
		try:
			self.bus.write_byte_data(self.address, wadd, wdata)
			if (self.debug or self.quiet != 1):
				print "Writing to %s, Address x%02x, Data x%02x" % (self.name, wadd, wdata)
		except IOError, err:
			return self.errMsg()
	
	def i2c_raw_read(self, addr):
		try:
			read_data = self.bus.read_byte_data(self.address, addr)
			if (self.debug or self.quiet != 1):
				print "Read %s register 0x%02x and data is 0x%02x" % (self.name, addr, read_data)
			return read_data
		except IOError, err:
			return self.errMsg()
	
	def i2c_raw_get(self, addr):
		try:
			read_data = self.bus.read_byte_data(self.address, addr)
			if (self.debug or self.quiet != 1):
				print "Read %s register 0x%02x and data is 0x%02x" % (self.name, addr, read_data)
			return read_data
		except IOError, err:
			return self.errMsg()

if __name__ == '__main__':
  try:
    bus = rpi_i2c(address=0)
    print "Default i2c bus is accessible"
  except:
    print "Error accessing default i2c bus"
