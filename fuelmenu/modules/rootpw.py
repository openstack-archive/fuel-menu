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

import crypt
from fuelmenu.common import modulehelper as helper
from fuelmenu.common import utils
from fuelmenu import settings as settings_module

import logging
import urwid

log = logging.getLogger('fuelmenu.rootpw')
blank = urwid.Divider()


class rootpw(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Root Password"
        self.priority = 60
        self.visible = True
        self.parent = parent
        # UI text
        self.header_content = ["Set root user password", ""]
        self.fields = ["PASSWORD", "CONFIRM_PASSWORD"]
        self.defaults = \
            {
                "PASSWORD": {"label": "Enter password",
                             "tooltip": "Use ASCII characters only",
                             "value": ""},
                "CONFIRM_PASSWORD": {"label": "Confirm password",
                                     "tooltip": "Use ASCII characters only",
                                     "value": ""},
            }

        self.screen = None

    def check(self, args):
        """Validate that all fields have valid values and sanity checks."""
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()
        # Get field information
        responses = dict()

        for index, fieldname in enumerate(self.fields):
            if fieldname != "blank":
                responses[fieldname] = self.edits[index].get_edit_text()

        # Validate each field
        errors = []

        password = responses["PASSWORD"]

        # Passwords must match
        if password != responses["CONFIRM_PASSWORD"]:
            errors.append("Passwords do not match.")

        # password needs to be in ASCII character set
        try:
            if password.decode('ascii'):
                pass
        except UnicodeDecodeError:
            errors.append("Password contains non-ASCII characters.")

        if len(errors) > 0:
            self.parent.footer.set_text("Errors occurred.")
            log.error("Errors: %s %s" % (len(errors), errors))
            helper.ModuleHelper.display_failed_check_dialog(self, errors)
            return False

        # check empty password
        if len(password) == 0:
            self.parent.footer.set_text("Password is empty, "
                                        "no changes will be made.")
            log.warning("Empty password, skipping.")
        else:
            self.parent.footer.set_text("No errors found.")
        return password

    def apply(self, args):
        password = self.check(args)
        if password is False:
            log.error("Check failed. Not applying")
            return False

        if len(password) > 0:
            return self.save(password)
        return True

    def save(self, password):
        hashed = crypt.crypt(password, utils.gensalt())
        log.info("Changing root password")
        # clear any locks first
        rm_command = ["rm", "-f", "/etc/passwd.lock", "/etc/shadow.lock"]
        utils.execute(rm_command)
        usermod_command = ["usermod", "-p", hashed, "root"]
        usermod_code, _, errout = utils.execute(usermod_command)

        if usermod_code == 0:
            self.parent.footer.set_text("Changes applied successfully.")
            log.info("Root password successfully changed.")
            # Reset fields
            self.cancel(None)
        else:
            log.error("Root password change failed with error:"
                      "\"{0}\"".format(errout))
            self.parent.footer.set_text("Unable to apply changes. Check logs "
                                        "for more details.")
            return False

        self.save_settings(hashed)
        return True

    def save_settings(self, hashed_pwd):
        bootstrap = helper.ModuleHelper.load(self)['BOOTSTRAP']
        bootstrap['hashed_root_password'] = hashed_pwd

        settings_module.Settings().write(
            {'BOOTSTRAP': bootstrap},
            defaultsfile=self.parent.defaultsettingsfile,
            outfn=self.parent.settingsfile)

    def cancel(self, button):
        helper.ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def screenUI(self):
        return helper.ModuleHelper.screenUI(self, self.header_content,
                                            self.fields, self.defaults)
