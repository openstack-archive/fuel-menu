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
import re
import six

from fuelmenu.common import dialog
from fuelmenu.common.modulehelper import BLANK_KEY
from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.common.modulehelper import WidgetType
import fuelmenu.common.urwidwrapper as widget
from fuelmenu.settings import Settings
import logging
import url_access_checker.api as urlck
import url_access_checker.errors as url_errors
import urwid
import urwid.raw_display
import urwid.web_display

log = logging.getLogger('fuelmenu.mirrors')
blank = urwid.Divider()

FUEL_RELEASE_FILE = '/etc/fuel_release'
FUEL_BOOTSTRAP_IMAGE_CONF = '/etc/fuel-bootstrap-image.conf'
MOS_REPO_DEFAULT = \
    'http://mirror.fuel-infra.org/mos-repos/ubuntu/{mos_version}'

BOOTSTRAP_FLAVOR_KEY = 'BOOTSTRAP/flavor'
BOOTSTRAP_MIRROR_DISTRO_KEY = "BOOTSTRAP/MIRROR_DISTRO"
BOOTSTRAP_DISTRO_RELEASE_KEY = "BOOTSTRAP/DISTRO_RELEASE"
BOOTSTRAP_MIRROR_MOS_KEY = "BOOTSTRAP/MIRROR_MOS"
BOOTSTRAP_HTTP_PROXY_KEY = "BOOTSTRAP/HTTP_PROXY"
BOOTSTRAP_HTTPS_PROXY_KEY = "BOOTSTRAP/HTTPS_PROXY"
BOOTSTRAP_EXTRA_DEB_REPOS_KEY = "BOOTSTRAP/EXTRA_DEB_REPOS"
BOOTSTRAP_SKIP_BUILD_KEY = "BOOTSTRAP/SKIP_DEFAULT_IMG_BUILD"

ADD_REPO_BUTTON_KEY = 'add_repo_button'


