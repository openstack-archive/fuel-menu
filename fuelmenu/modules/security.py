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

from fuelmenu.common.modulehelper import BLANK_KEY
from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.common import network

import logging
import urwid

log = logging.getLogger('fuelmenu.security')


class security(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Security Setup"
        self.priority = 6
        self.visible = True
        self.parent = parent
        self.screen = None

        # UI text
        self.header_content = ["Security settings", ""]
        self.fields = ["ADMIN_NETWORK/ssh_network"]

        settings = self.parent.settings
        try:
            self.ssh_network = settings["ADMIN_NETWORK"]["ssh_network"]
        except KeyError:
            self.ssh_network = network.getCidr(
                settings["ADMIN_NETWORK"]["ipaddress"],
                settings["ADMIN_NETWORK"]["netmask"])

        self.defaults = {
            "ADMIN_NETWORK/ssh_network": {
                "label": "Restrict SSH access on network ",
                "tooltip": "Enter network address in CIDR format",
                "value": self.ssh_network
            }
        }
        self.load()
        self.screen = None

    def check(self, args):
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()

        responses = dict()
        for index, fieldname in enumerate(self.fields):
            if fieldname != BLANK_KEY:
                responses[fieldname] = self.edits[index].get_edit_text()

        ssh_network = responses["ADMIN_NETWORK/ssh_network"]
        errors = []

        if len(ssh_network) == 0:
            self.parent.footer.set_text("Address is empty, "
                                        "will be changed to 0.0.0.0/0")
            log.warning("Empty address, changed to 0.0.0.0/0")
            responses["ADMIN_NETWORK/ssh_network"] = "0.0.0.0/0"
        else:
            if not network.getCidrSize(ssh_network):
                errors.append("Incorrect network address format: {0}."
                              .format(ssh_network))

        if len(errors) > 0:
            log.error("Errors: %s %s", len(errors), errors)
            ModuleHelper.display_failed_check_dialog(self, errors)
            return False

        self.parent.footer.set_text("No errors found.")
        return responses

    def apply(self, args):
        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            log.error("%s" % (responses))
            return False
        self.save(responses)
        return True

    def save(self, responses):
        newsettings = ModuleHelper.make_settings_from_responses(responses)
        self.parent.settings.merge(newsettings)

    def load(self):
        ModuleHelper.load_to_defaults(self.parent.settings, self.defaults)

    def refresh(self):
        pass

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content,
                                     self.fields, self.defaults)
