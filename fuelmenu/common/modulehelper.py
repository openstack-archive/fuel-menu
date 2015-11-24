# -*- coding: utf-8 -*-

# Copyright 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from fuelmenu.common import dialog
from fuelmenu.common import network
import fuelmenu.common.urwidwrapper as widget
from fuelmenu.common.utils import dict_merge
from fuelmenu.settings import Settings
import logging
import netifaces
import re
import socket
import struct
import subprocess
import urwid
import urwid.raw_display
import urwid.web_display

log = logging.getLogger('fuelmenu.modulehelper')

# magic. calculated as 80 (standard terminal width) - 20 (menu size)
MAX_WIDTH = 60

BLANK_KEY = "blank"

blank = urwid.Divider()


class WidgetType(object):
    TEXT_FIELD = 1  # default value. may be skipped
    LABEL = 2
    RADIO = 3
    CHECKBOX = 4
    LIST = 5
    BUTTON = 6


class ModuleHelper(object):
    @classmethod
    def load(cls, modobj, ignoredparams=None):
        """Returns settings found in settings files that are found in class

        :param cls: ModuleHelper object
        :param modobj: object from calling class
        :param ignoredparams: list of parameters to skip lookup from settings
        :returns: OrderedDict of settings for calling class
        """

        # Read in yaml
        defaultsettings = Settings().read(modobj.parent.defaultsettingsfile)
        usersettings = Settings().read(modobj.parent.settingsfile)
        oldsettings = dict_merge(defaultsettings, usersettings)
        for setting in modobj.defaults.keys():
            if "label" in setting:
                continue
            elif ignoredparams and setting in ignoredparams:
                continue
            elif "/" in setting:
                part1, part2 = setting.split("/")
                modobj.defaults[setting]["value"] = oldsettings[part1][part2]
            else:
                modobj.defaults[setting]["value"] = oldsettings[setting]
        return oldsettings

    @classmethod
    def save(cls, modobj, responses):
        newsettings = dict()
        for setting in responses.keys():
            if "/" in setting:
                part1, part2 = setting.split("/")
                if part1 not in newsettings:
                    # We may not touch all settings, so copy oldsettings first
                    newsettings[part1] = modobj.oldsettings[part1]
                newsettings[part1][part2] = responses[setting]
            else:
                newsettings[setting] = responses[setting]
        return newsettings

    @classmethod
    def cancel(cls, modobj, button=None):
        for index, fieldname in enumerate(modobj.fields):
            if fieldname != BLANK_KEY and "label" not in fieldname:
                try:
                    modobj.edits[index].set_edit_text(
                        modobj.defaults[fieldname][
                            'value'])
                except AttributeError:
                    log.warning("Field %s unable to reset text" % fieldname)

    @classmethod
    def display_dialog(cls, modobj, error_msg, title):
        body = widget.TextLabel(error_msg)
        dialog.display_dialog(modobj, body, title)

    @classmethod
    def display_failed_check_dialog(cls, modobj, errors):
        error_msg = "Errors:\n  {0}".format("\n  ".join(errors))
        title = "Check failed in module {0}".format(modobj.name)
        cls.display_dialog(modobj, error_msg, title)

    @classmethod
    def _create_checkbox_widget(cls, default_data):
        callback = default_data.get("callback", None)
        enabled = bool(default_data.get("value"))
        return widget.CheckBox(
            default_data["label"],
            state=enabled,
            callback=callback
        )

    @classmethod
    def _create_radiobutton_widget(cls, default_data):
        label = widget.TextLabel(default_data["label"])
        callback = default_data.get("callback", None)

        choices_list = default_data.get("choices")
        if not choices_list:
            choices_list = ["Yes", "No"]
        choices = widget.ChoicesGroup(choices_list,
                                      default_value=choices_list[0],
                                      fn=callback)
        columns = widget.Columns([('weight', 2, label),
                                  ('weight', 3, choices)])
        # Attach choices rb_group so we can use it later
        columns.rb_group = choices.rb_group
        return columns

    @classmethod
    def _create_button_widget(cls, default_data):
        button = widget.Button(default_data.get('label', ''),
                               default_data.get('callback'))
        return widget.Columns([button])

    @classmethod
    def _create_list_widget(cls, default_data, toolbar):

        label = default_data.get("label")

        objects = []
        box_size = 0

        if label:
            label = urwid.Text(label)
            objects.append(label)
            box_size += label.rows((MAX_WIDTH,))

        elements = default_data.get("value", [])
        scheme = default_data.get("value_scheme", {})

        for e in elements:
            object_size = 0
            object_fields = []
            for key in sorted(scheme.keys()):
                data = scheme[key]
                data["value"] = e.get(key, "")
                new_widget = cls._create_widget(key, data, toolbar)
                object_fields.append(new_widget)
                object_size += new_widget.rows((MAX_WIDTH,))
            object_fields.append(blank)
            object_size += blank.rows((MAX_WIDTH,))

            objects.append(
                urwid.BoxAdapter(
                    widget.WalkerStoredListBox(
                        widget.SimpleListWalker(object_fields)),
                    object_size))
            box_size += object_size

        return urwid.BoxAdapter(
            widget.WalkerStoredListBox(widget.SimpleListWalker(objects)),
            box_size)

    @classmethod
    def _create_widget(cls, key, default_data, toolbar):
        if key == BLANK_KEY:
            return blank

        field_type = default_data.get('type', WidgetType.TEXT_FIELD)

        if field_type == WidgetType.CHECKBOX:
            return cls._create_checkbox_widget(default_data)

        if field_type == WidgetType.RADIO:
            return cls._create_radiobutton_widget(default_data)

        if field_type == WidgetType.LABEL:
            return widget.TextLabel(default_data["label"])

        if field_type == WidgetType.LIST:
            return cls._create_list_widget(default_data, toolbar)

        if field_type == WidgetType.BUTTON:
            return cls._create_button_widget(default_data)

        if field_type == WidgetType.TEXT_FIELD:
            ispassword = "PASSWORD" in key.upper()
            caption = default_data["label"]
            default = default_data["value"]
            tooltip = default_data["tooltip"]
            return widget.TextField(key, caption, width=23,
                                    default_value=default,
                                    tooltip=tooltip, toolbar=toolbar,
                                    ispassword=ispassword)

    @classmethod
    def screenUI(cls, modobj, headertext, fields, defaults,
                 showallbuttons=False, buttons_visible=True):

        log.debug("Preparing screen UI for %s" % modobj.name)
        # Define text labels, text fields, and buttons first
        header_content = []
        for text in headertext:
            if isinstance(text, str):
                header_content.append(urwid.Text(text))
            else:
                header_content.append(text)

        edits = []
        toolbar = modobj.parent.footer
        for key in fields:
            edits.append(cls._create_widget(key,
                                            defaults.get(key, {}),
                                            toolbar))

        listbox_content = []
        listbox_content.extend(header_content)
        listbox_content.append(blank)
        listbox_content.extend(edits)
        listbox_content.append(blank)

        # Wrap buttons into Columns so it doesn't expand and look ugly
        if buttons_visible:
            # Button to check
            button_check = widget.Button("Check", modobj.check)
            # Button to revert to previously saved settings
            button_cancel = widget.Button("Cancel", modobj.cancel)
            # Button to apply (and check again)
            button_apply = widget.Button("Apply", modobj.apply)

            if modobj.parent.globalsave and showallbuttons is False:
                check_col = widget.Columns([button_check])
            else:
                check_col = widget.Columns([button_check, button_cancel,
                                            button_apply,
                                            ('weight', 2, blank)])
            listbox_content.append(check_col)

        # Add everything into a ListBox and return it
        listwalker = widget.TabbedListWalker(listbox_content)
        screen = urwid.ListBox(listwalker)
        modobj.edits = edits
        modobj.walker = listwalker
        modobj.listbox_content = listbox_content
        return screen

    @classmethod
    def getNetwork(cls, modobj):
        """Returns addr, broadcast, netmask for each network interface."""
        for iface in network.get_physical_ifaces():
            try:
                modobj.netsettings.update({iface: netifaces.ifaddresses(iface)[
                    netifaces.AF_INET][0]})
                modobj.netsettings[iface]["onboot"] = "Yes"
            except (TypeError, KeyError):
                modobj.netsettings.update({iface: {"addr": "", "netmask": "",
                                                   "onboot": "no"}})
            modobj.netsettings[iface]['mac'] = netifaces.ifaddresses(iface)[
                netifaces.AF_LINK][0]['addr']

            # Set link state
            try:
                with open("/sys/class/net/%s/operstate" % iface) as f:
                    content = f.readlines()
                    modobj.netsettings[iface]["link"] = content[0].strip()
            except IOError:
                log.warning("Unable to read operstate file for %s" % iface)
                modobj.netsettings[iface]["link"] = "unknown"
            # Change unknown link state to up if interface has an IP
            if modobj.netsettings[iface]["link"] == "unknown":
                if modobj.netsettings[iface]["addr"] != "":
                    modobj.netsettings[iface]["link"] = "up"

            # Read bootproto from /etc/sysconfig/network-scripts/ifcfg-DEV
            modobj.netsettings[iface]['bootproto'] = "none"
            try:
                with open("/etc/sysconfig/network-scripts/ifcfg-%s" % iface) \
                        as fh:
                    for line in fh:
                        if re.match("^BOOTPROTO=", line):
                            modobj.netsettings[iface]['bootproto'] = \
                                line.split('=')[1].strip()
                            break
            except Exception:
                # Check for dhclient process running for this interface
                if modobj.getDHCP(iface):
                    modobj.netsettings[iface]['bootproto'] = "dhcp"
                else:
                    modobj.netsettings[iface]['bootproto'] = "none"
        modobj.gateway = modobj.get_default_gateway_linux()

    @classmethod
    def getDHCP(cls, iface):
        """Returns True if the interface has a dhclient process running."""
        noout = open('/dev/null', 'w')
        dhclient_running = subprocess.call(["pgrep", "-f", "dhclient.*%s" %
                                            iface], stdout=noout,
                                           stderr=noout)
        return dhclient_running == 0

    @classmethod
    def get_default_gateway_linux(cls):
        """Read the default gateway directly from /proc."""
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    continue
                return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
