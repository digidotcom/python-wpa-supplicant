Python wpa_supplicant Library
=============================

[Full Documentation](http://digidotcom.github.io/python-wpa-supplicant/)

Motivation
----------

This library provides an interface to the wpa_supplicant D-Bus interface.  As of now,
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
from wpa_supplicant.core import WpaSupplicantDriver
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
```

With the CLI, you can do it in 2 commands:

```
$ wpa create_interface wlan0
Interface(Path: /fi/w1/wpa_supplicant1/Interfaces/5, Name: wlan0, State: disconnected)
OK
$ wpa interface wlan0 scan
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

License
-------

This software is open-source. Copyright (c), Digi International Inc., 2015.

This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
If a copy of the MPL was not distributed with this file, you can obtain one at
http://mozilla.org/MPL/2.0/.

Digi, Digi International, the Digi logo, the Digi website, and Digi
Device Cloud are trademarks or registered trademarks of Digi
International, Inc. in the United States and other countries
worldwide. All other trademarks are the property of their respective
owners.

THE SOFTWARE AND RELATED TECHNICAL INFORMATION IS PROVIDED "AS IS"
WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL DIGI OR ITS
SUBSIDIARIES BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION IN CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT
OF OR IN CONNECTION WITH THE SOFTWARE AND TECHNICAL INFORMATION
HEREIN, INCLUDING ALL SOURCE AND OBJECT CODES, IRRESPECTIVE OF HOW IT
IS USED. YOU AGREE THAT YOU ARE NOT PROHIBITED FROM RECEIVING THIS
SOFTWARE AND TECHNICAL INFORMATION UNDER UNITED STATES AND OTHER
APPLICABLE COUNTRY EXPORT CONTROL LAWS AND REGULATIONS AND THAT YOU
WILL COMPLY WITH ALL APPLICABLE UNITED STATES AND OTHER COUNTRY EXPORT
LAWS AND REGULATIONS WITH REGARD TO USE AND EXPORT OR RE-EXPORT OF THE
SOFTWARE AND TECHNICAL INFORMATION.