class bootstrapimg(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Bootstrap Image"
        self.priority = 55
        self.visible = True
        self.deployment = "pre"
        self.parent = parent
        self.distro = 'ubuntu'
        self.mos_repo_name = 'mos'
        self._mos_version = None
        self._mos_release = None
        self._bootstrap_flavor = None

        # UI Text
        self.header_content = ["Bootstrap image configuration"]
        self.fields = (
            BOOTSTRAP_FLAVOR_KEY,
            BLANK_KEY,
            BOOTSTRAP_SKIP_BUILD_KEY,
            BLANK_KEY,
            BOOTSTRAP_MIRROR_DISTRO_KEY,
            BOOTSTRAP_DISTRO_RELEASE_KEY,
            BOOTSTRAP_MIRROR_MOS_KEY,
            BLANK_KEY,
            BOOTSTRAP_HTTP_PROXY_KEY,
            BOOTSTRAP_HTTPS_PROXY_KEY,
            BLANK_KEY,
            BOOTSTRAP_EXTRA_DEB_REPOS_KEY,
            ADD_REPO_BUTTON_KEY
        )

        # TODO(asheplyakov):
        # switch to the new MOS APT repo structure when it's ready
        mos_repo_default = MOS_REPO_DEFAULT.format(
            mos_version=self.mos_version)

        self.extra_repo_list = []

        self.extra_repo_value_scheme = {
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
                "type": WidgetType.CHECKBOX},
            BOOTSTRAP_FLAVOR_KEY: {
                "label": "Flavor",
                "tooltip": "",
                "type": WidgetType.RADIO,
                "choices": ["CentOS", "Ubuntu"]},
            BOOTSTRAP_MIRROR_DISTRO_KEY: {
                "label": "Ubuntu mirror",
                "tooltip": "Ubuntu APT repo URL",
                "value": "http://archive.ubuntu.com/ubuntu"},
            BOOTSTRAP_DISTRO_RELEASE_KEY: {
                "label": "Ubuntu release",
                "tooltip": "Ubuntu release, e.g. trusty, vivid, etc.",
                "value": ""},
            BOOTSTRAP_MIRROR_MOS_KEY: {
                "label": "MOS mirror",
                "tooltip": ("MOS APT repo URL (can use file:// protocol, will"
                            "use local mirror in such case"),
                "value": mos_repo_default},
            BOOTSTRAP_HTTP_PROXY_KEY: {
                "label": "HTTP proxy",
                "tooltip": "Use this proxy when building the bootstrap image",
                "value": ""},
            BOOTSTRAP_HTTPS_PROXY_KEY: {
                "label": "HTTPS proxy",
                "tooltip": "Use this proxy when building the bootstrap image",
                "value": ""},
            BOOTSTRAP_EXTRA_DEB_REPOS_KEY: {
                "label": "Extra Repositories",
                "type": WidgetType.LIST,
                "value_scheme": self.extra_repo_value_scheme,
                "value": self.extra_repo_list
            },
            ADD_REPO_BUTTON_KEY: {
                "label": "Add Extra Repository",
                "type": WidgetType.BUTTON,
                "callback": self.add_repo
            }
        }
        self.oldsettings = self.load()
        self.screen = None

    def _read_version_info(self):
        with open(FUEL_RELEASE_FILE) as f:
            self._mos_version = f.read().strip()

    @property
    def mos_version(self):
        if not self._mos_version:
            self._read_version_info()
        return self._mos_version

    @property
    def mos_release(self):
        if not self._mos_release:
            self._mos_release = 'mos{0}'.format(self.mos_version)
        return self._mos_release

    @property
    def responses(self):
        ret = dict()
        for index, fieldname in enumerate(self.fields):
            if fieldname == BLANK_KEY or 'button' in fieldname.lower():
                pass
            elif fieldname == BOOTSTRAP_FLAVOR_KEY:
                rb_group = self.edits[index].rb_group
                flavor = 'centos' if rb_group[0].state else 'ubuntu'
                ret[fieldname] = flavor
            elif fieldname == BOOTSTRAP_EXTRA_DEB_REPOS_KEY:
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
        if responses.get(BOOTSTRAP_FLAVOR_KEY) == 'ubuntu':
            errors.extend(self.check_apt_repos(responses))

        if errors:
            log.error("Errors: %s", errors)
            error_msg = "\n".join(errors)
            dialog.display_dialog(self, widget.TextLabel(error_msg),
                                  "Check failed.")
            return False
        else:
            self.parent.footer.set_text("No errors found.")
            return responses

    def check_apt_repos(self, responses):
        errors = []
        # APT repo URL must not be empty
        distro_repo_base = responses[BOOTSTRAP_MIRROR_DISTRO_KEY].strip()
        distro_repo_release = \
            responses[BOOTSTRAP_DISTRO_RELEASE_KEY].strip()
        mos_repo_base = responses[BOOTSTRAP_MIRROR_MOS_KEY].strip()
        http_proxy = responses[BOOTSTRAP_HTTP_PROXY_KEY].strip()
        https_proxy = responses[BOOTSTRAP_HTTPS_PROXY_KEY].strip()

        proxies = {
            'http': http_proxy,
            'https': https_proxy
        }

        if len(distro_repo_base) == 0:
            errors.append("Ubuntu mirror URL must not be empty.")

        if len(distro_repo_release) == 0:
            errors.append("Ubuntu release must not be empty.")

        if not self.check_distro_repo(distro_repo_base,
                                      distro_repo_release,
                                      proxies):
            errors.append("Ubuntu repository is not accessible.")

        if len(mos_repo_base) == 0:
            errors.append("MOS repo URL must not be empty.")

        if not self.check_mos_repo(mos_repo_base, proxies):
            errors.append("MOS repository is not accessible.")

        repos = responses.get(BOOTSTRAP_EXTRA_DEB_REPOS_KEY)

        for index, repo in enumerate(repos):
            name = repo['name']
            if not name:
                name = "#{0}".format(index + 1)
                errors.append("Empty name for extra repository {0}."
                              .format(name))
            if not all((repo['type'], repo['uri'], repo['suite'])):
                errors.append("Cannot parse extra repository {0}. "
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

        with open(FUEL_BOOTSTRAP_IMAGE_CONF, "w") as fbiconf:
            for var in self.fields:
                if var == BLANK_KEY:
                    continue
                name = var
                if "/" in name:
                    _, name = name.split('/')

                fbiconf.write('{0}="{1}"\n'.format(name, responses.get(var)))
            fbiconf.write('MOS_VERSION="{0}"'.format(self.mos_version))
        self.save(responses)
        return True

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def _ui_set_bootstrap_flavor(self):
        rb_index = self.fields.index(BOOTSTRAP_FLAVOR_KEY)
        is_ubuntu = self._bootstrap_flavor is not None and \
            'ubuntu' in self._bootstrap_flavor
        try:
            rb_group = self.edits[rb_index].rb_group
            rb_group[0].set_state(not is_ubuntu)
            rb_group[1].set_state(is_ubuntu)
        except AttributeError:
            # the UI hasn't been initalized yet
            pass

    def _set_bootstrap_flavor(self, flavor):
        is_ubuntu = flavor is not None and 'ubuntu' in flavor.lower()
        self._bootstrap_flavor = 'ubuntu' if is_ubuntu else 'centos'
        self._ui_set_bootstrap_flavor()

    def _get_repo_list_response(self, list_box):
        # Here we assumed that we get object of WalkerStoredListBox
        # which contains link for list_walker.
        if not hasattr(list_box, 'list_walker'):
            return []
        external_lw = list_box.list_walker

        # on UI we have labels, but not keys...
        label_to_key_mapping = dict((v['label'], k) for k, v in
                                    six.iteritems(
                                        self.extra_repo_value_scheme))
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
        if not priority:
            priority = None
        name = repo_from_ui.get('name')
        uri = repo_from_ui.get('uri', '')

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

    def _generate_mos_repos(self, uri):
        result = self._generate_repos_from_uri(
            uri=uri,
            codename=self.mos_release,
            name=self.mos_repo_name,
            components=['', '-updates', '-security'],
            section='main restricted',
            priority='1050'
        )
        result += self._generate_repos_from_uri(
            uri=uri,
            codename=self.mos_release,
            name=self.mos_repo_name,
            components=['-holdback'],
            section='main restricted',
            priority='1100'
        )
        return result

    def _generate_distro_repos(self, uri, release):
        return self._generate_repos_from_uri(
            uri=uri,
            codename=release,
            name=self.distro,
            components=['', '-updates', '-security'],
            section='main universe multiverse'
        )

    def _generate_repos_from_uri(self, uri, codename, name, components=None,
                                 section=None, type_=None, priority=None):
        if not components:
            components = ['']
        result = []
        for component in components:
            result.append({
                "name": "{0}{1}".format(name, component),
                "type": type_ or "deb",
                "uri": uri,
                "priority": priority,
                "section": section,
                "suite": "{0}{1}".format(codename, component),

            })
        return result

    def _get_repo_uri_by_name(self, name, repos):
        if not repos:
            return ""
        filter_result = filter(lambda x: x['name'] == name, repos)
        if filter_result:
            return filter_result[0].get("uri", "")
        return ""

    def _get_repo_suite_by_name(self, name, repos):
        if not repos:
            return ""
        filter_result = filter(lambda x: x['name'] == name, repos)
        if filter_result:
            return filter_result[0].get("suite", "")
        return ""

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
            "priority": priority
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

        responses = self.responses
        defaults = copy.copy(self.defaults)
        self._update_defaults(defaults,
                              self._make_settings_from_responses(responses))
        defaults[BOOTSTRAP_EXTRA_DEB_REPOS_KEY]['value'].append(
            dict((k, "") for k in self.extra_repo_value_scheme))
        self.screen = self._generate_screen_by_defaults(defaults)
        self.parent.draw_child_screen(self.screen)

    def _update_defaults(self, defaults, new_settings):
        for setting in defaults:
            try:
                if "/" in setting:
                    part1, part2 = setting.split("/")
                    new_value = new_settings[part1][part2]
                else:
                    new_value = new_settings[setting]

                if BOOTSTRAP_FLAVOR_KEY == setting:
                    self._set_bootstrap_flavor(new_value)
                    continue
                if BOOTSTRAP_MIRROR_MOS_KEY == setting:
                    defaults[setting]["value"] = \
                        self._get_repo_uri_by_name(self.mos_repo_name,
                                                   new_value)
                    continue
                if BOOTSTRAP_MIRROR_DISTRO_KEY == setting:
                    defaults[setting]["value"] = \
                        self._get_repo_uri_by_name(self.distro, new_value)
                    # We also should get release name
                    defaults[BOOTSTRAP_DISTRO_RELEASE_KEY]["value"] = \
                        self._get_repo_suite_by_name(self.distro, new_value)
                    continue

                if BOOTSTRAP_EXTRA_DEB_REPOS_KEY == setting:
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
        defaultsettings = Settings().read(self.parent.defaultsettingsfile)
        oldsettings = defaultsettings
        oldsettings.update(Settings().read(self.parent.settingsfile))

        self._update_defaults(self.defaults, oldsettings)
        return oldsettings

    def _make_settings_from_responses(self, responses):
        settings = dict()
        for setting in responses.keys():
            new_value = responses[setting]
            if BOOTSTRAP_MIRROR_MOS_KEY == setting:
                new_value = self._generate_mos_repos(new_value)
            if BOOTSTRAP_MIRROR_DISTRO_KEY == setting:
                new_value = self._generate_distro_repos(
                    new_value,
                    responses.get(BOOTSTRAP_DISTRO_RELEASE_KEY))
            if BOOTSTRAP_DISTRO_RELEASE_KEY == setting:
                continue  # It's handled above
            if "/" in setting:
                part1, part2 = setting.split("/")
                if part1 not in settings:
                    # We may not touch all settings, so copy oldsettings first
                    settings[part1] = self.oldsettings[part1]
                settings[part1][part2] = new_value
            else:
                settings[setting] = new_value
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
            return urlck.check_urls([url], proxies=proxies)
        except (url_errors.UrlNotAvailable,
                url_errors.InvalidProtocol):
            return False

    def _check_repo(self, base_url, suite, proxies):
        release_url = '{base_url}/dists/{suite}/Release'.format(
            base_url=base_url, suite=suite)
        return self.check_url(release_url, proxies)

    def check_distro_repo(self, base_url, distro_release, proxies):
        # TODO(asheplyakov):
        # check if it's possible to debootstrap with this repo
        return self._check_repo(base_url, distro_release, proxies)

    def check_mos_repo(self, base_url, proxies):
        # deb {repo_base_url}/mos/ubuntu mos{mos_version} main
        suite = self.mos_release
        return self._check_repo(base_url, suite, proxies)

    def refresh(self):
        pass

    def _generate_screen_by_defaults(self, defaults):
        screen = ModuleHelper.screenUI(self, self.header_content, self.fields,
                                       defaults)
        # set the radiobutton state (ModuleHelper handles only yes/no choice)
        self._ui_set_bootstrap_flavor()
        return screen

    def screenUI(self):
        return self._generate_screen_by_defaults(self.defaults)
