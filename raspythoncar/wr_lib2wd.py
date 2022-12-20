#!/usr/bin/python3
# -*- coding: utf-8 -*-

####  wr_lib2wd.py
####  The control library module for Raspberry Pi 2WD cars
####  2017.08  KYOHRITSU ELECTRONIC INDUSTRY CO., LTD.

from __future__ import print_function
try:
    import future_builtins
except ImportError:
    pass
import math
import sys
import signal
import time
import RPi.GPIO as gpio
from smbus import SMBus

def int12(value):
    return -(value & 0x800) | (value & 0x7ff)

def int16(value):
    return -(value & 0x8000) | (value & 0x7fff)

def signal_handler(signal, frame):
    RPI_POWER_PINS = [1, 2, 4, 6, 9, 14, 17, 20, 25, 30, 34, 39]
    RPI_FUNCTION_PINS = [3, 5, 27, 28]
    WR_UNMANAGED_PINS = [8, 10, 32, 36, 38, 40]
    pins_to_cleanup = set(range(1, 40 + 1)) - (set(RPI_POWER_PINS) | \
                      set(RPI_FUNCTION_PINS) | set(WR_UNMANAGED_PINS))
    gpio.cleanup(list(pins_to_cleanup))
    #print('wr_lib2wd: caught signal ' + str(signal) + ', quit...')
    sys.exit(0)

