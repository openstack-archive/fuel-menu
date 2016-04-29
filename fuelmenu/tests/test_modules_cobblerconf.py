import mock

from fuelmenu.tests.test_base import BaseModuleTests
import urwid.widget


@mock.patch("fuelmenu.modules.cobblerconf.utils.execute",
            return_value=(0, 'Success', 0))
@mock.patch("fuelmenu.modules.cobblerconf.puppet.puppetApply",
            return_value=None)
@mock.patch("fuelmenu.modules.cobblerconf.utils.is_post_deployment",
            return_value=False)
@mock.patch("fuelmenu.modules.cobblerconf.network.search_external_dhcp")
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
@mock.patch("fuelmenu.modules.cobblerconf.logging.getLogger")
@mock.patch("fuelmenu.modules.cobblerconf.network.inSameSubnet",
            return_value=True)
@mock.patch("fuelmenu.modules.cobblerconf."
            "ModuleHelper.get_default_gateway_linux",
            return_value="192.168.133.1")
@mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper.getDHCP",
            return_value=False)
@mock.patch("fuelmenu.modules.cobblerconf.ModuleHelper."
            "display_failed_check_dialog")
class TestCobblerconf(BaseModuleTests):
    def test_check(self, m_MH_display_failed, m_getDHCP,
                   m_get_default_gateway_linux,
                   m_inSameSubnet, m_log, m_get_physical_ifaces,
                   m_get_net, m_duplicateIPExists, m_search_external_dhcp,
                   m_post_deploy, m_puppetApply, m_execute):
        m_get_default_gateway_linux.return_value = "192.168.133.1"
        self.assertEqual(self.cobbler.check(123), self.responses)
        self.assertFalse(m_MH_display_failed.called)

    def test_check_incorrect_management_iface_addr(self, m_MH_display_failed,
                                                   m_getDHCP,
                                                   m_get_default_gateway_linux,
                                                   m_choicesGroup, m_log,
                                                   m_get_physical_ifaces,
                                                   m_get_net,
                                                   m_duplicateIPExists,
                                                   m_search_external_dhcp,
                                                   m_post_deploy,
                                                   m_puppetApply, m_execute):
        m_get_net.return_value = {"addr": "",
                                  "netmask": "255.255.255.0",
                                  "broadcast": "192.168.133.255",
                                  "mac": "52:54:00:05:bd:89",
                                  "link": "up",
                                  "bootproto": "none"}

        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(self.cobbler,
                                                    ['Go to Interfaces to'
                                                     ' configure management'
                                                     ' interface first.'])

    def test_check_incorrect_running_dhcp(self, m_MH_display_failed, m_getDHCP,
                                          m_get_default_gateway_linux,
                                          m_inSameSubnet, m_log,
                                          m_get_physical_ifaces, m_get_net,
                                          m_duplicateIPExists,
                                          m_search_external_dhcp,
                                          m_post_deploy, m_puppetApply,
                                          m_execute):
        m_get_net.return_value = {"addr": "192.168.133.2",
                                  "netmask": "255.255.255.0",
                                  "broadcast": "192.168.133.255",
                                  "mac": "52:54:00:05:bd:89",
                                  "link": "up",
                                  "bootproto": "dhcp"}

        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["eth0 is running DHCP. Change it to static first."])

    def test_check_incorrect_dhcp_pool_start_ip(self, m_MH_display_failed,
                                                m_getDHCP,
                                                m_get_default_gateway_linux,
                                                m_inSameSubnet, m_log,
                                                m_get_physical_ifaces,
                                                m_get_net,
                                                m_duplicateIPExists,
                                                m_search_external_dhcp,
                                                m_post_deploy,
                                                m_puppetApply, m_execute):
        self.cobbler.edits = ["test", urwid.widget.Edit("dhcp_poll_start",
                                                        "192.168.133.0.1"),
                              urwid.widget.Edit("dhcp_pool_end",
                                                "192.168.133.254"),
                              urwid.widget.Edit("ololol", "192.168.133.2")]
        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["Invalid IP address for DHCP Pool Start"])

    def test_check_incorrect_dhcp_gateway_ip(self, m_MH_display_failed,
                                             m_getDHCP,
                                             m_get_default_gateway_linux,
                                             m_inSameSubnet, m_log,
                                             m_get_physical_ifaces, m_get_net,
                                             m_duplicateIPExists,
                                             m_search_external_dhcp,
                                             m_post_deploy, m_puppetApply,
                                             m_execute):
        self.cobbler.edits = ["test", urwid.widget.Edit("dhcp_poll_start",
                                                        "192.168.133.3"),
                              urwid.widget.Edit("dhcp_pool_end",
                                                "192.168.133.254"),
                              urwid.widget.Edit("dhcp_gateway",
                                                "192.168.133.2.1")]
        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["Invalid IP address for DHCP Gateway"])

    def test_check_incorrect_dhcp_pool_end_ip(self, m_MH_display_failed,
                                              m_getDHCP,
                                              m_get_default_gateway_linux,
                                              m_inSameSubnet, m_log,
                                              m_get_physical_ifaces, m_get_net,
                                              m_duplicateIPExists,
                                              m_search_external_dhcp,
                                              m_post_deploy, m_puppetApply,
                                              m_execute):
        self.cobbler.edits = ["test", urwid.widget.Edit("dhcp_poll_start",
                                                        "192.168.133.3"),
                              urwid.widget.Edit("dhcp_pool_end",
                                                "192.168.133.256"),
                              urwid.widget.Edit("dhcp_gateway",
                                                "192.168.133.2")]
        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["Invalid IP address for DHCP Pool end"])

    def test_check_incorrect_dhcp_not_in_subnet(self, m_MH_display_failed,
                                                m_getDHCP,
                                                m_get_default_gateway_linux,
                                                m_inSameSubnet, m_log,
                                                m_get_physical_ifaces,
                                                m_get_net,
                                                m_duplicateIPExists,
                                                m_search_external_dhcp,
                                                m_post_deploy,
                                                m_puppetApply, m_execute):
        m_inSameSubnet.side_effect = [False, True, True, True]
        m_get_net.return_value = {"addr": "192.168.133.2",
                                  "netmask": "255.255.255.255",
                                  "broadcast": "192.168.133.255",
                                  "mac": "52:54:00:05:bd:89",
                                  "link": "up",
                                  "bootproto": "none"}

        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler,
            ["DHCP Pool start and end are not in the same subnet."])

    def test_check_incorrect_dhcp_pool_start_not_in_netmask(
            self, m_MH_display_failed, m_getDHCP,
            m_get_default_gateway_linux,
            m_inSameSubnet,
            m_log,
            m_get_physical_ifaces,
            m_get_net,
            m_duplicateIPExists,
            m_search_external_dhcp,
            m_post_deploy,
            m_puppetApply,
            m_execute):
        m_inSameSubnet.side_effect = [True, False, True, True]
        m_get_net.return_value = {"addr": "192.168.133.2",
                                  "netmask": "255.255.255.255",
                                  "broadcast": "192.168.133.255",
                                  "mac": "52:54:00:05:bd:89",
                                  "link": "up",
                                  "bootproto": "none"}

        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler,
            ["DHCP Pool start does not match management network."])

    def test_check_incorrect_dhcp_pool_end_not_in_netmask(
            self, m_MH_display_failed, m_getDHCP,
            m_get_default_gateway_linux,
            m_inSameSubnet,
            m_log,
            m_get_physical_ifaces,
            m_get_net,
            m_duplicateIPExists,
            m_search_external_dhcp,
            m_post_deploy,
            m_puppetApply,
            m_execute):
        m_inSameSubnet.side_effect = [True, True, False, True]
        m_get_net.return_value = {"addr": "192.168.133.2",
                                  "netmask": "255.255.255.255",
                                  "broadcast": "192.168.133.255",
                                  "mac": "52:54:00:05:bd:89",
                                  "link": "up",
                                  "bootproto": "none"}

        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["DHCP Pool end does not match management network."])

    def test_check_incorrect_dhcp_gateway_not_in_netmask(
            self, m_MH_display_failed, m_getDHCP,
            m_get_default_gateway_linux,
            m_inSameSubnet, m_log,
            m_get_physical_ifaces,
            m_get_net,
            m_duplicateIPExists,
            m_search_external_dhcp,
            m_post_deploy,
            m_puppetApply,
            m_execute):
        m_inSameSubnet.side_effect = [True, True, True, False]
        m_get_net.return_value = {"addr": "192.168.133.2",
                                  "netmask": "255.255.255.255",
                                  "broadcast": "192.168.133.255",
                                  "mac": "52:54:00:05:bd:89",
                                  "link": "up",
                                  "bootproto": "none"}

        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["DHCP Gateway does not match management network."])

    def test_check_incorrect_duplicate_ip(self, m_MH_display_failed, m_getDHCP,
                                          m_get_default_gateway_linux,
                                          m_inSameSubnet, m_log,
                                          m_get_physical_ifaces, m_get_net,
                                          m_duplicateIPExists,
                                          m_search_external_dhcp,
                                          m_post_deploy, m_puppetApply,
                                          m_execute):
        m_duplicateIPExists.return_value = True

        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["Duplicate host found with IP 192.168.133.2."])

    def test_check_incorrect_change_admin_iface(self, m_MH_display_failed,
                                                m_getDHCP,
                                                m_get_default_gateway_linux,
                                                m_inSameSubnet, m_log,
                                                m_get_physical_ifaces,
                                                m_get_net,
                                                m_duplicateIPExists,
                                                m_search_external_dhcp,
                                                m_post_deploy,
                                                m_puppetApply, m_execute):
        self.parent.settings = {"ADMIN_NETWORK": {"interface": "eth1",
                                                  "dhcp_pool_start":
                                                      "192.168.133.3",
                                                  "dhcp_pool_end":
                                                      "192.168.133.254"}}
        m_post_deploy.return_value = True
        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["Cannot change admin interface after deployment"])

    def test_check_incorrect_new_dhcp_start_range(self, m_MH_display_failed,
                                                  m_getDHCP,
                                                  m_get_default_gateway_linux,
                                                  m_inSameSubnet, m_log,
                                                  m_get_physical_ifaces,
                                                  m_get_net,
                                                  m_duplicateIPExists,
                                                  m_search_external_dhcp,
                                                  m_post_deploy,
                                                  m_puppetApply, m_execute):
        m_post_deploy.return_value = True

        self.cobbler.edits = ["test", urwid.widget.Edit("dhcp_poll_start",
                                                        "192.168.133.10"),
                              urwid.widget.Edit("dhcp_pool_end",
                                                "192.168.133.254"),
                              urwid.widget.Edit("dhcp_gateway",
                                                "192.168.133.2")]
        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler, ["DHCP range must contain previous values."])

    def test_check_incorrect_new_dhcp_end_range(self, m_MH_display_failed,
                                                m_getDHCP,
                                                m_get_default_gateway_linux,
                                                m_inSameSubnet, m_log,
                                                m_get_physical_ifaces,
                                                m_get_net,
                                                m_duplicateIPExists,
                                                m_search_external_dhcp,
                                                m_post_deploy,
                                                m_puppetApply, m_execute):
        m_post_deploy.return_value = True

        self.cobbler.edits = ["tets", urwid.widget.Edit("dhcp_poll_start",
                                                        "192.168.133.3"),
                              urwid.widget.Edit("dhcp_pool_end",
                                                "192.168.133.250"),
                              urwid.widget.Edit("dhcp_gateway",
                                                "192.168.133.2")]
        self.assertEqual(self.cobbler.check(123), False)
        m_MH_display_failed.assert_called_once_with(
            self.cobbler,
            ["DHCP range can only be increased after deployment."])

    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConf.check")
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConf.save")
    def test_apply(self, m_save, m_check, m_MH_display_failed, m_getDHCP,
                   m_get_default_gateway_linux,
                   m_inSameSubnet, m_log, m_get_physical_ifaces, m_get_net,
                   m_duplicateIPExists, m_search_external_dhcp, m_post_deploy,
                   m_puppetApply, m_execute):
        m_post_deploy.return_value = True
        m_check.return_value = self.responses
        pclass = [{'params': {'dhcp_netmask': '255.255.255.0',
                              'dhcp_end_address': '192.168.133.254',
                              'next_server': '192.168.133.2',
                              'dhcp_gateway': '192.168.133.2',
                              'dhcp_start_address': '192.168.133.3'},
                   'type': 'resource', 'class': 'fuel::dnsmasq::dhcp_range',
                   'name': 'default'}]
        self.assertEqual(self.cobbler.apply(123), True)
        m_puppetApply.assert_called_once_with(pclass)
        m_execute.assert_called_once_with(["cobbler", "sync"])

    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConf.check")
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConf.save")
    def test_apply_incorret_puppetApply(self, m_save, m_check,
                                        m_MH_display_failed, m_getDHCP,
                                        m_get_default_gateway_linux,
                                        m_inSameSubnet, m_log,
                                        m_get_physical_ifaces, m_get_net,
                                        m_duplicateIPExists,
                                        m_search_external_dhcp, m_post_deploy,
                                        m_puppetApply,
                                        m_execute):
        m_post_deploy.return_value = True
        m_puppetApply.return_value = False
        m_check.return_value = self.responses
        self.assertEqual(self.cobbler.apply(123), False)
        self.assertFalse(m_execute.called)

    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConf.check")
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConf.save")
    def test_apply_execute_failed(self, m_save, m_check, m_MH_display_failed,
                                  m_getDHCP, m_get_default_gateway_linux,
                                  m_inSameSubnet, m_log, m_get_physical_ifaces,
                                  m_get_net,
                                  m_duplicateIPExists, m_search_external_dhcp,
                                  m_post_deploy, m_puppetApply,
                                  m_execute):
        m_check.return_value = self.responses
        m_execute.return_value = (1, 'Fail', 5)
        m_post_deploy.return_value = True
        self.assertFalse(self.cobbler.apply(123))

    @mock.patch("fuelmenu.modules.cobblerconf.network.getNetwork")
    def test_setNetworkDetails(self, m_net_getNet, m_MH_display_failed,
                               m_getDHCP, m_get_default_gateway_linux,
                               m_inSameSubnet, m_log, m_get_physical_ifaces,
                               m_get_net,
                               m_duplicateIPExists, m_search_external_dhcp,
                               m_post_deploy, m_puppetApply,
                               m_execute):
        m_inSameSubnet.return_value = False
        self.cobbler.setNetworkDetails()
        m_inSameSubnet.assert_called_once_with("192.168.133.3",
                                               "192.168.133.2",
                                               "255.255.255.0")
        m_net_getNet.assert_called_once_with("192.168.133.2", "255.255.255.0",
                                             "192.168.133.1")
