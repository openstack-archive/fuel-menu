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
from fuelmenu.settings import Settings


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
        self.oldsettings = self.load()
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
        self.save(responses)
        return True

    def load(self):
        # Read in yaml
        defaultsettings = Settings().read(self.parent.defaultsettingsfile)
        oldsettings = defaultsettings
        oldsettings.update(Settings().read(self.parent.settingsfile))
        for setting in self.defaults:
            try:
                part1, part2 = setting.split("/")
                self.defaults[setting]["value"] = part2 in oldsettings[part1]
            except Exception as e:
                log.warning("unexpected error: %s", e.message)
        return oldsettings

    def save(self, responses):
        newsettings = {}
        for setting in responses.keys():
            part1, part2 = setting.split("/")
            if part1 not in newsettings:
                newsettings[part1] = []
            if responses[setting]:
                newsettings[part1].append(part2)

        Settings().write(newsettings,
                         defaultsfile=self.parent.defaultsettingsfile,
                         outfn=self.parent.settingsfile)

        self.oldsettings = newsettings
        for setting in self.defaults:
            part1, part2 = setting.split("/")
            self.defaults[setting]["value"] = part2 in newsettings[part1]

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def refresh(self):
        pass

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults, show_all_buttons=True)
