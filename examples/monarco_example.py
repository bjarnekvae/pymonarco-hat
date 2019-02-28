import pymonarco_hat as plc
import sys
import time

lib_path = sys.argv[1]
plc_handler = plc.Monarco(lib_path, debug_flag=plc.MONARCO_DPF_WRITE | plc.MONARCO_DPF_VERB)

plc_handler.set_pwm_frequency(plc.PWM_CHANNEL1, 1000)
plc_handler.set_pwm_out(plc.DOUT2, 0.75)
plc_handler.set_analog_out(plc.AOUT1, 5.0)

while 1:
    plc_handler.set_digital_out(plc.DOUT1, plc.HIGH)
    time.sleep(1)
    plc_handler.set_digital_out(plc.DOUT1, plc.LOW)
    time.sleep(1)

    print("DIN1:", plc_handler.get_digital_in(plc.DIN1))
    print("AIN1:", plc_handler.get_analog_in(plc.AIN1))




