#!/usr/bin/env python
# Copyright 2016 Mirantis, Inc.
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

from oslo_log import log as logging
import urwid

from fuelmenu.common import dialog
from fuelmenu.common import modulehelper as helper
from fuelmenu.common import network
from fuelmenu.common import puppet
from fuelmenu.common import urwidwrapper as widget
from fuelmenu.common import utils
from fuelmenu import consts

log = logging.getLogger('fuelmenu.security')

SSH_NETWORK = 'ADMIN_NETWORK/ssh_network'


class Security(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Security Setup"
        self.visible = True
        self.parent = parent
        self.screen = None

        # UI text
        self.header_content = ["Security settings", ""]
        self.fields = [SSH_NETWORK]

        self.defaults = {
            SSH_NETWORK: {
                "label": "Restrict SSH access on network ",
                "tooltip": "Enter network address in CIDR format",
                "value": ""
            }
        }
        self.load()
        self.screen = None

    def check(self, args):
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()

        responses = dict()
        for index, fieldname in enumerate(self.fields):
            if fieldname != helper.BLANK_KEY:
                responses[fieldname] = self.edits[index].get_edit_text()

        ssh_network = responses[SSH_NETWORK]
        errors = []

        if len(ssh_network) == 0:
            self.parent.footer.set_text("Address is empty, "
                                        "will be changed to 0.0.0.0/0")
            log.warning("Empty address, changed to 0.0.0.0/0")
            responses[SSH_NETWORK] = "0.0.0.0/0"

            msg = "If you continue without the address, you may able to"\
                  + " access the Fuel through SSH from any network. The"\
                  + " address will be changed to 0.0.0.0/0. This can lead"\
                  + " to the security issues."

            dialog.display_dialog(
                self, widget.TextLabel(msg), "Empty Address Warning")

        else:
            if not network.getCidrSize(ssh_network):
                errors.append("Incorrect network address format: {0}."
                              .format(ssh_network))

        if len(errors) > 0:
            log.error("Errors: %s %s", len(errors), errors)
            helper.ModuleHelper.display_failed_check_dialog(self, errors)
            return False

        self.parent.footer.set_text("No errors found.")
        return responses

    def apply(self, args):
        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            return False

        if utils.is_post_deployment():
            self.parent.apply_tasks.add(self.apply_to_master)

        self.save(responses)
        return True

    def apply_to_master(self):
        """Apply changes to the Fuel master"""

        msg = "Apply settings to Fuel master."
        log.info(msg)
        self.parent.footer.set_text(msg)
        self.parent.refreshScreen()

        result, msg = puppet.puppetApplyManifest(consts.PUPPET_FUEL_MASTER)

        self.parent.footer.set_text(msg)
        return result

    def save(self, responses):
        newsettings = helper.ModuleHelper.make_settings_from_responses(
            responses)
        self.parent.settings.merge(newsettings)

    def load(self):
        admin_network = network.get_iface_info(self.parent.managediface)
        self.defaults[SSH_NETWORK]['value'] = network.getCidr(
            admin_network["addr"],
            admin_network["netmask"])

        helper.ModuleHelper.load_to_defaults(
            self.parent.settings,
            self.defaults,
        )

    def refresh(self):
        pass

    def screenUI(self):
        return helper.ModuleHelper.screenUI(self, self.header_content,
                                            self.fields, self.defaults)
