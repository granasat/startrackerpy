#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author's code: https://github.com/RolfBly/DS1621/blob/master/DS1621.py
# The file has been adapted to our needs, basically encapsulating the
# funtionalities into a class and removing its main method.
# DS1621 manual: https://datasheets.maximintegrated.com/en/ds/DS1621.pdf
#
# We have also added the LSM303 library with a class wrapper.

from __future__ import division  # to calculate a float from integers
import smbus
import time
import Adafruit_LSM303
import os


class DS1621:
    """ Example:
    from lib.sensors import DS1621

    ds_sensor = DS1621(1, 0x48)
    ds_sensor.wake_up()
    ds_sensor.read_config()
    """
    # DS1621 commands
    START = 0xEE
    STOP = 0x22
    READ_TEMP = 0xAA
    READ_COUNTER = 0xA8
    READ_SLOPE = 0xA9
    ACCESS_CONFIG = 0xAC
    ACCESS_TH = 0xA1
    ACCESS_TL = 0xA2

    # read-only status bits
    DONE = 0x80
    TH_BIT = 0x40
    TL_BIT = 0x20
    NVB = 0x10  # Non-Volatile memory Busy

    # r/w status bits (bit masks)
    POL_HI = 0x02
    POL_LO = 0xFD
    ONE_SHOT = 0x01
    CONT_MODE = 0xFE
    CLR_TL_TH = 0x9F

    def __init__(self, bus_id, sensor):
        self.bus = smbus.SMBus(bus_id)
        self.sensor = sensor

    # assist functions
    def twos_comp(self, byte):
        """ Input byte in two's complement is returned as signed integer.
        """
        if len(bin(byte)[2:]) > 8:
            # shouldn't ever get here
            print('\nWarning: input ' + str(hex(byte)) +
                  ' truncated to least significant byte: ' +
                  str(hex(0xFF & byte)))
            byte = 0xFF & byte

        return ~(255 - byte) if byte > 127 else byte

    def decode_DS(self, word):
        """ 2-byte data from DS1621 is received as LSB MSB
        MSB is a two's complement number from -55 to +125
        If leftmost bit from LSB is set, add .5 to reading.
        """

        LSB = word // 256  # integer division with two
        MSB = word % 256
        value = self.twos_comp(MSB)

        return value + .5 if LSB == 128 else value + .0

    def encode_DS(self, num):
        """ 2-byte thermostat setting sent to DS1621
        in same format as data received, see decode_DS, above.
        """
        # warn for out of range and set within range.
        if num < -55:
            print('\nWarning: input ' + str(num) + ' out of range, set to -55')
            num = -55
        if num > 125:
            print('\nWarning: input ' + str(num) + ' out of range, set to 125')
            num = 125

        # round off to nearest .5
        num = round(num*2)/2.0
        MSB = int(num)
        decimal = num - MSB

        # LSB is binary 1000.0000 if decimal = .5, otherwise 0
        # data is sent LSB MSB
        if decimal == 0:
            return MSB
        else:
            if MSB > 0:
                return MSB | 0x8000
            else:
                return (MSB - 1) & 0x80FF

    # General read function, also updates a register
    def read_degreesC_byte(self):
        """ Returns temperature in degrees Celsius as integer
        """
        self.bus.read_byte_data(self.sensor, self.START)
        degreesC_byte = self.twos_comp(
            self.bus.read_byte_data(self.sensor, self.READ_TEMP)
        )

        return degreesC_byte

    # Oneshot read functions all give a START command.
    def read_degreesC_all_oneshot(self):
        """returns temperature in degrees Celsius,
        as integer,
        as same reading with added half degree precision
        and with high(er) resolution, as per DS1621 datasheet """

        self.bus.read_byte_data(self.sensor, self.START)

        degreesC_byte = self.twos_comp(
            self.bus.read_byte_data(self.sensor, self.READ_TEMP)
        )
        degreesC_word = self.decode_DS(
            self.bus.read_word_data(self.sensor, self.READ_TEMP)
        )
        slope = self.bus.read_byte_data(self.sensor, self.READ_SLOPE)
        counter = self.bus.read_byte_data(self.sensor, self.READ_COUNTER)
        degreesC_HR = degreesC_byte - .25 + (slope - counter)/slope
        # ~ print slope, counter, slope - counter, (slope - counter)/slope

        return degreesC_byte, degreesC_word, degreesC_HR

    def read_degreesC_hiRes_oneshot(self):
        """returns temperature as high-res value, as per DS1621 datasheet"""

        self.bus.read_byte_data(self.sensor, self.START)

        degreesC_byte = self.twos_comp(
            self.bus.read_byte_data(self.sensor, self.READ_TEMP)
        )

        slope = self.bus.read_byte_data(self.sensor, self.READ_SLOPE)
        counter = self.bus.read_byte_data(self.sensor, self.READ_COUNTER)
        degreesC_HR = degreesC_byte - .25 + (slope - counter)/slope

        return degreesC_HR

    # Continuous read function DOES NOT give a START command
    # the START command for Continuous mode is given by set_mode(Continous)
    def read_degreesC_continous(self):
        """returns temperature in degrees Celsius,
        as integer,
        as same reading with added half degree precision
        and with high(er) resolution, as per DS1621 datasheet """

        degreesC_byte = self.twos_comp(
            self.bus.read_byte_data(self.sensor, self.READ_TEMP)
        )
        degreesC_word = self.decode_DS(
            self.bus.read_word_data(self.sensor, self.READ_TEMP)
        )
        slope = self.bus.read_byte_data(self.sensor, self.READ_SLOPE)
        counter = self.bus.read_byte_data(self.sensor, self.READ_COUNTER)
        degreesC_HR = degreesC_byte - .25 + (slope - counter)/slope

        return degreesC_byte, degreesC_word, degreesC_HR

    # Continuous mode needs a stop-conversion command
    def stop_conversion(self):
        self.bus.read_byte_data(self.sensor, self.STOP)

    def read_config(self):
        Conf = self.bus.read_byte_data(self.sensor, self.ACCESS_CONFIG)

        TH = self.decode_DS(
            self.bus.read_word_data(self.sensor, self.ACCESS_TH)
        )
        TL = self.decode_DS(
            self.bus.read_word_data(self.sensor, self.ACCESS_TL)
        )

        if Conf & self.POL_HI:
            level, device = 'HIGH', 'cooler'
        else:
            level, device = 'LOW', 'heater'

        Rpt = '''\n  Status of DS1621 at address {sensor}:
        \tConversion is {convstat}
        \t{have_th} measured {th} degrees Celsius or more
        \t{have_tl} measured below {tl} degrees Celsius
        \tNon-volatile memory is {busy}
        \tThermostat output is Active {level} (1 turns the {device} on)
        \tMeasuring mode is {mode}'''

        print(Rpt.format(
            sensor=hex(self.sensor),
            convstat='done' if Conf & self.DONE else 'in process',
            have_th='HAVE' if Conf & self.TH_BIT else 'have NOT',
            th=TH,
            have_tl='HAVE' if Conf & self.TL_BIT else 'have NOT',
            tl=TL,
            busy='BUSY' if Conf & self.NVB else 'not busy',
            level=level,
            device=device,
            mode='One-Shot' if Conf & self.ONE_SHOT else 'Continuous',
        ))

        return Conf, TH, TL

    def get_thermostat(self):
        """returns low and high thermostat settings"""
        low_therm = self.decode_DS(
            self.bus.read_word_data(self.sensor, self.ACCESS_TL)
        )
        hi_therm = self.decode_DS(
            self.bus.read_word_data(self.sensor, self.ACCESS_TH)
        )

        return low_therm, hi_therm

    # write helper
    def wait_NVM(self):
        newConf = self.bus.read_byte_data(self.sensor, self.ACCESS_CONFIG)
        # wait for write to Non-Volatile Memory to finish
        while newConf & self.NVB:
            newConf = self.bus.read_byte_data(self.sensor, self.ACCESS_CONFIG)

        return

    def write_conf_byte(self, byte):
        self.bus.write_byte_data(self.sensor, self.ACCESS_CONFIG, byte)
        self.wait_NVM(self.bus, self.sensor)

        return

    def set_thermostat(self, lower, upper):
        """ set new lower and upper thermostat limits for thermostat pin
        in non-volatile memory; also reset TH and TH bits.
        """
        self.bus.write_word_data(self.sensor, self.ACCESS_TL,
                                 self.encode_DS(lower))
        self.bus.write_word_data(self.sensor, self.ACCESS_TH,
                                 self.encode_DS(upper))
        self.wait_NVM()

        Conf = self.bus.read_byte_data(self.sensor, self.ACCESS_CONFIG) \
            & self.CLR_TL_TH
        self.write_conf_byte(Conf)

        # take a reading to update the thermostat register
        self.read_degreesC_byte()

        return

    def set_thermohyst(self, upper, hyst=0.5):
        """ set upper temp with a hysteresis for thermostat pin
        and reset TH and TH bits.
        """
        self.set_thermostat(upper - hyst, upper)

        return

    def set_mode(self, mode):
        if mode == 'Continuous':
            Conf = self.bus.read_byte_data(self.sensor, self.ACCESS_CONFIG) \
                & self.CONT_MODE
            self.write_conf_byte(Conf)
            self.bus.read_byte_data(self.sensor, self.START)

        elif mode == 'OneShot':
            Conf = self.bus.read_byte_data(self.sensor, self.ACCESS_CONFIG) \
                | self.ONE_SHOT
            self.write_conf_byte(Conf)
        else:
            print('Unknown mode: {}'.format(mode))

        return

    def set_thermoLOW(self, LOW=True):
        Conf = self.bus.read_byte_data(self.sensor, self.ACCESS_CONFIG)
        Conf = Conf & self.POL_LO if LOW else Conf | self.POL_HI

        self.write_conf_byte(Conf)

        # take a reading to update the thermostat register
        self.read_degreesC_byte()

        return

    def read_logline(self, name):
        reading = self.read_degreesC_all_oneshot()

        return '\tSensor name: {:8} {:3} | {:5.1f} | {:7.3f}'.format(
            name, *reading
        )

    def wake_up(self):
        """ Device always starts in Idle mode, first reading is not usable.
        """
        self.read_degreesC_byte()
        time.sleep(0.6)


class LSM303:
    def __init__(self):
        self.sensor = Adafruit_LSM303.LSM303()

    def read_accel(self):
        return self.sensor.read()[0]

    def read_mag(self):
        return self.sensor.read()[1]


class CPU_SENSOR:
    def read_temp(self):
        """ Returns the CPU temperature"""
        temp = os.popen("vcgencmd measure_temp").readline()

        return (float(temp.replace("temp=", "")[0:4]))
