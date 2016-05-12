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

from fuelmenu.common import dialog
from fuelmenu.common.modulehelper import ModuleHelper
from fuelmenu.common import network
from fuelmenu.common import replace
import fuelmenu.common.urwidwrapper as widget
from fuelmenu.common import utils

import logging
import netaddr
import os
import re
import socket
import urwid
import urwid.raw_display
import urwid.web_display
log = logging.getLogger('fuelmenu.mirrors')
blank = urwid.Divider()


class DnsAndHostname(urwid.WidgetWrap):
    def __init__(self, parent):
        self.name = "DNS & Hostname"
        self.visible = True
        self.netsettings = dict()
        self.getNetwork()
        self.gateway = self.get_default_gateway_linux()
        self.extdhcp = True
        self.parent = parent

        # UI Text
        self.header_content = ["DNS and hostname setup", "Note: Leave "
                               "External DNS blank if you do not have "
                               "Internet access."]
        self.fields = ["HOSTNAME", "DNS_DOMAIN", "DNS_SEARCH", "DNS_UPSTREAM",
                       "blank", "TEST_DNS"]
        hostname, sep, domain = os.uname()[1].partition('.')
        self.defaults = \
            {
                "HOSTNAME": {"label": "Hostname",
                             "tooltip": "Hostname to use for Fuel master node",
                             "value": hostname},
                "DNS_UPSTREAM": {"label": "External DNS",
                                 "tooltip": "DNS server(s) (comma separated) \
to handle DNS requests (example 8.8.8.8,8.8.4.4)",
                                 "value": "8.8.8.8"},
                "DNS_DOMAIN": {"label": "Domain",
                               "tooltip": "Domain suffix to user for all \
nodes in your cluster",
                               "value": domain},
                "DNS_SEARCH": {"label": "Search Domain",
                               "tooltip": "Domains to search when looking up \
DNS (space separated)",
                               "value": domain},
                "TEST_DNS": {"label": "Hostname to test DNS:",
                             "value": "www.google.com",
                             "tooltip": "DNS record to resolve to see if DNS \
is accessible"}
            }

        self.load()
        self.screen = None

    def fixEtcHosts(self):
        # replace ip for env variable HOSTNAME in /etc/hosts
        if self.netsettings[self.parent.managediface]["addr"] != "":
            managediface_ip = self.netsettings[
                self.parent.managediface]["addr"]
        else:
            managediface_ip = "127.0.0.1"
        found = False
        with open("/etc/hosts") as fh:
            for line in fh:
                if re.match("%s.*%s" % (managediface_ip,
                            socket.gethostname()), line):
                    found = True
                    break
        if not found:
            expr = ".*%s.*" % socket.gethostname()
            replace.replaceInFile("/etc/hosts", expr, "%s   %s %s" % (
                                  managediface_ip,
                                  socket.gethostname(),
                                  socket.gethostname().split('.')[0]))

    def check(self, args):
        """Validate that all fields have valid values through sanity checks."""
        self.parent.footer.set_text("Checking data...")
        self.parent.refreshScreen()
        # Get field information
        responses = dict()

        for index, fieldname in enumerate(self.fields):
            if fieldname == "blank":
                pass
            else:
                responses[fieldname] = self.edits[index].get_edit_text()

        if self.parent.save_only:
            return responses

        # Validate each field
        errors = []

        # hostname must be under 60 chars
        if len(responses["HOSTNAME"]) >= 60:
            errors.append("Hostname must be under 60 chars.")

        # hostname must not be empty
        if len(responses["HOSTNAME"]) == 0:
            errors.append("Hostname must not be empty.")

        # hostname needs to have valid chars
        if re.search('[^a-z0-9-]', responses["HOSTNAME"]):
            errors.append(
                "Hostname must contain only alphanumeric and hyphen.")

        # domain must be under 180 chars
        if len(responses["DNS_DOMAIN"]) >= 180:
            errors.append("Domain must be under 180 chars.")

        # domain must not be empty
        if len(responses["DNS_DOMAIN"]) == 0:
            errors.append("Domain must not be empty.")

        # domain needs to have valid chars
        if re.match('[^a-z0-9-.]', responses["DNS_DOMAIN"]):
            errors.append(
                "Domain must contain only alphanumeric, period and hyphen.")
        # ensure external DNS is valid
        if len(responses["DNS_UPSTREAM"]) == 0:
            # We will allow empty if user doesn't need external networking
            # and present a strongly worded warning
            msg = "If you continue without DNS, you may not be able to access"\
                  + " external data necessary for installation needed for " \
                  + "some OpenStack Releases."

            dialog.display_dialog(
                self, widget.TextLabel(msg), "Empty DNS Warning")

        else:
            upstream_nameservers = responses["DNS_UPSTREAM"].split(',')

            # external DNS must contain only numbers, periods, and commas
            # Needs more serious ip address checking
            if re.match('[^0-9.,]', responses["DNS_UPSTREAM"]):
                errors.append(
                    "External DNS must contain only IP addresses and commas.")

            # Ensure local IPs are not in upstream list
            host_ips = network.list_host_ip_addresses()
            for nameserver in upstream_nameservers:
                if nameserver in host_ips:
                    errors.append("Host IPs cannot be in upstream DNS.")
                    break

            if len(upstream_nameservers) > 3:
                errors.append(
                    "Unable to specify more than 3 External DNS addresses.")

            # ensure test DNS name isn't empty
            if len(responses["TEST_DNS"]) == 0:
                errors.append("Test DNS must not be empty.")
            # Validate first IP address
            for nameserver in upstream_nameservers:
                if not netaddr.valid_ipv4(nameserver):
                    errors.append("Not a valid IP address for DNS server:"
                                  " {0}".format(nameserver))

            # Try to resolve with first address
            if not self.checkDNS(upstream_nameservers[0]):
                # Warn user that DNS resolution failed, but continue
                msg = "Unable to resolve %s.\n\n" % responses['TEST_DNS']\
                      + "Possible causes for DNS failure include:\n"\
                      + "* Invalid DNS server\n"\
                      + "* Invalid gateway\n"\
                      + "* Other networking issue\n\n"\
                      + "Fuel Setup can save this configuration, but "\
                      + "you may want to correct your settings."
                dialog.display_dialog(self, widget.TextLabel(msg),
                                      "DNS Failure Warning")
                self.parent.refreshScreen()

        if len(errors) > 0:
            log.error("Errors: %s %s" % (len(errors), errors))
            ModuleHelper.display_failed_check_dialog(self, errors)
            return False
        else:
            self.parent.footer.set_text("No errors found.")
            return responses

    def apply(self, args):
        self.fixEtcHosts()

        responses = self.check(args)
        if responses is False:
            log.error("Check failed. Not applying")
            log.error("%s" % (responses))
            return False

        self.save(responses)

        # Update network details so we write correct IP address
        self.getNetwork()

        # Apply hostname
        cmd = ["/usr/bin/hostnamectl", "set-hostname", responses["HOSTNAME"]]
        err_code, _, errout = utils.execute(cmd)
        if err_code != 0:
            log.error("Hostname change failed with an error: "
                      "\"{0}\"".format(errout))
            self.parent.footer.set_text("Unable to apply changes. Check logs "
                                        "for more details.")
            return False

        # remove old hostname from /etc/hosts
        f = open("/etc/hosts", "r")
        lines = f.readlines()
        f.close()
        with open("/etc/hosts", "w") as etchosts:
            for line in lines:
                if "localhost" in line:
                    etchosts.write(line)
                elif responses["HOSTNAME"] in line \
                        or self.parent.settings["HOSTNAME"] \
                        or self.netsettings[self.parent.managediface]['addr'] \
                        in line:
                    continue
                else:
                    etchosts.write(line)
            etchosts.close()

        # append hostname and ip address to /etc/hosts
        with open("/etc/hosts", "a") as etchosts:
            if self.netsettings[self.parent.managediface]["addr"] != "":
                managediface_ip = self.netsettings[
                    self.parent.managediface]["addr"]
            else:
                managediface_ip = "127.0.0.1"
            etchosts.write(
                "%s   %s.%s %s\n" % (managediface_ip, responses["HOSTNAME"],
                                     responses['DNS_DOMAIN'],
                                     responses["HOSTNAME"]))
            etchosts.close()

        def make_resolv_conf(filename):
            if self.netsettings[self.parent.managediface]["addr"] != "":
                managediface_ip = self.netsettings[
                    self.parent.managediface]["addr"]
            else:
                managediface_ip = "127.0.0.1"
            with open(filename, 'w') as f:
                f.write("search {0}\n".format(responses['DNS_SEARCH']))
                f.write("domain {0}\n".format(responses['DNS_DOMAIN']))
                if utils.is_post_deployment():
                    f.write("nameserver {0}\n".format(managediface_ip))
                for upstream_dns in responses['DNS_UPSTREAM'].split(','):
                    f.write("nameserver {0}\n".format(upstream_dns))

        # Create a temporary resolv.conf so DNS works before the cobbler
        # container is up and running.
        # TODO(asheplyakov): puppet does a similar thing, perhaps we can
        # use the corresponding template instead of duplicating it here.
        make_resolv_conf('/etc/resolv.conf')

        return True

    def cancel(self, button):
        ModuleHelper.cancel(self, button)

    def resolv_conf_settings(self):
        # Parse /etc/resolv.conf if it contains data
        settings = {}
        search, domain, nameservers = self.getDNS()
        if search:
            settings["DNS_SEARCH"] = search
        if domain:
            settings["DNS_DOMAIN"] = domain
        if nameservers:
            settings["DNS_UPSTREAM"] = nameservers
        return settings

    def load(self):
        # Precedence of DNS information:
        # Class defaults, fuelmenu default YAML, astute.yaml, uname,
        # /etc/resolv.conf
        oldsettings = self.parent.settings

        # Read hostname from uname
        try:
            hostname, sep, domain = os.uname()[1].partition('.')
            oldsettings["HOSTNAME"] = hostname
            oldsettings["DNS_DOMAIN"] = domain
            oldsettings["DNS_SEARCH"] = domain
        except Exception:
            log.warning("Unable to look up system hostname")

        if not self.parent.save_only:
            oldsettings.update(self.resolv_conf_settings())

        ModuleHelper.load_to_defaults(oldsettings,
                                      self.defaults,
                                      ignoredparams=['TEST_DNS'])

    def getDNS(self, resolver="/etc/resolv.conf"):
        nameservers = []
        domain = None
        searches = None

        try:
            with open(resolver, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("search "):
                        searches = ' '.join(line.split(' ')[1:])
                    if line.startswith("domain "):
                        domain = line.split(' ')[1]
                    if line.startswith("nameserver "):
                        nameservers.append(line.split(' ')[1])
        except EnvironmentError:
            log.warn("Unable to open /etc/resolv.conf")

        # Always remove local IPs from nameserver list
        host_ips = network.list_host_ip_addresses()
        for nameserver in nameservers:
            if nameserver in host_ips:
                nameservers.remove(nameserver)

        return searches, domain, ",".join(nameservers)

    def save(self, responses):
        newsettings = ModuleHelper.make_settings_from_responses(responses)
        self.parent.settings.merge(newsettings)

        # Update self.defaults
        for index, fieldname in enumerate(self.fields):
            if fieldname != "blank":
                self.defaults[fieldname]['value'] = newsettings[fieldname]

    def checkDNS(self, server):
        # Note: Python's internal resolver caches negative answers.
        # Therefore, we should call dig externally to be sure.

        command = ["dig", "+short", "+time=3", "+retries=1",
                   self.defaults["TEST_DNS"]['value'], "@{0}".format(server)]
        code, _, _ = utils.execute(command)
        return code == 0

    def getNetwork(self):
        ModuleHelper.getNetwork(self)

    def getDHCP(self, iface):
        return ModuleHelper.getDHCP(iface)

    def get_default_gateway_linux(self):
        return ModuleHelper.get_default_gateway_linux()

    def refresh(self):
        if self.parent.dns_might_have_changed:
            settings = self.resolv_conf_settings()
            for index, fieldname in enumerate(self.fields):
                if fieldname in settings:
                    self.edits[index].set_edit_text(settings[fieldname])
            self.parent.dns_might_have_changed = False

    def screenUI(self):
        return ModuleHelper.screenUI(self, self.header_content, self.fields,
                                     self.defaults, show_all_buttons=True)
