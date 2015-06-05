Development Tips and Tricks
===========================

D-Bus Configuration
-------------------

Give your user permissions to use the D-Bus system bus:

Add the following lines to the following files:

**/etc/dbus-1/system.d/org.freedesktop.ModemManager1.conf**

.. code-block:: shell

    <policy user="root">
        <allow own="org.freedesktop.ModemManager1"/>
    </policy>


**/etc/dbus-1/system.d/wpa_supplicant.conf**

.. code-block:: shell

    <policy user="root">
        <allow own="fi.epitest.hostap.WPASupplicant"/>
        <allow own="fi.w1.wpa_supplicant1"/>
    </policy>

Then, reset dbus:

.. code-block:: shell

    $ /etc/init.d/dbus stop
    $ /etc/init.d/dbus start


Disabling NetworkManager on Ubuntu
----------------------------------

It is often desired to disable NetworkMananger on your dev box because the WDNU-II
application is essentially the same thing and they likely do not play nicely together.
To do so while keeping your DHCP ethernet connection intact (interwebs), do the following:

.. code-block:: shell

    $ sudo service network-manager stop
    $ sudo ifconfig eth0 up  (make sure your interface is actually eth0!!)
    $ sudo dhclient eth0
