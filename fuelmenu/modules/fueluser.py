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

try:
    from collections import OrderedDict
except Exception:
    # python 2.6 or earlier use backport
    from ordereddict import OrderedDict

from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.settings import Settings
import logging
import re
import urwid
import urwid.raw_display
import urwid.web_display

log = logging.getLogger('fuelmenu.rootpw')
blank = urwid.Divider()


class fueluser(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Fuel User"
        self.priority = 1
        self.visible = True
        self.parent = parent
        # UI text
        self.header_content = [
            "Set Fuel User password.",
            "Default user: admin",
            "Default password: admin",
            "",
            "For better security please consider using at least 8 symbols"
            "password, both upper- and lowercase letters, and at least one"
            "digit and/or special character like !@#$%^&*()_+."
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

        self.oldsettings = self.load()
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
        if password != responses["CONFIRM_PASSWORD"]:
            # Ignore if password is unchanged
            if password != self.defaults['FUEL_ACCESS/password']['value']:
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
            self.parent.footer.set_text("Error: %s" % (errors[0]))
            log.error("Errors: %s %s" % (len(errors), errors))
            return False
        else:
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
        # Generic settings start
        newsettings = OrderedDict()
        for setting in responses.keys():
            if "/" in setting:
                part1, part2 = setting.split("/")
                if part1 not in newsettings:
                    # We may not touch all settings, so copy oldsettings first
                    try:
                        newsettings[part1] = self.oldsettings[part1]
                    except Exception:
                        if part1 not in newsettings.keys():
                            newsettings[part1] = OrderedDict()
                        log.warning("issues setting newsettings %s " % setting)
                        log.warning("current newsettings: %s" % newsettings)
                newsettings[part1][part2] = responses[setting]
            else:
                newsettings[setting] = responses[setting]
        Settings().write(newsettings,
                         defaultsfile=self.parent.defaultsettingsfile,
                         outfn=self.parent.settingsfile)

        self.parent.footer.set_text("Changes applied successfully.")
        # Reset fields
        self.cancel(None)

    def load(self):
        return ModuleHelper.load(self, ignoredparams=['CONFIRM_PASSWORD'])

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults)
