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

    @mock.patch('fuelmenu.common.network.netifaces')
    def test_get_physical_ifaces(self, netifaces_mock):
        all_ifaces = ['abc0', 'veth0', 'docker0']
        netifaces_mock.interfaces.return_value = all_ifaces
        data = network.getPhysicalIfaces()
        netifaces_mock.interfaces.assert_called_once_with()
        self.assertEqual(['abc0'], data)
