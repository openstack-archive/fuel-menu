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

from fuelmenu.common import dialog
from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.common.modulehelper import WidgetType
import fuelmenu.common.urwidwrapper as widget
from fuelmenu.common import utils
import logging
import re
import urwid
log = logging.getLogger('fuelmenu.mirrors')
blank = urwid.Divider()


class NtpSetup(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Time Sync"
        self.visible = True
        self.parent = parent

        # UI details
        self.header_content = ["NTP Setup", "Note: If you continue without "
                               "NTP, you may have issues with deployment "
                               "due to time synchronization issues. These "
                               "problems are exacerbated in virtualized "
                               "environments.", "",
                               "Deployed nodes will use Fuel Master as time "
                               "source if NTP is disabled."]

        self.fields = ["ntpenabled", "NTP1", "NTP2", "NTP3"]
        self.defaults = \
            {
                "ntpenabled": {"label": "Enable NTP:",
                               "tooltip": "",
                               "type": WidgetType.RADIO,
                               "callback": self.radioSelect},
                "NTP1": {"label": "NTP Server 1:",
                         "tooltip": "NTP Server for time synchronization",
                         "value": "time.nist.gov"},
                "NTP2": {"label": "NTP Server 2:",
                         "tooltip": "NTP Server for time synchronization",
                         "value": "time-a.nist.gov"},
                "NTP3": {"label": "NTP Server 3:",
                         "tooltip": "NTP Server for time synchronization",
                         "value": "time-b.nist.gov"},
            }

        # Load info
        self.gateway = self.get_default_gateway_linux()

        self.load()
        self.screen = None

    def check(self, args):
        """Validate that all fields have valid values and sanity checks."""
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()
        # Get field information
        responses = dict()
        ntp_enabled = False

        for index, fieldname in enumerate(self.fields):
            if fieldname == "blank":
                pass
            elif fieldname == "ntpenabled":
                rb_group = self.edits[index].rb_group
                if rb_group[0].state:
                    ntp_enabled = True
            else:
                responses[fieldname] = self.edits[index].get_edit_text()

        if self.parent.save_only:
            return responses

        # Validate each field
        errors = []
        warnings = []
        if not ntp_enabled:
            # Disabled NTP means passing no NTP servers to save method
            # Even though nodes will use Fuel Master, NTP[1,2,3] are empty so
            # Fuel Master can initialize itself as a time source.
            responses = {
                'NTP1': "",
                'NTP2': "",
                'NTP3': ""}
            self.parent.footer.set_text("No errors found.")
            log.info("No errors found")
            return responses

        for ntpfield, ntpvalue in responses.iteritems():
            # NTP must be under 255 chars
            if len(ntpvalue) >= 255:
                errors.append("%s must be under 255 chars." %
                              self.defaults[ntpfield]['label'])

            # NTP needs to have valid chars
            if re.search('[^a-zA-Z0-9-.]', ntpvalue):
                errors.append("%s contains illegal characters." %
                              self.defaults[ntpfield]['label'])

            # ensure external NTP is valid
            if len(ntpvalue) > 0:
                # Validate first NTP address
                try:
                    # Try to test NTP via ntpdate
                    if not self.checkNTP(ntpvalue):
                        warnings.append("%s unable to perform NTP."
                                        % self.defaults[ntpfield]['label'])
                except Exception:
                    warnings.append("%s unable to sync time with server.: %s"
                                    % self.defaults[ntpfield]['label'])
        if len(errors) > 0:
            log.error("Errors: %s %s" % (len(errors), errors))
            ModuleHelper.display_failed_check_dialog(self, errors)
            return False
        else:
            if len(warnings) > 0:
                msg = ["NTP configuration has the following warnings:"]
                msg.extend(warnings)
                msg.append("You may see errors during provisioning and "
                           "in system logs. NTP errors are not fatal.")
                warning_msg = '\n'.join(str(line) for line in msg)
                dialog.display_dialog(self, widget.TextLabel(warning_msg),
                                      "NTP Warnings")
                log.warning(warning_msg)
            self.parent.footer.set_text("No errors found.")
            log.info("No errors found")
            return responses

    def apply(self, args):
        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            log.error("%s" % (responses))
            return False

        self.save(responses)
        # Apply NTP now, ignoring errors
        if len(responses['NTP1']) > 0:
            # Stop ntpd, run ntpdate, start ntpd
            start_command = ["service", "ntpd", "start"]
            stop_command = ["service", "ntpd", "stop"]
            ntpdate_command = ["ntpdate", "-t5", responses['NTP1']]
            utils.execute(stop_command)
            utils.execute(ntpdate_command)
            utils.execute(start_command)
        return True

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def get_default_gateway_linux(self):
        return ModuleHelper.get_default_gateway_linux()

    def load(self):
        ModuleHelper.load_to_defaults(
            self.parent.settings, self.defaults, ignoredparams=['ntpenabled'])

    def save(self, responses):
        settings = self.parent.settings
        newsettings = ModuleHelper.make_settings_from_responses(responses)
        settings.merge(newsettings)

        # Update defaults
        for index, fieldname in enumerate(self.fields):
            if fieldname != "blank" and fieldname in settings:
                self.defaults[fieldname]['value'] = settings[fieldname]

    def checkNTP(self, server):
        # Use ntpdate to verify server answers NTP requests
        command = ["ntpdate", "-q", "-t2", server]
        code, _, _ = utils.execute(command)
        return (code == 0)

    def refresh(self):
        self.gateway = self.get_default_gateway_linux()
        # If gateway is empty, disable NTP
        if self.gateway is None:
            for index, fieldname in enumerate(self.fields):
                if fieldname == "ntpenabled":
                    log.info("Disabling NTP because there is no gateway")
                    rb_group = self.edits[index].rb_group
                    rb_group[0].set_state(False)
                    rb_group[1].set_state(True)

    def radioSelect(self, current, state, user_data=None):
        """Update network details and display information."""
        # This makes no sense, but urwid returns the previous object.
        # The previous object has True state, which is wrong.
        # Somewhere in current.group a RadioButton is set to True.
        # Our quest is to find it.
        for rb in current.group:
            if rb.get_label() == current.get_label():
                continue
            if rb.base_widget.state is True:
                self.extdhcp = (rb.base_widget.get_label() == "Yes")
                break

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults)
