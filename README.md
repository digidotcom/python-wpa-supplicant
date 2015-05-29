Python wpa_supplicant Library
=============================

Motivation
----------

This library is an implementation of the wpa_supplicant D-Bus interface.  As of now,
there is really no good option for interfacing with wpa_supplicant from Python and
to go a step further, the existing D-Bus libraries are difficult to work with.  This
library abstracts all of that away into a very clean API based on [wpa_supplicant
D-Bus documentation](http://w1.fi/wpa_supplicant/devel/dbus.html).


Overview
--------

This library is more than just a library that can be used programmatically, it also
serves as a command-line tool for easily using wpa_supplicant and exercising the library.

Here is a quick example of creating an wireless interface (wlan0) and performing a scan.

With the library:

```py
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
```

With the CLI, you can do it in 2 commands:

```
$ wpa create_interface wlan0
Interface(Path: /fi/w1/wpa_supplicant1/Interfaces/5, Name: wlan0, State: disconnected)
OK
$ wpa interface scan wlan0
 BSS(Path: /fi/w1/wpa_supplicant1/Interfaces/3/BSSs/13, SSID: WINKHUB-107, BSSID: B4:79:A7:17:38:B5, Signal: -75dBm),
 BSS(Path: /fi/w1/wpa_supplicant1/Interfaces/3/BSSs/20, SSID: Stage, BSSID: 04:18:D6:67:2A:9C, Signal: -67dBm),
 BSS(Path: /fi/w1/wpa_supplicant1/Interfaces/3/BSSs/22, SSID: DAP-GUEST, BSSID: 00:07:7D:34:DB:BD, Signal: -73dBm),
 BSS(Path: /fi/w1/wpa_supplicant1/Interfaces/3/BSSs/24, SSID: HaberHive, BSSID: E0:1C:41:B5:6F:D5, Signal: -71dBm),
 BSS(Path: /fi/w1/wpa_supplicant1/Interfaces/3/BSSs/25, SSID: CMLS Guest WiFi, BSSID: 02:18:4A:91:E9:50, Signal: -79dBm),
 BSS(Path: /fi/w1/wpa_supplicant1/Interfaces/3/BSSs/26, SSID: Shout Public, BSSID: 0A:18:D6:67:27:9E, Signal: -77dBm),
 BSS(Path: /fi/w1/wpa_supplicant1/Interfaces/3/BSSs/29, SSID: ThinkTank, BSSID: 00:12:5F:03:AD:B4, Signal: -79dBm)]
OK
```


Installation
------------

```sh
$ pip install wpa_supplicant
```


Feature Coverage Map
--------------------

Often times adding a command or method to the library is very trivial however due to
the finicky-ness of D-Bus in my experience, it is better to have an explicit method
in the library that maps to a method in the D-Bus interface, even if the implementation
is very cookie-cutter.

Here is the current feature coverage:


|Object               |  Method                         |  Supported|
|---------------------|---------------------------------|-----------|
|root                 |  CreateInterface                |  Yes      |  
|                     |  RemoveInterface                |  Yes      |  
|                     |  GetInterface                   |  Yes      |  
|                     |  Get (properties)               |  Yes      |  
|                     |  Set (properties)               |  Yes      |  
|                     |  Register (signal)              |  Yes      |  
|Interface            |  Scan                           |  Yes      |  
|                     |  Disconnect                     |  Yes      |  
|                     |  AddNetwork                     |  Yes      |  
|                     |  RemoveNetwork                  |  Yes      |  
|                     |  RemoveAllNetworks              |  Yes      |  
|                     |  SelectNetwork                  |  Yes      |  
|                     |  Reassociate                    |   *       |  
|                     |  Reattach                       |   *       |  
|                     |  AddBlob                        |   *       |  
|                     |  RemoveBlob                     |   *       |  
|                     |  GetBlob                        |   *       |  
|                     |  AutoScan                       |   *       |  
|                     |  TDLSDiscover                   |   *       |  
|                     |  TDLSSetup                      |   *       |  
|                     |  TDLSStatus                     |   *       |  
|                     |  TDLSTeardown                   |   *       |  
|                     |  EAPLogoff                      |   *       |  
|                     |  EAPLogon                       |   *       |  
|                     |  NetworkReply                   |   *       |  
|                     |  SetPKCS11EngineAndModulePath   |   *       |  
|                     |  SignalPoll                     |   *       |  
|                     |  FlushBSS                       |   *       |  
|                     |  SubscribeProbReq               |   *       |  
|                     |  UnsubscribeProbReq             |   *       |  
|                     |  Get (properties)               |  Yes      |  
|                     |  Set (properties)               |  Yes      |  
|                     |  Register (signal)              |  Yes      |  
|Interface.WPS        |  Start                          |   *       | 
|                     |  Get (properties)               |   *       | 
|                     |  Set (properties)               |   *       | 
|                     |  Register (signal)              |   *       | 
|Interface.P2PDevice  |  Find                           |   *       | 
|                     |  StopFind                       |   *       | 
|                     |  Listen                         |   *       | 
|                     |  ExtendedListen                 |   *       | 
|                     |  PresenceRequest                |   *       | 
|                     |  ProvisionDiscoveryRequest      |   *       | 
|                     |  Connect                        |   *       | 
|                     |  GroupAdd                       |   *       | 
|                     |  Invite                         |   *       | 
|                     |  Disconnect                     |   *       | 
|                     |  RejectPeer                     |   *       | 
|                     |  Flush                          |   *       |    
|                     |  AddService                     |   *       | 
|                     |  DeleteService                  |   *       | 
|                     |  FlushService                   |   *       | 
|                     |  ServiceDiscoveryRequest        |   *       | 
|                     |  ServiceDiscoveryResponse       |   *       | 
|                     |  ServiceDiscoveryCancelRequest  |   *       | 
|                     |  ServiceUpdate                  |   *       | 
|                     |  Register (signal)              |   *       | 
|BSS                  |  Get (properties)               |  Yes      |  
|                     |  Set (properties)               |  Yes      |  
|                     |  Register (signal)              |  Yes      |  
|Network              |  Get (properties)               |  Yes      |  
|                     |  Set (properties)               |  Yes      |  
|                     |  Register (signal)              |  Yes      |  
|Peer                 |  Get (properties)               |   *       | 
|                     |  Set (properties)               |   *       | 
|                     |  Register (signal)              |   *       | 
|Group                |  Get (properties)               |   *       | 
|                     |  Set (properties)               |   *       | 
|                     |  Register (signal)              |   *       | 
|PersistentGroup      |  Get (properties)               |   *       | 
|                     |  Set (properties)               |   *       | 
|                     |  Register (signal)              |   *       |