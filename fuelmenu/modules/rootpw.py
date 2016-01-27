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
from fuelmenu.common.modulehelper import ModuleHelper
import logging
import subprocess
import urwid
import urwid.raw_display
import urwid.web_display

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
        warnings = []

        password = responses["PASSWORD"]

        # Passwords must match
        if password != responses["CONFIRM_PASSWORD"]:
            errors.append("Passwords do not match.")

        # password must not be empty
        if len(password) == 0:
            self.parent.footer.set_text("Password is empty, "
                                        "no changes will be made.")
            log.warning("Empty password, skipping.")

        # password needs to be in ASCII character set
        try:
            if password.decode('ascii'):
                pass
        except UnicodeDecodeError:
            errors.append("Password contains non-ASCII characters.")

        if len(errors) > 0:
            self.parent.footer.set_text("Errors occurred.")
            log.error("Errors: %s %s" % (len(errors), errors))
            ModuleHelper.display_failed_check_dialog(self, errors)
            return False
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
        hashed = crypt.crypt(password)
        log.info("Changing root password")
        try:
            # clear any locks first
            noout = open('/dev/null', 'w')
            subprocess.call(["rm", "-f", "/etc/passwd.lock",
                             "/etc/shadow.lock"], stdout=noout,
                            stderr=noout)
            retcode = subprocess.call(["usermod", "-p", hashed, "root"],
                                      stdout=noout,
                                      stderr=noout)
        except OSError:
            log.error("Unable to change password.")
            self.parent.footer.set_text("Unable to change password.")
            return False

        if retcode == 0:
            self.parent.footer.set_text("Changes applied successfully.")
            log.info("Root password successfully changed.")
            # Reset fields
            self.cancel(None)
        else:
            self.parent.footer.set_text("Unable to apply changes. Check logs "
                                        "for more details.")
            return False
        return True

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults)
