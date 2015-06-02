# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International Inc. All Rights Reserved.

"""

    This module (library) is an intuitive wrapper around wpa_supplicant's D-Bus API

For the most part, the library aims to provide a one-to-one mapping into the D-Bus
interfaces offered by wpa_supplicant.  Certain abstractions or niceties have been made
to make the usage of the API more intuitive.

The libraries API was mainly derived from the following documentation:

    http://w1.fi/wpa_supplicant/devel/dbus.html

"""
from twisted.internet import defer, threads
from txdbus.interface import DBusInterface, Method, Signal
from txdbus import client, error
from functools import wraps
import threading
import logging

#
# Constants/Globals
#
BUS_NAME = 'fi.w1.wpa_supplicant1'
logger = logging.getLogger('wpasupplicant')


#
# Helpers
#
def _catch_remote_errors(fn):
    """Decorator for catching and wrapping txdbus.error.RemoteError exceptions"""
    @wraps(fn)
    def closure(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except error.RemoteError, ex:
            match = _REMOTE_EXCEPTIONS.get(str(ex.errName))
            if match is not None:
                raise match(ex.message)
            else:
                logger.warn("Unrecognized error: %s" % ex.errName)
                raise WpaSupplicantException(ex.message)
    return closure


def _eval(deferred, reactor):
        """Evaluate a deferred on a given reactor and return the result

        This function is safe to call with a deferred that has already been evaluated.
        """

        @defer.inlineCallbacks
        def closure():
            if deferred.called:
                result = deferred.result
            else:
                result = yield deferred

            defer.returnValue(result)

        if threading.currentThread().getName() == reactor.thread_name:
            return closure()
        else:
            return threads.blockingCallFromThread(reactor, closure)


#
# Exceptions
#
class WpaSupplicantException(Exception):
    """Base class for all exception types raised from this lib"""


class UnknownError(WpaSupplicantException):
    """Something failed for an unknown reason

    Possible sources:
        Basically everything in this library
    """


class MethodTimeout(WpaSupplicantException):
    """Raised when a timeout occurs while waiting on DeferredQueue.get()

    Possible sources:
        :meth:`~Interface.scan` with block=True
    """


class InterfaceExists(WpaSupplicantException):
    """wpa_supplicant already controls this interface

    Possible sources:
        :meth:`~WpaSupplicant.create_interface`
    """


class InvalidArgs(WpaSupplicantException):
    """Invalid entries were found in the passed arguments
    
    Possible sources:
        :meth:`~WpaSupplicant.create_interface`
        :meth:`~Interface.scan`
        :meth:`~Interface.add_network`
        :meth:`~Interface.remove_network`
        :meth:`~Interface.select_network`
    """


class InterfaceUnknown(WpaSupplicantException):
    """Object pointed by the path doesn't exist or doesn't represent an interface
    
    Possible sources:
        :meth:`~WpaSupplicant.get_interface`
        :meth:`~WpaSupplicant.remove_interface`
    """


class NotConnected(WpaSupplicantException):
    """Interface is not connected to any network

    Possible sources:
        :meth:`~Interface.disconnect`
    """


class NetworkUnknown(WpaSupplicantException):
    """A passed path doesn't point to any network object

    Possible sources:
        :meth:`~Interface.remove_network`
        :meth:`~Interface.select_network`
    """


class ReactorNotRunning(WpaSupplicantException):
    """In order to connect to the WpaSupplicantDriver a reactor must be started"""


# These are exceptions defined by the wpa_supplicant D-Bus API
_REMOTE_EXCEPTIONS = {
    'fi.w1.wpa_supplicant1.UnknownError': UnknownError,
    'fi.w1.wpa_supplicant1.InvalidArgs': InvalidArgs,
    'fi.w1.wpa_supplicant1.InterfaceExists': InterfaceExists,
    'fi.w1.wpa_supplicant1.InterfaceUnknown': InterfaceUnknown,
    'fi.w1.wpa_supplicant1.NotConnected': NotConnected,
    'fi.w1.wpa_supplicant1.NetworkUnknown': NetworkUnknown,
}


#
# Library Core
#
class TimeoutDeferredQueue(defer.DeferredQueue):
    """Deferred Queue implementation that provides .get() a timeout keyword arg"""

    def __init__(self, reactor):
        defer.DeferredQueue.__init__(self)
        self._reactor = reactor

    def _timed_out(self, deferred):
        """A timeout occurred while waiting for the deferred to be fired"""

        if not deferred.called:
            if deferred in self.waiting:
                self.waiting.remove(deferred)
                deferred.errback(MethodTimeout('Timed out waiting for response'))

    def _stop_timeout(self, result, call_id):
        """One of the callbacks in the deferreds callback-chain"""

        call_id.cancel()
        return result

    def get(self, timeout=None):
        """Synchronously get the result of :meth:`defer.DeferredQueue.get()`

        :param timeout: optional timeout parameter (integer # of sections)
        :returns: The result value that has been put onto the deferred queue
        :raises MethodTimeout: More time has elapsed than the specified `timeout`
        """

        deferred = defer.DeferredQueue.get(self)

        if timeout:
            call_id = self._reactor.callLater(timeout, self._timed_out, deferred)
            deferred.addCallback(self._stop_timeout, call_id)

        return _eval(deferred, self._reactor)


class RemoteSignal(object):
    """Encapsulation of a signal object returned by signal registration methods"""

    def __init__(self, signal_name, callback, remote_object, remote_interface, reactor):
        self._signal_name = signal_name
        self._callback = callback
        self._remote_object = remote_object
        self._remote_interface = remote_interface
        self._reactor = reactor
        self._deferred = remote_object.notifyOnSignal(signal_name, callback, remote_interface)

    def get_signal_name(self):
        return self._signal_name

    def cancel(self):
        self._remote_object.cancelSignalNotification(_eval(self._deferred, self._reactor))


class BaseIface(object):
    """Base class for all Interfaces defined in the wpa_supplicant D-Bus API"""

    def __init__(self, obj_path, conn, reactor):
        self._obj_path = obj_path
        self._conn = conn
        self._reactor = reactor
        self._introspection = _eval(self._conn.getRemoteObject(BUS_NAME, self._obj_path),
                                    self._reactor)
        self._without_introspection = _eval(self._conn.getRemoteObject(BUS_NAME, self._obj_path, self.iface),
                                            self._reactor)

    def get_path(self):
        """Return the full D-Bus object path that defines this interface

        :returns: String D-Bus object path, e.g. /w1/fi/wpa_supplicant1/Interfaces/0
        :rtype: str
        """

        return self._obj_path

    @_catch_remote_errors
    def _call_remote(self, method, *args):
        """Call a remote D-Bus interface method using introspection"""

        return _eval(self._introspection.callRemote(method, *args), self._reactor)

    @_catch_remote_errors
    def _call_remote_without_introspection(self, method, *args):
        """Call a remote D-Bus interface method without using introspection"""

        return _eval(self._without_introspection.callRemote(method, *args), self._reactor)

    @_catch_remote_errors
    def register_signal_once(self, signal_name):
        """Register a signal on an Interface object

        .. note::

            Since this de-registers itself after the signal fires the only real
            use for this function is code that wants to block and wait for a signal
            to fire, hence the queue it returns.

        :param signal_name: Case-sensitive name of the signal
        :returns: Object of type :class:`~EventSignal`
        """

        q = TimeoutDeferredQueue(self._reactor)

        signal = None

        def signal_callback(result):
            q.put(result)
            if signal is not None:
                signal.cancel()

        signal = RemoteSignal(signal_name,
                              signal_callback,
                              self._introspection,
                              self.INTERFACE_PATH,
                              self._reactor)

        return q

    @_catch_remote_errors
    def register_signal(self, signal_name, callback):
        """Register a callback when a signal fires

        :param signal_name: Case-sensitve name of the signal
        :param callback: Callable object
        :returns: ~`RemoteSignal`
        """
        if not callable(callback):
            raise WpaSupplicantException('callback must be callable')

        return RemoteSignal(signal_name,
                            callback,
                            self._introspection,
                            self.INTERFACE_PATH,
                            self._reactor)

    @_catch_remote_errors
    def get(self, property_name):
        """Get the value of a property defined by the interface

        :param property_name: Case-sensitive string of the property name
        :returns: Variant type of the properties value
        """
        return self._call_remote('Get', self.INTERFACE_PATH, property_name)

    @_catch_remote_errors
    def set(self, property_name, value):
        """Set the value of a property defined by the interface

        :param property_name: Case-sensitive string of the property name
        :param value: Variant type value to set for property
        :returns: `None`
        """

        logger.info('Setting `%s` -> `%s`', property_name, value)
        return self._call_remote('Set', self.INTERFACE_PATH, property_name, value)


class WpaSupplicant(BaseIface):
    """Interface implemented by the main wpa_supplicant D-Bus object

            Registered in the bus as "fi.w1.wpa_supplicant1"
    """

    INTERFACE_PATH = 'fi.w1.wpa_supplicant1'

    iface = DBusInterface(
        INTERFACE_PATH,
        Method('CreateInterface', arguments='a{sv}', returns='o'),
        Method('GetInterface', arguments='s', returns='o'),
        Method('RemoveInterface', arguments='o'),
        Signal('InterfaceAdded', 'o,a{sv}'),
        Signal('InterfaceRemoved', 'o'),
        Signal('PropertiesChanged', 'a{sv}')
    )

    def __init__(self, *args, **kwargs):
        BaseIface.__init__(self, *args, **kwargs)
        self._interfaces_cache = dict()

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "WpaSupplicant(Interfaces: %s)" % self.get_interfaces()

    #
    # Methods
    #
    def get_interface(self, interface_name):
        """Get D-Bus object related to an interface which wpa_supplicant already controls

        :returns: Interface object that implements the wpa_supplicant Interface API.
        :rtype: :class:`~Interface`
        :raises InterfaceUnknown: wpa_supplicant doesn't know anything about `interface_name`
        :raises UnknownError: An unknown error occurred
        """

        interface_path = self._call_remote_without_introspection('GetInterface',
                                                                 interface_name)
        interface = self._interfaces_cache.get(interface_path, None)
        if interface is not None:
            return interface
        else:
            interface = Interface(interface_path, self._conn, self._reactor)
            self._interfaces_cache[interface_path] = interface
            return interface

    def create_interface(self, interface_name):
        """Registers a wireless interface in wpa_supplicant

        :returns: Interface object that implements the wpa_supplicant Interface API
        :raises InterfaceExists: The `interface_name` specified is already registered
        :raises UnknownError: An unknown error occurred
        """

        interface_path = self._call_remote_without_introspection('CreateInterface',
                                                                 {'Ifname': interface_name})
        return Interface(interface_path, self._conn, self._reactor)

    def remove_interface(self, interface_path):
        """Deregisters a wireless interface from wpa_supplicant

        :param interface_path: D-Bus object path to the interface to be removed
        :returns: None
        :raises InterfaceUnknown: wpa_supplicant doesn't know anything about `interface_name`
        :raises UnknownError: An unknown error occurred
        """

        self._call_remote_without_introspection('RemoveInterface', interface_path)

    #
    # Properties
    #
    def get_debug_level(self):
        """Global wpa_supplicant debugging level

        :returns:  Possible values: "msgdump" (verbose debugging)
                                    "debug" (debugging)
                                    "info" (informative)
                                    "warning" (warnings)
                                    "error" (errors)
        :rtype: str
        """

        return self.get('DebugLevel')

    def get_debug_timestamp(self):
        """ Determines if timestamps are shown in debug logs"""

        return self.get('DebugTimestamp')

    def get_debug_showkeys(self):
        """Determines if secrets are shown in debug logs"""

        return self.get('DebugShowKeys')

    def get_interfaces(self):
        """An array with paths to D-Bus objects representing controlled interfaces"""

        return self.get('Interfaces')

    def get_eap_methods(self):
        """An array with supported EAP methods names"""

        return self.get('EapMethods')


class Interface(BaseIface):
    """Interface implemented by objects related to network interface added to wpa_supplicant"""

    INTERFACE_PATH = 'fi.w1.wpa_supplicant1.Interface'

    iface = DBusInterface(
        INTERFACE_PATH,
        Method('Scan', arguments='a{sv}'),
        Method('AddNetwork', arguments='a{sv}', returns='o'),
        Method('RemoveNetwork', arguments='o'),
        Method('SelectNetwork', arguments='o'),
        Method('Disconnect'),
        Signal('ScanDone', 'b'),
        Signal('PropertiesChanged', 'a{sv}')
    )

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "Interface(Path: %s, Name: %s, State: %s)" % (self.get_path(),
                                                             self.get_ifname(),
                                                             self.get_state())

    #
    # Methods
    #
    def scan(self, type='active', ssids=None, ies=None, channels=None, block=False):
        """Triggers a scan

        :returns: List of `BSS` objects if block=True else None
        :raises InvalidArgs: Invalid argument format
        :raises MethodTimeout: Scan has timed out (only if block=True)
        :raises UnknownError: An unknown error occurred
        """

        # TODO: Handle the other arguments
        scan_options = {
            'Type': type
        }

        # If blocking, register for the ScanDone signal and return BSSs
        if block:
            deferred_queue = self.register_signal_once('ScanDone')
            self._call_remote('Scan', scan_options)  # Trigger scan
            success = deferred_queue.get(timeout=10)
            if success:
                return [BSS(path, self._conn, self._reactor) for path in self.get_all_bss()]
            else:
                raise UnknownError('ScanDone signal received without success')
        else:
            self._call_remote('Scan', scan_options)  # Trigger scan

    def add_network(self, network_cfg):
        """Adds a new network to the interface

        :param network_cfg: Dictionary of config, see wpa_supplicant.conf for k/v pairs
        :returns: `Network` object that was registered w/ wpa_supplicant
        :raises InvalidArgs: Invalid argument format
        :raises UnknownError: An unknown error occurred
        """

        network_path = self._call_remote('AddNetwork', network_cfg)
        return Network(network_path, self._conn, self._reactor)

    def remove_network(self, network_path):
        """Removes a configured network from the interface

        :param network_path: D-Bus object path to the desired network
        :returns: None
        :raises NetworkUnknown: The specified `network_path` is invalid
        :raises InvalidArgs: Invalid argument format
        :raises UnknownError: An unknown error occurred
        """

        self._call_remote('RemoveNetwork', network_path)

    def select_network(self, network_path):
        """Attempt association with a configured network

        :param network_path: D-Bus object path to the desired network
        :returns: None
        :raises NetworkUnknown: The specified `network_path` has not been added
        :raises InvalidArgs: Invalid argument format
        """

        self._call_remote('SelectNetwork', network_path)

    def disconnect_network(self):
        """Disassociates the interface from current network

        :returns: None
        :raises NotConnected: The interface is not currently connected to a network
        """

        self._call_remote('Disconnect')

    #
    # Properties
    #
    def get_ifname(self):
        """Name of network interface controlled by the interface, e.g., wlan0"""

        return self.get('Ifname')

    def get_current_bss(self):
        """BSS object path which wpa_supplicant is associated with

                Returns "/" if is not associated at all
        """

        bss_path = self.get('CurrentBSS')
        if bss_path == '/' or bss_path is None:
            return None
        else:
            return BSS(bss_path, self._conn, self._reactor)

    def get_current_network(self):
        """The `Network` object which wpa_supplicant is associated with

                Returns `None` if is not associated at all
        """

        network_path = self.get('CurrentNetwork')
        if network_path == '/' or network_path is None:
            return None
        else:
            return Network(network_path, self._conn, self._reactor)

    def get_networks(self):
        """List of `Network` objects representing configured networks"""

        networks = list()
        paths = self.get('Networks')
        for network_path in paths:
            if network_path == '/':
                networks.append(None)
            else:
                networks.append(Network(network_path, self._conn, self._reactor))
        return networks

    def get_state(self):
        """A state of the interface.

            Possible values are: "disconnected"
                                 "inactive"
                                 "scanning"
                                 "authenticating"
                                 "associating"
                                 "associated"
                                 "4way_handshake"
                                 "group_handshake"
                                 "completed"
                                 "unknown"
        """

        return self.get('State')

    def get_scanning(self):
        """Determines if the interface is already scanning or not"""

        return self.get('Scanning')

    def get_scan_interval(self):
        """Time (in seconds) between scans for a suitable AP. Must be >= 0"""

        return self.get('ScanInterval')

    def get_fast_reauth(self):
        """Identical to fast_reauth entry in wpa_supplicant.conf"""

        return self.get('FastReauth')

    def get_all_bss(self):
        """List of D-Bus objects paths representing BSSs known to the interface"""

        return self.get('BSSs')

    def get_driver(self):
        """Name of driver used by the interface, e.g., nl80211"""

        return self.get('Driver')

    def get_country(self):
        """Identical to country entry in wpa_supplicant.conf"""

        return self.get('Country')

    def get_bridge_ifname(self):
        """Name of bridge network interface controlled by the interface, e.g., br0"""

        return self.get('BridgeIfname')

    def get_bss_expire_age(self):
        """Identical to bss_expiration_age entry in wpa_supplicant.conf file"""

        return self.get('BSSExpireAge')

    def get_bss_expire_count(self):
        """Identical to bss_expiration_scan_count entry in wpa_supplicant.conf file"""

        return self.get('BSSExpireCount')

    def get_ap_scan(self):
        """Identical to ap_scan entry in wpa_supplicant configuration file.

                Possible values are 0, 1 or 2.
        """

        return self.get('ApScan')

    def set_country(self, country_code):
        self.set('Country', country_code)


class BSS(BaseIface):
    """Interface implemented by objects representing a scanned BSSs (scan results)"""

    INTERFACE_PATH = 'fi.w1.wpa_supplicant1.BSS'

    iface = DBusInterface(
        INTERFACE_PATH,
        Signal('PropertiesChanged', 'a{sv}')
    )

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "BSS(Path: %s, SSID: %s, BSSID: %s, Signal: %sdBm)" % (self.get_path(),
                                                                      self.get_ssid(),
                                                                      self.get_bssid(),
                                                                      self.get_signal_dbm())

    def to_dict(self):
        """Dict representation of a BSS object"""

        elements = (
            ('ssid', self.get_ssid),
            ('rsn', self.get_rsn),
            ('channel', self.get_channel),
            ('privacy', self.get_privacy),
            ('wpa', self.get_wpa),
            ('signal_dbm', self.get_signal_dbm),
            ('signal_quality', self.get_signal_quality),
            ('network_type', self.get_network_type),
            ('privacy', self.get_privacy),
        )
        out = {}
        for k, v in elements:
            try:
                out[k] = v()
            except:
                logger.exception('Error while fetching BSS information')
        return out

    #
    # Properties
    #
    def get_channel(self):
        """Wi-Fi channel number (1-14)"""
        freq = self.get_frequency()

        if freq == 2484:  # Handle channel 14
            return 14
        elif freq > 2472 or freq < 2412:
            logger.warn('Unexpected frequency %s', freq)
            raise WpaSupplicantException('Unexpected frequency in WiFi connection.')
        else:
            return 1 + (freq - 2412) / 5

    def get_ssid(self):
        """SSID of the BSS in ASCII"""

        return "".join(chr(i) for i in self.get('SSID'))

    def get_bssid(self):
        """BSSID of the BSS as hex bytes delimited by a colon"""

        return ":".join(["{:02X}".format(i) for i in self.get('BSSID')])

    def get_frequency(self):
        """Frequency of the BSS in MHz"""

        return self.get('Frequency')

    def get_wpa(self):
        """WPA information of the BSS, empty dictionary indicates no WPA support

        Dictionaries are::

            {
                "KeyMgmt": <Possible array elements: "wpa-psk", "wpa-eap", "wpa-none">,
                "Pairwise": <Possible array elements: "ccmp", "tkip">,
                "Group": <Possible values are: "ccmp", "tkip", "wep104", "wep40">,
                "MgmtGroup": <Possible values are: "aes128cmac">
            }
        """

        return self.get('WPA')

    def get_rsn(self):
        """RSN/WPA2 information of the BSS, empty dictionary indicates no RSN support

        Dictionaries are::

            {
                "KeyMgmt": <Possible array elements: "wpa-psk", "wpa-eap", "wpa-ft-psk", "wpa-ft-eap", "wpa-psk-sha256", "wpa-eap-sha256">,
                "Pairwise": <Possible array elements: "ccmp", "tkip">,
                "Group": <Possible values are: "ccmp", "tkip", "wep104", "wep40">,
                "MgmtGroup": <Possible values are: "aes128cmac">,
            }
        """

        return self.get('RSN')

    def get_ies(self):
        """All IEs of the BSS as a chain of TLVs"""

        return self.get('IEs')

    def get_privacy(self):
        """Indicates if BSS supports privacy"""

        return self.get('Privacy')

    def get_mode(self):
        """Describes mode of the BSS

            Possible values are: "ad-hoc"
                                 "infrastructure"

        """

        return self.get('Mode')

    def get_rates(self):
        """Descending ordered array of rates supported by the BSS in bits per second"""

        return self.get('Rates')

    def get_signal_dbm(self):
        """Signal strength of the BSS in dBm"""

        return self.get('Signal')

    def get_signal_quality(self):
        """Signal strength of the BSS as a percentage (0-100)"""

        dbm = self.get_signal_dbm()
        if dbm <= -100:
            return 0
        elif dbm >= -50:
            return 100
        else:
            return 2 * (dbm + 100)

    def get_network_type(self):
        """Return the network type as a string

        Possible values are:
                'WPA'
                'WPA2'
                'WEP'
                'OPEN'
        """

        if self.get_privacy():
            rsn_key_mgmt = self.get_rsn().get('KeyMgmt')
            if rsn_key_mgmt:
                return 'WPA2'

            wpa_key_mgmt = self.get_wpa().get('KeyMgmt')
            if wpa_key_mgmt:
                return 'WPA'

            return 'WEP'
        else:
            return 'OPEN'


class Network(BaseIface):
    """Interface implemented by objects representing configured networks"""

    INTERFACE_PATH = 'fi.w1.wpa_supplicant1.Network'

    iface = DBusInterface(
        INTERFACE_PATH,
        Signal('PropertiesChanged', 'a{sv}')
    )

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "Network(Path: %s, Properties: %s)" % (self.get_path(),
                                                      self.get_properties())

    #
    # Properties
    #
    def get_properties(self):
        """Properties of the configured network

        Dictionary contains entries from "network" block of  wpa_supplicant.conf.
        All values are string type, e.g., frequency is "2437", not 2437.
        """

        network_properties = self.get('Properties')
        ssid = network_properties.get('ssid', '')
        if ssid:
            quote_chars = {'"', "'"}
            ssid = ssid[1:] if ssid[0] in quote_chars else ssid
            ssid = ssid[:-1] if ssid[-1] in quote_chars else ssid
        network_properties.update({
            'ssid': ssid
        })
        return network_properties

    def get_enabled(self):
        """Determines if the configured network is enabled or not"""

        return self.get('Enabled')


class WpaSupplicantDriver(object):
    """Driver object for starting, stopping and connecting to wpa_supplicant"""

    def __init__(self, reactor):
        self._reactor = reactor

    @_catch_remote_errors
    def connect(self):
        """Connect to wpa_supplicant over D-Bus

        :returns: Remote D-Bus proxy object of the root wpa_supplicant interface
        :rtype: :class:`~WpaSupplicant`
        """

        if not self._reactor.running:
            raise ReactorNotRunning('Twisted Reactor must be started (call .run())')

        @defer.inlineCallbacks
        def get_conn():
            self._reactor.thread_name = threading.currentThread().getName()
            conn = yield client.connect(self._reactor, busAddress='system')
            defer.returnValue(conn)

        conn = threads.blockingCallFromThread(self._reactor, get_conn)
        return WpaSupplicant('/fi/w1/wpa_supplicant1', conn, self._reactor, )
