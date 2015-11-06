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

from fuelmenu.common.modulehelper import BLANK_KEY
from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.common.modulehelper import WidgetType
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
MOS_REPO_DFLT = 'http://mirror.fuel-infra.org/mos-repos/ubuntu/{mos_version}'

BOOTSTRAP_FLAVOR_KEY = 'BOOTSTRAP/flavor'
BOOTSTRAP_MIRROR_DISTRO_KEY = "BOOTSTRAP/MIRROR_DISTRO"
BOOTSTRAP_DISTRO_RELEASE_KEY = "BOOTSTRAP/DISTRO_RELEASE"
BOOTSTRAP_MIRROR_MOS_KEY = "BOOTSTRAP/MIRROR_MOS"
BOOTSTRAP_HTTP_PROXY_KEY = "BOOTSTRAP/HTTP_PROXY"
BOOTSTRAP_HTTPS_PROXY_KEY = "BOOTSTRAP/HTTPS_PROXY"
BOOTSTRAP_EXTRA_DEB_REPOS_KEY = "BOOTSTRAP/EXTRA_DEB_REPOS"
BOOTSTRAP_SKIP_BUILD_KEY = "BOOTSTRAP/SKIP_DEFAULT_IMG_BUILD"


class bootstrapimg(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "Bootstrap Image"
        self.priority = 55
        self.visible = True
        self.deployment = "pre"
        self.parent = parent
        self.distro = 'ubuntu'
        self._mos_version = None
        self._bootstrap_flavor = None

        # UI Text
        self.header_content = ["Bootstrap image configuration"]
        self.fields = (
            BOOTSTRAP_SKIP_BUILD_KEY,
            BLANK_KEY,
            BOOTSTRAP_FLAVOR_KEY,
            BOOTSTRAP_MIRROR_DISTRO_KEY,
            BOOTSTRAP_DISTRO_RELEASE_KEY,
            BOOTSTRAP_MIRROR_MOS_KEY,
            BOOTSTRAP_HTTP_PROXY_KEY,
            BOOTSTRAP_HTTPS_PROXY_KEY,
            BOOTSTRAP_EXTRA_DEB_REPOS_KEY)

        # TODO(asheplyakov):
        # switch to the new MOS APT repo structure when it's ready
        mos_repo_dflt = MOS_REPO_DFLT.format(mos_version=self.mos_version)

        self.defaults = {
            BOOTSTRAP_SKIP_BUILD_KEY: {
                "label": "Skip building bootstrap image",
                "tooltip": "",
                "type": WidgetType.CHECKBOX},
            BOOTSTRAP_FLAVOR_KEY: {
                "label": "Flavor",
                "tooltip": "",
                "type": WidgetType.RADIO,
                "choices": ["CentOS", "Ubuntu (EXPERIMENTAL)"]},
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
                "value": mos_repo_dflt},
            BOOTSTRAP_HTTP_PROXY_KEY: {
                "label": "HTTP proxy",
                "tooltip": "Use this proxy when building the bootstrap image",
                "value": ""},
            BOOTSTRAP_HTTPS_PROXY_KEY: {
                "label": "HTTPS proxy",
                "tooltip": "Use this proxy when building the bootstrap image",
                "value": ""},
            BOOTSTRAP_EXTRA_DEB_REPOS_KEY: {
                "label": "Extra APT repositories",
                "tooltip": "Additional repositories for bootstrap image",
                "value": ""}
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
    def distro_release(self):
        if not self._distro_release:
            self._read_version_info()
        return self._distro_release

    @property
    def responses(self):
        ret = dict()
        for index, fieldname in enumerate(self.fields):
            if fieldname == BLANK_KEY:
                pass
            elif fieldname == BOOTSTRAP_FLAVOR_KEY:
                rb_group = self.edits[index].rb_group
                flavor = 'centos' if rb_group[0].state else 'ubuntu'
                ret[fieldname] = flavor
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
            self.parent.footer.set_text("Error: %s" % (errors[0]))
            log.error("Errors: %s", errors)
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

        if not self.checkDistroRepo(distro_repo_base,
                                    distro_repo_release, proxies):
            errors.append("Ubuntu repository is not accessible.")

        if len(mos_repo_base) == 0:
            errors.append("MOS repo URL must not be empty.")

        if not self.checkMOSRepo(mos_repo_base, proxies):
            errors.append("MOS repository is not accessible.")

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

    def load(self):
        # Read in yaml
        defaultsettings = Settings().read(self.parent.defaultsettingsfile)
        oldsettings = defaultsettings
        oldsettings.update(Settings().read(self.parent.settingsfile))

        for setting in self.defaults:
            try:
                if BOOTSTRAP_FLAVOR_KEY == setting:
                    section, key = BOOTSTRAP_FLAVOR_KEY.split('/')
                    flavor = oldsettings[section][key]
                    self._set_bootstrap_flavor(flavor)
                elif "/" in setting:
                    part1, part2 = setting.split("/")
                    self.defaults[setting]["value"] = oldsettings[part1][part2]
                else:
                    self.defaults[setting]["value"] = oldsettings[setting]
            except KeyError:
                log.warning("no setting named %s found.", setting)
            except Exception as e:
                log.warning("unexpected error: %s", e.message)
        return oldsettings

    def save(self, responses):
        # Generic settings start
        newsettings = dict()
        for setting in responses.keys():
            if "/" in setting:
                part1, part2 = setting.split("/")
                if part1 not in newsettings:
                    # We may not touch all settings, so copy oldsettings first
                    newsettings[part1] = self.oldsettings[part1]
                newsettings[part1][part2] = responses[setting]
            else:
                newsettings[setting] = responses[setting]
        # Generic settings end

        Settings().write(newsettings,
                         defaultsfile=self.parent.defaultsettingsfile,
                         outfn=self.parent.settingsfile)

        # Set oldsettings to reflect new settings
        self.oldsettings = newsettings
        # Update self.defaults
        for index, fieldname in enumerate(self.fields):
            if fieldname != BLANK_KEY:
                log.info("resetting %s", fieldname)
                if fieldname not in self.defaults.keys():
                    log.error("no such field: %s, valid are %s",
                              fieldname, ' '.join(self.defaults.keys()))
                    continue
                if fieldname not in newsettings.keys():
                    log.error("newsettings: no such field: %s, valid are %s",
                              fieldname, ' '.join(newsettings.keys()))
                    continue
                self.defaults[fieldname]['value'] = newsettings[fieldname]

    def check_url(self, url, proxies):
        try:
            return urlck.check_urls([url], proxies=proxies)
        except url_errors.UrlNotAvailable:
            return False

    def checkDistroRepo(self, base_url, distro_release, proxies):
        release_url = '{base_url}/dists/{distro_release}/Release'.format(
            base_url=base_url, distro_release=distro_release)
        available = self.check_url(release_url, proxies)
        # TODO(asheplyakov):
        # check if it's possible to debootstrap with this repo
        return available

    def checkMOSRepo(self, base_url, proxies):
        # deb {repo_base_url}/mos/ubuntu mos{mos_version} main
        codename = 'mos{0}'.format(self.mos_version)
        release_url = '{base_url}/dists/{codename}/Release'.format(
            base_url=base_url, codename=codename)
        available = self.check_url(release_url, proxies)
        return available

    def refresh(self):
        pass

    def screenUI(self):
        screen = ModuleHelper.screenUI(self, self.header_content, self.fields,
                                       self.defaults)
        # set the radiobutton state (ModuleHelper handles only yes/no choice)
        self._ui_set_bootstrap_flavor()
        return screen
