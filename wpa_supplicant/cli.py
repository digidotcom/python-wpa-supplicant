import click
from contextlib import contextmanager
import threading
from twisted.internet.selectreactor import SelectReactor
import time
from wpa_supplicant.libcore import WpaSupplicantDriver


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
# The outer commands
#
@click.group()
@click.option('--debug/--no-debug', default=False, help="Show log debug on stdout")
def wpacli(debug):
    """Command line interface for wpa_supplicant D-Bus"""


@click.group()
def interface():
    pass


#
# fi.w1.wpa_supplicant1 API
#
@wpacli.command()
@click.argument('ifname', 'e.g. wlan0')
@click.option('--bridge_if_name', default=None, help='Bridge to control, e.g., br0')
@click.option('--driver', default=None, help='e.g. nl80211')
@click.option('--config_file', default=None, help='Config file path')
def create_interface(ifname, bridge_if_name, driver, config_file):
    args = add_optional_args([ifname, ], bridge_if_name, driver, config_file)
    with supplicant() as supp:
        print supp.create_interface(*args)


@wpacli.command()
def remove_interface():
    pass


@wpacli.command()
@click.argument('ifname', 'e.g. wlan0')
def get_interface(ifname):
    with supplicant() as supp:
        print supp.get_interface(ifname)


#
# fi.w1.wpa_supplicant1.Interface API
#
@interface.command()
def scan():
    raise NotImplemented


@interface.command()
def disconnect():
    raise NotImplemented


def run():
    wpacli()


if __name__ == '__main__':
    run()