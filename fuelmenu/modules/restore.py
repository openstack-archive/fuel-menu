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

import logging
import os

import urwid
import yaml

from fuelmenu.common import modulehelper
from fuelmenu.common import utils
from fuelmenu import settings as settings_utils

LOG = logging.getLogger('fuelmenu.restore')


class restore(urwid.WidgetWrap):
    # NOTE(akscram): A list of settings to restore from the specified
    #                location.
    keys_to_restore = [
        "ADMIN_NETWORK/interface",
        "ADMIN_NETWORK/ipaddress",
        "ADMIN_NETWORK/netmask",
        "ADMIN_NETWORK/mac",
        "ADMIN_NETWORK/dhcp_pool_start",
        "ADMIN_NETWORK/dhcp_pool_end",
        "ADMIN_NETWORK/dhcp_gateway",
        "HOSTNAME",
        "DNS_DOMAIN",
        "DNS_SEARCH",
        "astute/user",
        "astute/password",
        "cobbler/user",
        "cobbler/password",
        "keystone/admin_token",
        "keystone/ostf_user",
        "keystone/ostf_password",
        "keystone/nailgun_user",
        "keystone/nailgun_password",
        "keystone/monitord_user",
        "keystone/monitord_password",
        "mcollective/user",
        "mcollective/password",
        "postgres/keystone_dbname",
        "postgres/keystone_user",
        "postgres/keystone_password",
        "postgres/nailgun_dbname",
        "postgres/nailgun_user",
        "postgres/nailgun_password",
        "postgres/ostf_dbname",
        "postgres/ostf_user",
        "postgres/ostf_password",
        "FUEL_ACCESS/user",
        "FUEL_ACCESS/password",
    ]

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
                               "NOTE: Carefully check all settings in all "
                               "tabs after restoring settings from the "
                               "specified path. It is a very important step "
                               "before continuing installation."]
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
        modulehelper.ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def check(self, args):
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()

        path = self.edits[0].get_edit_text()
        path = os.path.abspath(path)

        errors = []
        if not path:
            errors.append("The path should not be empty.")
        else:
            try:
                with open(path) as f:
                    settings = yaml.load(f)
            except IOError as err:
                msg = "Could not fetch settings: {0}".format(err)
                LOG.exception(msg)
                errors.append(msg)
            except yaml.YAMLError as err:
                msg = "Could not parse YAML from the source: {0}.".format(err)
                LOG.exception(msg)
                errors.append(msg)
            else:
                LOG.debug("Successfully loaded settings: %s", settings)
                if not settings:
                    errors.append("Settings should not be emty.")
                else:
                    responses = utils.OrderedDict()
                    required_keys = []
                    for key in self.keys_to_restore:
                        key1, _, key2 = key.partition('/')
                        if key1 not in settings or \
                                key1 in settings and key2 and \
                                key2 not in settings[key1]:
                            required_keys.append(key)
                        else:
                            if key2:
                                responses[key] = settings[key1][key2]
                            else:
                                responses[key] = settings[key1]
                    if required_keys:
                        errors.append("Fetched settings should contain keys: "
                                      "{0}".format(', '.join(required_keys)))
        if errors:
            LOG.error("Errors: %s", errors)
            modulehelper.ModuleHelper.display_failed_check_dialog(self, errors)
            return False
        self.parent.footer.set_text("No errors found.")
        return responses

    def apply(self, args):
        responses = self.check(args)
        if not responses:
            msg = "Checking failed. Not applying."
            LOG.error(msg)
            self.parent.footer.set_text(msg)
            return False
        self.parent.footer.set_text("Applying changes...")
        self.save(responses)
        self.parent.footer.set_text("Changes saved successfully.")

    def load(self):
        return modulehelper.ModuleHelper.load(self, ignoredparams=('PATH',))

    def save(self, responses):
        newsettings = modulehelper.ModuleHelper.save(self, responses)
        settings_utils.Settings().write(
            newsettings,
            defaultsfile=self.parent.defaultsettingsfile,
            outfn=self.parent.settingsfile)
        self.oldsettings = newsettings

    def screenUI(self):
        return modulehelper.ModuleHelper.screenUI(self, self.header_content,
                                                  self.fields, self.defaults,
                                                  showallbuttons=True)
