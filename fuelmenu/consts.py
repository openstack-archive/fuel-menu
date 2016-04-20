# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
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

LOGFILE = "/var/log/fuelmenu.log"

PUPPET_LOGFILE = "/var/log/puppet/fuelmenu-puppet.log"

SETTINGS_FILE = "/etc/fuel/astute.yaml"
RELEASE_FILE = "/etc/fuel_release"

DEFAULT_LOCK_FILE = "/var/run/fuelmenu.lock"

PRE_DEPLOYMENT_MODE = "pre"
POST_DEPLOYMENT_MODE = "post"

PUPPET_TYPE_LITERAL = "literal"
PUPPET_TYPE_RESOURCE = "resource"
PUPPET_TYPE_CLASS = "class"
