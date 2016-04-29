import unittest

import mock

import fuelmenu.settings


class BaseModuleTests(unittest.TestCase):
    def setUp(self):
        super(BaseModuleTests, self).setUp()
        self.parent = mock.Mock(managediface="eth0",
                                     settings=fuelmenu.settings.Settings(
                                         {"ADMIN_NETWORK": {
                                             "interface": "eth0",
                                             "dhcp_pool_start":
                                                 "192.168.133.3",
                                             "dhcp_pool_end":
                                                 "192.168.133.254"}}
                                     ))
