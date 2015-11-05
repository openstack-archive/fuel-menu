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

import fuelmenu.common.urwidwrapper as widget
import logging
import urwid

blank = urwid.Divider()

#Need to define fields in order so it will render correctly

class FeatureGroups(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Feature groups"
        self.priority = 10
        self.visible = True
        self.deployment = "pre"
        self.parent = parent

        #UI details
        self.header_content = ["Feature groups", "Note: Depending on which "
                               "feature groups are chosen, some options "
                               "on UI will be shown or hidden."]

        self.fields = ["FEATURE_GROUPS"]
        self.defaults = {
            "FEATURE_GROUPS": {
                "label": "Feature groups",
                "tooltip": "",
                "value": [
                    "experimental",
                    "advanced",
                ]
            }
        }
        self.dialog = widget.MultiChoiceGroup(self.fields, self.defaults)
        self.oldsettings = self.load()
        self.screen = None

    def check(self, args):
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()
        return self.responses

    def apply(self, args):
        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            log.error("%s", responses)
            return False
        self.save(responses)
        return True


    def callback(self, chbox, new_state, user_data=None):
        fgrp = chbox.get_label()
        if new_state and fgrp not in self.feature_groups:
            self.feature_group.append(fgrp)
        elif not new_state and fgrp in self.feature_groups:
            self.feature_groups.


    def cancel(self):
        pass

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults, showallbuttons=True)
