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
from fuelmenu.common import utils
from fuelmenu.settings import Settings

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
        #UI text
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
        #Get field information
        responses = dict()

        for index, fieldname in enumerate(self.fields):
            if fieldname != "blank":
                responses[fieldname] = self.edits[index].get_edit_text()

        ###Validate each field
        errors = []

        #Passwords must match
        if responses["PASSWORD"] != responses["CONFIRM_PASSWORD"]:
            errors.append("Passwords do not match.")

        #password must not be empty
        if len(responses["PASSWORD"]) == 0:
            errors.append("Password must not be empty.")

        #password needs to be in ASCII character set
        try:
            if responses["PASSWORD"].decode('ascii'):
                pass
        except UnicodeDecodeError:
            errors.append("Password contains non-ASCII characters.")

        if len(errors) > 0:
            log.error("Errors: %s %s" % (len(errors), errors))
            ModuleHelper.display_failed_check_dialog(self, errors)
            return False
        else:
            self.parent.footer.set_text("No errors found.")
            responses['HASHED_PASSWORD'] = crypt.crypt(responses["PASSWORD"])

            return responses

    def apply(self, args):
        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            log.error("%s" % (responses))
            for index, fieldname in enumerate(self.fields):
                if fieldname == "PASSWORD":
                    return (self.edits[index].get_edit_text() == "")
            return False

        self.save(responses)

        hashed = responses['HASHED_PASSWORD']
        log.info("Changing root password")
        #clear any locks first
        rm_command = ["rm", "-f", "/etc/passwd.lock", "/etc/shadow.lock"]
        utils.execute(rm_command)
        usermod_command = ["usermod", "-p", hashed, "root"]
        usermod_code, _, errout = utils.execute(usermod_command)

        if usermod_code == 0:
            self.parent.footer.set_text("Changed applied successfully.")
            log.info("Root password successfully changed.")
            # Reset fields
            self.cancel(None)
        else:
            log.error("Root password change failed with error:"
                      "\"{0}\"".format(errout))
            self.parent.footer.set_text("Unable to apply changes. Check logs "
                                        "for more details.")
            return False
        return True

    def save(self, responses):
        Settings().write(
            {'HASHED_ROOT_PASSWORD': responses['HASHED_PASSWORD']},
            defaultsfile=self.parent.defaultsettingsfile,
            outfn=self.parent.settingsfile,
        )

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults)
