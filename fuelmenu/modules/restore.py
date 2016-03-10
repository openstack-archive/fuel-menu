#!/usr/bin/env python
# Copyright 2015 Mirantis, Inc.
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

import collections
import logging
import os

import urwid
import yaml

from fuelmenu.common import modulehelper as helper
from fuelmenu import settings as settings_utils

LOG = logging.getLogger('fuelmenu.restore')
KEYS_TO_RESTORE = [
    ("HOSTNAME", None),
    ("DNS_DOMAIN", None),
    ("DNS_SEARCH", None),
    ("DNS_UPSTREAM", None),
    ("ADMIN_NETWORK", [
        "interface",
        "ipaddress",
        "netmask",
        "mac",
        "dhcp_pool_start",
        "dhcp_pool_end",
        "dhcp_gateway",
    ]),
    ("astute", ["user", "password"]),
    ("cobbler", ["user", "password"]),
    ("keystone", [
        "admin_token",
        "ostf_user",
        "ostf_password",
        "nailgun_user",
        "nailgun_password",
        "monitord_user",
        "monitord_password",
    ]),
    ("mcollective", ["user", "password"]),
    ("postgres", [
        "keystone_dbname",
        "keystone_user",
        "keystone_password",
        "nailgun_dbname",
        "nailgun_user",
        "nailgun_password",
        "ostf_dbname",
        "ostf_user",
        "ostf_password",
    ]),
    ("FUEL_ACCESS", ["user", "password"]),
]


class restore(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Restore settings"
        self.priority = 98
        self.visible = True
        self.parent = parent
        self.deployment = "pre"
        self.screen = None

        self.header_content = ["Load settings from a file",
                               "(Use 'Shell Login' if you want fetch "
                               "settings manually from a remote host and then "
                               "return to this menu to restore them.)",
                               "NOTE: After restoring settings in this "
                               "section, please exit from the menu without "
                               "saving changes."]
        self.fields = ["PATH"]
        self.defaults = {
            "PATH": {
                "label": "Enter filename",
                "tooltip": "Use absolute path to a file "
                           "(e.g. /etc/fuel/astute70.yaml).",
                "value": "",
            },
        }

        self.oldsettings = self.load()

    def cancel(self, button):
        helper.ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def check_settings(self, settings):
        required_keys = []
        responses = collections.OrderedDict()
        for key, subkeys in KEYS_TO_RESTORE:
            if key not in settings:
                if subkeys:
                    required_keys.extend("{0}/{1}".format(key, subkey)
                                         for subkey in subkeys)
                    continue
                required_keys.append(key)
                continue
            parameters = settings[key]
            if not subkeys:
                responses[key] = parameters
                continue
            for subkey in subkeys:
                subkey_name = "{0}/{1}".format(key, subkey)
                if subkey not in parameters:
                    required_keys.append(subkey_name)
                    continue
                responses[subkey_name] = parameters[subkey]
        return responses, required_keys

    def show_error_msg(self, error_msg, exc_info=False):
        LOG.error("Error: %s", error_msg, exc_info=exc_info)
        helper.ModuleHelper.display_failed_check_dialog(self, [error_msg])

    def check(self, args):
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()

        path = self.edits[0].get_edit_text()
        # The PATH field is not required and if it is empty, then there
        # is nothing to check.
        if not path:
            self.parent.footer.set_text("Nothing to check.")
            return None

        path = os.path.abspath(path)
        try:
            with open(path) as f:
                settings = yaml.load(f)
        except IOError as err:
            self.show_error_msg("Could not fetch settings: {0}".format(err),
                                exc_info=True)
            return False
        except yaml.YAMLError as err:
            self.show_error_msg("Could not parse YAML from the source: {0}."
                                .format(err), exc_info=True)
            return False

        LOG.debug("Successfully loaded settings: %s", settings)

        if not settings:
            self.show_error_msg("Settings should not be empty.")
            return False

        responses, required_keys = self.check_settings(settings)
        if required_keys:
            self.show_error_msg("Settings should contain keys: {0}"
                                .format(', '.join(required_keys)))
            return False

        self.parent.footer.set_text("No errors found.")
        return responses

    def apply(self, args):
        responses = self.check(args)
        if responses is None:
            self.parent.footer.set_text("Nothing to restore, skipping.")
            return True
        elif not responses:
            msg = "Checking failed. Not applying."
            LOG.error(msg)
            self.parent.footer.set_text(msg)
            return False
        self.parent.footer.set_text("Applying changes...")
        self.save(responses)
        self.parent.footer.set_text("Changes saved successfully.")
        return True

    def load(self):
        return helper.ModuleHelper.load(self, ignoredparams=('PATH',))

    def save(self, responses):
        newsettings = helper.ModuleHelper.save(self, responses)
        # TODO(akscram): The restore module writes settings itself into
        #                the configuration file and requires from the
        #                user to exit from the menu without saving
        #                changes. It is a necessary requirement due to
        #                the limitations of fuel menu. For more
        #                information see the bug report
        #                https://bugs.launchpad.net/fuel/+bug/1527111.
        settings_utils.Settings().write(
            newsettings,
            defaultsfile=self.parent.defaultsettingsfile,
            outfn=self.parent.settingsfile)
        self.oldsettings = newsettings

    def screenUI(self):
        return helper.ModuleHelper.screenUI(
            self, self.header_content, self.fields, self.defaults,
            show_all_buttons=True)
