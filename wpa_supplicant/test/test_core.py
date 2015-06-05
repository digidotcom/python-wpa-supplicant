# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.
import time
import unittest
import threading

import six
from six.moves.queue import Queue
from wpa_supplicant.core import WpaSupplicantDriver, Interface, BSS, Network, \
    InterfaceUnknown, InterfaceExists, NotConnected, NetworkUnknown, WpaSupplicant
from twisted.internet.selectreactor import SelectReactor
import mock
from wpa_supplicant.test import mocks


class Task(object):
    def __init__(self, fn, *args, **kwargs):
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def do(self):
        self._fn(*self._args, **self._kwargs)


class ThreadedTaskRunner(threading.Thread):
    _QUIT = object()

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self._tasks = Queue()

    def run(self):
        while True:
            task = self._tasks.get()
            if task is self._QUIT:
                break
            else:
                if isinstance(task, Task):
                    task.do()

    def stop(self):
        self._tasks.put(self._QUIT)

    def queue(self, task):
        self._tasks.put(task)


class TestWpaSupplicant(unittest.TestCase):
    def setUp(self):
        mocks.init()
        self._taskrunner = ThreadedTaskRunner()
        self._taskrunner.start()
        self._reactor = SelectReactor()
        self._driver = WpaSupplicantDriver(self._reactor)
        self._reactor_thread = threading.Thread(target=self._reactor.run,
                                                kwargs={'installSignalHandlers': 0})
        self._reactor_thread.start()
        time.sleep(0.1)
        self._supplicant = self._driver.connect()

    def tearDown(self):
        self._reactor.disconnectAll()
        self._reactor.sigTerm()
        self._reactor_thread.join()
        self._taskrunner.stop()

    #
    # Helpers
    #
    def _get_interface(self, interface_name):
        return self._supplicant.get_interface(interface_name)

    def _get_any_bss(self):
        iface = self._get_interface('wlan0')
        return BSS('/fi/w1/wpa_supplicant1/Interfaces/1/BSSs/1',
                   iface._conn,
                   iface._reactor)

    #
    # Test Driver
    #
    def test_connect(self):
        supplicant = self._driver.connect()
        self.assertIsInstance(supplicant, WpaSupplicant)

    #
    # Test Base
    #
    def test_register_for_signal(self):
        cb = mock.Mock()
        self._supplicant.register_signal('mysig', cb)
        self._supplicant._introspection.fire_signal('mysig', True)
        cb.assert_called_once_with(True)

    def test_register_for_signal_once(self):
        def fire_signal(result):
            time.sleep(1)
            self._supplicant._introspection.fire_signal('mysig', result)

        deferred_queue = self._supplicant.register_signal_once('mysig')
        self._taskrunner.queue(Task(fire_signal, True))
        result = deferred_queue.get()
        self.assertEqual(result, True)

    #
    # Test Supplicant
    #
    def test_get_interface(self):
        interface = self._supplicant.get_interface('wlan0')
        self._supplicant._without_introspection.callRemote.assert_called_with(
            'GetInterface', 'wlan0')
        self.assertTrue(isinstance(interface, Interface))
        self.assertEqual(interface.get_path(), '/fi/w1/wpa_supplicant1/Interfaces/3')

    def test_get_unknown_interface(self):
        self.assertRaises(InterfaceUnknown, self._supplicant.get_interface, 'wlan99')

    def test_create_interface(self):
        interface = self._supplicant.create_interface('wlan0')
        self._supplicant._without_introspection.callRemote.assert_called_with(
            'CreateInterface',
            {'Ifname': 'wlan0'})
        self.assertTrue(isinstance(interface, Interface))
        self.assertEqual(interface.get_path(), '/fi/w1/wpa_supplicant1/Interfaces/3')

    def test_create_interface_already_exists(self):
        self.test_create_interface()
        self.assertRaises(InterfaceExists, self._supplicant.create_interface, 'wlan0')

    def test_remove_interface(self):
        self._supplicant.create_interface('wlan0')
        returnval = self._supplicant.remove_interface(
            '/fi/w1/wpa_supplicant1/Interfaces/3')
        self._supplicant._without_introspection.callRemote.assert_called_with(
            'RemoveInterface',
            '/fi/w1/wpa_supplicant1/Interfaces/3')
        self.assertEqual(returnval, None)

    def test_remove_unknown_interface(self):
        supplicant = self._driver.connect()
        self.assertRaises(InterfaceUnknown, supplicant.remove_interface, 'wlan99')

    def test_get_debug_level(self):
        supplicant = self._driver.connect()
        self.assertEqual(supplicant.get_debug_level(), six.u('info'))

    def test_get_debug_timestamp(self):
        supplicant = self._driver.connect()
        self.assertEqual(supplicant.get_debug_timestamp(), False)

    def test_get_debug_showkeys(self):
        supplicant = self._driver.connect()

    def test_get_interfaces(self):
        supplicant = self._driver.connect()
        self.assertEqual(supplicant.get_interfaces(),
                         [u'/fi/w1/wpa_supplicant1/Interfaces/7'])

    def test_get_eap_methods(self):
        supplicant = self._driver.connect()
        self.assertEqual(supplicant.get_eap_methods(), [u'MD5',
                                                        u'TLS',
                                                        u'MSCHAPV2',
                                                        u'PEAP',
                                                        u'TTLS',
                                                        u'GTC',
                                                        u'OTP',
                                                        u'SIM',
                                                        u'LEAP',
                                                        u'PSK',
                                                        u'AKA',
                                                        u"AKA'",
                                                        u'FAST',
                                                        u'PAX',
                                                        u'SAKE',
                                                        u'GPSK',
                                                        u'WSC',
                                                        u'IKEV2',
                                                        u'TNC',
                                                        u'PWD'])

    #
    # Test Interface
    #
    def test_interface_scan(self):
        interface = self._get_interface('wlan0')
        scan_results = interface.scan()
        self.assertEqual(scan_results, None)

    def test_interface_blocking_scan(self):
        interface = self._get_interface('wlan0')

        def fire_signal():
            time.sleep(1)
            interface._introspection.fire_signal('ScanDone', True)

        self._taskrunner.queue(Task(fire_signal))
        scan_results = interface.scan(block=True)
        for res in scan_results:
            self.assertTrue(isinstance(res, BSS))
            self.assertEqual(res.get_path(),
                             '/fi/w1/wpa_supplicant1/Interfaces/3/BSSs/1234')

    def test_add_network(self):
        interface = self._get_interface('wlan0')
        network = interface.add_network({})
        self.assertTrue(isinstance(network, Network))
        self.assertEqual(network.get_path(), '/fi/w1/wpa_supplicant1/Networks/0')

    def test_remove_network(self):
        interface = self._get_interface('wlan0')
        network = interface.add_network({})
        result = interface.remove_network(network.get_path())
        self.assertEqual(result, None)

    def test_remove_unknown_network(self):
        interface = self._get_interface('wlan0')
        self.assertRaises(NetworkUnknown,
                          interface.remove_network,
                          '/fi/w1/wpa_supplicant1/Networks/44')

    def test_select_network(self):
        interface = self._get_interface('wlan0')
        network = interface.add_network({})
        interface.select_network(network.get_path())
        current_network = interface.get_current_network()
        self.assertEqual(current_network.get_path(), network.get_path())

    def test_get_ifname(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_ifname(), 'wlan0')

    def test_get_current_bss(self):
        interface = self._get_interface('wlan0')
        bss = interface.get_current_bss()
        self.assertTrue(isinstance(bss, BSS))

    def test_get_current_network(self):
        interface = self._get_interface('wlan0')
        net = interface.get_current_network()
        self.assertEqual(net, None)

    def test_network_disconnect(self):
        interface = self._get_interface('wlan0')
        network = interface.add_network({})
        interface.select_network(network.get_path())
        interface.disconnect_network()
        self.assertIsNone(interface.get_current_network())

    def test_network_disconnect_not_connected(self):
        interface = self._get_interface('wlan0')
        self.assertRaises(NotConnected, interface.disconnect_network)

    def test_get_networks(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_networks(), [])

    def test_get_state(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_state(), u'inactive')

    def test_get_scanning(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_scanning(), False)

    def test_get_scan_interval(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_scan_interval(), 5)

    def test_get_fast_reauth(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_fast_reauth(), True)

    def test_get_all_bss(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_all_bss(),
                         ['/fi/w1/wpa_supplicant1/Interfaces/3/BSSs/1234', ])

    def test_get_driver(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_driver(), u'nl80211')

    def test_get_country(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_country(), u'US')

    def test_get_bridge_ifname(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_bridge_ifname(), u'')

    def test_get_bss_expire_age(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_bss_expire_age(), 180)

    def test_get_bss_expire_count(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_bss_expire_count(), 2)

    def test_get_ap_scan(self):
        interface = self._get_interface('wlan0')
        self.assertEqual(interface.get_ap_scan(), 1)

    #
    # Test BSS
    #
    def test_get_channel(self):
        # The "channel" is a conversion from frequency, so we need to test
        # the calculation being used
        bss = self._get_any_bss()
        self.assertEqual(bss.get_channel(), 11)

    def test_get_ssid(self):
        bss = self._get_any_bss()
        self.assertEqual(bss.get_ssid(), 'FGHI')

    def test_get_bssid(self):
        bss = self._get_any_bss()
        self.assertEqual(bss.get_bssid(), '46:47:48:49')

    def test_get_frequency(self):
        bss = self._get_any_bss()
        self.assertEqual(bss.get_frequency(), 2462)

    def test_get_wpa(self):
        bss = self._get_any_bss()
        self.assertEqual(bss.get_wpa(),
                         {u'Group': u'tkip', u'KeyMgmt': [u'wpa-psk'], u'Pairwise': [u'tkip']})

    def test_get_rsn(self):
        bss = self._get_any_bss()
        self.assertEqual(bss.get_rsn(), {u'Group': u'', u'KeyMgmt': [], u'Pairwise': []})

    def test_get_ies(self):
        bss = self._get_any_bss()
        self.assertEqual(bss.get_ies(), [0, 9, 68, 65, 80, 150, 24, 36])

    def test_get_privacy(self):
        interface = self._get_interface('wlan0')
        bss = interface.get_current_bss()
        self.assertEqual(bss.get_privacy(), True)

    def test_get_mode(self):
        bss = self._get_any_bss()
        self.assertEqual(bss.get_mode(), u'infrastructure')

    def test_get_rates(self):
        bss = self._get_any_bss()
        self.assertEqual(bss.get_rates(), [54000000, 48000000, 6000000])

    def test_get_signal_dbm(self):
        interface = self._get_interface('wlan0')
        bss = interface.get_current_bss()
        self.assertEqual(-60, bss.get_signal_dbm())

    def test_get_signal_quality(self):
        interface = self._get_interface('wlan0')
        bss = interface.get_current_bss()
        self.assertEqual(80, bss.get_signal_quality())

    #
    # Test Network
    #
    def test_get_properties(self):
        interface = self._get_interface('wlan0')
        desired_network = interface.add_network({'ssid': 'foo', 'psk': 'bar'})
        interface.select_network(desired_network.get_path())
        curr_network = interface.get_current_network()
        props = curr_network.get_properties()
        self.assertEqual(props['ssid'], 'wdnu-dvt1')

    def test_get_enabled(self):
        pass
