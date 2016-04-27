# coding: utf-8

# Copyright 2016 Mirantis, Inc.
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

from fuelmenu.modules.bootstrapimg import BootstrapImage
from fuelmenu.modules.cobblerconf import CobblerConfig
from fuelmenu.modules.dnsandhostname import DnsAndHostname
from fuelmenu.modules.feature_groups import FeatureGroups
from fuelmenu.modules.fueluser import FuelUser
from fuelmenu.modules.interfaces import Interfaces
from fuelmenu.modules.ntpsetup import NtpSetup
from fuelmenu.modules.restore import Restore
from fuelmenu.modules.rootpw import RootPassword
from fuelmenu.modules.saveandquit import SaveAndQuit
from fuelmenu.modules.security import Security
from fuelmenu.modules.servicepws import ServicePasswords
from fuelmenu.modules.shell import Shell


# Note that order matters.
# objects loading and settings dumping will be made in this order
__all__ = [
    FuelUser,
    Interfaces,
    Security,
    CobblerConfig,
    DnsAndHostname,
    BootstrapImage,
    NtpSetup,
    RootPassword,
    FeatureGroups,
    Shell,
    Restore,
    SaveAndQuit,
    ServicePasswords,
]
