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

from fuelmenu.common import network

import mock
import unittest


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
