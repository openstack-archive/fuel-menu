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

from __future__ import absolute_import

from fuelmenu.common import dialog
from fuelmenu.common import network
from fuelmenu.common import timeout
from fuelmenu.common import urwidwrapper as widget
from fuelmenu.common import utils
from fuelmenu import consts
from fuelmenu import modules
from fuelmenu import settings as settings_module


import logging
from optparse import OptionParser
import os
import signal
import sys
import urwid
import urwid.raw_display
import urwid.web_display

# set up logging
logging.basicConfig(filename=consts.LOGFILE,
                    format="%(asctime)s %(levelname)s %(message)s",
                    level=logging.DEBUG)
log = logging.getLogger('fuelmenu.loader')


class FuelSetup(object):

    def __init__(self, save_only=False, managed_iface=None):
        self.save_only = save_only
        self.footer = None
        self.frame = None
        self.screen = None
        self.dns_might_have_changed = False
        self.managediface = managed_iface or network.get_physical_ifaces()[0]
        # Set to true to move all settings to end
        self.globalsave = True
        # Tasks to be executed on Apply
        self.apply_tasks = set()
        self.version = utils.get_fuel_version()

        # settings load
        self.settings = settings_module.Settings()

        self.settings.load(
            os.path.join(os.path.dirname(__file__), "settings.yaml"),
            template_kwargs={"mos_version": self.version})

        self.settings.load(
            consts.SETTINGS_FILE,
            template_kwargs={"mos_version": self.version})

        self.main()
        self.choices = []

    def menu(self, title, choices):
        body = [urwid.Text(title), urwid.Divider()]
        for c in choices:
            button = urwid.Button(c)
            urwid.connect_signal(button, 'click', self.menu_chosen, c)
            body.append(urwid.AttrMap(button, None, focus_map='reversed'))
        return urwid.ListBox(urwid.SimpleListWalker(body))
        # return urwid.ListBox(urwid.SimpleFocusListWalker(body))

    def menu_chosen(self, button, choice):
        size = self.screen.get_cols_rows()
        self.screen.draw_screen(size, self.frame.render(size))
        for item in self.menuitems.body.contents:
            try:
                if isinstance(item.base_widget, urwid.Button):
                    if item.base_widget.get_label() == choice:
                        item.set_attr_map({None: 'header'})
                    else:
                        item.set_attr_map({None: None})
            except AttributeError:
                log.exception("Unable to set menu item %s" % item)
        self.setChildScreen(name=choice)

    def draw_child_screen(self, child_screen, focus_on_child=False):
        self.childpage = child_screen
        self.childfill = urwid.Filler(self.childpage, 'top', 40)
        self.childbox = urwid.BoxAdapter(self.childfill, 40)
        self.cols = urwid.Columns(
            [
                ('fixed', 20, urwid.Pile([
                    urwid.AttrMap(self.menubox, 'body'),
                    urwid.Divider(" ")])),
                ('weight', 3, urwid.Pile([
                    urwid.Divider(" "),
                    self.childbox,
                    urwid.Divider(" ")]))
            ], 1)
        if focus_on_child:
            self.cols.focus_position = 1  # focus on childbox
        self.child.refresh()
        self.listwalker[:] = [self.cols]

    def setChildScreen(self, name=None):
        if name is None:
            self.child = self.children[0]
        else:
            self.child = self.children[int(self.choices.index(name))]
        if not self.child.screen:
            self.child.screen = self.child.screenUI()
        self.draw_child_screen(self.child.screen)

    def refreshScreen(self):
        if self.save_only:
            return
        size = self.screen.get_cols_rows()
        self.screen.draw_screen(size, self.frame.render(size))

    def main(self):
        text_header = (u"Fuel %s setup "
                       u"Use Up/Down/Left/Right to navigate.  F8 exits. "
                       u"Remember to save your changes."
                       % self.version)
        text_footer = (u"Status messages go here.")

        # Top and bottom lines of frame
        self.header = urwid.AttrWrap(urwid.Text(text_header), 'header')
        self.footer = urwid.AttrWrap(urwid.Text(text_footer), 'footer')

        self.children = []
        for clsobj in modules.__all__:
            modobj = clsobj(self)
            self.children.append(modobj)

        self.choices = [m.name for m in self.children]

        if len(self.children) == 0:
            sys.exit(1)

        # Build list of choices excluding visible
        self.visiblechoices = []
        for child, choice in zip(self.children, self.choices):
            if child.visible:
                self.visiblechoices.append(choice)

        self.menuitems = self.menu(u'Menu', self.visiblechoices)
        menufill = urwid.Filler(self.menuitems, 'top', 40)
        self.menubox = urwid.BoxAdapter(menufill, 40)

        self.child = self.children[0]
        self.childpage = self.child.screenUI()
        self.childfill = urwid.Filler(self.childpage, 'top', 22)
        self.childbox = urwid.BoxAdapter(self.childfill, 22)
        self.cols = urwid.Columns(
            [
                ('fixed', 20, urwid.Pile([
                    urwid.AttrMap(self.menubox, 'body'),
                    urwid.Divider(" ")])),
                ('weight', 3, urwid.Pile([
                    urwid.Divider(" "),
                    self.childbox,
                    urwid.Divider(" ")]))
            ], 1)
        self.listwalker = urwid.SimpleListWalker([self.cols])
        # self.listwalker = urwid.TreeWalker([self.cols])
        self.listbox = urwid.ListBox(self.listwalker)
        # listbox = urwid.ListBox(urwid.SimpleListWalker(listbox_content))

        self.frame = urwid.Frame(urwid.AttrWrap(self.listbox, 'body'),
                                 header=self.header, footer=self.footer)

        palette = \
            [
                ('body', 'black', 'light gray', 'standout'),
                ('header', 'light red', 'light gray', 'bold'),
                ('footer', 'light red', 'light gray', 'bold'),
                ('menu', 'black', 'light gray', 'bold'),
                ('menuf', 'white', 'dark red', 'bold'),
                ('important', 'light red', 'light gray',
                    ('standout', 'underline')),
                ('editlbl', 'black', 'light gray'),
                ('editfc', 'light gray', 'black', 'bold'),
                ('editbx', 'light gray', 'dark gray'),
                ('buttn', 'white', 'dark green', 'bold'),
                ('buttnf', 'light gray', 'dark green', 'bold'),
            ]

        # use appropriate Screen class
        if urwid.web_display.is_web_request():
            self.screen = urwid.web_display.Screen()
        else:
            self.screen = urwid.raw_display.Screen()

        def unhandled(key):
            if key == 'f8':
                raise urwid.ExitMainLoop()
            if key == 'shift tab':
                self.child.walker.tab_prev()
            if key == 'tab':
                self.child.walker.tab_next()

        self.mainloop = urwid.MainLoop(self.frame, palette, self.screen,
                                       unhandled_input=unhandled)
        # Initialize each module completely before any events are handled
        for child in reversed(self.children):
            self.setChildScreen(name=child.name)

        signal.signal(signal.SIGUSR1, self.handle_sigusr1)

        dialog.display_dialog(
            self.child,
            widget.TextLabel("It is highly recommended to change default "
                             "admin password."),
            "WARNING!")
        if not self.save_only:
            self.mainloop.run()
        else:
            self._save_only()

    def exit_program(self, button):
        # Fix /etc/hosts before quitting
        dnsobj = self.children[int(self.choices.index("DNS & Hostname"))]
        dnsobj.fixEtcHosts()

        raise urwid.ExitMainLoop()

    def handle_sigusr1(self, signum, stack):
        log.info("Received signal: %s" % signum)
        try:
            savetimeout = 60
            success, modulename = timeout.run_with_timeout(
                self.global_save, timeout=savetimeout)
            if success:
                log.info("Save successful!")
            else:
                log.error("Save failed on module %s" % modulename)

        except timeout.TimeoutError:
            log.exception("Save on signal timed out. Save not complete.")
        except KeyboardInterrupt:
            log.exception("Save was interrupted by the user.")
        except Exception:
            log.exception("Save failed for unknown reason:")
        self.exit_program(None)

    def global_save(self):
        # Runs save function for every module
        for module, modulename in zip(self.children, self.choices):
            # Run invisible modules. They may not have screen methods
            if not module.visible:
                try:
                    self._save_module(module)
                except Exception as e:
                    log.error("Unable to save module %s: %s" % (modulename, e))
                    continue
            else:
                try:
                    log.info("Checking and applying module: %s"
                             % modulename)
                    self.footer.set_text("Checking and applying module: %s"
                                         % modulename)
                    self.refreshScreen()
                    module.refresh()
                    if self._save_module(module):
                        log.info("Saving module: %s" % modulename)
                    else:
                        return False, modulename
                except AttributeError as e:
                    log.debug("Module %s does not have save function: %s"
                              % (modulename, e))

        self.settings.write(outfn=consts.SETTINGS_FILE)

        # Runs tasks for every module, stop on error
        for apply_task in self.apply_tasks:
            if not apply_task():
                return False, None

        return True, None

    def _save_module(self, module):
        if self.save_only:
            if hasattr(module, 'check') and hasattr(module, 'save'):
                resp = module.check(None)
                module.save(resp)
            return True

        return module.apply(None)

    def _save_only(self):
        if utils.is_post_deployment():
            print(
                "Not updating settings when invoked during post-deployment"
                ".\nRun fuelmenu manually to make changes."
            )
            sys.exit(0)

        success, module_name = self.global_save()
        if not success:
            msg = ("Problems with module '{}'."
                   " Settings have not been saved.".format(module_name))
            log.error(msg)
            sys.stderr.write(msg + '\n')
            sys.exit(1)

    def reload_modules(self):
        for child in self.children:
            if hasattr(child, 'load') and callable(child.load):
                child.load()
                child.screen = child.screenUI()
                self.draw_child_screen(child.screen)

        self.refreshScreen()


