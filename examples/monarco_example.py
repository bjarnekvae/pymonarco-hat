import pymonarco_hat as plc
import sys
import time

lib_path = sys.argv[1]

print(lib_path)
plc_object = plc.Monarco(lib_path, '/dev/spidev0.0', 4000000, "Monarco")

while(1):
    plc_object.set_digital_out(2, 1)
    time.sleep(1)
    plc_object.set_digital_out(2, 0)
    time.sleep(1)



