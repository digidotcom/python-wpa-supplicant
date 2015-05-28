from twisted.internet import defer
from collections import OrderedDict
from txdbus import client, error
import mock
import re


def init():
    """Call at the beginning of ``testCase.setUp`` to mock D-Bus Layer"""

    conn = MockConnection()

    @defer.inlineCallbacks
    def mock_connect(reactor, busAddress):
        yield
        defer.returnValue(conn)

    client.connect = mock_connect


class MockDBusObject(object):
    """Base class for mocked txdbus objects which implement D-Bus interfaces"""

    def __init__(self, *args, **kwargs):
        self.callRemote = mock.Mock(side_effect=self._callRemote)
        self.notifyOnSignal = mock.Mock(side_effect=self._notifyOnSignal)
        self.cancelSignalNotification = mock.Mock(side_effect=self._cancelSignalNotification)

        self._signals = dict()

    def _callRemote(self, method_name, *args):
        if method_name == 'Get':
            property_name = args[1]
            property_method = getattr(self, 'Get_%s' % property_name)
            if property_method:
                deferred = mock.Mock()
                deferred.result = property_method()
                deferred.called = True
                return deferred
            else:
                return None

        elif method_name == 'Set':
            return NotImplementedError()

        else:
            native_method = getattr(self, method_name)
            if native_method:
                deferred = mock.Mock()
                deferred.result = native_method(*args)
                deferred.called = True
                return deferred

    def _notifyOnSignal(self, signal_name, callback, interface=None):
        d = defer.Deferred()
        d.addCallback(callback)
        self._signals.setdefault(signal_name, list()).append(d)
        return d

    def _cancelSignalNotification(self, rule_id):
        pass

    def fire_signal(self, signal_name, value):
        deferreds = self._signals.get(signal_name, None)
        if deferreds is not None:
            for d in deferreds:
                d.callback(value)


class MockWpaSupplicant(MockDBusObject):
    """Mock wpa_supplicant `Root` object"""

    def __init__(self, *args, **kwargs):
        MockDBusObject.__init__(self, *args, **kwargs)
        self._valid_interfaces = {
            'wlan0': '/fi/w1/wpa_supplicant1/Interfaces/3',
            'sta0': '/fi/w1/wpa_supplicant1/Interfaces/4'
        }
        self._created_interfaces = []

    #--------------------------------------------------------------------------
    # Methods
    #--------------------------------------------------------------------------
    def GetInterface(self, interface_name):
        if interface_name in self._valid_interfaces:
            return self._valid_interfaces.get(interface_name)
        else:
            raise error.RemoteError('fi.w1.wpa_supplicant1.InterfaceUnknown')

    def RemoveInterface(self, interface_path):
        for i, path in enumerate(self._created_interfaces[:]):
            if path == interface_path:
                del self._created_interfaces[i]
                break
        else:
            raise error.RemoteError('fi.w1.wpa_supplicant1.InterfaceUnknown')

    def CreateInterface(self, cfg):
        if not isinstance(cfg, dict):
            raise error.RemoteError('fi.w1.wpa_supplicant1.InvalidArgs')

        interface_name = cfg.get('Ifname', None)  # required argument
        if interface_name is None:
            raise error.RemoteError('fi.w1.wpa_supplicant1.InvalidArgs')

        iface_path = self._valid_interfaces.get(interface_name)

        if not iface_path:
            raise error.RemoteError('fi.w1.wpa_supplicant1.UnknownError')

        if iface_path in self._created_interfaces:
            raise error.RemoteError('fi.w1.wpa_supplicant1.InterfaceExists')

        self._created_interfaces.append(iface_path)
        return iface_path

    #--------------------------------------------------------------------------
    # Properties
    #--------------------------------------------------------------------------
    def Get_Interfaces(self):
        return None

    def Get_EapMethods(self):
        return None

    def Get_DebugLevel(self):
        return None

    def Get_DebugTimestamp(self):
        return None

    def Get_DebugLevel(self):
        return None