class WR2WD:
    I2C_BUS = 1

    @staticmethod
    def version():
        return "2018.05.28"

    class LED:
        PIN_RED = 11
        PIN_GREEN = 13
        PIN_BLUE = 15

        def __init__(self):
            pass

        def off(self):
            self.write(0, 0, 0)

        def on(self):
            self.write(1, 1, 1)

        def red(self):
            self.write(1, 0, 0)

        def green(self):
            self.write(0, 1, 0)

        def blue(self):
            self.write(0, 0, 1)

        def cyan(self):
            self.write(0, 1, 1)

        def magenta(self):
            self.write(1, 0, 1)

        def yellow(self):
            self.write(1, 1, 0)

        def white(self):
            self.write(1, 1, 1)

        def black(self):
            self.write(0, 0, 0)

        def set(self, color):
            if color is not None:
                if color == 'black':
                    self.write(0, 0, 0)
                elif color == 'red':
                    self.write(1, 0, 0)
                elif color == 'green':
                    self.write(0, 1, 0)
                elif color == 'blue':
                    self.write(0, 0, 1)
                elif color == 'cyan':
                    self.write(0, 1, 1)
                elif color == 'magenta':
                    self.write(1, 0, 1)
                elif color == 'yellow':
                    self.write(1, 1, 0)
                elif color == 'white':
                    self.write(1, 1, 1)
                else:
                    raise ValueError('unknown color name')

        def onoff(self, value):
            if value is not None:
                self.write(value, value, value)

        def write_red(self, value):
            if value is not None:
                gpio.output(self.PIN_RED, value != 0)

        def write_green(self, value):
            if value is not None:
                gpio.output(self.PIN_GREEN, value != 0)

        def write_blue(self, value):
            if value is not None:
                gpio.output(self.PIN_BLUE, value != 0)

        def write(self, red, green, blue):
            if red is not None:
                gpio.output(self.PIN_RED, red != 0)
            if green is not None:
                gpio.output(self.PIN_GREEN, green != 0)
            if blue is not None:
                gpio.output(self.PIN_BLUE, blue != 0)

        def read(self):
            result = {i: None for i in ['red', 'green', 'blue']}
            result['red'] = gpio.input(self.PIN_RED)
            result['green'] = gpio.input(self.PIN_GREEN)
            result['blue'] = gpio.input(self.PIN_BLUE)
            return result

    class ColorSensorS11059:
        ADDRESS = 0x2a
        REGS = {
            'control': 0x00,
            'timing': [0x01, 0x02],
            'timing_h': 0x01,
            'timing_l': 0x02,
            'red': [0x03, 0x04],
            'red_h': 0x03,
            'red_l': 0x04,
            'green': [0x05, 0x06],
            'green_h': 0x05,
            'green_l': 0x06,
            'blue': [0x07, 0x08],
            'blue_h': 0x07,
            'blue_l': 0x08,
            'infrared': [0x09, 0x0a],
            'infrared_h': 0x09,
            'infrared_l': 0x0a
        }
        PIN_LIGHT = 7

        def __init__(self):
            pass

        def light_on(self):
            gpio.output(self.PIN_LIGHT, 1)

        def light_off(self):
            gpio.output(self.PIN_LIGHT, 0)

        def light(self, value):
            if value is not None:
                gpio.output(self.PIN_LIGHT, value != 0)

        def read(self, address):
            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Read register byte
            result = i2c.read_byte_data(self.ADDRESS, address & 0xff)
            return result

        def write(self, address, value):
            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Write register byte
            i2c.write_byte_data(self.ADDRESS, address & 0xff, value & 0xff)

        def get_response(self):
            result = None

            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Read Device ID
            try:
                result = i2c.read_byte_data(self.ADDRESS, self.REGS['control'])
            except OSError:
                return False
            else:
                return result is not None

        def get(self, integ_time, gain=0):
            BASE_TIME = [0.175, 2.8, 44.8, 358.4]
            result = {i: None for i in ['red', 'green', 'blue', 'infrared']}
            c = 0x04
            n = 0
            tint = None

            # Check integration time
            if integ_time <= 0:
                raise ValueError('invalid integration time')

            # Find the best parameters tint and n
            for i in range(4):
                if integ_time <= BASE_TIME[i] * 65535:
                    tint = i
                    n = math.ceil(integ_time / BASE_TIME[i])
                    break
            if tint is None:
                # Error if n overflowed even with the longest tint setting
                raise ValueError('too long integration time')
            c = (c & 0xfc) | tint

            # Check gain select
            if gain == 0:
                c = c & ~0x08
            elif gain == 1:
                c = c | 0x08
            else:
                raise ValueError('invalid gain select')

            # Preserve light state and set to On
            light_state = gpio.input(self.PIN_LIGHT)
            self.light_on()

            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Reset ADC
            i2c.write_byte_data(self.ADDRESS, self.REGS['control'], \
                                c | 0x80)
            # Specify manual timing
            i2c.write_byte_data(self.ADDRESS, self.REGS['timing'][0], \
                                n >> 8)
            i2c.write_byte_data(self.ADDRESS, self.REGS['timing'][1], \
                                n & 0xff)
            # Start ADC
            i2c.write_byte_data(self.ADDRESS, self.REGS['control'], \
                                c)
            # Wait for integration
            time.sleep(4 * integ_time / 1000)
            # Poll control register to check if the data is ready
            while True:
                c = i2c.read_byte_data(self.ADDRESS, self.REGS['control'])
                if c & 0x20:
                    break
                time.sleep(0.01)
            # Read data registers
            rb = i2c.read_i2c_block_data(self.ADDRESS, \
                                         self.REGS['red'][0], 8)
            result['red'] = (rb[0] << 8) + rb[1]
            result['green'] = (rb[2] << 8) + rb[3]
            result['blue'] = (rb[4] << 8) + rb[5]
            result['infrared'] = (rb[6] << 8) + rb[7]

            # Writeback initial light state
            self.light(light_state)

            return result

    class AccelSensorADXL343:
        ADDRESS = 0x53
        REGS = {
            'dev_id': 0x00,
            'thresh_tap': 0x1d,
            'ofsx': 0x1e,
            'ofsy': 0x1f,
            'ofsz': 0x20,
            'dur': 0x21,
            'latent': 0x22,
            'window': 0x23,
            'thresh_act': 0x24,
            'thresh_inact': 0x25,
            'time_inact': 0x26,
            'act_inact_ctl': 0x27,
            'thresh_ff': 0x28,
            'time_ff': 0x29,
            'tap_axes': 0x2a,
            'act_tap_status': 0x2b,
            'bw_rate': 0x2c,
            'power_ctl': 0x2d,
            'int_enable': 0x2e,
            'int_map': 0x2f,
            'int_source': 0x30,
            'data_format': 0x31,
            'datax': [0x32, 0x33],
            'datax_0': 0x32,
            'datax_1': 0x33,
            'datay': [0x34, 0x35],
            'datay_0': 0x34,
            'datay_1': 0x35,
            'dataz': [0x36, 0x37],
            'dataz_0': 0x36,
            'dataz_1': 0x37,
            'fifo_ctl': 0x38,
            'fifo_status': 0x39
        }

        def __init__(self):
            pass

        def get_response(self):
            result = None

            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Read Device ID
            try:
                result = i2c.read_byte_data(self.ADDRESS, self.REGS['dev_id'])
            except OSError:
                return False
            else:
                return result == 0xe5

        def read(self, address):
            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Read register byte
            result = i2c.read_byte_data(self.ADDRESS, address & 0xff)
            return result

        def write(self, address, value):
            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Write register byte
            i2c.write_byte_data(self.ADDRESS, address & 0xff, value & 0xff)

        def get(self):
            result = {i: None for i in ['x', 'y', 'z']}

            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Start measurement
            i2c.write_byte_data(self.ADDRESS, self.REGS['power_ctl'], 0x08)
            # Set to Full Resolution Mode, +/- 16g range
            self.write(self.REGS['data_format'], 0x0b)
            # Read data registers
            rb = i2c.read_i2c_block_data(self.ADDRESS, \
                                         self.REGS['datax'][0], 6)
            result['x'] = int16((rb[1] << 8) + rb[0])
            result['y'] = int16((rb[3] << 8) + rb[2])
            result['z'] = int16((rb[5] << 8) + rb[4])
            return result

    class NineAxisSensorMPU9250:
        ADDRESS = 0x68
        REGS = {
            'self_test_x_gyro': 0x00,
            'self_test_y_gyro': 0x01,
            'self_test_z_gyro': 0x02,
            'self_test_x_accel': 0x0d,
            'self_test_y_accel': 0x0e,
            'self_test_z_accel': 0x0f,
            'xg_offset': [0x13, 0x14],
            'xg_offset_h': 0x13,
            'xg_offset_l': 0x14,
            'yg_offset': [0x15, 0x16],
            'yg_offset_h': 0x15,
            'yg_offset_l': 0x16,
            'zg_offset': [0x17, 0x18],
            'zg_offset_h': 0x17,
            'zg_offset_l': 0x18,
            'smplrt_div': 0x19,
            'config': 0x1a,
            'gyro_config': 0x1b,
            'accel_config': 0x1c,
            'accel_config2': 0x1d,
            'lp_accel_odr': 0x1e,
            'wom_thr': 0x1f,
            'fifo_en': 0x23,
            'i2c_mst_ctrl': 0x24,
            'i2c_slv0_addr': 0x25,
            'i2c_slv0_reg': 0x26,
            'i2c_slv0_ctrl': 0x27,
            'i2c_slv1_addr': 0x28,
            'i2c_slv1_reg': 0x29,
            'i2c_slv1_ctrl': 0x2a,
            'i2c_slv2_addr': 0x2b,
            'i2c_slv2_reg': 0x2c,
            'i2c_slv2_ctrl': 0x2d,
            'i2c_slv3_addr': 0x2e,
            'i2c_slv3_reg': 0x2f,
            'i2c_slv3_ctrl': 0x30,
            'i2c_slv4_addr': 0x31,
            'i2c_slv4_reg': 0x32,
            'i2c_slv4_do': 0x33,
            'i2c_slv4_ctrl': 0x34,
            'i2c_slv4_di': 0x35,
            'i2c_mst_status': 0x36,
            'int_pin_cfg': 0x37,
            'int_enable': 0x38,
            'int_status': 0x3a,
            'accel_xout': [0x3b, 0x3c],
            'accel_xout_h': 0x3b,
            'accel_xout_l': 0x3c,
            'accel_yout': [0x3d, 0x3e],
            'accel_yout_h': 0x3d,
            'accel_yout_l': 0x3e,
            'accel_zout': [0x3f, 0x40],
            'accel_zout_h': 0x3f,
            'accel_zout_l': 0x40,
            'temp_out': [0x41, 0x42],
            'temp_out_h': 0x41,
            'temp_out_l': 0x42,
            'gyro_xout': [0x43, 0x44],
            'gyro_xout_h': 0x43,
            'gyro_xout_l': 0x44,
            'gyro_yout': [0x45, 0x46],
            'gyro_yout_h': 0x45,
            'gyro_yout_l': 0x46,
            'gyro_zout': [0x47, 0x48],
            'gyro_zout_h': 0x47,
            'gyro_zout_l': 0x48,
            'ext_sens_data': [i for i in range(0x49, 0x60 + 1)],
            'ext_sens_data_00': 0x49,
            'ext_sens_data_01': 0x4a,
            'ext_sens_data_02': 0x4b,
            'ext_sens_data_03': 0x4c,
            'ext_sens_data_04': 0x4d,
            'ext_sens_data_05': 0x4e,
            'ext_sens_data_06': 0x4f,
            'ext_sens_data_07': 0x50,
            'ext_sens_data_08': 0x51,
            'ext_sens_data_09': 0x52,
            'ext_sens_data_10': 0x53,
            'ext_sens_data_11': 0x54,
            'ext_sens_data_12': 0x55,
            'ext_sens_data_13': 0x56,
            'ext_sens_data_14': 0x57,
            'ext_sens_data_15': 0x58,
            'ext_sens_data_16': 0x59,
            'ext_sens_data_17': 0x5a,
            'ext_sens_data_18': 0x5b,
            'ext_sens_data_19': 0x5c,
            'ext_sens_data_20': 0x5d,
            'ext_sens_data_21': 0x5e,
            'ext_sens_data_22': 0x5f,
            'ext_sens_data_23': 0x60,
            'i2c_slv0_do': 0x63,
            'i2c_slv1_do': 0x64,
            'i2c_slv2_do': 0x65,
            'i2c_slv3_do': 0x66,
            'i2c_mst_delay_ctrl': 0x67,
            'signal_path_reset': 0x68,
            'mot_detect_ctrl': 0x69,
            'user_ctrl': 0x6a,
            'pwr_mgmt_1': 0x6b,
            'pwr_mgmt_2': 0x6c,
            'fifo_count': [0x72, 0x73],
            'fifo_count_h': 0x72,
            'fifo_count_l': 0x73,
            'fifo_r_w': 0x74,
            'who_am_i': 0x75,
            'xa_offset': [0x77, 0x78],
            'xa_offset_h': 0x77,
            'xa_offset_l': 0x78,
            'ya_offset': [0x7a, 0x7b],
            'ya_offset_h': 0x7a,
            'ya_offset_l': 0x7b,
            'za_offset': [0x7d, 0x7e],
            'za_offset_h': 0x7d,
            'za_offset_l': 0x7e
        }
        COMP_ADDRESS = 0x0c
        COMP_REGS = {
            'wia': 0x00,
            'info': 0x01,
            'st1': 0x02,
            'hx': [0x03, 0x04],
            'hxl': 0x03,
            'hxh': 0x04,
            'hy': [0x05, 0x06],
            'hyl': 0x05,
            'hyh': 0x06,
            'hz': [0x07, 0x08],
            'hzl': 0x07,
            'hzh': 0x08,
            'st2': 0x09,
            'cntl1': 0x0a,
            'cntl2': 0x0b,
            'astc': 0x0c,
            'i2cdis': 0x0f,
            'asax': 0x10,
            'asay': 0x11,
            'asaz': 0x12
        }

        def __init__(self, address_bit):
            if address_bit:
                self.ADDRESS = 0x69
            else:
                self.ADDRESS = 0x68

        def read(self, address):
            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Read register byte
            result = i2c.read_byte_data(self.ADDRESS, address & 0xff)
            return result

        def write(self, address, value):
            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Write register byte
            i2c.write_byte_data(self.ADDRESS, address & 0xff, value & 0xff)

        def read_m(self, address):
            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Read register byte
            result = i2c.read_byte_data(self.COMP_ADDRESS, address & 0xff)
            return result

        def write_m(self, address, value):
            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Write register byte
            i2c.write_byte_data(self.COMP_ADDRESS, address & 0xff, value & 0xff)

        def get_response(self):
            result = None

            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Read Device ID
            try:
                result = i2c.read_byte_data(self.ADDRESS, self.REGS['who_am_i'])
            except OSError:
                return False
            else:
                return result == 0x71

        def setup_compass(self):
            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Power up magnetometer
            self.write(self.REGS['pwr_mgmt_1'], 0x00)
            self.write(self.REGS['int_pin_cfg'], 0x02)

        def get_accel(self):
            result = {i: None for i in ['x', 'y', 'z']}

            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Read data registers
            rb = i2c.read_i2c_block_data(self.ADDRESS, \
                                         self.REGS['accel_xout'][0], 6)
            result['x'] = int16((rb[0] << 8) + rb[1])
            result['y'] = int16((rb[2] << 8) + rb[3])
            result['z'] = int16((rb[4] << 8) + rb[5])
            return result

        def get_gyro(self):
            result = {i: None for i in ['x', 'y', 'z']}

            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Read data registers
            rb = i2c.read_i2c_block_data(self.ADDRESS, \
                                         self.REGS['gyro_xout'][0], 6)
            result['x'] = int16((rb[0] << 8) + rb[1])
            result['y'] = int16((rb[2] << 8) + rb[3])
            result['z'] = int16((rb[4] << 8) + rb[5])
            return result

        def get_compass(self):
            result = {i: None for i in ['x', 'y', 'z']}

            # Initialize I2C
            i2c = SMBus(WR2WD.I2C_BUS)
            # Enable continuous measurement, 16-bit output for magnetometer
            i2c.write_byte_data(self.COMP_ADDRESS, self.COMP_REGS['cntl1'], \
                                0x12)
            time.sleep(0.08)
            # Read data registers
            rb = i2c.read_i2c_block_data(self.COMP_ADDRESS, \
                                         self.COMP_REGS['hx'][0], 6)
            result['x'] = int16((rb[1] << 8) + rb[0])
            result['y'] = int16((rb[3] << 8) + rb[2])
            result['z'] = int16((rb[5] << 8) + rb[4])
            return result

    class MotorControl:
        PIN_LEFT_FORWARD = 37
        PIN_LEFT_REVERSE = 35
        PIN_RIGHT_FORWARD = 31
        PIN_RIGHT_REVERSE = 33
        PIN_PWM = 12
        PWM_FREQUENCY = 50

        class Driver2P:
            def __init__(self, pin_fwd, pin_rev):
                self.pin_forward = pin_fwd
                self.pin_reverse = pin_rev

            def set(self, mode):
                if mode is not None:
                    if mode == 'stop':
                        self.write(0, 0)
                    elif mode == 'forward':
                        self.write(1, 0)
                    elif mode == 'reverse':
                        self.write(0, 1)
                    elif mode == 'brake':
                        self.write(1, 1)
                    else:
                        raise ValueError('unknown mode')

            def write(self, fwd, rev):
                if fwd is not None:
                    gpio.output(self.pin_forward, fwd != 0)
                if rev is not None:
                    gpio.output(self.pin_reverse, rev != 0)

        def __init__(self):
            self.left = self.Driver2P(self.PIN_LEFT_FORWARD, \
                                      self.PIN_LEFT_REVERSE)
            self.right = self.Driver2P(self.PIN_RIGHT_FORWARD, \
                                       self.PIN_RIGHT_REVERSE)

        def setup_pwm(self):
            self.pwm = gpio.PWM(self.PIN_PWM, self.PWM_FREQUENCY)
            self.pwm.start(100.0)

        def cleanup_pwm(self):
            self.pwm.stop()

        def stop(self):
            self.left.write(0, 0)
            self.right.write(0, 0)

        def front(self):
            self.left.write(1, 0)
            self.right.write(1, 0)

        def front_tl(self):
            self.left.write(0, 0)
            self.right.write(1, 0)

        def front_tr(self):
            self.left.write(1, 0)
            self.right.write(0, 0)

        def back(self):
            self.left.write(0, 1)
            self.right.write(0, 1)

        def back_tl(self):
            self.left.write(0, 0)
            self.right.write(0, 1)

        def back_tr(self):
            self.left.write(0, 1)
            self.right.write(0, 0)

        def turn_left(self):
            self.left.write(0, 1)
            self.right.write(1, 0)

        def turn_right(self):
            self.left.write(1, 0)
            self.right.write(0, 1)

        def brake(self):
            self.left.write(1, 1)
            self.right.write(1, 1)

        def set(self, left, right):
            lb = (None, None)
            rb = (None, None)

            if left is not None:
                if left == 'stop':
                    lb = (0, 0)
                elif left == 'forward':
                    lb = (1, 0)
                elif left == 'reverse':
                    lb = (0, 1)
                elif left == 'brake':
                    lb = (1, 1)
                else:
                    raise ValueError('unknown mode')
            if right is not None:
                if right == 'stop':
                    rb = (0, 0)
                elif right == 'forward':
                    rb = (1, 0)
                elif right == 'reverse':
                    rb = (0, 1)
                elif right == 'brake':
                    rb = (1, 1)
                else:
                    raise ValueError('unknown mode')
            self.write(lb[0], lb[1], rb[0], rb[1])

        def write(self, left_fwd, left_rev, right_fwd, right_rev):
            self.left.write(left_fwd, left_rev)
            self.right.write(right_fwd, right_rev)

        def read(self):
            result = {i: None for i in \
                      ['left_fwd', 'left_rev', 'right_fwd', 'right_rev']}
            result['left_fwd'] = gpio.input(self.PIN_LEFT_FORWARD)
            result['left_rev'] = gpio.input(self.PIN_LEFT_REVERSE)
            result['right_fwd'] = gpio.input(self.PIN_RIGHT_FORWARD)
            result['right_rev'] = gpio.input(self.PIN_RIGHT_REVERSE)
            return result

        def speed(self, value):
            if value is not None:
                if value < 0.0:
                    value = 0.0
                if value > 100.0:
                    value = 100.0
                self.pwm.ChangeDutyCycle(value)

    class Microphone:
        PIN_MIC0 = 26

        def __init__(self):
            pass

        def read(self):
            return gpio.input(self.PIN_MIC0) == 0

        def listen(self, timeout, break_on_detect=False):
            result = False
            ts = time.time()

            while time.time() - ts < timeout:
                if gpio.input(self.PIN_MIC0) != 0:
                    result = True
                    if break_on_detect != 0:
                        break
            return result

    class PhotoSensor:
        PIN_LED = {
            'front': 21,
            'left': 29,
            'right': 16,
            'bottom': 22
        }
        PIN_SENS = {
            'front': 19,
            'left': 23,
            'right': 18,
            'bottom': 24
        }
        DEFAULT_DELAY = 0.004
        DISTURBANCE_CHECK_DURATION = 0.02
        ERROR_RATE_THRESHOLD = 0.01

        def __init__(self):
            self.set_delay(self.DEFAULT_DELAY)

        def get_delay(self):
            return self.delay
        def set_delay(self, value):
            if value < 0.0:
                raise ValueError('invalid delay time')
            else:
                self.delay = value

        def __get(self, pos):
            gpio.output(self.PIN_LED[pos], 1)
            time.sleep(self.delay)
            result = gpio.input(self.PIN_SENS[pos]) == 0
            gpio.output(self.PIN_LED[pos], 0)
            return result

        def __get_dd(self, pos, error_rate):
            gpio.output(self.PIN_LED[pos], 0)
            check_count = 0
            check_errors = 0
            t_start = time.time()
            while time.time() < t_start + self.DISTURBANCE_CHECK_DURATION:
                check_count += 1
                if gpio.input(self.PIN_SENS[pos]) == 0:
                    check_errors += 1
                time.sleep(0.0)
            if error_rate <= 0.0:
                if check_errors > 0:
                    return None
            else:
                if check_errors / check_count >= error_rate:
                    return None
            gpio.output(self.PIN_LED[pos], 1)
            time.sleep(self.delay)
            result = gpio.input(self.PIN_SENS[pos]) == 0
            gpio.output(self.PIN_LED[pos], 0)
            return result

        def front(self):
            return self.__get('front')

        def left(self):
            return self.__get('left')

        def right(self):
            return self.__get('right')

        def bottom(self):
            return self.__get('bottom')

        def read(self):
            result = {i: None for i in ['front', 'left', 'right', 'bottom']}
            result['front'] = self.front()
            result['left'] = self.left()
            result['right'] = self.right()
            result['bottom'] = self.bottom()
            return result

        def front_dd(self, error_rate=0.01):
            return self.__get_dd('front', error_rate)

        def left_dd(self, error_rate=0.01):
            return self.__get_dd('left', error_rate)

        def right_dd(self, error_rate=0.01):
            return self.__get_dd('right', error_rate)

        def bottom_dd(self, error_rate=0.01):
            return self.__get_dd('bottom', error_rate)

        def read_dd(self, error_rate=0.01):
            result = {i: None for i in ['front', 'left', 'right', 'bottom']}
            result['front'] = self.front_dd(error_rate)
            result['left'] = self.left_dd(error_rate)
            result['right'] = self.right_dd(error_rate)
            result['bottom'] = self.bottom_dd(error_rate)
            return result

    def __init__(self):
        # Instanciate subclasses
        self.led = self.LED()
        self.cs = self.ColorSensorS11059()
        self.acs = self.AccelSensorADXL343()
        self.nxs0 = self.NineAxisSensorMPU9250(0)
        self.nxs1 = self.NineAxisSensorMPU9250(1)
        self.mc = self.MotorControl()
        self.ps = self.PhotoSensor()
        self.mic = self.Microphone()

        # IO pins used in this lib
        self.INPUT_FLOAT_PINS = [
            self.mic.PIN_MIC0,
            self.ps.PIN_SENS['front'],
            self.ps.PIN_SENS['left'],
            self.ps.PIN_SENS['right'],
            self.ps.PIN_SENS['bottom']
        ]
        self.INPUT_PULLUP_PINS = [
        ]
        self.OUTPUT_LOW_PINS = [
            self.led.PIN_RED,
            self.led.PIN_GREEN,
            self.led.PIN_BLUE,
            self.cs.PIN_LIGHT,
            self.mc.PIN_LEFT_FORWARD,
            self.mc.PIN_LEFT_REVERSE,
            self.mc.PIN_RIGHT_FORWARD,
            self.mc.PIN_RIGHT_REVERSE,
            self.ps.PIN_LED['front'],
            self.ps.PIN_LED['left'],
            self.ps.PIN_LED['right'],
            self.ps.PIN_LED['bottom']
        ]
        self.OUTPUT_HIGH_PINS = [
            self.mc.PIN_PWM
        ]
        # Attach callback function for signals
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        # Initialize GPIO
        gpio.setwarnings(False)
        gpio.setmode(gpio.BOARD)
        # Setup each input/output pins
        gpio.setup(self.INPUT_FLOAT_PINS, gpio.IN)
        gpio.setup(self.INPUT_PULLUP_PINS, gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.setup(self.OUTPUT_LOW_PINS, gpio.OUT, initial=gpio.LOW)
        gpio.setup(self.OUTPUT_HIGH_PINS, gpio.OUT, initial=gpio.HIGH)
        # Setup PWM for motor control
        self.mc.setup_pwm()

    def cleanup(self):
        self.mc.cleanup_pwm()
        gpio.cleanup(self.INPUT_FLOAT_PINS)
        gpio.cleanup(self.INPUT_PULLUP_PINS)
        gpio.cleanup(self.OUTPUT_LOW_PINS)
        gpio.cleanup(self.OUTPUT_HIGH_PINS)
