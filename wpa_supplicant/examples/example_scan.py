from wpa_supplicant.libcore import WpaSupplicantDriver
from twisted.internet.selectreactor import SelectReactor
import threading
import time

# Start a simple Twisted SelectReactor
reactor = SelectReactor()
threading.Thread(target=reactor.run, kwargs={'installSignalHandlers': 0}).start()
time.sleep(0.1)  # let reactor start

# Start Driver
driver = WpaSupplicantDriver(reactor)

# Connect to the supplicant, which returns the "root" D-Bus object for wpa_supplicant
supplicant = driver.connect()

# Register an interface w/ the supplicant, this can raise an error if the supplicant
# already knows about this interface
interface = supplicant.create_interface('wlan0')

# Issue the scan
scan_results = interface.scan(block=True)
for bss in scan_results:
    print bss.get_ssid()
