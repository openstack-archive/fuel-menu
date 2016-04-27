#!/usr/bin/env python
# Copyright 2014 Mirantis, Inc.
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
import logging
import re
import urwid
import urwid.raw_display
import urwid.web_display

log = logging.getLogger('fuelmenu.rootpw')
blank = urwid.Divider()


class FuelUser(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Fuel User"
        self.visible = True
        self.parent = parent
        # UI text
        self.header_content = [
            "Set Fuel User password.",
            "Default user: admin",
            "Default password: admin",
            "",
            "For the better security please consider using password with "
            "at least 8 symbols, both upper- and lowercase letters, and "
            "at least one digit and special character like !@#$%^&*()_+."
        ]
        self.fields = ["FUEL_ACCESS/password", "CONFIRM_PASSWORD"]
        self.defaults = \
            {
                "FUEL_ACCESS/password": {"label": "Fuel password",
                                         "tooltip": "ASCII characters only",
                                         "value": ""},
                "CONFIRM_PASSWORD": {"label": "Confirm password",
                                     "tooltip": "ASCII characters only",
                                     "value": ""},
            }

        self.load()
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

        password = responses["FUEL_ACCESS/password"]

        # Validate each field
        errors = []
        warnings = []

        # Passwords must match
        if password != responses["CONFIRM_PASSWORD"] and \
                password != self.defaults['FUEL_ACCESS/password']['value']:
            errors.append("Passwords do not match.")

        # Password must not be empty
        if len(password) == 0:
            errors.append("Password must not be empty.")

        # Password needs to be in ASCII character set
        try:
            if password.decode('ascii'):
                pass
        except UnicodeDecodeError:
            errors.append("Password contains non-ASCII characters.")

        # Passwords should be at least 8 symbols
        if len(password) < 8:
            warnings.append("8 symbols")

        # Passwords should contain at least one digit
        if re.search(r"\d", password) is None:
            warnings.append("one digit")

        if re.search(r"[A-Z]", password) is None:
            warnings.append("one uppercase letter")

        if re.search(r"[a-z]", password) is None:
            warnings.append("one lowercase letter")

        if re.search(r"[!#$%&'()*+,-./[\\\]^_`{|}~" + r'"]', password) is None:
            warnings.append("one special character")

        if len(errors) > 0:
            log.error("Errors: %s %s" % (len(errors), errors))
            ModuleHelper.display_failed_check_dialog(self, errors)
            return False

        if len(warnings) > 0:
            self.parent.footer.set_text("Warning: Password should have "
                                        "at least %s." % (warnings[0]))
        else:
            self.parent.footer.set_text("No errors found.")

        # Remove confirm from responses so it isn't saved
        del responses["CONFIRM_PASSWORD"]
        return responses

    def apply(self, args):
        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            log.error("%s" % (responses))
            for index, fieldname in enumerate(self.fields):
                if fieldname == "FUEL_ACCESS/password":
                    return (self.edits[index].get_edit_text() == "")
            return False
        self.save(responses)
        return True

    def save(self, responses):
        newsettings = ModuleHelper.make_settings_from_responses(responses)
        self.parent.settings.merge(newsettings)

        self.parent.footer.set_text("Changes applied successfully.")
        # Reset fields
        self.cancel(None)

    def load(self):
        ModuleHelper.load_to_defaults(
            self.parent.settings,
            self.defaults,
            ignoredparams=['CONFIRM_PASSWORD'])

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults)
