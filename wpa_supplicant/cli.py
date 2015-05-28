# TODO: There is no good way to accept array type arguments

import click
from contextlib import contextmanager
import threading
from twisted.internet.selectreactor import SelectReactor
import time
from wpa_supplicant.libcore import WpaSupplicantDriver
import pprint

#
# Helpers
#
@contextmanager
def supplicant():
    """Run a reactor and provide access to the supplicant driver"""
    reactor = SelectReactor()
    t = threading.Thread(target=reactor.run, kwargs={'installSignalHandlers': 0})
    t.start()
    time.sleep(0.1)  # let reactor start
    driver = WpaSupplicantDriver(reactor)
    supplicant = driver.connect()
    try:
        yield supplicant
    except Exception, e:
        print 'FAIL - {}'.format(e)
    else:
        print 'OK'
    reactor.disconnectAll()
    reactor.sigTerm()
    t.join()


def add_optional_args(args, *optionals):
    for opt in optionals:
        if opt is not None:
            args.append(opt)
    return args


#
# The following CLI "groups" follow the natural hierarchy of the D-Bus
# object system:
#
# * fi.w1.wpa_supplicant1
#     * fi.w1.wpa_supplicant1.Interface
#     * fi.w1.wpa_supplicant1.Interface.WPS
#     * fi.w1.wpa_supplicant1.Interface.P2PDevice
#     * fi.w1.wpa_supplicant1.BSS
#     * fi.w1.wpa_supplicant1.Network
#     * fi.w1.wpa_supplicant1.Peer
#     * fi.w1.wpa_supplicant1.Group
#     * fi.w1.wpa_supplicant1.PersistentGroup
#

@click.group()
@click.option('--debug/--no-debug', default=False, help="Show log debug on stdout")
def wpacli(debug):
    """Command line interface for wpa_supplicant D-Bus"""


@wpacli.group()
def interface():
    """Access fi.w1.wpa_supplicant1.Interface object"""


@interface.group(name='wps')
def interface_wps():
    """Access fi.w1.wpa_supplicant1.Interface.WPS object"""


@interface.group(name='p2p_device')
def interface_p2p_device():
    """Access fi.w1.wpa_supplicant1.Interface.P2PDevice object"""


@wpacli.group()
def bss():
    """Access fi.w1.wpa_supplicant1.BSS object"""


@wpacli.group()
def network():
    """Access fi.w1.wpa_supplicant1.Network object"""


@wpacli.group()
def peer():
    """Access fi.w1.wpa_supplicant1.Peer object"""


@wpacli.group()
def group():
    """Access fi.w1.wpa_supplicant1.Group object"""


@wpacli.group()
def persistent_group():
    """Access fi.w1.wpa_supplicant1.PersistentGroup object"""


#
# fi.w1.wpa_supplicant1 API
#
@wpacli.command()
@click.argument('ifname', 'e.g. wlan0')
@click.option('--bridge_if_name', default=None, help='Bridge to control, e.g., br0')
@click.option('--driver', default=None, help='e.g. nl80211')
@click.option('--config_file', default=None, help='Config file path')
def create_interface(ifname, bridge_if_name, driver, config_file):
    """Method: Registers a wireless interface in wpa_supplicant"""
    args = add_optional_args([ifname, ], bridge_if_name, driver, config_file)
    with supplicant() as supp:
        pprint.pprint(supp.create_interface(*args))


@wpacli.command()
def remove_interface():
    """Method: Deregisters a wireless interface from wpa_supplicant"""


@wpacli.command()
@click.argument('ifname', 'e.g. wlan0')
def get_interface(ifname):
    """Method: Returns a D-Bus path to an object related to an interface which wpa_supplicant already controls"""
    with supplicant() as supp:
        pprint.pprint(supp.get_interface(ifname))


#
# fi.w1.wpa_supplicant1.Interface API
#
@interface.command()
@click.argument('ifname', 'e.g. wlan0')
@click.option('--scan_type', default='active', help='Active or Passive')
def scan(ifname, scan_type):
    with supplicant() as supp:
        iface = supp.get_interface(ifname)
        pprint.pprint(iface.scan(type=scan_type, block=True))


@interface.command()
def disconnect():
    raise NotImplemented


def run():
    wpacli()


if __name__ == '__main__':
    run()