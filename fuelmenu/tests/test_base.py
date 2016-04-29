from fuelmenu.modules.cobblerconf import cobblerconf
import fuelmenu.settings
import mock
import unittest
import urwid.widget


class BaseModuleTests(unittest.TestCase):
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    def setUp(self, m_get_physical_ifaces, m_get_net):
        super(BaseModuleTests, self).setUp()
        self.responses = {
            "ADMIN_NETWORK/interface": "eth0",
            "ADMIN_NETWORK/netmask": "255.255.255.0",
            "ADMIN_NETWORK/mac": "52:54:00:05:bd:89",
            "ADMIN_NETWORK/ipaddress": "192.168.133.2",
            "ADMIN_NETWORK/dhcp_pool_start": "192.168.133.3",
            "ADMIN_NETWORK/dhcp_pool_end": "192.168.133.254",
            "ADMIN_NETWORK/dhcp_gateway": "192.168.133.2",

        }
        self.parent = mock.MagicMock(managediface=None,
                                     settings=fuelmenu.settings.Settings(
                                         {"ADMIN_NETWORK": {
                                             "interface": "eth0",
                                             "dhcp_pool_start":
                                                 "192.168.133.3",
                                             "dhcp_pool_end":
                                                 "192.168.133.254"}}
                                     ))

        self.cobbler = cobblerconf(self.parent)
        self.cobbler.edits = ["test", urwid.widget.Edit("dhcp_poll_start",
                                                        "192.168.133.3"),
                              urwid.widget.Edit("dhcp_pool_end",
                                                "192.168.133.254"),
                              urwid.widget.Edit("dhcp_gateway",
                                                "192.168.133.2")]
