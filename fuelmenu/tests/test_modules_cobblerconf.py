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
from fuelclient.cli import error
import mock
import urwid.widget

from fuelmenu.modules import cobblerconf
from fuelmenu.tests import base


class TestCobblerConfig(base.BaseModuleTests):
    ADMIN_NET = {
        "ADMIN_NETWORK": {
            "interface": "eth0",
            "netmask": "255.255.255.0",
            "ipaddress": "192.168.133.2",
            "dhcp_pool_start": "192.168.133.3",
            "dhcp_pool_end": "192.168.133.254",
            "dhcp_gateway": "192.168.133.2"
        }
    }
    NET = {
        "addr": "192.168.133.2",
        "netmask": "255.255.255.0",
        "broadcast": "192.168.133.255",
        "mac": "52:54:00:05:bd:89",
        "link": "up",
        "bootproto": "none"}
    DEFAULT_GATEWAY = "192.168.133.1"

    def set_edits_value(self, field_name, value):
        for field in self.cobbler.edits[1:]:
            if field_name == field.caption:
                field.set_edit_text(value)

    def setUp(self):
        super(TestCobblerConfig, self).setUp()

        self.get_physical_ifaces_patch = mock.patch(
            "fuelmenu.common.network.get_physical_ifaces",
            return_value=["eth0"])
        self.m_get_physical_ifaces = self.get_physical_ifaces_patch.start()

        self.getDHCP_patch = mock.patch(
            "fuelmenu.common.modulehelper.ModuleHelper.getDHCP",
            return_value=False)
        self.m_getDHCP = self.getDHCP_patch.start()

        self._get_net_patch = mock.patch(
            "fuelmenu.common.modulehelper.ModuleHelper._get_net",
            return_value=self.NET)
        self.m_get_net = self._get_net_patch.start()

        self.get_default_gateway_linux_patch = mock.patch(
            "fuelmenu.common.modulehelper.ModuleHelper."
            "get_default_gateway_linux", return_value=self.DEFAULT_GATEWAY)
        self.m_get_default_gateway_linux = \
            self.get_default_gateway_linux_patch.start()

        self.responses = {
            "ADMIN_NETWORK/interface": "eth0",
            "ADMIN_NETWORK/netmask": "255.255.255.0",
            "ADMIN_NETWORK/mac": "52:54:00:05:bd:89",
            "ADMIN_NETWORK/ipaddress": "192.168.133.2",
            "ADMIN_NETWORK/dhcp_pool_start": "192.168.133.3",
            "ADMIN_NETWORK/dhcp_pool_end": "192.168.133.254",
            "ADMIN_NETWORK/dhcp_gateway": "192.168.133.2",
        }
        self.parent.managediface = "eth0"
        self.parent.settings.update(self.ADMIN_NET)
        self.cobbler = cobblerconf.CobblerConfig(self.parent)
        self.cobbler.edits = ["DHCP Pool for node discovery",
                              urwid.widget.Edit("dhcp_pool_start",
                                                "192.168.133.3"),
                              urwid.widget.Edit("dhcp_pool_end",
                                                "192.168.133.254"),
                              urwid.widget.Edit("dhcp_gateway",
                                                "192.168.133.2")]
        self.is_post_d_patch = mock.patch(
            "fuelmenu.common.utils.is_post_deployment", return_value=False)
        self.m_is_post_d = self.is_post_d_patch.start()

        self.search_external_dhcp_patch = mock.patch(
            "fuelmenu.common.network.search_external_dhcp",
            return_value=[])
        self.m_search_external_dhcp = self.search_external_dhcp_patch.start()

        self.duplicateIPExists_patch = mock.patch(
            "fuelmenu.common.network.duplicateIPExists", return_value=False)
        self.m_duplicateIPExists = self.duplicateIPExists_patch.start()

        self.mh_display_failed_patch = mock.patch(
            "fuelmenu.common.modulehelper.ModuleHelper."
            "display_failed_check_dialog")
        self.m_mh_display_failed = self.mh_display_failed_patch.start()

    def tearDown(self):
        mock.patch.stopall()

    def test_check(self):
        self.assertEqual(self.cobbler.check(None), self.responses)

        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()
        self.m_mh_display_failed.assert_not_called()

    def test_check_post_deploy(self):
        self.m_is_post_d.return_value = True
        self.assertEqual(self.cobbler.check(None), self.responses)

        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()
        self.m_mh_display_failed.assert_not_called()

    def test_check_incorrect_management_iface_addr(self):
        net = self.NET.copy()
        net["addr"] = ""
        self.m_get_net.return_value = net
        self.assertEqual(self.cobbler.check(None), False)

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler,
            ['Go to Interfaces to configure management interface first.'])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_not_called()
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_incorrect_running_dhcp(self):
        net = self.NET.copy()
        net["bootproto"] = "dhcp"
        self.m_get_net.return_value = net
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler, ["eth0 is running DHCP. Change it to static first."])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_incorrect_dhcp_pool_start_ip(self):
        self.set_edits_value("dhcp_pool_start", "192.168.133.256")
        self.assertFalse(self.cobbler.check(None))

        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()
        self.m_mh_display_failed.assert_called_with(
            self.cobbler,
            ['Invalid IP address for DHCP Pool Start',
             'DHCP Pool start and end are not in the same subnet.',
             'DHCP Pool start does not match management network.'])

    def test_check_incorrect_dhcp_gateway_ip(self):
        self.set_edits_value("dhcp_gateway", "192.168.133.2.1")
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler, ['Invalid IP address for DHCP Gateway',
                           'DHCP Gateway does not match management network.'])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_incorrect_dhcp_pool_end_ip(self):
        self.set_edits_value("dhcp_pool_end", "192.168.133.256")
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler,
            ['Invalid IP address for DHCP Pool end',
             'DHCP Pool start and end are not in the same subnet.',
             'DHCP Pool end does not match management network.']
        )
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_dhcp_gateway_not_in_subnet(self):
        self.set_edits_value("dhcp_gateway", "172.16.0.2")
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler,
            ['DHCP Gateway does not match management network.'])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_dhcp_pool_start_not_in_netmask(self):
        self.set_edits_value("dhcp_pool_start", "172.168.133.3")
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler,
            ['DHCP Pool start and end are not in the same subnet.',
             'DHCP Pool start does not match management network.'])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_dhcp_pool_end_not_in_netmask(self):
        net = self.NET.copy()
        net["netmask"] = "255.255.255.255"
        self.m_get_net.return_value = net
        self.set_edits_value("dhcp_pool_end", "192.167.133.254")
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler,
            ['DHCP Pool start and end are not in the same subnet.',
             'DHCP Pool start does not match management network.',
             'DHCP Pool end does not match management network.'])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_duplicate_ip(self):
        self.m_duplicateIPExists.return_value = True
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler, ["Duplicate host found with IP 192.168.133.2."])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_change_admin_iface_post_deloyment(self):
        self.m_is_post_d.return_value = True
        self.parent.settings.update({
            "ADMIN_NETWORK":
                {"interface": "eth1",
                 "dhcp_pool_start": "192.168.133.4",
                 "dhcp_pool_end": "192.168.133.254"
                 }
        })
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler,
            ["Cannot change admin interface after deployment"])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_incorrect_new_dhcp_start_range(self):
        self.m_is_post_d.return_value = True
        self.set_edits_value("dhcp_pool_start", "192.168.133.10")
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler, ["DHCP range must contain previous values."])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    def test_check_incorrect_new_dhcp_end_range(self):
        self.m_is_post_d.return_value = True
        self.set_edits_value("dhcp_pool_end", "192.168.133.250")
        self.assertFalse(self.cobbler.check(None))

        self.m_mh_display_failed.assert_called_once_with(
            self.cobbler,
            ["DHCP range can only be increased after deployment."])
        self.m_getDHCP.assert_called_with("eth0")
        self.m_get_default_gateway_linux.assert_called_with()
        self.m_get_physical_ifaces.assert_called_with()
        self.m_get_net.assert_called_with("eth0", False)
        self.m_duplicateIPExists.assert_called_once_with("192.168.133.2",
                                                         "eth0",
                                                         True)
        self.m_search_external_dhcp.assert_called_once_with("eth0", 5)
        self.m_is_post_d.assert_called_once_with()

    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig.save")
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig.check")
    def test_apply(self, m_check, m_save):
        self.m_is_post_d.return_value = True
        m_check.return_value = self.responses
        self.assertTrue(self.cobbler.apply(None))

        m_check.assert_called_once_with(None)
        m_save.assert_called_once_with(self.responses)
        self.m_is_post_d.assert_called_once_with()
        self.assertIn(self.cobbler.update_dhcp,
                      self.cobbler.parent.apply_tasks)

    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig.save")
    @mock.patch("fuelmenu.modules.cobblerconf.CobblerConfig.check",
                return_value=False)
    def test_apply_not_responses(self, m_check, m_save):
        self.m_is_post_d.return_value = True
        self.assertFalse(self.cobbler.apply(None))

        m_check.assert_called_once_with(None)
        m_save.assert_not_called()
        self.m_is_post_d.assert_not_called()

    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_dnsmasq")
    @mock.patch("fuelmenu.common.utils.execute",
                return_value=(0, 'Success', 0))
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_hiera_dnsmasq",
        return_value=(True, "Puppet apply successfully executed."))
    @mock.patch("os.path.exists", return_value=True)
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_nailgun",
        return_value=True)
    def test_update_dhcp_with_hiera(self, m_update_nailgun, m_p_exists,
                                    m_update_hiera_dnsmasq, m_execute,
                                    m_update_dnsmasq):
        self.assertTrue(self.cobbler.update_dhcp())

        m_update_nailgun.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_p_exists.assert_called_once_with("/etc/hiera/networks.yaml")
        m_update_hiera_dnsmasq.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_update_dnsmasq.assert_not_called()
        m_execute.assert_called_once_with(["cobbler", "sync"])
        self.m_mh_display_failed.assert_not_called()

    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_hiera_dnsmasq")
    @mock.patch("fuelmenu.common.utils.execute",
                return_value=(0, 'Success', 0))
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_dnsmasq",
        return_value=True)
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_nailgun",
        return_value=True)
    def test_update_dhcp_dnsmasq(self, m_update_nailgun, m_p_exists,
                                 m_update_dnsmasq, m_execute,
                                 m_update_hiera_dnsmasq):
        self.assertTrue(self.cobbler.update_dhcp())

        m_update_nailgun.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_p_exists.assert_called_once_with("/etc/hiera/networks.yaml")
        m_update_dnsmasq.assert_called_once_with(
            self.cobbler.parent.settings["ADMIN_NETWORK"])
        m_update_hiera_dnsmasq.assert_not_called()
        m_execute.assert_called_once_with(["cobbler", "sync"])
        self.m_mh_display_failed.assert_not_called()

    @mock.patch("fuelmenu.common.modulehelper.ModuleHelper.display_dialog")
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_hiera_dnsmasq")
    @mock.patch("fuelmenu.common.utils.execute",
                return_value=(1, 'Not Success', 0))
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_dnsmasq",
        return_value=True)
    @mock.patch("os.path.exists", return_value=False)
    @mock.patch(
        "fuelmenu.modules.cobblerconf.CobblerConfig._update_nailgun",
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
            error_msg=self.cobbler.apply_dialog_message["message"],
            title=self.cobbler.apply_dialog_message['title'])

    @mock.patch("fuelclient.objects.network_group.NetworkGroup.set")
    @mock.patch("fuelmenu.common.puppet.puppetApplyManifest",
                return_value=(True, "Puppet apply successfully executed."))
    def test_update_nailgun(self, m_puppet, m_netgroup):
        data = {
            "gateway": "192.168.133.2",
            "ip_ranges": [
                ["192.168.133.3", "192.168.133.254"]
            ]
        }
        self.assertTrue(self.cobbler._update_nailgun(
            self.cobbler.parent.settings["ADMIN_NETWORK"]))
        m_puppet.assert_called_once_with(
            "/etc/puppet/modules/fuel/examples/nailgun.pp")
        m_netgroup.assert_called_once_with(data)

    @mock.patch("fuelmenu.common.modulehelper.ModuleHelper.display_dialog")
    @mock.patch("fuelclient.objects.NetworkGroup.set",
                side_effect=error.HTTPError(''))
    @mock.patch("fuelmenu.common.puppet.puppetApplyManifest",
                return_value=(True, "Puppet apply successfully executed."))
    def test_update_nailgun_api_failed(self, m_puppet, m_netgroup,
                                       m_mh_display_failed):
        data = {
            "gateway": "192.168.133.5",
            "ip_ranges": [
                ["192.168.133.3", "192.168.133.254"]
            ]
        }
        self.cobbler.parent.settings["ADMIN_NETWORK"]["dhcp_gateway"] = \
            "192.168.133.5"
        self.assertFalse(self.cobbler._update_nailgun(
            self.cobbler.parent.settings["ADMIN_NETWORK"]))
        m_puppet.assert_called_once_with(
            "/etc/puppet/modules/fuel/examples/nailgun.pp")
        m_netgroup.assert_called_once_with(data)
        m_mh_display_failed.assert_called_once_with(
            self.cobbler,
            error_msg=self.cobbler.apply_dialog_message["message"],
            title=self.cobbler.apply_dialog_message['title'])

    @mock.patch("fuelmenu.common.modulehelper.ModuleHelper.display_dialog")
    @mock.patch("fuelclient.objects.NetworkGroup.set",
                side_effect=error.HTTPError(''))
    @mock.patch("fuelmenu.modules.cobblerconf.puppet.puppetApplyManifest",
                return_value=(
                    False,
                    "Puppet apply failed. Check logs for more details."
                ))
    def test_update_nailgun_puppet_failed(self, m_puppet, m_netgroup,
                                          m_mh_display_failed):
        self.assertFalse(self.cobbler._update_nailgun(
            self.cobbler.parent.settings["ADMIN_NETWORK"]))
        m_puppet.assert_called_once_with(
            "/etc/puppet/modules/fuel/examples/nailgun.pp")
        m_mh_display_failed.assert_called_once_with(
            self.cobbler,
            error_msg=self.cobbler.apply_dialog_message["message"],
            title=self.cobbler.apply_dialog_message['title'])
        m_netgroup.assert_not_called()

    @mock.patch("fuelmenu.common.puppet.puppetApplyManifest",
                return_value=(True, "Puppet apply successfully executed."))
    @mock.patch("yaml.safe_dump")
    @mock.patch("yaml.safe_load")
    @mock.patch("__builtin__.open")
    def test_update_hiera_dnsmasq(self, m_open, m_yaml_load, m_yaml_dump,
                                  m_puppet):
        self.assertEqual(
            self.cobbler._update_hiera_dnsmasq(
                self.cobbler.parent.settings["ADMIN_NETWORK"]),
            (True, "Puppet apply successfully executed.")
        )
        m_open.assert_any_call("/etc/hiera/networks.yaml", "r")
        m_open.assert_any_call("/etc/hiera/networks.yaml", "w")
        m_yaml_load.assert_called_once_with(mock.ANY)
        m_yaml_dump.assert_called_once_with(mock.ANY, mock.ANY)
        m_puppet.assert_called_once_with(
            "/etc/puppet/modules/fuel/examples/dhcp-ranges.pp")

    @mock.patch("fuelmenu.common.puppet.puppetApply",
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
        self.assertEqual(
            self.cobbler._update_dnsmasq(
                self.cobbler.parent.settings["ADMIN_NETWORK"]),
            (0, 'Success', 0)
        )
        m_puppet.assert_called_once_with(puppetclasses)

    def test_setNetworkDetails(self):
        self.m_get_default_gateway_linux.return_value = "192.168.134.1"
        self.cobbler.gateway = "192.168.133.1"
        self.cobbler.netsettings = {
            'eth0':
                {'addr': '192.168.134.2',
                 'mac': '52:54:00:05:bd:89',
                 'broadcast': '192.168.134.255',
                 'netmask': '255.255.255.0',
                 'bootproto': 'none',
                 'link': 'up'}
        }
        edits = ["DHCP Pool for node discovery",
                 urwid.widget.Edit("dhcp_pool_start", "192.168.134.3"),
                 urwid.widget.Edit("dhcp_pool_end", "192.168.134.254"),
                 urwid.widget.Edit("dhcp_gateway", "192.168.134.2")]
        self.cobbler.setNetworkDetails()
        self.m_get_default_gateway_linux.assert_called_with()
        for field1, field2 in zip(edits[1:], self.cobbler.edits[1:]):
            self.assertEqual(field1.edit_text, field2.edit_text)
