# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import json
import mock
from mock import patch
import subprocess

import netifaces
import unittest

from fuelmenu.common import errors
from fuelmenu.common import network


class TestUtils(unittest.TestCase):

    @mock.patch('fuelmenu.common.network.os')
    def test_is_physical_false(self, os_mock):
        iface = 'lo'
        os_mock.path.realpath.return_value = '/sys/devices/virtual/net/lo'
        self.assertFalse(network.is_physical(iface))
        os_mock.path.realpath.assert_called_once_with(
            '/sys/class/net/{0}'.format(iface))

    @mock.patch('fuelmenu.common.network.os')
    def test_is_physical_true(self, os_mock):
        iface = 'eth0'
        os_mock.path.realpath.return_value = \
            '/sys/devices/pci0000:00/0000:00:03.0/net/eth0'
        self.assertTrue(network.is_physical(iface))
        os_mock.path.realpath.assert_called_once_with(
            '/sys/class/net/{0}'.format(iface))

    @mock.patch('fuelmenu.common.network.netifaces')
    @mock.patch('fuelmenu.common.network.is_physical')
    def test_get_physical_ifaces(self, is_physical_mock, netifaces_mock):
        all_ifaces = ['eth0', 'lo', 'veth0']

        is_physical_mock.side_effect = [True, False, False]
        netifaces_mock.interfaces.return_value = all_ifaces
        data = network.get_physical_ifaces()
        netifaces_mock.interfaces.assert_called_once_with()
        self.assertEqual(['eth0'], data)

    @mock.patch('fuelmenu.common.network.netifaces')
    def test_list_host_ip_addresses(self, netifaces_mock):
        all_ifaces = ['eth0', 'lo', 'veth0']
        netifaces_mock.AF_INET = netifaces.AF_INET
        netifaces_mock.interfaces.return_value = all_ifaces
        netifaces_mock.ifaddresses.side_effect = [
            {netifaces.AF_INET: [{'addr': '10.20.0.2'}]},
            {netifaces.AF_INET: [{'addr': '127.0.0.1'}]},
            {netifaces.AF_INET: [{'addr': '192.168.122.1'}]},
        ]
        data = network.list_host_ip_addresses()
        netifaces_mock.interfaces.assert_called_once_with()
        self.assertEqual(['10.20.0.2', '127.0.0.1', '192.168.122.1'], data)

    @mock.patch('fuelmenu.common.network.netifaces')
    def test_list_host_ip_addresses_ignore_no_ip(self, netifaces_mock):
        all_ifaces = ['eth0']
        netifaces_mock.AF_INET = netifaces.AF_INET
        netifaces_mock.interfaces.return_value = all_ifaces
        netifaces_mock.ifaddresses.return_value = []
        data = network.list_host_ip_addresses()
        netifaces_mock.interfaces.assert_called_once_with()
        self.assertEqual([], data)

    @mock.patch('fuelmenu.common.network.netifaces')
    def test_list_host_ip_addresses_raises_for_bad_iface(self, netifaces_mock):
        all_ifaces = ['eth0']
        bad_iface = "nonexistent"
        netifaces_mock.AF_INET = netifaces.AF_INET
        netifaces_mock.interfaces.return_value = all_ifaces
        netifaces_mock.ifaddresses.side_effect = ValueError(
            "You must specify a valid interface name.")
        self.assertRaises(errors.NetworkException,
                          network.list_host_ip_addresses,
                          bad_iface)

    def make_process_mock(self, return_code=0, retval=('stdout', 'stderr')):
        process_mock = mock.Mock(
            communicate=mock.Mock(return_value=retval))
        process_mock.stdout = ['Stdout line 1', 'Stdout line 2']
        process_mock.returncode = return_code

        return process_mock

    def test_search_external_dhcp(self):
        output = '[{"mac": "52:54:00:12:35:02"}]'

        interface = "abc0"
        timeout = 1

        process_mock = self.make_process_mock(return_code=0,
                                              retval=(output, ''))
        with patch.object(subprocess, 'Popen', return_value=process_mock):
            data = network.search_external_dhcp(interface, timeout)
            process_mock.communicate.assert_called_once_with(input=None)
            self.assertEqual(data, json.loads(output))

    def test_search_external_dhcp_nodata(self):
        output = ''

        interface = "abc0"
        timeout = 1

        process_mock = self.make_process_mock(return_code=0,
                                              retval=(output, ''))
        with patch.object(subprocess, 'Popen', return_value=process_mock):
            data = network.search_external_dhcp(interface, timeout)
            process_mock.communicate.assert_called_once_with(input=None)
            self.assertEqual(data, [])

    def test_search_external_dhcp_raises_exception(self):
        interface = "abc0"
        timeout = 1

        with patch.object(subprocess, 'Popen', side_effect=OSError()):
            self.assertRaises(errors.NetworkException,
                              network.search_external_dhcp,
                              interface, timeout)
