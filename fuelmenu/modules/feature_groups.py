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

import logging

import urwid

from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.common.modulehelper import WidgetType
from fuelmenu.common import utils
from fuelmenu import consts


log = logging.getLogger(__name__)


class feature_groups(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Feature groups"
        self.priority = 70
        self.visible = True
        self.parent = parent

        # UI details
        self.header_content = [
            "Feature groups",
            "Note: Depending on which feature groups are enabled, "
            "some options on UI will be shown or hidden."
        ]
        self.fields = (
            "FEATURE_GROUPS/experimental",
            "FEATURE_GROUPS/advanced",
        )
        self.defaults = {
            "FEATURE_GROUPS/experimental": {
                "label": "Experimental features",
                "tooltip": "(not thoroughly tested)",
                "type": WidgetType.CHECKBOX,
            },
            "FEATURE_GROUPS/advanced": {
                "label": "Advanced features",
                "tooltip": "",
                "type": WidgetType.CHECKBOX,
            }
        }
        self.load()
        self.screen = None

    @property
    def responses(self):
        ret = dict()
        for index, fieldname in enumerate(self.fields):
            ret[fieldname] = self.edits[index].get_state()
        return ret

    def check(self, args):
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()
        self.parent.footer.set_text("No errors found.")
        return self.responses

    def apply(self, args):
        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            log.error("%s", responses)
            return False
        newsettings = self.save(responses)

        if utils.is_post_deployment() and newsettings:
            # Force save setting to the file
            self.parent.force_save(newsettings)
            # Apply changes to the Nailgun
            cmd = ["puppet", "apply", "--debug", "--verbose", "--logdest",
                   consts.PUPPET_LOGFILE, consts.PUPPET_NAILGUN]
            err_code, _, errout = utils.execute(cmd)
            if err_code != 0:
                log.error("Puppet apply failed with an error: "
                          "\"{0}\"".format(errout))
                self.parent.footer.set_text("Puppet apply failed. "
                                            "Check logs for more details.")
                return False
            self.parent.footer.set_text("Changes successfully applied.")

        return True

    def load(self):
        # Read in yaml
        oldsettings = self.parent.settings

        for setting in self.defaults:
            try:
                part1, part2 = setting.split("/")
                self.defaults[setting]["value"] = part2 in oldsettings[part1]
            except Exception as e:
                log.warning("unexpected error: %s", e.message)

    def save(self, responses):
        newsettings = {}
        for setting in responses:
            part1, part2 = setting.split("/")
            if part1 not in newsettings:
                newsettings[part1] = []
            if responses[setting]:
                newsettings[part1].append(part2)
        self.parent.settings.merge(newsettings)
        return newsettings

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults, show_all_buttons=True)
