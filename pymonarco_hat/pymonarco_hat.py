import ctypes

class _monarco_struct_sdc_t(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('value', ctypes.c_uint16),
              ('address', ctypes.c_uint16, 12),
              ('write', ctypes.c_uint8, 1),
              ('error', ctypes.c_uint8, 1),
              ('reserved', ctypes.c_uint8, 2), ]


class _monarco_struct_control_byte_t(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('status_led_en', ctypes.c_uint8, 1),
                ('status_led_on ', ctypes.c_uint8, 1),
                ('ow_shutdown ', ctypes.c_uint8, 1),
                ('reserved1', ctypes.c_uint8, 1),
                ('cnt1_reset', ctypes.c_uint8, 1),
                ('cnt2_reset', ctypes.c_uint8, 1),
                ('sign_of_life', ctypes.c_uint8, 2), ]


class _monarco_struct_status_byte_t(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('reserved1', ctypes.c_uint8, 4),
                ('cnt1_reset_done', ctypes.c_uint8, 1),
                ('cnt2_reset_done', ctypes.c_uint8, 1),
                ('sign_of_life', ctypes.c_uint8, 2), ]


class _monarco_struct_tx_t(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('sdc_req', _monarco_struct_sdc_t),
                ('control_byte', _monarco_struct_control_byte_t),
                ('led_en', ctypes.c_uint8),
                ('led_on', ctypes.c_uint8),
                ('dout', ctypes.c_uint8),
                ('pwm1_div', ctypes.c_uint16),
                ('pwm1a_dc', ctypes.c_uint16),
                ('pwm1b_dc', ctypes.c_uint16),
                ('pwm1c_dc', ctypes.c_uint16),
                ('pwm2_div', ctypes.c_uint16),
                ('pwm2a_dc', ctypes.c_uint16),
                ('aout1', ctypes.c_uint16),
                ('aout2', ctypes.c_uint16),
                ('crc', ctypes.c_uint16), ]


class _monarco_struct_rx_t(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('sdc_resp', _monarco_struct_sdc_t),
                ('status_byte', _monarco_struct_status_byte_t),
                ('reserved1', ctypes.c_uint16),
                ('din', ctypes.c_uint8),
                ('cnt1', ctypes.c_uint32),
                ('cnt2', ctypes.c_uint32),
                ('cnt3', ctypes.c_uint32),
                ('ain1', ctypes.c_uint16),
                ('ain2', ctypes.c_uint16),
                ('crc', ctypes.c_uint16), ]


class _monarco_sdc_item_t(ctypes.Structure):
    _fields_ = [('address', ctypes.c_uint16),
                ('value', ctypes.c_uint16),
                ('factor', ctypes.c_int),
                ('counter', ctypes.c_int),
                ('busy', ctypes.c_int),
                ('write', ctypes.c_uint8, 1),
                ('request', ctypes.c_uint8, 1),
                ('done', ctypes.c_uint8, 1),
                ('error', ctypes.c_uint8, 1), ]


class _monarco_cxt_t(ctypes.Structure):
    _fields_ = [('platform', ctypes.c_void_p),
                ('tx_data', _monarco_struct_tx_t),
                ('rx_data', _monarco_struct_rx_t),
                ('spi_fd', ctypes.c_int),
                ('sdc_size', ctypes.c_int),
                ('sdc_idx', ctypes.c_int),
                ('sdc_items', _monarco_sdc_item_t*256),
                ('err_throttle_crc', ctypes.c_int), ]


class Monarco:
    def __init__(self, lib_path, spi_interface, spi_clock, debug_print_prefix):
        self.__monarco = ctypes.CDLL(lib_path)
        self.__cxt = _monarco_cxt_t()
        self.__monarco.monarco_init(ctypes.pointer(self.__cxt), spi_interface, spi_clock, debug_print_prefix)
        self.__cxt.tx_data.led_en = ctypes.c_uint8(0)  # Disable control over LEDs

    def set_analog_out(self, port, value):
        if port == 1:
            self.__cxt.tx_data.aout1 = self.__monarco.monarco_util_aout_volts_to_u16(ctypes.c_double(value))
            return True
        elif port == 2:
            self.__cxt.tx_data.aout2 = self.__monarco.monarco_util_aout_volts_to_u16(ctypes.c_double(value))
            return True

        return False

    def set_digital_out(self, port, value):
        if not 1 <= port <= 4:
            return False

        if value > 1:
            value = 1
        if value < 0:
            value = 0

        if value == 0:
            self.__cxt.tx_data.dout = ctypes.c_uint8(self.__cxt.tx_data.dout & ~(1 << port-1))
        elif value == 1:
            self.__cxt.tx_data.dout = ctypes.c_uint8(self.__cxt.tx_data.dout | (1 << port-1))
        return True

    def set_pwm_frequency(self, channel,  freq):
        if channel == 1:  # DOUT 1, 2, 3
            self.__cxt.tx_data.pwm1_div = self.__monarco.monarco_util_pwm_freq_to_u16(ctypes.c_double(freq))
            return True
        elif channel == 2:  # DOUT 4
            self.__cxt.tx_data.pwm2_div = self.__monarco.monarco_util_pwm_freq_to_u16(ctypes.c_double(freq))
            return True
        return False

    def set_pwm_out(self, output, value):
        if output == 1:
            self.__cxt.tx_data.pwm1a_dc = self.__monarco.monarco_util_pwm_dc_to_u16(ctypes.c_double(value))
        elif output == 2:
            self.__cxt.tx_data.pwm1b_dc = self.__monarco.monarco_util_pwm_dc_to_u16(ctypes.c_double(value))
        elif output == 3:
            self.__cxt.tx_data.pwm1c_dc = self.__monarco.monarco_util_pwm_dc_to_u16(ctypes.c_double(value))
        elif output == 4:
            self.__cxt.tx_data.pwm2a_dc = self.__monarco.monarco_util_pwm_dc_to_u16(ctypes.c_double(value))

    def update(self):
        return self.__monarco.monarco_main(ctypes.pointer(self.__cxt))

    def get_analog_in(self, port):
        if port == 1:
            return self.__cxt.rx_data.ain1 * 10.0/4095.0
        elif port == 2:
            return self.__cxt.rx_data.ain2 * 10.0/4095.0
        else:
            return -1.0

    def get_digital_in(self, port):
        if not 1 <= port <= 4:
            return -1

        return self.__cxt.rx_data.din & (1 << port-1)

    def close(self):
        self.__monarco.monarco_exit(ctypes.pointer(self.__cxt))


