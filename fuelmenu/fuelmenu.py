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
from fuelmenu.common import errors
from fuelmenu.common import network
from fuelmenu.common import timeout
from fuelmenu.common import urwidwrapper as widget
from fuelmenu.common import utils
from fuelmenu import consts
from fuelmenu.settings import Settings
import logging
import operator
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


class Loader(object):

    def __init__(self, parent):
        self.modlist = []
        self.choices = []
        self.child = None
        self.children = []
        self.childpage = None
        self.parent = parent

    def load_modules(self, module_dir):
        if module_dir not in sys.path:
            sys.path.append(module_dir)

        modules = [os.path.splitext(f)[0] for f in os.listdir(module_dir)
                   if f.endswith('.py')]

        for module in modules:
            log.info('loading module %s' % module)
            try:
                imported = __import__(module)
                pass
            except ImportError as e:
                log.error('module could not be imported: %s' % e)
                continue

            clsobj = getattr(imported, module, None)
            modobj = clsobj(self.parent)

            # add the module to the list
            self.modlist.append(modobj)
        # sort modules
        self.modlist.sort(key=operator.attrgetter('priority'))
        for module in self.modlist:
            self.choices.append(module.name)
        return (self.modlist, self.choices)


class FuelSetup(object):

    def __init__(self):
        self.footer = None
        self.frame = None
        self.screen = None
        self.defaultsettingsfile = os.path.join(os.path.dirname(__file__),
                                                "settings.yaml")
        self.settingsfile = consts.SETTINGS_FILE
        self.managediface = network.get_physical_ifaces()[0]
        # Set to true to move all settings to end
        self.globalsave = True
        self.version = utils.get_fuel_version()
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
                    urwid.AttrMap(self.menubox, 'bright'),
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
        size = self.screen.get_cols_rows()
        self.screen.draw_screen(size, self.frame.render(size))

    def refreshChildScreen(self, name):
        child = self.children[int(self.choices.index(name))]

        child.screen = child.screenUI()

        self.draw_child_screen(child.screen)

    def main(self):
        text_header = (u"Fuel %s setup "
                       u"Use Up/Down/Left/Right to navigate.  F8 exits. "
                       u"Remember to save your changes."
                       % self.version)
        text_footer = (u"Status messages go here.")

        # Top and bottom lines of frame
        self.header = urwid.AttrWrap(urwid.Text(text_header), 'header')
        self.footer = urwid.AttrWrap(urwid.Text(text_footer), 'footer')

        # Prepare submodules
        loader = Loader(self)
        moduledir = "%s/modules" % (os.path.dirname(__file__))
        self.children, self.choices = loader.load_modules(module_dir=moduledir)

        if len(self.children) == 0:
            import sys
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
                    urwid.AttrMap(self.menubox, 'bright'),
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
                ('reverse', 'light gray', 'black'),
                ('header', 'white', 'dark red', 'bold'),
                ('important', 'dark blue', 'light gray',
                    ('standout', 'underline')),
                ('editfc', 'white', 'dark blue', 'bold'),
                ('editbx', 'light gray', 'dark blue'),
                ('editcp', 'black', 'light gray', 'standout'),
                ('bright', 'dark gray', 'light gray', ('bold', 'standout')),
                ('buttn', 'black', 'dark cyan'),
                ('buttnf', 'white', 'dark blue', 'bold'),
                ('light gray', 'white', 'light gray', 'bold'),
                ('red', 'dark red', 'light gray', 'bold'),
                ('black', 'black', 'black', 'bold'),
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
        self.mainloop.run()

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
                    module.apply(None)
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
                    if module.apply(None):
                        log.info("Saving module: %s" % modulename)
                    else:
                        return False, modulename
                except AttributeError as e:
                    log.debug("Module %s does not have save function: %s"
                              % (modulename, e))
        return True, None


def setup():
    urwid.web_display.set_preferences("Fuel Setup")
    # try to handle short web requests quickly
    if urwid.web_display.handle_short_request():
        return
    FuelSetup()


