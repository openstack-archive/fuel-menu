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

from .bootstrapimg import BootstrapImg
from .cobblerconf import CobblerConf
from .dnsandhostname import DnsAndHostname
from .feature_groups import FeatureGroups
from .fueluser import FuelUser
from .interfaces import Interfaces
from .ntpsetup import NtpSetup
from .restore import Restore
from .rootpw import Rootpw
from .saveandquit import SaveAndQuit
from .security import Security
from .servicepws import Servicepws
from .shell import Shell


all_modules = [
    BootstrapImg,
    CobblerConf,
    DnsAndHostname,
    FeatureGroups,
    FuelUser,
    Interfaces,
    NtpSetup,
    Restore,
    Rootpw,
    SaveAndQuit,
    Security,
    Servicepws,
    Shell,
]
