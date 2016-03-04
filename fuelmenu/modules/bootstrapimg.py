#!/usr/bin/env python
# Copyright 2015 Mirantis, Inc.
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
import copy
import logging
import re
import requests
import types

import six
import urwid
import urwid.raw_display
import urwid.web_display

from fuelmenu.common.modulehelper import BLANK_KEY
from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.common.modulehelper import WidgetType
from fuelmenu.common import utils
from fuelmenu.settings import Settings

log = logging.getLogger('fuelmenu.mirrors')
blank = urwid.Divider()

local_repo_pattern = re.compile(r'^http[s]?://(127.0.0.1|localhost)([:/].*)?$')


BOOTSTRAP_HTTP_PROXY_KEY = "BOOTSTRAP/http_proxy"
BOOTSTRAP_HTTPS_PROXY_KEY = "BOOTSTRAP/https_proxy"
BOOTSTRAP_REPOS_KEY = "BOOTSTRAP/repos"
BOOTSTRAP_SKIP_BUILD_KEY = "BOOTSTRAP/skip_default_img_build"

ADD_REPO_BUTTON_KEY = 'add_repo_button'


class bootstrapimg(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Bootstrap Image"
        self.priority = 55
        self.visible = True
        self.parent = parent
        self._mos_version = None

        # UI Text
        self.header_content = ["Bootstrap image configuration"]

        self._common_fields = (
            BLANK_KEY,
            BOOTSTRAP_SKIP_BUILD_KEY,
        )

        self._repo_related_fields = (
            BLANK_KEY,
            BOOTSTRAP_HTTP_PROXY_KEY,
            BOOTSTRAP_HTTPS_PROXY_KEY,
            BLANK_KEY,
            BOOTSTRAP_REPOS_KEY,
            ADD_REPO_BUTTON_KEY
        )

        self.fields = self._common_fields

        self.repo_list = []

        self.repo_value_scheme = {
            "name": {
                "type": WidgetType.TEXT_FIELD,
                "label": "Name",
                "tooltip": "Repository name"
            },
            "uri": {
                "type": WidgetType.TEXT_FIELD,
                "label": "Deb repo",
                "tooltip": "Repo in format: "
                           "deb uri distribution [component1] [...]"
            },
            "priority": {
                "type": WidgetType.TEXT_FIELD,
                "label": "Priority",
                "tooltip": "Repository priority"
            }
        }

        self.defaults = {
            BOOTSTRAP_SKIP_BUILD_KEY: {
                "label": "Skip building bootstrap image",
                "tooltip": "",
                "type": WidgetType.CHECKBOX,
                "callback": self.skip_build_callback},
            BOOTSTRAP_HTTP_PROXY_KEY: {
                "label": "HTTP proxy",
                "tooltip": "Use this proxy when building the bootstrap image",
                "value": ""},
            BOOTSTRAP_HTTPS_PROXY_KEY: {
                "label": "HTTPS proxy",
                "tooltip": "Use this proxy when building the bootstrap image",
                "value": ""},
            BOOTSTRAP_REPOS_KEY: {
                "label": "List of repositories",
                "type": WidgetType.LIST,
                "value_scheme": self.repo_value_scheme,
                "value": self.repo_list
            },
            ADD_REPO_BUTTON_KEY: {
                "label": "Add repository",
                "type": WidgetType.BUTTON,
                "callback": self.add_repo
            }
        }
        self.oldsettings = self.load()
        self.screen = None

    @property
    def mos_version(self):
        if not self._mos_version:
            self._mos_version = utils.get_fuel_version()
        return self._mos_version

    @property
    def responses(self):
        ret = dict()
        for index, fieldname in enumerate(self.fields):
            if fieldname == BLANK_KEY or 'button' in fieldname.lower():
                pass
            elif fieldname == BOOTSTRAP_REPOS_KEY:
                ret[fieldname] = \
                    self._get_repo_list_response(self.edits[index])
            elif fieldname == BOOTSTRAP_SKIP_BUILD_KEY:
                ret[fieldname] = self.edits[index].get_state()
            else:
                ret[fieldname] = self.edits[index].get_edit_text()
        return ret

    def check(self, args):
        """Validate that all fields have valid values through sanity checks."""
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()
        responses = self.responses

        errors = []
        if not responses.get(BOOTSTRAP_SKIP_BUILD_KEY):
            errors.extend(self.check_apt_repos(responses))

        if errors:
            log.error("Errors: %s", errors)
            ModuleHelper.display_failed_check_dialog(self, errors)
            return False
        else:
            self.parent.footer.set_text("No errors found.")
            return responses

    def check_apt_repos(self, responses):
        errors = []

        http_proxy = responses[BOOTSTRAP_HTTP_PROXY_KEY].strip()
        https_proxy = responses[BOOTSTRAP_HTTPS_PROXY_KEY].strip()

        proxies = {
            'http': http_proxy,
            'https': https_proxy
        }

        repos = responses.get(BOOTSTRAP_REPOS_KEY)

        if not repos:
            errors.append("Specify at least one repository.")

        for index, repo in enumerate(repos):
            name = repo['name']
            priority = repo['priority']
            if priority and not isinstance(priority,
                                           (types.IntType, types.NoneType)):
                errors.append("Priority value for repository {0} should be "
                              "empty or numeric.".format(name))
            if not name:
                name = "#{0}".format(index + 1)
                errors.append("Empty name for repository {0}."
                              .format(name))
            if not all((repo['type'], repo['uri'], repo['suite'])):
                errors.append("Cannot parse repository {0}. "
                              "Expected format: "
                              "'deb uri distribution [component1] [...]'."
                              .format(name))
                continue
            if not self._check_repo(repo['uri'], repo['suite'], proxies):
                errors.append("URL for repository {0} is not accessible."
                              .format(name))

        return errors

    def apply(self, args):
        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            log.error("%s" % (responses))
            return False
        self.save(responses)
        return True

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def _get_repo_list_response(self, list_box):
        # Here we assumed that we get object of WalkerStoredListBox
        # which contains link for list_walker.
        if not hasattr(list_box, 'list_walker'):
            return []
        external_lw = list_box.list_walker

        # on UI we have labels, but not keys...
        label_to_key_mapping = dict((v['label'], k) for k, v in
                                    six.iteritems(self.repo_value_scheme))
        result = []
        for lb in external_lw:
            repo = {}
            internal_lw = getattr(lb, 'list_walker', None)
            if not internal_lw:
                continue

            for edit in internal_lw:
                if not hasattr(edit, 'caption'):
                    continue
                key = label_to_key_mapping[edit.caption.strip()]
                repo[key] = edit.edit_text

            if any(repo.values()):  # skip empty entries
                result.append(self._parse_ui_repo_entry(repo))
        return result

    def _parse_ui_repo_entry(self, repo_from_ui):
        regexp = r"(?P<type>\w+) (?P<uri>[^\s]+) (?P<suite>[^\s]+)( " \
                 r"(?P<section>[\w\s]*))?"

        priority = repo_from_ui.get('priority')
        name = repo_from_ui.get('name')
        uri = repo_from_ui.get('uri', '')
        try:
            priority = int(priority) if priority else None
        except (TypeError, ValueError):
            log.debug("Wrong priority value for repository '{0}': "
                      "'{1}'.".format(name, priority))

        match = re.match(regexp, uri)

        repo_type = match.group('type') if match else ''
        repo_suite = match.group('suite') if match else ''
        repo_section = match.group('section') if match else ''
        repo_uri = match.group('uri') if match else uri

        return {
            "name": name,
            "type": repo_type,
            "uri": repo_uri,
            "priority": priority,
            "suite": repo_suite,
            "section": repo_section
        }

    def _parse_config_repo_entry(self, repo_from_config):
        uri_template = "{type} {uri} {suite}"
        section_suffix = " {section}"

        section = repo_from_config.get('section')
        name = repo_from_config.get('name', '')
        priority = repo_from_config.get('priority', '')
        if not priority:
            # we can get None from config
            priority = ""

        data = {
            "suite": repo_from_config.get('suite', ''),
            "type": repo_from_config.get('type', ''),
            "uri": repo_from_config.get('uri', '')
        }

        if section:
            data["section"] = section
            uri_template += section_suffix
        uri = ''
        if any(data.values()):
            uri = uri_template.format(**data).strip()
        result = {
            "uri": uri,
            "name": name,
            "priority": str(priority)
        }

        return result

    def _parse_config_repo_list(self, repos_from_config):
        # There are two different formats for repositories in config and UI:
        # on UI we have 3 fields: Name, URI and Priority,
        # where 'URI' actually contains repo type, suite and section. Example:
        # deb http://archive.ubuntu.com/ubuntu/ trusty main universe multiverse
        # In config file 'uri', 'type', 'suite' and 'section' are stored
        # separate. So we need to convert this list from one format to another.

        repos_for_ui = []
        for entry in repos_from_config:
            repos_for_ui.append(self._parse_config_repo_entry(entry))
        return repos_for_ui

    def add_repo(self, data=None):

        defaults = self._get_fresh_defaults()
        repo_list = defaults[BOOTSTRAP_REPOS_KEY]['value']
        repo_list.append(
            dict((k, "") for k in self.repo_value_scheme))
        button_position = self._calculate_field_position(ADD_REPO_BUTTON_KEY)
        self._redraw_screen(defaults, button_position)

    def _update_defaults(self, defaults, new_settings):
        for setting in defaults:
            try:
                new_value = ModuleHelper.get_setting(new_settings, setting)
                if BOOTSTRAP_REPOS_KEY == setting:
                    defaults[setting]["value"] = \
                        self._parse_config_repo_list(new_value)
                    continue

                defaults[setting]["value"] = new_value
            except KeyError:
                log.warning("no setting named {0} found.".format(setting))
            except Exception as e:
                log.warning("unexpected error: {0}".format(e))

    def load(self):
        # Read in yaml
        default_settings = Settings().read(
            self.parent.defaultsettingsfile,
            template_kwargs={"mos_version": self.mos_version})
        settings = default_settings
        settings.update(Settings().read(self.parent.settingsfile))

        self._update_defaults(self.defaults, settings)
        self._select_fields_to_show(self.defaults)
        return settings

    def _make_settings_from_responses(self, responses):
        settings = dict()
        for setting in responses:
            new_value = responses[setting]
            ModuleHelper.set_setting(settings, setting, new_value,
                                     self.oldsettings)
        return settings

    def save(self, responses):

        newsettings = self._make_settings_from_responses(responses)

        Settings().write(newsettings,
                         defaultsfile=self.parent.defaultsettingsfile,
                         outfn=self.parent.settingsfile)

        # Set oldsettings to reflect new settings
        self.oldsettings = newsettings
        # Update self.defaults

        self._update_defaults(self.defaults, newsettings)

    def check_url(self, url, proxies):
        try:
            resp = requests.get(url, proxies=proxies, verify=False)
        except (requests.exceptions.RequestException,
                requests.exceptions.BaseHTTPError) as e:
            log.error(e)
            return False
        return resp.ok

    def _check_repo(self, base_url, suite, proxies):
        release_url = '{base_url}/dists/{suite}/Release'.format(
            base_url=base_url, suite=suite)
        if (local_repo_pattern.search(release_url) and
                utils.is_pre_deployment()):
            # Due to pre-deployment stage we can't check accessibility of local
            # repository since it is not created at that moment. Although we
            # still should provide an ability to use it, because in fact
            # it will be created at the end of deployment.
            log.warn('Accessibility check is skipped for local repository: %s',
                     release_url)
            return True

        return self.check_url(release_url, proxies)

    def refresh(self):
        pass

    def _generate_screen_by_defaults(self, defaults):
        screen = ModuleHelper.screenUI(self, self.header_content, self.fields,
                                       defaults)
        return screen

    def _get_fresh_defaults(self):
        defaults = copy.copy(self.defaults)
        self._update_defaults(defaults,
                              self._make_settings_from_responses(
                                  self.responses))
        return defaults

    def _redraw_screen(self, defaults=None, focus_position=None):
        if not defaults:
            defaults = self.defaults
        self.screen = self._generate_screen_by_defaults(defaults)
        if focus_position:
            self.walker.set_focus(focus_position)
        self.parent.draw_child_screen(self.screen, focus_on_child=True)

    def _calculate_field_position(self, field_name):
        return self._calculate_edits_offset() + self.fields.index(field_name)

    def _calculate_edits_offset(self):
        """Returns position of first widget."""
        first_edit = self.edits[0] if self.edits else None
        result = 0
        for widget in self.walker.lst:
            if widget == first_edit:
                break
            result += 1
        return result

    def _select_fields_to_show(self, defaults):
        skip_build = defaults[BOOTSTRAP_SKIP_BUILD_KEY].get('value')
        if skip_build:
            self.fields = self._common_fields
            return
        self.fields = \
            self._common_fields +\
            self._repo_related_fields

    def skip_build_callback(self, widget, new_state):
        defaults = self._get_fresh_defaults()
        defaults[BOOTSTRAP_SKIP_BUILD_KEY]['value'] = new_state
        self._select_fields_to_show(defaults)
        self._redraw_screen(
            defaults,
            self._calculate_field_position(BOOTSTRAP_SKIP_BUILD_KEY))

    def screenUI(self):
        return self._generate_screen_by_defaults(self.defaults)
