# Copyright 2013 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from fuelmenu.common.errors import BadIPException
from fuelmenu.common.errors import NetworkException

import json
import netaddr
import netifaces
import os
import subprocess


def inSameSubnet(ip1, ip2, netmask_or_cidr):
    try:
        cidr1 = netaddr.IPNetwork("%s/%s" % (ip1, netmask_or_cidr))
        cidr2 = netaddr.IPNetwork("%s/%s" % (ip2, netmask_or_cidr))
        return cidr1 == cidr2
    except netaddr.AddrFormatError:
        return False


def getCidr(ip, netmask):
    try:
        ipn = netaddr.IPNetwork("%s/%s" % (ip, netmask))
        return str(ipn.cidr)
    except netaddr.AddrFormatError:
        return False


def getCidrSize(cidr):
    try:
        ipn = netaddr.IPNetwork(cidr)
        return ipn.size
    except netaddr.AddrFormatError:
        return False


def getNetwork(ip, netmask, additionalip=None):
    #Return a list excluding ip and broadcast IPs
    try:
        ipn = netaddr.IPNetwork("%s/%s" % (ip, netmask))
        ipn_list = list(ipn)
        #Drop broadcast and network ip
        ipn_list = ipn_list[1:-1]
        #Drop ip
        ipn_list[:] = [value for value in ipn_list if str(value) != ip]
        #Drop additionalip
        if additionalip:
            ipn_list[:] = [value for value in ipn_list if
                           str(value) != additionalip]

        return ipn_list
    except netaddr.AddrFormatError:
        return False


def get_physical_ifaces():
    """Returns a sorted list of physical interfaces."""
    ifaces = netifaces.interfaces()
    return sorted(filter(is_physical, ifaces))


def is_physical(iface):
    """Returns true if virtual is not in the iface's linked path."""
    # A virtual interface has a symlink in /sys/class/net pointing to
    # a subdirectory of /sys/devices/virtual
    # $ cd /sys/class/net
    # $ readlink lo
    # ../../devices/virtual/net/lo
    # $ readlink enp2s0f0
    # ../../devices/pci0000:00/0000:00:1c.0/0000:02:00.0/net/enp2s0f0
    return 'virtual' not in \
        os.path.realpath('/sys/class/net/{0}'.format(iface))


def list_host_ip_addresses(interfaces="all"):
    """Returns a list of IP addresses for optionally specified interfaces."""
    if interfaces == "all":
        interfaces = netifaces.interfaces()

    ips = []
    for iface in interfaces:
        try:
            ip = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
            ips.append(ip)
        except (KeyError, IndexError):
            # Skip if interface has no IP
            continue
        except ValueError:
            raise NetworkException("Invalid specified interface: "
                                   "{0}".format(iface))
    return ips


def range(startip, endip):
    #Return a list of IPs between startip and endip
    try:
        return list(netaddr.iter_iprange(startip, endip))
    except netaddr.AddrFormatError:
        raise BadIPException("Invalid IP address(es) specified.")


def intersects(range1, range2):
    #Returns true if any IPs in range1 exist in range2
    return range1 & range2


def netmaskToCidr(netmask):
    return sum([bin(int(x)).count('1') for x in netmask.split('.')])


def duplicateIPExists(ip, iface, arping_bind=False):
    """Checks for duplicate IP addresses using arping
    Don't use arping_bind unless you know what you are doing.

    :param ip: IP to scan for
    :param iface: Interface on which to send requests
    :param arping_bind: Bind to IP when probing (IP must be already assigned.)
    :returns: boolean
    """
    noout = open('/dev/null', 'w')
    if arping_bind:
        bind_ip = ip
    else:
        bind_ip = "0.0.0.0"
    no_dupes = subprocess.call(["arping", "-D", "-c3", "-w1", "-I", iface,
                               "-s", bind_ip, ip], stdout=noout, stderr=noout)
    return (no_dupes != 0)


def searchExternalDHCP(iface, timeout):
    """Checks for non-local DHCP servers discoverable on specified iface

    :param iface: Interface for scanning
    :param timeout: command timeout in seconds
    :returns: list of DHCP data
    """
    command = ["dhcpcheck", "discover", "--timeout", str(timeout), "-f",
               "json", "--ifaces", iface]
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        output, errout = process.communicate()
        data = json.loads(output.strip())
        # FIXME(mattymo): Sometimes dhcpcheck prints json with keys, but no
        # values instead of empty array.
        if len(data) and not data[0]['mac']:
            return []
        return data
    except OSError:
        raise NetworkException('Unable to check DHCP.')


def upIface(iface):
    noout = open('/dev/null', 'w')
    result = subprocess.call(["ifconfig", iface, "up"], stdout=noout,
                             stderr=noout)
    if result != 0:
        raise NetworkException("Failed to up interface {0}".format(iface))
