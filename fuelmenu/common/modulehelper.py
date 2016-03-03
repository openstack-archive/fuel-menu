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


import collections
import logging
import netifaces
import socket
import struct

import six
import urwid
import urwid.raw_display
import urwid.web_display

from fuelmenu.common import dialog
from fuelmenu.common import network
import fuelmenu.common.urwidwrapper as widget
from fuelmenu.common import utils
from fuelmenu import settings

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
    def get_setting(cls, settings, key):
        """Retrieving setting by key.

        :param settings: settings from config file
        :param key: setting name (format: '[{section_name}/]{setting_name}')
        :returns: setting value
        :raises: KeyError if there are no setting with such key
        """
        part1, _, part2 = key.partition('/')
        if part2:
            value = settings[part1][part2]
        else:
            value = settings[part1]
        return value

    @classmethod
    def set_setting(cls, settings, key, value, default_settings=None):
        """Sets new setting by key.

        :param settings: settings from config file
        :param key: setting name (format: '[{section_name}/]{setting_name}')
        :param value: new value
        :param default_settings: settings, which will be used to find missed
               section
        """
        part1, _, part2 = key.partition('/')
        if part2:
            if part1 not in settings:
                settings.setdefault(part1, collections.OrderedDict())
                if default_settings and part1 in default_settings:
                    settings[part1].update(default_settings[part1])
            settings[part1][part2] = value
        else:
            settings[part1] = value

    @classmethod
    def load(cls, modobj, ignoredparams=None):
        """Returns settings found in settings files that are found in class

        :param cls: ModuleHelper object
        :param modobj: object from calling class
        :param ignoredparams: list of parameters to skip lookup from settings
        :returns: OrderedDict of settings for calling class
        """

        # Read in yaml
        defaultsettings = settings.Settings().read(
            modobj.parent.defaultsettingsfile)
        usersettings = settings.Settings().read(modobj.parent.settingsfile)
        oldsettings = utils.dict_merge(defaultsettings, usersettings)

        types_to_skip = (WidgetType.BUTTON, WidgetType.LABEL)
        for setting, setting_def in six.iteritems(modobj.defaults):
            if (setting_def.get('type') in types_to_skip or
               ignoredparams and setting in ignoredparams):
                    continue
            try:
                setting_def["value"] = cls.get_setting(oldsettings, setting)
            except KeyError:
                log.warning("Failed to load %s value from settings", setting)
        return oldsettings

    @classmethod
    def save(cls, modobj, responses):
        newsettings = collections.OrderedDict()
        for setting in responses:
            cls.set_setting(newsettings,
                            setting,
                            responses[setting],
                            modobj.oldsettings)
        return newsettings

    @classmethod
    def cancel(cls, modobj, *args):
        for index, fieldname in enumerate(modobj.fields):
            if fieldname != BLANK_KEY and "label" not in fieldname:
                try:
                    modobj.edits[index].set_edit_text(
                        modobj.defaults[fieldname][
                            'value'])
                except AttributeError:
                    log.warning("Field %s unable to reset text", fieldname)

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
            for key in sorted(scheme):
                data = dict(scheme[key])
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
            caption = default_data.get("label", "")
            default = default_data.get("value", "")
            tooltip = default_data.get("tooltip", "")
            return widget.TextField(key, caption, width=23,
                                    default_value=default,
                                    tooltip=tooltip, toolbar=toolbar,
                                    ispassword=ispassword)

    @staticmethod
    def _get_header_content(header_text):
        def _convert(text):
            if isinstance(text, six.string_types):
                return urwid.Text(text)
            return text

        return [_convert(text) for text in header_text]

    @classmethod
    def setup_widgets(cls, toolbar, fields, defaults):
        return [cls._create_widget(key, defaults.get(key, {}), toolbar)
                for key in fields]

    @staticmethod
    def _get_check_column(modobj, show_all_buttons):
        # Button to check
        button_check = widget.Button("Check", modobj.check)

        if modobj.parent.globalsave and show_all_buttons is False:
            return widget.Columns([button_check])

        # Button to revert to previously saved settings
        button_cancel = widget.Button("Cancel", modobj.cancel)
        # Button to apply (and check again)
        button_apply = widget.Button("Apply", modobj.apply)

        return widget.Columns([
            button_check, button_cancel,
            button_apply, ('weight', 2, blank)])

    @classmethod
    def screenUI(cls, modobj, header_text, fields, defaults,
                 show_all_buttons=False, buttons_visible=True):

        log.debug("Preparing screen UI for %s", modobj.name)

        # Define text labels, text fields, and buttons first
        listbox_content = cls._get_header_content(header_text)

        edits = cls.setup_widgets(modobj.parent.footer, fields, defaults)

        listbox_content.append(blank)
        listbox_content.extend(edits)
        listbox_content.append(blank)

        # Wrap buttons into Columns so it doesn't expand and look ugly
        if buttons_visible:
            listbox_content.append(cls._get_check_column(
                modobj, show_all_buttons))

        # Add everything into a ListBox and return it
        listwalker = widget.TabbedListWalker(listbox_content)
        screen = urwid.ListBox(listwalker)
        modobj.edits = edits
        modobj.walker = listwalker
        modobj.listbox_content = listbox_content
        return screen

    @staticmethod
    def _get_iface_info(iface, address_family):
        return netifaces.ifaddresses(iface)[address_family][0]

    @staticmethod
    def _get_iface_settings(iface):
        try:
            settings = ModuleHelper._get_iface_info(iface, netifaces.AF_INET)
            settings["onboot"] = "Yes"
        except (TypeError, KeyError):
            settings = {"addr": "", "netmask": "", "onboot": "no"}

        settings['mac'] = ModuleHelper._get_iface_info(
            iface, netifaces.AF_LINK)['addr']
        return settings

    @staticmethod
    def _get_link_state(iface, addr):
        try:
            with open("/sys/class/net/{0}/operstate".format(iface)) as f:
                arr = f.readlines()
                return arr[0].strip()
        except IOError:
            log.warning("Unable to read operstate file for %s", iface)
            # if interface has an IP then it is up
            return "unknown" if addr == "" else "up"

    @staticmethod
    def _get_boot_proto(iface, dhcp_exists):
        proto = "none"
        try:
            fname = "/etc/sysconfig/network-scripts/ifcfg-{0}".format(iface)
            with open(fname) as fh:
                for line in fh:
                    if line.startswith("BOOTPROTO="):
                        proto = line.split('=', 1)[1].strip()
        except Exception:
            pass
        return "dhcp" if proto == "none" and dhcp_exists else proto

    @classmethod
    def _get_net(cls, iface, dhcp_exists):
        net = cls._get_iface_settings(iface)
        net['link'] = cls._get_link_state(iface, net["addr"])
        net['bootproto'] = cls._get_boot_proto(iface, dhcp_exists)
        return net

    @classmethod
    def getNetwork(cls, modobj):
        """Returns addr, broadcast, netmask for each network interface."""
        for iface in network.get_physical_ifaces():
            dhcp_exists = modobj.getDHCP(iface)
            modobj.netsettings.update(
                {iface: cls._get_net(iface, dhcp_exists)}
            )
        modobj.gateway = modobj.get_default_gateway_linux()

    @classmethod
    def getDHCP(cls, iface):
        """Returns True if the interface has a dhclient process running."""
        command = ["pgrep", "-f", "dhclient.*{0}".format(iface)]
        code, output, errout = utils.execute(command)
        return code == 0

    @classmethod
    def get_default_gateway_linux(cls):
        """Read the default gateway directly from /proc."""
        with open("/proc/net/route") as fh:
            for line in fh:
                fields = line.strip().split()
                if fields[1] != '00000000' or not int(fields[3], 16) & 2:
                    continue
                return socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))
