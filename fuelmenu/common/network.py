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

import json
import os

import netaddr
import netifaces
from oslo_log import log as logging

from fuelmenu.common import errors
from fuelmenu.common.utils import execute

log = logging.getLogger('fuelmenu.common.network')


def inSameSubnet(ip1, ip2, netmask_or_cidr):
    if not all([ip1, ip2]):
        return False
    try:
        cidr1 = netaddr.IPNetwork("%s/%s" % (ip1, netmask_or_cidr))
        cidr2 = netaddr.IPNetwork("%s/%s" % (ip2, netmask_or_cidr))
        return cidr1 == cidr2
    except netaddr.AddrFormatError as e:
        log.exception(e.message)
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
    # Return a list excluding ip and broadcast IPs
    try:
        ipn = netaddr.IPNetwork("%s/%s" % (ip, netmask))
        ipn_list = list(ipn)
        # Drop broadcast and network ip
        ipn_list = ipn_list[1:-1]
        # Drop ip
        ipn_list[:] = [value for value in ipn_list if str(value) != ip]
        # Drop additionalip
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


def is_interface_has_ip(interface):
    addr = netifaces.ifaddresses(interface)
    return netifaces.AF_INET in addr


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
            raise errors.NetworkException("Invalid specified interface: "
                                          "{0}".format(iface))
    return ips


def range(startip, endip):
    # Return a list of IPs between startip and endip
    try:
        return list(netaddr.iter_iprange(startip, endip))
    except netaddr.AddrFormatError:
        raise errors.BadIPException("Invalid IP address(es) specified.")


def intersects(range1, range2):
    # Returns true if any IPs in range1 exist in range2
    return range1 & range2


def netmaskToCidr(netmask):
    return sum([bin(int(x)).count('1') for x in netmask.split('.')])


def addr_in_cidr_notation(ip, netmask):
    try:
        return str(netaddr.IPNetwork("{0}/{1}".format(ip, netmask)))
    except Exception:
        log.exception('Invalid IP address or netmask, '
                      'ip: "%s", netmask: "%s"', ip, netmask)


def duplicateIPExists(ip, iface, arping_bind=False):
    """Checks for duplicate IP addresses using arping.

    Don't use arping_bind unless you know what you are doing.

    :param ip: IP to scan for
    :param iface: Interface on which to send requests
    :param arping_bind: Bind to IP when probing (IP must be already assigned.)
    :returns: boolean
    """
    if arping_bind:
        bind_ip = ip
    else:
        bind_ip = "0.0.0.0"
    command = ["arping", "-D", "-c3", "-w1", "-I", iface, "-s", bind_ip, ip]
    code, _, _ = execute(command)
    return (code != 0)


def search_external_dhcp(iface, timeout):
    """Checks for non-local DHCP servers discoverable on specified iface.

    :param iface: Interface for scanning.
    :type iface: string
    :param timeout: command timeout in seconds.
    :type timeout: int
    :returns: list of DHCP data
    :raises: errors.NetworkException
    """
    command = ["dhcpcheck", "listservers", "--timeout", str(timeout), "-f",
               "json", "--ifaces", iface]
    try:
        upIface(iface)  # ensure iface is up
        _, output, _ = execute(command)
        data = json.loads(output.strip())
        # FIXME(mattymo): Sometimes dhcpcheck prints json with keys, but no
        # values instead of empty array.
        if len(data) and not data[0]['mac']:
            return []
        return data
    except ValueError:
        # ValueError thrown if output is completely empty
        log.debug('Unable to parse JSON.')
        return []
    except OSError:
        raise errors.NetworkException('Unable to check DHCP.')


def upIface(iface):
    code, _, _ = execute(["ifconfig", iface, "up"])
    if code != 0:
        raise errors.NetworkException(
            "Failed to up interface {0}".format(iface))


def get_iface_info(iface, address_family=netifaces.AF_INET):
    return netifaces.ifaddresses(iface)[address_family][0]