class MockInterfaceObject(MockDBusObject):
    """Mock wpa_supplicant `Interface` object"""

    def __init__(self, *args, **kwargs):
        MockDBusObject.__init__(self, *args,  **kwargs)

        # Internal State
        self._network_counter = -1
        self._networks = dict()
        self._current_network = None

    #--------------------------------------------------------------------------
    # Methods
    #--------------------------------------------------------------------------
    def Scan(self, scan_config):
        return None

    def AddNetwork(self, cfg):
        self._network_counter += 1
        network_path = '/fi/w1/wpa_supplicant1/Networks/%s' % self._network_counter
        self._networks[network_path] = cfg
        return network_path

    def RemoveNetwork(self, network_path):
        if network_path in self._networks:
            del self._networks[network_path]
        else:
            raise error.RemoteError('fi.w1.wpa_supplicant1.NetworkUnknown')

    def SelectNetwork(self, network_path):
        self._current_network = network_path

    def Disconnect(self):
        if self._current_network is None:
            raise error.RemoteError('fi.w1.wpa_supplicant1.NotConnected')
        else:
            self._current_network = None

    #--------------------------------------------------------------------------
    # Properties
    #--------------------------------------------------------------------------
    def Get_CurrentNetwork(self):
        return self._current_network

    def Get_Ifname(self):
        return 'wlan0'

    def Get_BSSs(self):
        return ['/fi/w1/wpa_supplicant1/Interfaces/3/BSSs/1234', ]

    def Get_CurrentBSS(self):
        return '/fi/w1/wpa_supplicant1/Interfaces/3/BSSs/1234'

    def Get_ApScan(self):
        return None

    def Get_Scanning(self):
        return None

    def Get_State(self):
        return None

    def Get_Capabilities(self):
        return None


class MockBSSObject(MockDBusObject):
    """Mock txdbus/wpa_supplicant .fi.w1.wpa_supplicant1.BSS object"""

    #--------------------------------------------------------------------------
    # Properties
    #--------------------------------------------------------------------------
    def Get_BSSID(self):
        return [1, 2, 3, 4]

    def Get_SSID(self):
        return [1, 2, 3, 4]

    def Get_WPA(self):
        return {'Group': '', 'KeyMgmt': [], 'Pairwise': []}

    def Get_RSN(self):
        return None

    def Get_IEs(self):
        return None

    def Get_Privacy(self):
        return False

    def Get_Mode(self):
        return 'infrastructure'

    def Get_Frequency(self):
        return 2462

    def Get_Rates(self):
        return [54000000, 48000000, 6000000]

    def Get_Signal(self):
        return -60


class MockNetworkObject(MockDBusObject):
    """Mock txdbus/wpa_supplicant .fi.w1.wpa_supplicant1.Networks object"""

    def Get_Properties(self):
        return {
            u'ap_max_inactivity': u'0',
            u'beacon_int': u'0',
            u'bg_scan_period': u'-1',
            u'disabled': u'0',
            u'dtim_period': u'0',
            u'eap_workaround': u'-1',
            u'eapol_flags': u'3',
            u'engine': u'0',
            u'engine2': u'0',
            u'fragment_size': u'1398',
            u'frequency': u'0',
            u'group': u'CCMP TKIP WEP104 WEP40',
            u'ignore_broadcast_ssid': u'0',
            u'key_mgmt': u'WPA-PSK WPA-EAP',
            u'mixed_cell': u'0',
            u'mode': u'0',
            u'ocsp': u'0',
            u'pairwise': u'CCMP TKIP',
            u'peerkey': u'0',
            u'priority': u'0',
            u'proactive_key_caching': u'-1',
            u'proto': u'WPA RSN',
            u'scan_ssid': u'0',
            u'ssid': u'"wdnu-dvt1"',
            u'wep_tx_keyidx': u'0',
            u'wpa_ptk_rekey': u'0'
        }


class MockConnection(object):
    """Mock txdbus client connection to a D-Bus server"""

    mock_objects = OrderedDict([
        ('/fi/w1/wpa_supplicant1/Interfaces/.+/BSSs/.+', MockBSSObject),
        ('/fi/w1/wpa_supplicant1/Networks/.+', MockNetworkObject),
        ('/fi/w1/wpa_supplicant1/Interfaces/.+', MockInterfaceObject),
        ('/fi/w1/wpa_supplicant1', MockWpaSupplicant)
    ])

    @defer.inlineCallbacks
    def getRemoteObject(self, busName, objectPath, interfaces=None):
        interface_object = None
        for opath, interface in self.mock_objects.items():
            match = re.match(opath, objectPath)
            if match:
                interface_object = interface()
                break
        yield
        defer.returnValue(interface_object)
