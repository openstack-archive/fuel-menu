import unittest

import mock

import fuelmenu.settings


class BaseModuleTests(unittest.TestCase):
    def setUp(self):
        super(BaseModuleTests, self).setUp()
        self.parent = mock.Mock(managediface="eth0", apply_tasks=set(),
                                settings=fuelmenu.settings.Settings(
                                    {"ADMIN_NETWORK": {
                                        "interface": "eth0",
                                        "netmask": "255.255.255.0",
                                        "ipaddress": "192.168.133.2",
                                        "dhcp_pool_start":
                                            "192.168.133.3",
                                        "dhcp_pool_end":
                                            "192.168.133.254",
                                        "dhcp_gateway": "192.168.133.2"
                                    }}))
