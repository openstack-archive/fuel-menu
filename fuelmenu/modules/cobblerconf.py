#!/usr/bin/env python
# Copyright 2013 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import os

from fuelclient.cli import error
from fuelclient import objects
import netaddr
import urwid
import urwid.raw_display
import urwid.web_display
import yaml

from fuelmenu.common import dialog
from fuelmenu.common import errors as f_errors
from fuelmenu.common import modulehelper
from fuelmenu.common import network
from fuelmenu.common import puppet
import fuelmenu.common.urwidwrapper as widget
from fuelmenu.common import utils
from fuelmenu import consts
log = logging.getLogger('fuelmenu.pxe_setup')
blank = urwid.Divider()


class CobblerConfig(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "PXE Setup"
        self.visible = True
        self.netsettings = dict()
        self.parent = parent
        self.getNetwork()
        self.gateway = self.get_default_gateway_linux()
        self.activeiface = self.parent.managediface

        # UI text
        text1 = "Settings for PXE booting of slave nodes."
        text2 = "Select the interface where PXE will run:"
        # Placeholder for network settings text
        self.net_choices = widget.ChoicesGroup(sorted(self.netsettings.keys()),
                                               default_value=self.activeiface,
                                               fn=self.radioSelect)
        self.net_text1 = widget.TextLabel("")
        self.net_text2 = widget.TextLabel("")
        self.net_text3 = widget.TextLabel("")
        self.net_text4 = widget.TextLabel("")
        self.header_content = [text1, text2, self.net_choices, self.net_text1,
                               self.net_text2, self.net_text3, self.net_text4]
        self.fields = ["dynamic_label", "ADMIN_NETWORK/dhcp_pool_start",
                       "ADMIN_NETWORK/dhcp_pool_end",
                       "ADMIN_NETWORK/dhcp_gateway"]

        self.defaults = \
            {
                "ADMIN_NETWORK/dhcp_pool_start": {"label": "DHCP Pool Start",
                                                  "tooltip": "Used for \
defining IPs for hosts and instance public addresses",
                                                  "value": "10.0.0.3"},
                "ADMIN_NETWORK/dhcp_pool_end": {"label": "DHCP Pool End",
                                                "tooltip": "Used for defining \
IPs for hosts and instance public addresses",
                                                "value": "10.0.0.254"},
                "ADMIN_NETWORK/dhcp_gateway": {"label": "DHCP Gateway",
                                               "tooltip": "Default gateway \
to advertise via DHCP to nodes",
                                               "value": "10.0.0.2"},
                "dynamic_label": {"label": "DHCP pool for node discovery:",
                                  "tooltip": "",
                                  "type": modulehelper.WidgetType.LABEL},
            }

        self.load()
        self.extdhcp = True
        self.screen = None
        self.apply_dialog_message = {
            'title': "Apply failed in module {0}".format(self.name),
            "message": "Error applying changes. Check logs for details."
        }

    def check(self, args):
        """Validates all fields have valid values and some sanity checks."""
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()

        # Refresh networking to make sure IP matches
        self.getNetwork()

        # Get field information
        responses = dict()

        for index, fieldname in enumerate(self.fields):
            if fieldname != "blank" and "label" not in fieldname:
                responses[fieldname] = self.edits[index].get_edit_text()

        # Validate each field
        errors = []

        # Set internal_{ipaddress,netmask,interface}
        responses["ADMIN_NETWORK/interface"] = self.activeiface
        responses["ADMIN_NETWORK/netmask"] = self.netsettings[
            self.activeiface]["netmask"]
        responses["ADMIN_NETWORK/mac"] = self.netsettings[
            self.activeiface]["mac"]
        responses["ADMIN_NETWORK/ipaddress"] = self.netsettings[
            self.activeiface]["addr"]

        # ensure management interface is valid
        if responses["ADMIN_NETWORK/interface"] not in self.netsettings.keys():
            errors.append("Management interface not valid")
        else:
            self.parent.footer.set_text("Scanning for DHCP servers. \
Please wait...")
            self.parent.refreshScreen()

            try:
                dhcptimeout = 5
                dhcp_server_data = network.search_external_dhcp(
                    self.activeiface, dhcptimeout)
            except network.NetworkException:
                log.warning('DHCP scan failed.')
                dhcp_server_data = []

            num_dhcp = len(dhcp_server_data)
            if num_dhcp == 0:
                log.debug("No DHCP servers found")
            else:
                # Problem exists, but permit user to continue
                log.error("%s foreign DHCP server(s) found: %s" %
                          (num_dhcp, dhcp_server_data))

                # Build dialog elements
                dhcp_info = []
                dhcp_info.append(urwid.Padding(
                                 urwid.Text(("header", "!!! WARNING !!!")),
                                 "center"))
                dhcp_info.append(widget.TextLabel("You have selected an \
interface that contains one or more DHCP servers. This will impact \
provisioning. You should disable these DHCP servers before you continue, or \
else deployment will likely fail."))
                dhcp_info.append(widget.TextLabel(""))
                for index, dhcp_server in enumerate(dhcp_server_data):
                    dhcp_info.append(widget.TextLabel("DHCP Server #%s:" %
                                     (index + 1)))
                    dhcp_info.append(widget.TextLabel("IP address: %-10s" %
                                     dhcp_server['server_ip']))
                    dhcp_info.append(widget.TextLabel("MAC address: %-10s" %
                                     dhcp_server['mac']))
                    dhcp_info.append(widget.TextLabel(""))
                dialog.display_dialog(self, urwid.Pile(dhcp_info),
                                      "DHCP Servers Found on %s"
                                      % self.activeiface)
            # Ensure pool start and end are on the same subnet as mgmt_if
            # Ensure mgmt_if has an IP first
            if len(self.netsettings[responses[
               "ADMIN_NETWORK/interface"]]["addr"]) == 0:
                errors.append("Go to Interfaces to configure management \
interface first.")
            else:
                # Ensure ADMIN_NETWORK/interface is not running DHCP
                if self.netsettings[responses[
                        "ADMIN_NETWORK/interface"]]["bootproto"] == "dhcp":
                    errors.append("%s is running DHCP. Change it to static "
                                  "first." % self.activeiface)
                # Ensure DHCP Pool Start and DHCP Pool are valid IPs
                try:
                    if netaddr.valid_ipv4(responses[
                                          "ADMIN_NETWORK/dhcp_pool_start"]):
                        dhcp_start = netaddr.IPAddress(
                            responses["ADMIN_NETWORK/dhcp_pool_start"])
                        if not dhcp_start:
                            raise f_errors.BadIPException(
                                "Not a valid IP address")
                    else:
                        raise f_errors.BadIPException("Not a valid IP address")
                except Exception:
                    errors.append("Invalid IP address for DHCP Pool Start")
                try:
                    if netaddr.valid_ipv4(responses[
                            "ADMIN_NETWORK/dhcp_gateway"]):
                        dhcp_gateway = netaddr.IPAddress(
                            responses["ADMIN_NETWORK/dhcp_gateway"])
                        if not dhcp_gateway:
                            raise f_errors.BadIPException(
                                "Not a valid IP address")
                    else:
                            raise f_errors.BadIPException(
                                "Not a valid IP address")
                except Exception:
                    errors.append("Invalid IP address for DHCP Gateway")

                try:
                    if netaddr.valid_ipv4(responses[
                            "ADMIN_NETWORK/dhcp_pool_end"]):
                        dhcp_end = netaddr.IPAddress(
                            responses["ADMIN_NETWORK/dhcp_pool_end"])
                        if not dhcp_end:
                            raise f_errors.BadIPException(
                                "Not a valid IP address")
                    else:
                        raise f_errors.BadIPException(
                            "Not a valid IP address")
                except Exception:
                    errors.append("Invalid IP address for DHCP Pool end")

                # Ensure pool start and end are in the same
                # subnet of each other
                netmask = self.netsettings[responses[
                                           "ADMIN_NETWORK/interface"
                                           ]]["netmask"]
                if not network.inSameSubnet(
                        responses["ADMIN_NETWORK/dhcp_pool_start"],
                        responses["ADMIN_NETWORK/dhcp_pool_end"], netmask):
                    errors.append("DHCP Pool start and end are not in the "
                                  "same subnet.")

                # Ensure pool start and end are in the right netmask
                mgmt_if_ipaddr = self.netsettings[responses[
                    "ADMIN_NETWORK/interface"]]["addr"]
                if network.inSameSubnet(responses[
                                        "ADMIN_NETWORK/dhcp_pool_start"],
                                        mgmt_if_ipaddr, netmask) is False:
                    errors.append("DHCP Pool start does not match management"
                                  " network.")
                if network.inSameSubnet(responses[
                                        "ADMIN_NETWORK/dhcp_pool_end"],
                                        mgmt_if_ipaddr, netmask) is False:
                    errors.append("DHCP Pool end does not match management "
                                  "network.")

                if network.inSameSubnet(responses[
                                        "ADMIN_NETWORK/dhcp_gateway"],
                                        mgmt_if_ipaddr, netmask) is False:
                    errors.append("DHCP Gateway does not match management "
                                  "network.")

                self.parent.footer.set_text("Scanning for duplicate IP address"
                                            "es. Please wait...")
                # Bind arping to mgmt_if_ipaddr if it assigned
                assigned_ips = [v.get('addr') for v in
                                self.netsettings.itervalues()]
                arping_bind = mgmt_if_ipaddr in assigned_ips
                if network.duplicateIPExists(mgmt_if_ipaddr, self.activeiface,
                                             arping_bind):
                    errors.append("Duplicate host found with IP {0}.".format(
                        mgmt_if_ipaddr))

        # Extra checks for post-deployment changes
        if utils.is_post_deployment():
            settings = self.parent.settings

            # Admin interface cannot change
            if self.activeiface != settings["ADMIN_NETWORK"]["interface"]:
                errors.append("Cannot change admin interface after deployment")

            # PXE network range must contain previous PXE network range
            old_range = network.range(
                settings["ADMIN_NETWORK"]["dhcp_pool_start"],
                settings["ADMIN_NETWORK"]["dhcp_pool_end"])
            new_range = network.range(
                responses["ADMIN_NETWORK/dhcp_pool_start"],
                responses["ADMIN_NETWORK/dhcp_pool_end"])
            if old_range[0] not in new_range:
                errors.append("DHCP range must contain previous values.")
            if old_range[-1] not in new_range:
                errors.append("DHCP range can only be increased after "
                              "deployment.")

        if len(errors) > 0:
            log.error("Errors: %s %s" % (len(errors), errors))
            modulehelper.ModuleHelper.display_failed_check_dialog(self, errors)
            return False
        else:
            self.parent.footer.set_text("No errors found.")
            return responses

    def apply(self, args):
        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            log.error("%s" % (responses))
            return False
        self.save(responses)
        if utils.is_post_deployment():
            self.parent.apply_tasks.add(self.update_dhcp)
        return True

    def update_dhcp(self):
        settings = self.parent.settings.get("ADMIN_NETWORK")
        if not self._update_nailgun(settings):
            return False
        if os.path.exists(consts.HIERA_NET_SETTINGS):
            result, msg = self._update_hiera_dnsmasq(settings)
        else:
            result = self._update_dnsmasq(settings)
        if not result:
            modulehelper.ModuleHelper.display_dialog(
                self, error_msg=self.apply_dialog_message["message"],
                title=self.apply_dialog_message["title"])
            return False
        cobbler_sync = ["cobbler", "sync"]
        code, out, err = utils.execute(cobbler_sync)
        if code != 0:
            log.error(err)
            modulehelper.ModuleHelper.display_dialog(
                self, error_msg=self.apply_dialog_message["message"],
                title=self.apply_dialog_message["title"])
            return False
        return True

    def _update_nailgun(self, settings):
        msg = "Apply changes to Nailgun"
        log.info(msg)
        self.parent.footer.set_text(msg)
        self.parent.refreshScreen()

        # TODO(mzhnichkov) this manifest apply twice(here and in feature
        # groups). Need to combine this calls
        result, msg = puppet.puppetApplyManifest(consts.PUPPET_NAILGUN)
        if not result:
            modulehelper.ModuleHelper.display_dialog(
                self, error_msg=self.apply_dialog_message["message"],
                title=self.apply_dialog_message["title"])
            return False

        data = {
            "gateway": settings["dhcp_gateway"],
            "ip_ranges": [
                [settings["dhcp_pool_start"], settings["dhcp_pool_end"]]
            ]
        }
        try:
            objects.NetworkGroup(consts.ADMIN_NETWORK_ID).set(data)
        except error.HTTPError as e:
            log.error(str(e))
            modulehelper.ModuleHelper.display_dialog(
                self, error_msg=self.apply_dialog_message["message"],
                title=self.apply_dialog_message["title"])
            return False
        return True

    def _update_hiera_dnsmasq(self, settings):
        """Update Hiera and dnsmasq

        PXE related configuration should be written in separate
        configuration file when you create additional admin
        network(this behavior was introduced in nailgun's
        DnsmasqUpdateTask class)
        """

        msg = "Apply changes to Hiera and Dnsmasq"
        log.info(msg)
        self.parent.footer.set_text(msg)
        self.parent.refreshScreen()
        with open(consts.HIERA_NET_SETTINGS, "r") as hiera_settings:
            networks = yaml.safe_load(hiera_settings)
        net = netaddr.IPNetwork(
            "{0}/{1}".format(settings["ipaddress"],
                             settings["netmask"]))
        for admin_net in networks["admin_networks"]:
            if str(net.cidr) == admin_net["cidr"]:
                admin_net["ip_ranges"] = [
                    [settings["dhcp_pool_start"],
                     settings["dhcp_pool_end"]]
                ]
                admin_net["gateway"] = settings["dhcp_gateway"]
        with open(consts.HIERA_NET_SETTINGS, "w") as hiera_settings:
            yaml.safe_dump(networks, hiera_settings)
        return puppet.puppetApplyManifest(consts.PUPPET_DHCP_RANGES)

    def _update_dnsmasq(self, settings):
        puppet_classes = [{
            "type": "resource",
            "class": "fuel::dnsmasq::dhcp_range",
            "name": "default",
            "params": {
                "dhcp_start_address": settings["dhcp_pool_start"],
                "dhcp_end_address": settings["dhcp_pool_end"],
                "dhcp_netmask": settings["netmask"],
                "dhcp_gateway": settings["dhcp_gateway"],
                "next_server": settings["ipaddress"]
            }
        }]
        log.debug("Start puppet with data {0}".format(puppet_classes))
        return puppet.puppetApply(puppet_classes)

    def cancel(self, button):
        modulehelper.ModuleHelper.cancel(self, button)
        self.setNetworkDetails()

    def load(self):
        settings = self.parent.settings
        modulehelper.ModuleHelper.load_to_defaults(settings, self.defaults)

        iface = settings.get("ADMIN_NETWORK", {}).get("interface")
        if iface in self.netsettings.keys():
            self.activeiface = iface

    def save(self, responses):
        newsettings = modulehelper.ModuleHelper.make_settings_from_responses(
            responses)

        # Need to calculate and netmask
        newsettings['ADMIN_NETWORK']['netmask'] = \
            self.netsettings[newsettings['ADMIN_NETWORK']['interface']][
                "netmask"]

        # Update self.defaults
        for index, fieldname in enumerate(self.fields):
            if fieldname != "blank" and "label" not in fieldname:
                self.defaults[fieldname]['value'] = responses[fieldname]

        self.parent.settings.merge(newsettings)
        self.parent.footer.set_text("Changes saved successfully.")

    def getNetwork(self):
        modulehelper.ModuleHelper.getNetwork(self)

    def getDHCP(self, iface):
        return modulehelper.ModuleHelper.getDHCP(iface)

    def get_default_gateway_linux(self):
        return modulehelper.ModuleHelper.get_default_gateway_linux()

    def radioSelect(self, current, state, user_data=None):
        """Update network details and display information."""
        # Urwid returns the previously selected radio button.
        # The previous object has True state, which is wrong.
        # Somewhere in rb group a RadioButton is set to True.
        for rb in current.group:
            if rb.get_label() == current.get_label():
                continue
            if rb.base_widget.state is True:
                self.activeiface = rb.base_widget.get_label()
                self.parent.managediface = self.activeiface
                break
        self.gateway = self.get_default_gateway_linux()
        self.getNetwork()
        self.setNetworkDetails()
        return

    def setNetworkDetails(self):
        self.net_text1.set_text("Interface: %-13s  Link: %s" % (
            self.activeiface, self.netsettings[self.activeiface]['link'].
            upper()))
        self.net_text2.set_text("IP:      %-15s  MAC: %s" % (self.netsettings[
            self.activeiface]['addr'],
            self.netsettings[self.activeiface]['mac']))
        self.net_text3.set_text("Netmask: %-15s  Gateway: %s" % (
            self.netsettings[self.activeiface]['netmask'],
            self.gateway))
        if self.netsettings[self.activeiface]['link'].upper() == "UP":
            if self.netsettings[self.activeiface]['bootproto'] == "dhcp":
                self.net_text4.set_text("WARNING: Cannot use interface running"
                                        " DHCP.\nReconfigure as static in "
                                        "Network Setup screen.")
            else:
                self.net_text4.set_text("")
        else:
            self.net_text4.set_text("WARNING: This interface is DOWN. "
                                    "Configure it first.")

        # If DHCP pool start and matches activeiface network, don't update
        # This means if you change your pool values, go to another page, then
        # go back, it will not reset your changes. But what is more likely is
        # you will change the network settings for admin interface and then
        # come back to this page to update your DHCP settings. If the
        # inSameSubnet test fails, just recalculate and set new values.
        for index, key in enumerate(self.fields):
            if key == "ADMIN_NETWORK/dhcp_pool_start":
                dhcp_start = self.edits[index].get_edit_text()
                break
        if network.inSameSubnet(dhcp_start,
                                self.netsettings[self.activeiface]['addr'],
                                self.netsettings[self.activeiface]['netmask']):
            log.debug("Valid network settings configured. Skipping "
                      "generation.")
            return
        else:
            log.debug("Existing network settings missing or invalid. "
                      "Updating...")

        # Calculate and set Static/DHCP pool fields
        # Max IPs = net size - 2 (master node + bcast)
        # Add gateway so we exclude it
        net_ip_list = network.getNetwork(
            self.netsettings[self.activeiface]['addr'],
            self.netsettings[self.activeiface]['netmask'],
            self.gateway)
        try:
            dhcp_pool = net_ip_list[1:]
            dynamic_start = str(dhcp_pool[0])
            dynamic_end = str(dhcp_pool[-1])
            if self.net_text4.get_text() == "":
                self.net_text4.set_text("This network configuration can "
                                        "support %s nodes." % len(dhcp_pool))
        except Exception:
            # We don't have valid values, so mark all fields empty
            dynamic_start = ""
            dynamic_end = ""
        for index, key in enumerate(self.fields):
            if key == "ADMIN_NETWORK/dhcp_pool_start":
                self.edits[index].set_edit_text(dynamic_start)
            elif key == "ADMIN_NETWORK/dhcp_pool_end":
                self.edits[index].set_edit_text(dynamic_end)
            elif key == "ADMIN_NETWORK/dhcp_gateway":
                self.edits[index].set_edit_text(self.netsettings[
                    self.activeiface]['addr'])

    def refresh(self):
        self.getNetwork()
        self.setNetworkDetails()

    def screenUI(self):
        return modulehelper.ModuleHelper.screenUI(self, self.header_content,
                                                  self.fields, self.defaults)
