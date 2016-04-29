import mock
import urwid.widget

from fuelclient.cli import error
from fuelmenu.modules.cobblerconf import CobblerConfig
from fuelmenu.tests.test_base import BaseModuleTests


class TestCobblerConfig(BaseModuleTests):
    def set_value_to_edits(self, field_name, value):
        for field in self.cobbler.edits[1:]:
            if field_name == field.caption:
                field.set_edit_text(value)

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
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    def setUp(self, m_get_dhcp, m_get_default_gateway_linux, m_get_net,
              m_get_physical_ifaces):
        super(TestCobblerConfig, self).setUp()
        self.responses = {
            "ADMIN_NETWORK/interface": "eth0",
            "ADMIN_NETWORK/netmask": "255.255.255.0",
            "ADMIN_NETWORK/mac": "52:54:00:05:bd:89",
            "ADMIN_NETWORK/ipaddress": "192.168.133.2",
            "ADMIN_NETWORK/dhcp_pool_start": "192.168.133.3",
            "ADMIN_NETWORK/dhcp_pool_end": "192.168.133.254",
            "ADMIN_NETWORK/dhcp_gateway": "192.168.133.2",
        }

        self.cobbler = CobblerConfig(self.parent)
        self.cobbler.edits = ["DHCP Pool for node discovery",
                              urwid.widget.Edit("dhcp_pool_start",
                                                "192.168.133.3"),
                              urwid.widget.Edit("dhcp_pool_end",
                                                "192.168.133.254"),
                              urwid.widget.Edit("dhcp_gateway",
                                                "192.168.133.2")]

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    def test_check(self, m_getDHCP,
                   m_get_default_gateway_linux,
                   m_get_physical_ifaces,
                   m_get_net, m_duplicateIPExists, m_search_external_dhcp,
                   m_post_deploy):
        self.assertEqual(self.cobbler.check(None), self.responses)
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=True)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    def test_check_post_deploy(self, m_getDHCP,
                               m_get_default_gateway_linux,
                               m_get_physical_ifaces,
                               m_get_net, m_duplicateIPExists,
                               m_search_external_dhcp,
                               m_post_deploy):
        self.assertEqual(self.cobbler.check(None), self.responses)
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_incorrect_management_iface_addr(self, m_MH_display_failed,
                                                   m_getDHCP,
                                                   m_get_default_gateway_linux,
                                                   m_get_physical_ifaces,
                                                   m_get_net,
                                                   m_duplicateIPExists,
                                                   m_search_external_dhcp,
                                                   m_post_deploy):
        self.assertEqual(self.cobbler.check(None), False)
        m_MH_display_failed.assert_called_once_with(self.cobbler,
                                                    ['Go to Interfaces to'
                                                     ' configure management'
                                                     ' interface first.'])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_not_called()
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={"addr": "192.168.133.2",
                              "netmask": "255.255.255.0",
                              "broadcast": "192.168.133.255",
                              "mac": "52:54:00:05:bd:89",
                              "link": "up",
                              "bootproto": "dhcp"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_incorrect_running_dhcp(self, m_MH_display_failed, m_getDHCP,
                                          m_get_default_gateway_linux,
                                          m_get_physical_ifaces, m_get_net,
                                          m_duplicateIPExists,
                                          m_search_external_dhcp,
                                          m_post_deploy):
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["eth0 is running DHCP. Change it to static first."])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_incorrect_dhcp_pool_start_ip(self, m_MH_display_failed,
                                                m_getDHCP,
                                                m_get_default_gateway_linux,
                                                m_get_physical_ifaces,
                                                m_get_net,
                                                m_duplicateIPExists,
                                                m_search_external_dhcp,
                                                m_post_deploy):
        self.set_value_to_edits("dhcp_pool_start", "192.168.133.256")
        self.assertFalse(self.cobbler.check(None))
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()
        m_MH_display_failed.assert_called_with(
            self.cobbler,
            ['Invalid IP address for DHCP Pool Start',
             'DHCP Pool start and end are not in the same subnet.',
             'DHCP Pool start does not match management network.'])

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_incorrect_dhcp_gateway_ip(self, m_MH_display_failed,
                                             m_getDHCP,
                                             m_get_default_gateway_linux,
                                             m_get_physical_ifaces,
                                             m_get_net, m_duplicateIPExists,
                                             m_search_external_dhcp,
                                             m_post_deploy):
        self.set_value_to_edits("dhcp_gateway", "192.168.133.2.1")
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ['Invalid IP address for DHCP Gateway',
                           'DHCP Gateway does not match management network.'])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_incorrect_dhcp_pool_end_ip(self, m_MH_display_failed,
                                              m_getDHCP,
                                              m_get_default_gateway_linux,
                                              m_get_physical_ifaces,
                                              m_get_net, m_duplicateIPExists,
                                              m_search_external_dhcp,
                                              m_post_deploy):
        self.set_value_to_edits("dhcp_pool_end", "192.168.133.256")
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler,
            ['Invalid IP address for DHCP Pool end',
             'DHCP Pool start and end are not in the same subnet.',
             'DHCP Pool end does not match management network.'])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"}
                )
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_dhcp_gateway_not_in_subnet(self, m_MH_display_failed,
                                              m_getDHCP,
                                              m_get_default_gateway_linux,
                                              m_get_physical_ifaces,
                                              m_get_net, m_duplicateIPExists,
                                              m_search_external_dhcp,
                                              m_post_deploy):
        self.set_value_to_edits("dhcp_gateway", "172.16.0.2")
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ['DHCP Gateway does not match management network.'])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_dhcp_pool_start_not_in_netmask(self,
                                                  m_MH_display_failed,
                                                  m_getDHCP,
                                                  m_get_default_gateway_linux,
                                                  m_get_physical_ifaces,
                                                  m_get_net,
                                                  m_duplicateIPExists,
                                                  m_search_external_dhcp,
                                                  m_post_deploy):
        self.set_value_to_edits("dhcp_pool_start", "172.168.133.3")
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler,
            ['DHCP Pool start and end are not in the same subnet.',
             'DHCP Pool start does not match management network.'])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.255",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_dhcp_pool_end_not_in_netmask(self, m_MH_display_failed,
                                                m_getDHCP,
                                                m_get_default_gateway_linux,
                                                m_get_physical_ifaces,
                                                m_get_net, m_duplicateIPExists,
                                                m_search_external_dhcp,
                                                m_post_deploy):
        self.set_value_to_edits("dhcp_pool_end", "192.167.133.254")
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler,
            ['DHCP Pool start and end are not in the same subnet.',
             'DHCP Pool start does not match management network.',
             'DHCP Pool end does not match management network.'])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=True)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_duplicate_ip(self, m_MH_display_failed, m_getDHCP,
                                m_get_default_gateway_linux,
                                m_get_physical_ifaces, m_get_net,
                                m_duplicateIPExists,
                                m_search_external_dhcp,
                                m_post_deploy):
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["Duplicate host found with IP 192.168.133.2."])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=True)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_change_admin_iface_post_deloyment(
            self, m_MH_display_failed, m_getDHCP, m_get_default_gateway_linux,
            m_get_physical_ifaces, m_get_net, m_duplicateIPExists,
            m_search_external_dhcp, m_post_deploy):
        self.parent.settings = {"ADMIN_NETWORK": {"interface": "eth1",
                                                  "dhcp_pool_start":
                                                      "192.168.133.4",
                                                  "dhcp_pool_end":
                                                      "192.168.133.254"}}
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["Cannot change admin interface after deployment"])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=True)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_incorrect_new_dhcp_start_range(self, m_MH_display_failed,
                                                  m_getDHCP,
                                                  m_get_default_gateway_linux,
                                                  m_get_physical_ifaces,
                                                  m_get_net,
                                                  m_duplicateIPExists,
                                                  m_search_external_dhcp,
                                                  m_post_deploy):
        self.set_value_to_edits("dhcp_pool_start", "192.168.133.10")
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["DHCP range must contain previous values."])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=True)
    @mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp",
                return_value=[])
    @mock.patch("fuelmenu.modules.cobblerconf.network.duplicateIPExists",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper._get_net",
                return_value={
                    "addr": "192.168.133.2",
                    "netmask": "255.255.255.0",
                    "broadcast": "192.168.133.255",
                    "mac": "52:54:00:05:bd:89",
                    "link": "up",
                    "bootproto": "none"})
    @mock.patch("fuelmenu.modules.cobblerconf.network.get_physical_ifaces",
                return_value=["eth0"])
    @mock.patch("fuelmenu.modules.cobblerconf."
                "ModuleHelper.get_default_gateway_linux",
                return_value="192.168.133.1")
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
                return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    def test_check_incorrect_new_dhcp_end_range(self, m_MH_display_failed,
                                                m_getDHCP,
                                                m_get_default_gateway_linux,
                                                m_get_physical_ifaces,
                                                m_get_net,
                                                m_duplicateIPExists,
                                                m_search_external_dhcp,
                                                m_post_deploy):
        self.set_value_to_edits("dhcp_pool_end", "192.168.133.250")
        self.assertFalse(self.cobbler.check(None))
        m_MH_display_failed.assert_called_once_with(
            self.cobbler,
            ["DHCP range can only be increased after deployment."])
        m_getDHCP.assert_called_once_with("eth0")
        m_get_default_gateway_linux.assert_called_once_with()
        m_get_physical_ifaces.assert_called_once_with()
        m_get_net.assert_called_once_with("eth0", False)
        m_duplicateIPExists.assert_called_once_with("192.168.133.2", "eth0",
                                                    True)
        m_search_external_dhcp.assert_called_once_with("eth0", 5)
        m_post_deploy.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig.save")
    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=True)
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig.check")
    def test_apply(self, m_check, m_post_d, m_save):
        m_check.return_value = self.responses
        self.assertTrue(self.cobbler.apply(None))
        m_check.assert_called_once_with(None)
        m_save.assert_called_once_with(self.responses)
        m_post_d.assert_called_once_with()
        self.assertIn(self.cobbler.update_dhcp,
                      self.cobbler.parent.apply_tasks)

    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig.save")
    @mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
                return_value=True)
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig.check",
                return_value=False)
    def test_apply_not_responses(self, m_check, m_post_d, m_save):
        self.assertFalse(self.cobbler.apply(None))
        m_check.assert_called_once_with(None)
        m_save.assert_not_called()
        m_post_d.assert_not_called()

    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_dnsmasq")
    @mock.patch("fuelmenu.modules.cobblerconf.utils.execute",
                return_value=(0, 'Success', 0))
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_hiera_dnsmasq",
        return_value=(True, "Puppet apply successfully executed."))
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig._update_nailgun",
                return_value=True)
    def test_update_dhcp_with_hiera(self, m_update_nailgun, m_p_exists,
                                    m_update_hiera_dnsmasq, m_execute,
                                    m_update_dnsmasq, m_display_failed):
        self.assertTrue(self.cobbler.update_dhcp())
        m_update_nailgun.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_p_exists.assert_called_once_with("/etc/hiera/networks.yaml")
        m_update_hiera_dnsmasq.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_update_dnsmasq.assert_not_called()
        m_execute.assert_called_once_with(["cobbler", "sync"])
        m_display_failed.assert_not_called()

    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_failed_check_dialog")
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_hiera_dnsmasq")
    @mock.patch("fuelmenu.modules.cobblerconf.utils.execute",
                return_value=(0, 'Success', 0))
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_dnsmasq",
        return_value=True)
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig._update_nailgun",
                return_value=True)
    def test_update_dhcp_dnsmasq(self, m_update_nailgun, m_p_exists,
                                 m_update_dnsmasq, m_execute,
                                 m_update_hiera_dnsmasq, m_display_failed):
        self.assertTrue(self.cobbler.update_dhcp())
        m_update_nailgun.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_p_exists.assert_called_once_with("/etc/hiera/networks.yaml")
        m_update_dnsmasq.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_update_hiera_dnsmasq.assert_not_called()
        m_execute.assert_called_once_with(["cobbler", "sync"])
        m_display_failed.assert_not_called()

    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_dialog")
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_hiera_dnsmasq")
    @mock.patch("fuelmenu.modules.cobblerconf.utils.execute",
                return_value=(1, 'Not Success', 0))
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_dnsmasq",
        return_value=True)
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig._update_nailgun",
                return_value=True)
    def test_update_dhcp_failed(self, m_update_nailgun, m_p_exists,
                                m_update_dnsmasq, m_execute,
                                m_update_hiera_dnsmasq, m_display_failed):
        self.assertFalse(self.cobbler.update_dhcp())
        m_update_nailgun.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_p_exists.assert_called_once_with("/etc/hiera/networks.yaml")
        m_update_dnsmasq.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_update_hiera_dnsmasq.assert_not_called()
        m_execute.assert_called_once_with(["cobbler", "sync"])
        m_display_failed.assert_called_once_with(
            self.cobbler,
            error_msg="Error applying changes. Check logs for details.",
            title="Apply failed in module PXE Setup")

    @mock.patch("fuelclient.client.APIClient.put_request")
    @mock.patch("fuelmenu.modules.cobblerconf.puppet.puppetApplyManifest",
                return_value=(True, "Puppet apply successfully executed."))
    def test_update_nailgun(self, m_puppet, m_api_put):
        data = {"gateway": "192.168.133.2", "ip_ranges": [
            ["192.168.133.3", "192.168.133.254"]
        ]}
        self.assertTrue(self.cobbler._update_nailgun(
            self.cobbler.parent.settings["ADMIN_NETWORK"]))
        m_puppet.assert_called_once_with(
            "/etc/puppet/modules/fuel/examples/nailgun.pp")
        m_api_put.assert_called_once_with("networks/1/", data)

    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_dialog")
    @mock.patch("fuelclient.client.APIClient.put_request",
                side_effect=error.HTTPError(''))
    @mock.patch("fuelmenu.modules.cobblerconf.puppet.puppetApplyManifest",
                return_value=(True, "Puppet apply successfully executed."))
    def test_update_nailgun_api_failed(self, m_puppet, m_api_put,
                                       m_MH_display_failed):
        data = {"gateway": "192.168.133.5", "ip_ranges": [
            ["192.168.133.3", "192.168.133.254"]
        ]}
        self.cobbler.parent.settings["ADMIN_NETWORK"]["dhcp_gateway"] = \
            "192.168.133.5"
        self.assertFalse(self.cobbler._update_nailgun(
            self.cobbler.parent.settings["ADMIN_NETWORK"]))
        m_puppet.assert_called_once_with(
            "/etc/puppet/modules/fuel/examples/nailgun.pp")
        m_api_put.assert_called_once_with("networks/1/", data)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler,
            error_msg="Error applying changes. Check logs for details.",
            title="Apply failed in module PXE Setup")

    @mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
                "display_dialog")
    @mock.patch("fuelclient.client.APIClient.put_request",
                side_effect=error.HTTPError(''))
    @mock.patch("fuelmenu.modules.cobblerconf.puppet.puppetApplyManifest",
                return_value=(
                    False,
                    "Puppet apply failed. Check logs for more details."
                ))
    def test_update_nailgun_puppet_failed(self, m_puppet, m_api,
                                          m_MH_display_failed):
        self.assertFalse(self.cobbler._update_nailgun(
            self.cobbler.parent.settings["ADMIN_NETWORK"]))
        m_puppet.assert_called_once_with(
            "/etc/puppet/modules/fuel/examples/nailgun.pp")
        m_MH_display_failed.assert_called_once_with(
            self.cobbler,
            error_msg="Error applying changes. Check logs for details.",
            title="Apply failed in module PXE Setup")
        m_api.assert_not_called()

    @mock.patch("fuelmenu.modules.cobblerconf.puppet.puppetApplyManifest",
                return_value=(True, "Puppet apply successfully executed."))
    @mock.patch("yaml.safe_dump")
    @mock.patch("yaml.safe_load")
    @mock.patch("__builtin__.open")
    def test_update_hiera_dnsmasq(self, m_open, m_yaml_load, m_yaml_dump,
                                  m_puppet):
        self.assertEqual(self.cobbler._update_hiera_dnsmasq(
            self.cobbler.parent.settings["ADMIN_NETWORK"]),
            (True, "Puppet apply successfully executed."))
        m_open.assert_any_call("/etc/hiera/networks.yaml", "r")
        m_open.assert_any_call("/etc/hiera/networks.yaml", "w")
        self.assertEqual(m_yaml_load.call_count, 1)
        self.assertEqual(m_yaml_dump.call_count, 1)
        m_puppet.assert_called_once_with(
            "/etc/puppet/modules/fuel/examples/dhcp-ranges.pp")

    @mock.patch("fuelmenu.modules.cobblerconf.puppet.puppetApply",
                return_value=(0, 'Success', 0))
    def test_update_dnsmasq(self, m_puppet):
        puppetclasses = [{
            "type": "resource",
            "class": "fuel::dnsmasq::dhcp_range",
            "name": "default",
            "params": {
                "dhcp_start_address": "192.168.133.3",
                "dhcp_end_address": "192.168.133.254",
                "dhcp_netmask": "255.255.255.0",
                "dhcp_gateway": "192.168.133.2",
                "next_server": "192.168.133.2"}
        }]
        self.assertEqual(self.cobbler._update_dnsmasq(
            self.cobbler.parent.settings["ADMIN_NETWORK"]), (0, 'Success', 0))
        m_puppet.assert_called_once_with(puppetclasses)

    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig.get_default_gateway_linux",
        return_value="192.168.134.1")
    def test_setNetworkDetails(self, m_get_d_gateway):
        self.cobbler.gateway = "192.168.134.1"
        self.cobbler.netsettings = {'eth0':
                                    {'addr': '192.168.134.2',
                                     'mac': '52:54:00:05:bd:89',
                                     'broadcast': '192.168.134.255',
                                     'netmask': '255.255.255.0',
                                     'bootproto': 'none',
                                     'link': 'up'}}
        edits = ["DHCP Pool for node discovery",
                 urwid.widget.Edit("dhcp_pool_start", "192.168.134.4"),
                 urwid.widget.Edit("dhcp_pool_end", "192.168.134.254"),
                 urwid.widget.Edit("dhcp_gateway", "192.168.134.1")]
        self.cobbler.setNetworkDetails()
        m_get_d_gateway.assert_called_once_with()
        for index, field in enumerate(self.cobbler.edits[1:]):
            self.assertEqual(field.edit_text, edits[index + 1].edit_text)
