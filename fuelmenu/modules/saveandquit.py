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
import time
import urwid
import urwid.raw_display
import urwid.web_display

from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.common import utils
from fuelmenu import consts
import fuelmenu.common.urwidwrapper as widget


log = logging.getLogger(__name__)
blank = urwid.Divider()


class saveandquit(object):
    def __init__(self, parent):
        self.name = "Quit Setup"
        self.priority = 99
        self.visible = True
        self.parent = parent
        self.screen = None
        # UI text
        saveandcontinue_button = widget.Button("Save and Continue",
                                               self.save_and_continue)
        saveandquit_button = widget.Button("Save and Quit", self.save_and_quit)
        quitwithoutsaving_button = widget.Button("Quit without saving",
                                                 self.quit_without_saving)
        self.header_content = ["Save configuration before quitting?", blank,
                               saveandcontinue_button, saveandquit_button,
                               quitwithoutsaving_button]

        self.fields = []
        self.defaults = dict()

    def save_and_continue(self, args):
        self.save()

    def save_and_quit(self, args):
        if self.save():
            self.parent.refreshScreen()
            time.sleep(1.5)

            if utils.is_post_deployment() and \
                    self.parent.feature_groups_changed:
                # Apply changes to the Nailgun
                cmd = ["puppet", "apply", "--debug", "--verbose", "--logdest",
                       consts.PUPPET_LOGFILE,
                       "/etc/puppet/modules/fuel/examples/nailgun.pp"]
                err_code, _, errout = utils.execute(cmd)
                if err_code != 0:
                    log.error("Puppet apply failed with an error: "
                              "\"{0}\"".format(errout))
                    self.parent.footer.set_text("Puppet apply failed. "
                                                "Check logs for more details.")
                    return False
                self.parent.footer.set_text("Changes successfully applied.")

            self.parent.exit_program(None)

    def save(self):
        results, modulename = self.parent.global_save()
        if results:
            self.parent.footer.set_text("All changes saved successfully!")
            return True
        else:
            return False

    def quit_without_saving(self, args):
        self.parent.exit_program(None)

    def refresh(self):
        pass

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults, buttons_visible=False)
