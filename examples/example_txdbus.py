"""Example of using the raw txdbus APIs

Note: There are some hardcoded values in this example and should not be expected
to run on every PC but serves as a reference.
"""

from twisted.internet import reactor, defer
from txdbus import client, error
from txdbus.interface import DBusInterface, Method, Signal
import time

dbus_name = 'fi.w1.wpa_supplicant1'
root_iface_str = 'fi.w1.wpa_supplicant1'
root_iface_obj_path = "/" + root_iface_str.replace('.', '/')

interface_iface_str = root_iface_str + ".Interface"
interface_iface = DBusInterface(interface_iface_str,
                                Signal('ScanDone', 'b'),
                                Method('Scan', arguments='a{sv}'),
                                Method('AddNetwork', arguments='a{sv}', returns='o'),
                                Method('RemoveNetwork', arguments='o'),
                                Method('SelectNetwork', arguments='o'))


@defer.inlineCallbacks
def set_mode_example():
    cli = yield client.connect(reactor, busAddress='system')

    root_obj = yield cli.getRemoteObject(dbus_name, root_iface_obj_path)
    print "Root Object: %s" % root_obj

    wlan0_obj_path = yield root_obj.callRemote('GetInterface', 'wlan1')
    print "WLAN0 Object Path: %s" % wlan0_obj_path

    wlan0_obj = yield cli.getRemoteObject(dbus_name, wlan0_obj_path, interface_iface)
    print "WLAN0 Object: %s" % wlan0_obj

    # wpa_supplicant will validate keys, but does not validate values.
    # There are a bunch of additional configuration options for 801.11ac.
    network_settings = {
        "disabled": 0,  # Not disabled
        # "id_str": "ExtScriptID",
        "ssid": "funny-ssid",  # SSID
        # "frequency": 2412,  # When IBSS only, ignored in mode=0
        # "proto": "WPA",
        # "bssid": "Somebss",
        "mode": 0,  # 0 = managed(default), 1 = IBSS (Ad-hoc, p2p), 2: AP (access point)
        # "freq_list": None,   #
        # "bgscan": "simple:30:-45:300",
        # "proto": "WPA",
        "key_mgmt": "WPA-PSK",
        # "ieee80211w": 0,
        "auth_alg": "OPEN",
        "pairwise": "CCMP",
        # "group": None,
        "psk": "funnypsk",
        # "eapol_flags": 3,
        # "macsec_policy": 0,
        # "mixed_cell": 0,
        # "proactive_key_caching": 0,
        # "wep_key0": None,
        # "wep_key1": None,
        # "wep_key2": None,
        # "wep_key3": None,
        # "wep_tx_keyidx": None,
        # "peerkey": 0,
        # "wpa_ptk_rekey": 100000,
        # "eap": "MD5 MSCHAPV2 OTP GTC TLS PEAP TTLS",
        # "identity": "Some one",  # EAP identity
        # "anonymous_identity": "Anonymous one",  # EAP anonymous
        # "password": "Some one's password",
        # "ca_cert": "file path to CA certificates",
        # "ca_path": "directory path for CA certificate files (PEM)",
        # "client_cert": "file path to client certificate file",
        # "private_key": "file path to private key",
        # "private_key_passwd": "password for private key",
        # "dh_file": "file path to DH/DSA params",
        # "subject_match": "x",
        # "altsubject_match": "alt",
        # "phase1": "peapver=1",  # See wpa_supplicant.conf for phase1 TLS details
        # "phase2": "auth=MSCHAPV2",  # See wpa_supplicant.conf for phase2 TLS details
        # "ca_cert2": "file path to phase2 CA certificates",
        # "ca_path2": "directory path for phase2 CA certificate files (PEM)",
        # "client_cert2": "file path to phase2 client certificate",
        # "private_key2": "file path to phase2 client private key",
        # "private_key2_passwd": "password for phase2 private key",
        # "dh_file2": "file path to phase2 DH/DSA params",
        # "subject_match2": "x",
        # "altsubject_match2": "alt2",
        # "fragment_size": "1398",
        # "ocsp": 0,
        # "ap_max_inactivity": 300,  # Seconds
        # "disable_ht": "0",  # High Throughput 802.11n enabled
        # "disable_ht40": 0,  # High Throughput 802.11n enabled (40 MHz channel)
        # "disable_sgi": 0,  # short guard interval enabled
        # "disable_ldpc": 0,  # low density parity check enabled
        # "ht40_intolerant": 0,  # HT-40 tolerated
        # "ht_mcs": "",  # Use all available
        # "disable_max_amsdu": -1,
        # "ampdu_factor": 3,
        # "ampdu_density": -1,
        # "disable_vht": 0,  # Very High Throughput 802.11ac enabled
    }

    network_obj = yield wlan0_obj.callRemote('AddNetwork', network_settings)
    print "Network Object Path: %s" % network_obj
    yield wlan0_obj.callRemote('SelectNetwork', network_obj)
    time.sleep(20)
    yield wlan0_obj.callRemote('RemoveNetwork', network_obj)
    reactor.stop()


reactor.callWhenRunning(set_mode_example)
reactor.run()
