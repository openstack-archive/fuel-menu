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
    "HOSTNAME",
    "DNS_DOMAIN",
    "DNS_SEARCH",
]
COMPOSED_KEYS_TO_RESTORE = [
    ("ADMIN_NETWORK", "interface"),
    ("ADMIN_NETWORK", "ipaddress"),
    ("ADMIN_NETWORK", "netmask"),
    ("ADMIN_NETWORK", "mac"),
    ("ADMIN_NETWORK", "dhcp_pool_start"),
    ("ADMIN_NETWORK", "dhcp_pool_end"),
    ("ADMIN_NETWORK", "dhcp_gateway"),
    ("astute", "user"),
    ("astute", "password"),
    ("cobbler", "user"),
    ("cobbler", "password"),
    ("keystone", "admin_token"),
    ("keystone", "ostf_user"),
    ("keystone", "ostf_password"),
    ("keystone", "nailgun_user"),
    ("keystone", "nailgun_password"),
    ("keystone", "monitord_user"),
    ("keystone", "monitord_password"),
    ("mcollective", "user"),
    ("mcollective", "password"),
    ("postgres", "keystone_dbname"),
    ("postgres", "keystone_user"),
    ("postgres", "keystone_password"),
    ("postgres", "nailgun_dbname"),
    ("postgres", "nailgun_user"),
    ("postgres", "nailgun_password"),
    ("postgres", "ostf_dbname"),
    ("postgres", "ostf_user"),
    ("postgres", "ostf_password"),
    ("FUEL_ACCESS", "user"),
    ("FUEL_ACCESS", "password"),
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

    def check(self, args):
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()

        path = self.edits[0].get_edit_text()
        # The PATH field is not required and if it is empty, then there
        # is nothing to check.
        if not path:
            self.parent.footer.set_text("Nothing to check.")
            return

        error_msg = None
        path = os.path.abspath(path)
        try:
            with open(path) as f:
                settings = yaml.load(f)
        except IOError as err:
            error_msg = "Could not fetch settings: {0}".format(err)
            LOG.exception(error_msg)
        except yaml.YAMLError as err:
            error_msg = "Could not parse YAML from the source: {0}." \
                        .format(err)
            LOG.exception(error_msg)
        else:
            LOG.debug("Successfully loaded settings: %s", settings)
            if not settings:
                error_msg = "Settings should not be empty."
            else:
                required_keys = []
                responses = collections.OrderedDict()
                for key in KEYS_TO_RESTORE:
                    if key not in settings:
                        required_keys.append(key)
                        continue
                    responses[key] = settings[key]
                for section, key in COMPOSED_KEYS_TO_RESTORE:
                    setting_key = "{0}/{1}".format(section, key)
                    if section not in settings or key not in settings[section]:
                        required_keys.append(setting_key)
                        continue
                    responses[setting_key] = settings[section][key]
                if required_keys:
                    error_msg = "Settings should contain keys: {0}"\
                                .format(', '.join(required_keys))
        if error_msg:
            LOG.error("Error: %s", error_msg)
            helper.ModuleHelper.display_failed_check_dialog(self, [error_msg])
            return False
        self.parent.footer.set_text("No errors found.")
        return responses

    def apply(self, args):
        responses = self.check(args)
        if responses is None:
            self.parent.footer.set_text("Nothing to restore, skipping.")
            return False
        elif not responses:
            msg = "Checking failed. Not applying."
            LOG.error(msg)
            self.parent.footer.set_text(msg)
            return False
        self.parent.footer.set_text("Applying changes...")
        self.save(responses)
        self.parent.footer.set_text("Changes saved successfully.")

    def load(self):
        return helper.ModuleHelper.load(self, ignoredparams=('PATH',))

    def save(self, responses):
        newsettings = helper.ModuleHelper.save(self, responses)
        settings_utils.Settings().write(
            newsettings,
            defaultsfile=self.parent.defaultsettingsfile,
            outfn=self.parent.settingsfile)
        self.oldsettings = newsettings

    def screenUI(self):
        return helper.ModuleHelper.screenUI(
            self, self.header_content, self.fields, self.defaults,
            showallbuttons=True)
