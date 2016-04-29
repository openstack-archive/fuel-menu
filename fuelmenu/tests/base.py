# -*- coding: utf-8 -*-

#    Copyright 2016 Mirantis, Inc.
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

import unittest

import mock

from fuelmenu import settings


class BaseModuleTests(unittest.TestCase):
    SETTINGS = {"ADMIN_NETWORK": {
        "interface": "eth0",
        "netmask": "255.255.255.0",
        "ipaddress": "192.168.133.2",
        "dhcp_pool_start": "192.168.133.3",
        "dhcp_pool_end": "192.168.133.254",
        "dhcp_gateway": "192.168.133.2"
    }}

    def setUp(self):
        super(BaseModuleTests, self).setUp()
        self.parent = mock.Mock(managediface="eth0", apply_tasks=set(),
                                settings=settings.Settings(
                                    self.SETTINGS))