def setup(**kwargs):
    urwid.web_display.set_preferences("Fuel Setup")
    # try to handle short web requests quickly
    if urwid.web_display.handle_short_request():
        return
    FuelSetup(**kwargs)


def main(*args, **kwargs):
    if urwid.VERSION < (1, 1, 0):
        print("This program requires urwid 1.1.0 or greater.")

    network_interfaces = network.get_physical_ifaces()
    if not network_interfaces:
        print("Unable to detect any network interfaces. Could not start")
        sys.exit(1)

    default_iface = network_interfaces[0]

    for nic in network_interfaces:
        if network.is_interface_has_ip(nic):
            default_iface = nic
            break

    parser = OptionParser()
    parser.add_option("-s", "--save-only", dest="save_only",
                      action="store_true",
                      help="Save default values and exit.")

    parser.add_option("-i", "--iface", dest="iface", metavar="IFACE",
                      default=default_iface, help="Set IFACE as primary.")

    parser.add_option("-l", "--lock-file",
                      default=consts.DEFAULT_LOCK_FILE,
                      help="Path to the process lock file. If unspecified, "
                           "the default {} is used."
                           .format(consts.DEFAULT_LOCK_FILE))

    options, args = parser.parse_args()

    if not utils.lock_running(options.lock_file):
        sys.exit(1)

    if not network.is_interface_has_ip(options.iface):
        print("Selected interface '{0}' has no assigned IP. "
              "Could not start.".format(options.iface))
        sys.exit(1)

    if options.save_only:
        setup(save_only=True,
              managed_iface=options.iface)
    else:
        setup()

if '__main__' == __name__ or urwid.web_display.is_web_request():
    setup()
