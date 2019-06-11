import ctypes
import threading
import time


class _monarco_struct_sdc_t(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('value', ctypes.c_uint16),
                ('address', ctypes.c_uint16, 12),
                ('write', ctypes.c_uint8, 1),
                ('error', ctypes.c_uint8, 1),
                ('reserved', ctypes.c_uint8, 2), ]


class _monarco_struct_control_byte_t(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('status_led_mask', ctypes.c_uint8, 1),
                ('status_led_value ', ctypes.c_uint8, 1),
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
                ('led_mask', ctypes.c_uint8),
                ('led_value', ctypes.c_uint8),
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


MONARCO_DPF_ERROR = 0x01
MONARCO_DPF_WARNING = 0x02
MONARCO_DPF_INFO = 0x04
MONARCO_DPF_VERB = 0x08
MONARCO_DPF_READ = 0x10
MONARCO_DPF_WRITE = 0x20

DOUT1 = 1
DOUT2 = 2
DOUT3 = 3
DOUT4 = 4

DIN1 = 1
DIN2 = 2
DIN3 = 3
DIN4 = 4

PWM_CHANNEL1 = 1
PWM_CHANNEL2 = 2

LOW = 0
HIGH = 1

AOUT1 = 1
AOUT2 = 2

AIN1 = 1
AIN2 = 2


class Monarco(threading.Thread):
    def __init__(self, lib_path, spi_interface='/dev/spidev0.0', spi_clock=4000000,
                 dprint_prefix='', debug_flag=0, cycle_interval=0.01,
                 ain_configs = {"ain1":"v", "ain2":"v"}):
        """
        Initiate Monarco HAT shield, start thread for writing to IO.
        :param lib_path: Path to Monarco-HAT lib file (eg. /path/to/lib/libmonarco.so)
        :param spi_interface: Raspberry Pi SPI interface used to communicate with shield
        :param spi_clock: SPI clock speed in hz
        :param dprint_prefix: Prefix string to debug functionality
        :param debug_flag: Debug data to print (e.g debug_flag = MONARCO_DPF_ERROR | MONARCO_DPF_WARNING), for printing
        errors and warnings
        :param cycle_interval: How often to read/write PLC IO in seconds.
        :param ain_configs: Set device to measure Volt or Ampere ("v" or "a")
        """

        self.__monarco = ctypes.CDLL(lib_path)
        self.__cxt = _monarco_cxt_t()
        self.__monarco.set_dprint_flag(debug_flag)
        self.__monarco.monarco_init(ctypes.pointer(self.__cxt), ctypes.c_char_p(spi_interface.encode('utf-8')),
                                    ctypes.c_uint32(spi_clock), ctypes.c_char_p(dprint_prefix.encode('utf-8')))

        # Set configuration for Analog Inputs
        self._ain_configs = ain_configs
        self.set_config(ain_configs)

        threading.Thread.__init__(self)
        self.cycle_interval = cycle_interval
        self.__mutex = threading.Lock()
        self.daemon = True
        self.start()

    def run(self):
        while True:
            with self.__mutex:
                self.__monarco.monarco_main(ctypes.pointer(self.__cxt))
            time.sleep(self.cycle_interval)

    def set_config(self, conf):
        """Configure analog inputs to read Volt or Ampere

        See the Monarco C driver complex example for more information

        :param conf: Dictionary with keys ain1 and ain2 to specify measurement unit
        """
        # Status code
        self.__cxt.sdc_items[0] = _monarco_sdc_item_t(address = int('0000', 2), factor=1)

        # Firmware Version
        self.__cxt.sdc_items[1] = _monarco_sdc_item_t(address = int('0001', 2), request=1)
        self.__cxt.sdc_items[2] = _monarco_sdc_item_t(address = int('0010', 2), request=1)

        # Hardware Version
        self.__cxt.sdc_items[3] = _monarco_sdc_item_t(address = int('0011', 2), request=1)
        self.__cxt.sdc_items[4] = _monarco_sdc_item_t(address = int('0100', 2), request=1)

        # MCU ID
        self.__cxt.sdc_items[5] = _monarco_sdc_item_t(address = int('0101', 2), request=1)
        self.__cxt.sdc_items[6] = _monarco_sdc_item_t(address = int('0110', 2), request=1)
        self.__cxt.sdc_items[7] = _monarco_sdc_item_t(address = int('0111', 2), request=1)
        self.__cxt.sdc_items[8] = _monarco_sdc_item_t(address = int('1000', 2), request=1)

        # Hardware configuration register 1 - Enable RS-485 termination, Volt or Ampere
        if (conf["ain1"].lower() == "a" and conf["ain2"] == "a"):
            self.__cxt.sdc_items[9] = _monarco_sdc_item_t(address = int('1010', 2), request=1, write=1, value=int("111", 2))
        elif (conf["ain1"].lower() == "v" and conf["ain2"] == "a"):
            self.__cxt.sdc_items[9] = _monarco_sdc_item_t(address = int('1010', 2), request=1, write=1, value=int("101", 2))
        elif (conf["ain1"].lower() == "a" and conf["ain2"] == "v"):
            self.__cxt.sdc_items[9] = _monarco_sdc_item_t(address = int('1010', 2), request=1, write=1, value=int("011", 2))
        elif (conf["ain1"].lower() == "v" and conf["ain2"] == "v"):
            self.__cxt.sdc_items[9] = _monarco_sdc_item_t(address = int('1010', 2), request=1, write=1, value=int("001", 2))
        else:
            raise ValueError("Unknown values in ain_configs. Must be a or v for Ampere or Volt!")

        self.__cxt.sdc_size = 10

    def set_digital_out(self, port, value):
        """
        Write to digital output
        :param port: What output to write to, must be DOUT[1-4]
        :param value: What value to write to port, must be HIGH or LOW
        :return: None
        """

        assert port in [DOUT1, DOUT2, DOUT3, DOUT4], "Invalid digital out port"
        assert value == LOW or value == HIGH, "Invalid digital out value"

        with self.__mutex:
            if value == LOW:
                self.__cxt.tx_data.dout = ctypes.c_uint8(self.__cxt.tx_data.dout & ~(1 << port-1))
            elif value == HIGH:
                self.__cxt.tx_data.dout = ctypes.c_uint8(self.__cxt.tx_data.dout | (1 << port-1))

    def get_digital_in(self, port):
        """
        Read digital input
        :param port: What port to read from, must be DIN[1-4]
        :return: True og False
        """

        assert port in [DIN1, DIN2, DIN3, DIN4], "Invalid digital in port"

        with self.__mutex:
            return self.__cxt.rx_data.din & (1 << port-1)

    def set_pwm_frequency(self, channel,  pwm_frequency):
        """
        Set PWM output frequency.
        PWM_CHANNEL1 set frequency for port DOUT1, DOUT2, DOUT3
        PWM_CHANNEL2 set frequency for port DOUT4
        :param channel: What channel to set PWM frequency, must be PWM_CHANNEL[1-2]
        :param pwm_frequency: PWM frequency in Hz, must be between 1 Hz and 100.000 Hz
        :return: None
        """

        assert channel in [PWM_CHANNEL1, PWM_CHANNEL2], "Invalid PWM port"
        assert 1.0 <= pwm_frequency < 100000.0, "PWM frequency out of range: {}".format(pwm_frequency)

        with self.__mutex:
            if channel == PWM_CHANNEL1:  # DOUT 1, 2, 3
                self.__cxt.tx_data.pwm1_div = self.__monarco.monarco_util_pwm_freq_to_u16(ctypes.c_double(pwm_frequency))
            elif channel == PWM_CHANNEL2:  # DOUT 4
                self.__cxt.tx_data.pwm2_div = self.__monarco.monarco_util_pwm_freq_to_u16(ctypes.c_double(pwm_frequency))

    def set_pwm_out(self, port, value):
        """
        Write to PWM output
        :param port: What output to write to, must be DOUT[1-4]
        :param value: What value to write to port, must be between 0 and 1
        :return: None
        """

        assert port in [DOUT1, DOUT2, DOUT3, DOUT4], "Invalid digital out port"
        assert 0 <= value <= 1, "PWM value out of range: {}".format(value)

        with self.__mutex:
            if port == DOUT1:
                self.__cxt.tx_data.pwm1a_dc = self.__monarco.monarco_util_pwm_dc_to_u16(ctypes.c_double(value))
            elif port == DOUT2:
                self.__cxt.tx_data.pwm1b_dc = self.__monarco.monarco_util_pwm_dc_to_u16(ctypes.c_double(value))
            elif port == DOUT3:
                self.__cxt.tx_data.pwm1c_dc = self.__monarco.monarco_util_pwm_dc_to_u16(ctypes.c_double(value))
            elif port == DOUT4:
                self.__cxt.tx_data.pwm2a_dc = self.__monarco.monarco_util_pwm_dc_to_u16(ctypes.c_double(value))

    def set_analog_out(self, port, value):
        """
        Write to analog output
        :param port: What output to write to, must be AOUT[1-2]
        :param value: Output value in volts, must be between 0V and 10V
        :return: None
        """

        assert port in [AOUT1, AOUT2], "Invalid analog out port"
        assert 0 <= value <= 10, "Analog value out of range: {}".format(value)

        with self.__mutex:
            if port == AOUT1:
                self.__cxt.tx_data.aout1 = self.__monarco.monarco_util_aout_volts_to_u16(ctypes.c_double(value))
            elif port == AOUT2:
                self.__cxt.tx_data.aout2 = self.__monarco.monarco_util_aout_volts_to_u16(ctypes.c_double(value))

    def get_analog_in(self, port):
        """
        Read analog input
        :param port: What port to read from, must be AIN[1-2]
        :return: Value in volts
        """

        V_MAX = 10.0
        RANGE = 4095.0
        A_MAX = 52.475

        assert port in [AIN1, AIN2], "Invalid analog in port"

        with self.__mutex:
            if port == AIN1:
                if self._ain_configs["ain1"] == "a":
                    return self.__cxt.rx_data.ain1 * A_MAX/RANGE
                elif self._ain_configs["ain1"] == "v":
                    return self.__cxt.rx_data.ain1 * V_MAX/RANGE
                else:
                    raise ValueError("Config for AIN1 must be a or v. Got %s", self._ain_configs["ain1"])

            elif port == AIN2:
                if self._ain_configs["ain2"] == "a":
                    return self.__cxt.rx_data.ain2 * A_MAX/RANGE
                elif self._ain_configs["ain2"] == "v":
                    return self.__cxt.rx_data.ain2 * V_MAX/RANGE
                else:
                    raise ValueError("Config for AIN2 must be a or v. Got %s", self._ain_configs["ain2"])


    def close(self):
        """
        Close connection
        :return: None
        """

        self.__monarco.monarco_exit(ctypes.pointer(self.__cxt))
