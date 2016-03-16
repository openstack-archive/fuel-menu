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

from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.common import utils

import urwid

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
            ssh_network = self.parent.settings["ADMIN_NETWORK"]["cidr"]

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
            if fieldname != "blank":
                responses[fieldname] = self.edits[index].get_edit_text()
        ssh_network = responses["SSH_NETWORK"]

        if len(ssh_network) == 0:
            self.parent.footer.set_text("Address is empty, "
                                        "no changes will be made.")
            log.warning("Empty address, skipping.")
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
        return ModuleHelper.screenUI(self, self.header_content,
                                     self.fields, self.defaults)
