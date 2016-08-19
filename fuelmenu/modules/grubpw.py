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

import logging
import re
import urwid

from fuelmenu.common import modulehelper as helper
from fuelmenu.common import utils

log = logging.getLogger('fuelmenu.grubpw')


class GrubPassword(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Grub Password"
        self.visible = True
        self.parent = parent

        # UI text
        self.header_content = ["Set Grub password.", "",
                               "Default user: root", ""]
        self.fields = ["PASSWORD", "CONFIRM_PASSWORD"]

        self.defaults = {
            "PASSWORD": {"label": "Enter new password",
                         "tooltip": "Use ASCII characters only",
                         "value": ""},
            "CONFIRM_PASSWORD": {"label": "Confirm new password",
                                 "tooltip": "Use ASCII characters only",
                                 "value": ""},
        }

        self.screen = None

    def check(self, args):
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()

        responses = dict()
        for index, fieldname in enumerate(self.fields):
            if fieldname != helper.BLANK_KEY:
                responses[fieldname] = self.edits[index].get_edit_text()

        password = responses["PASSWORD"]
        errors = []

        # passwords must match
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
            log.error("Errors: %s %s", len(errors), errors)
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
        if self.parent.save_only:
            # We shouldn't change root password in save_only mode
            return True

        # there is no convinient way to create grub2 pbkdf password
        # grub2-mkpasswd-pbkdf2 can read input password only from stdin
        cmd = ["/usr/bin/grub2-mkpasswd-pbkdf2"]
        stdin = "{0}\n{0}".format(password)
        errcode, out, errout = utils.execute(cmd, stdin=stdin)

        # parse grub2-mkpasswd-pbkdf2 output
        pbkdf2 = re.findall('grub.pbkdf2.*', out, re.M)

        if errcode == 0 and pbkdf2 != []:
            grub2_password = "GRUB2_PASSWORD={0}".format(pbkdf2[0])
            log.info(grub2_password)

            log.info("Creating new /boot/grub2/user.cfg file")
            # overwrite /boot/grub2/user.cfg file if exists
            with open("/boot/grub2/user.cfg", "w") as usercfg:
                usercfg.write(grub2_password)
                usercfg.write("\n")
                usercfg.close()

            self.parent.footer.set_text("Changes applied successfully.")
            log.info("Grub password successfully set.")
            # Reset fields
            self.cancel(None)
        else:
            log.error("Command grub2-mkpasswd-pbkdf2 failed with an error:"
                      "\"{0}\"".format(errout))
            self.parent.footer.set_text("Unable to apply changes. Check logs "
                                        "for more details.")
            return False

        return True

    def cancel(self, button):
        helper.ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def screenUI(self):
        return helper.ModuleHelper.screenUI(self, self.header_content,
                                            self.fields, self.defaults)
