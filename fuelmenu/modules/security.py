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

from fuelmenu.common import modulehelper
from fuelmenu.common import network

import logging
import urwid

log = logging.getLogger('fuelmenu.security')
blank = urwid.Divider()


class security(object):
    def __init__(self, parent):
        self.name = "Security Setup"
        self.priority = 6
        self.visible = True
        self.parent = parent
        self.screen = None
        # UI text
        self.header_content = ["Security settings", ""]
        self.fields = ["SSH_NETWORK"]

        # default settings
        try:
            ssh_network = self.parent.settings["FUEL_ACCESS"]["ssh_network"]
        except KeyError:
            ssh_network = network.getCidr(
                self.parent.settings["ADMIN_NETWORK"]["ipaddress"],
                self.parent.settings["ADMIN_NETWORK"]["netmask"])

        self.defaults = {
            "SSH_NETWORK": {"label": "Restrict SSH access on network ",
                            "tooltip": "Enter network address in CIDR format",
                            "value": ssh_network},
        }

        self.screen = None

    def check(self, args):
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()

        responses = dict()
        for index, fieldname in enumerate(self.fields):
            if fieldname != modulehelper.BLANK_KEY:
                responses[fieldname] = self.edits[index].get_edit_text()
        ssh_network = responses["SSH_NETWORK"]

        errors = []

        if len(ssh_network) == 0:
            self.parent.footer.set_text("Address is empty, "
                                        "will be changed to 0.0.0.0")
            log.warning("Empty address, changed to 0.0.0.0")
            ssh_network = "0.0.0.0"
        else:
            if not network.getCidrSize(ssh_network):
                errors.append("Incorrect network address format: {0}."
                              .format(ssh_network))

        if len(errors) > 0:
            log.error("Errors: %s %s" % (len(errors), errors))
            modulehelper.ModuleHelper.display_failed_check_dialog(self, errors)
            return False
        else:
            self.parent.footer.set_text("No errors found.")
            return ssh_network

    def apply(self, args):
        ssh_network = self.check(args)
        if ssh_network is False:
            log.error("Check failed. Not applying")
            return False

        newsettings = {'FUEL_ACCESS': {
            'ssh_network': ssh_network,
        }}
        self.parent.settings.merge(newsettings)
        return True

    def refresh(self):
        pass

    def screenUI(self):
        return modulehelper.ModuleHelper.screenUI(self, self.header_content,
                                                  self.fields, self.defaults)