def save_only(iface, settingsfile=consts.SETTINGS_FILE):
    from fuelmenu.common import pwgen
    import netifaces

    if utils.is_post_deployment():
        print("Not updating settings when invoked during post-deployment.\n"
              "Run fuelmenu manually to make changes.")
        sys.exit(0)

    # Calculate and set Static/DHCP pool fields
    # Max IPs = net size - 2 (master node + bcast)
    try:
        ip = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
        netmask = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['netmask']
        mac = netifaces.ifaddresses(iface)[netifaces.AF_LINK][0]['addr']
    except Exception:
        print("Interface %s is missing either IP address or netmask"
              % (iface))
        sys.exit(1)
    net_ip_list = network.getNetwork(ip, netmask)
    try:
        dhcp_pool = net_ip_list[1:]
        dynamic_start = str(dhcp_pool[0])
        dynamic_end = str(dhcp_pool[-1])
    except Exception:
        print("Unable to define DHCP pools")
        sys.exit(1)
    try:
        hostname, sep, domain = os.uname()[1].partition('.')
    except Exception:
        print("Unable to calculate hostname and domain")
        sys.exit(1)
    try:
        dhcptimeout = 5
        dhcp_server_data = network.search_external_dhcp(iface, dhcptimeout)
    except errors.NetworkException:
        log.error("DHCP scan failed")
        dhcp_server_data = []

    num_dhcp = len(dhcp_server_data)
    if num_dhcp == 0:
        log.debug("No DHCP servers found")
    else:
        # Problem exists, but permit user to continue
        log.error("%s foreign DHCP server(s) found: %s" %
                  (num_dhcp, dhcp_server_data))
        print("ERROR: %s foreign DHCP server(s) found: %s" %
              (num_dhcp, dhcp_server_data))
    if network.duplicateIPExists(ip, iface):
        log.error("Duplicate host found with IP {0}".format(ip))
        print("ERROR: Duplicate host found with IP {0}".format(ip))

    default_settings_file = os.path.join(os.path.dirname(__file__),
                                         "settings.yaml")
    mos_version = utils.get_fuel_version()
    settings = Settings().read(
        default_settings_file,
        template_kwargs={"mos_version": mos_version})
    settings.update(Settings().read(
        settingsfile,
        template_kwargs={"mos_version": mos_version}))
    settings_upd = \
        {
            "ADMIN_NETWORK/interface": iface,
            "ADMIN_NETWORK/ipaddress": ip,
            "ADMIN_NETWORK/netmask": netmask,
            "ADMIN_NETWORK/mac": mac,
            "ADMIN_NETWORK/dhcp_pool_start": dynamic_start,
            "ADMIN_NETWORK/dhcp_pool_end": dynamic_end,
            "ADMIN_NETWORK/dhcp_gateway": ip,
            "HOSTNAME": hostname,
            "DNS_DOMAIN": domain,
            "DNS_SEARCH": domain,
            "astute/user": "naily",
            "astute/password": pwgen.password(),
            "cobbler/user": "cobbler",
            "cobbler/password": pwgen.password(),
            "keystone/admin_token": pwgen.password(),
            "keystone/ostf_user": "ostf",
            "keystone/ostf_password": pwgen.password(),
            "keystone/nailgun_user": "nailgun",
            "keystone/nailgun_password": pwgen.password(),
            "keystone/monitord_user": "monitord",
            "keystone/monitord_password": pwgen.password(),
            "mcollective/user": "mcollective",
            "mcollective/password": pwgen.password(),
            "postgres/keystone_dbname": "keystone",
            "postgres/keystone_user": "keystone",
            "postgres/keystone_password": pwgen.password(),
            "postgres/nailgun_dbname": "nailgun",
            "postgres/nailgun_user": "nailgun",
            "postgres/nailgun_password": pwgen.password(),
            "postgres/ostf_dbname": "ostf",
            "postgres/ostf_user": "ostf",
            "postgres/ostf_password": pwgen.password(),
            "FUEL_ACCESS/user": "admin",
            "FUEL_ACCESS/password": "admin",
        }
    for setting in settings_upd.keys():
        if "/" in setting:
            part1, part2 = setting.split("/")
            settings.setdefault(part1, {})
            # Keep old values for passwords if already set
            if "password" in setting:
                settings[part1].setdefault(part2, settings_upd[setting])
            else:
                settings[part1][part2] = settings_upd[setting]
        else:
            if "password" in setting:
                settings.setdefault(setting, settings_upd[setting])
            else:
                settings[setting] = settings_upd[setting]

    # Write astute.yaml
    Settings().write(settings, defaultsfile=default_settings_file,
                     outfn=settingsfile)


def main(*args, **kwargs):
    if urwid.VERSION < (1, 1, 0):
        print("This program requires urwid 1.1.0 or greater.")

    try:
        default_iface = network.get_physical_ifaces()[0]
    except IndexError:
        print("Unable to detect any network interfaces. Could not start")
        sys.exit(1)

    parser = OptionParser()
    parser.add_option("-s", "--save-only", dest="save_only",
                      action="store_true",
                      help="Save default values and exit.")

    parser.add_option("-i", "--iface", dest="iface", metavar="IFACE",
                      default=default_iface, help="Set IFACE as primary.")

    options, args = parser.parse_args()

    if not network.is_interface_has_ip(options.iface):
        print("Selected interface '{0}' has no assigned IP. "
              "Could not start.".format(options.iface))
        sys.exit(1)

    if options.save_only:
        save_only(options.iface)
    else:
        setup()

if '__main__' == __name__ or urwid.web_display.is_web_request():
    setup()
