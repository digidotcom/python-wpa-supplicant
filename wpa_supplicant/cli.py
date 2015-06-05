# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

# TODO: There is no good way to accept array type arguments

import click
from contextlib import contextmanager
import threading
from twisted.internet.selectreactor import SelectReactor
import time
from wpa_supplicant.core import WpaSupplicantDriver, BSS
import pprint
import sys


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
    except Exception as e:
        print('FAIL - {}'.format(e))
    else:
        print('OK')
    reactor.disconnectAll()
    reactor.sigTerm()
    t.join()


def add_optional_args(args, *optionals):
    for opt in optionals:
        if opt is not None:
            args.append(opt)
    return args


def ctx_get(ctx, key, default=None):
    """Iterate up context tree and return the value at `key` if found"""

    while not getattr(ctx, 'is_root', False):
        value = getattr(ctx, key, None)
        if value is not None:
            return value
        ctx = ctx.parent
    return default


#
# The following CLI "groups" follow the natural hierarchy of the D-Bus
# object system:
#
# * fi.w1.wpa_supplicant1
# * fi.w1.wpa_supplicant1.Interface
# * fi.w1.wpa_supplicant1.Interface.WPS
#     * fi.w1.wpa_supplicant1.Interface.P2PDevice
#     * fi.w1.wpa_supplicant1.BSS
#     * fi.w1.wpa_supplicant1.Network
#     * fi.w1.wpa_supplicant1.Peer
#     * fi.w1.wpa_supplicant1.Group
#     * fi.w1.wpa_supplicant1.PersistentGroup
#

@click.group()
@click.option('--debug/--no-debug', default=False, help="Show log debug on stdout")
@click.pass_context
def root(ctx, debug):
    """Command line interface for wpa_supplicant D-Bus"""
    ctx.is_root = True


@root.group()
@click.argument('ifname', 'e.g. wlan0')
@click.pass_context
def interface(ctx, ifname):
    """Access fi.w1.wpa_supplicant1.Interface object"""
    ctx.ifname = ifname


@interface.group(name='wps')
def interface_wps():
    """Access fi.w1.wpa_supplicant1.Interface.WPS object"""
    raise NotImplemented


@interface.group(name='p2p_device')
def interface_p2p_device():
    """Access fi.w1.wpa_supplicant1.Interface.P2PDevice object"""
    raise NotImplemented


@root.group()
@click.argument('ifname', 'e.g. wlan0')
@click.option('--ssid', default=None, help='Look at scan results for BSS examples')
@click.option('--bssid', default=None, help='Look at scan results for BSS examples')
@click.pass_context
def bss(ctx, ifname, ssid, bssid):
    """Access fi.w1.wpa_supplicant1.BSS object"""
    ctx.ifname = ifname
    ctx.ssid = None
    ctx.bssid = None
    at_least_one_option = False
    if ssid is not None:
        ctx.ssid = ssid
        at_least_one_option = True
    if bssid is not None:
        ctx.bssid = bssid
        at_least_one_option = True
    if not at_least_one_option:
        print('BSS sub-commands require a valid ssid or bssid option')
        sys.exit(1)


@root.group()
def network():
    """Access fi.w1.wpa_supplicant1.Network object"""


@root.group()
def peer():
    """Access fi.w1.wpa_supplicant1.Peer object"""
    raise NotImplemented


@root.group()
def group():
    """Access fi.w1.wpa_supplicant1.Group object"""
    raise NotImplemented


@root.group()
def persistent_group():
    """Access fi.w1.wpa_supplicant1.PersistentGroup object"""
    raise NotImplemented


#
# fi.w1.wpa_supplicant1 API
#
@root.command()
@click.argument('ifname', 'e.g. wlan0')
@click.option('--bridge_if_name', default=None, help='Bridge to control, e.g., br0')
@click.option('--driver', default=None, help='e.g. nl80211')
@click.option('--config_file', default=None, help='Config file path')
def create_interface(ifname, bridge_if_name, driver, config_file):
    """Method: Registers a wireless interface in wpa_supplicant"""
    args = add_optional_args([ifname, ], bridge_if_name, driver, config_file)
    with supplicant() as supp:
        pprint.pprint(supp.create_interface(*args))


@root.command()
@click.argument('ifname', 'e.g. wlan0')
def remove_interface(ifname):
    """Method: Deregisters a wireless interface from wpa_supplicant"""
    with supplicant() as supp:
        iface = supp.get_interface(ifname)
        supp.remove_interface(iface.get_path())


@root.command()
@click.argument('ifname', 'e.g. wlan0')
def get_interface(ifname):
    """Method: Returns a D-Bus path to an object related to an interface which wpa_supplicant already controls"""
    with supplicant() as supp:
        pprint.pprint(supp.get_interface(ifname))


@root.command(name='get')
@click.argument('name', 'Name of property (case sensitive)')
def root_get(name):
    """Method: Get Property (case sensitive)"""
    with supplicant() as supp:
        pprint.pprint(supp.get(name))


@root.command(name='set')
@click.argument('name', 'Name of property (case sensitive)')
@click.argument('value', 'Value to be set')
def root_set(name, value):
    """Method: Set Property (case sensitive)"""
    with supplicant() as supp:
        pprint.pprint(supp.set(name, value))


#
# fi.w1.wpa_supplicant1.Interface API
#
@interface.command()
@click.option('--scan_type', default='active', help='Active or Passive')
@click.pass_context
def scan(ctx, scan_type):
    """Method: Trigger a scan and block for results"""
    with supplicant() as supp:
        iface = supp.get_interface(ctx_get(ctx, 'ifname'))
        pprint.pprint(iface.scan(type=scan_type, block=True))


@interface.command()
@click.pass_context
def disconnect(ctx):
    """Method: Disassociates the interface from current network"""
    with supplicant() as supp:
        iface = supp.get_interface(ctx_get(ctx, 'ifname'))
        iface.disconnect()


@interface.command(name='get')
@click.argument('name', 'Name of property (case sensitive)')
@click.pass_context
def interface_get(ctx, name):
    """Method: Get Property (case sensitive)"""
    with supplicant() as supp:
        iface = supp.get_interface(ctx_get(ctx, 'ifname'))
        pprint.pprint(iface.get(name))


@interface.command(name='set')
@click.argument('name', 'Name of property (case sensitive)')
@click.argument('value', 'Value to be set')
@click.pass_context
def interface_set(ctx, name, value):
    """Method: Set Property (case sensitive)"""
    with supplicant() as supp:
        iface = supp.get_interface(ctx_get(ctx, 'ifname'))
        pprint.pprint(iface.set(name, value))


#
# fi.w1.wpa_supplicant1.BSS API
#
@bss.command(name='get')
@click.argument('name', 'Name of property (case sensitive)')
@click.pass_context
def bss_get(ctx, name):
    """Method: Get Property (case sensitive)"""
    with supplicant() as supp:
        iface = supp.get_interface(ctx_get(ctx, 'ifname'))
        scan_results = iface.scan(block=True)
        for result in scan_results:
            if result.get_ssid() == ctx_get(ctx, 'ssid') or \
                            result.get_bssid() == ctx_get(ctx, 'bssid'):
                bss = result
                break
        else:
            print('No BSS found')
            sys.exit(1)

        pprint.pprint(bss.get(name))


@bss.command(name='set')
@click.argument('name', 'Name of property (case sensitive)')
@click.argument('value', 'Value to be set')
@click.pass_context
def bss_set(ctx, name, value):
    """Method: Set Property (case sensitive)"""
    raise NotImplemented


def run():
    root()


if __name__ == '__main__':
    run()