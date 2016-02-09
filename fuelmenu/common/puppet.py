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

import logging

from fuelmenu.common.utils import execute
from fuelmenu import consts


def _to_string(value):
    if isinstance(value, bool):
        return '%s,' % str(value).lower()
    return '"%s",' % value


def puppetApply(classes):
    """Runs puppet apply

    :param classes: list of {'type': 'name': params}. name should be a string
    :type classes: dict or list of dicts
    """
    log = logging
    log.info("Puppet start")

    command = ["puppet", "apply", "-d", "-v", "--logdest",
               "/var/log/puppet/fuelmenu-puppet.log"]

    puppet_type_handlers = {
        consts.PUPPET_TYPE_LITERAL: lambda item: [item['name']],
        consts.PUPPET_TYPE_RESOURCE: lambda item: [
            item["class"], "{", '"%s":' % item["name"]],
        consts.PUPPET_TYPE_CLASS: lambda item: [
            "class", "{", '"%s":' % cls["class"]]
    }

    input = list()
    for cls in classes:
        if cls['type'] not in puppet_type_handlers:
            log.error("Invalid type %s", cls['type'])
            return False

        input.extend(puppet_type_handlers[cls['type']](cls))
        if cls['type'] == consts.PUPPET_TYPE_LITERAL:
            continue

        #Build params
        for key, value in cls["params"].iteritems():
            input.extend([key, "=>", _to_string(value)])
        input.append('}')

    stdin = ' '.join(input)
    log.debug(' '.join(command))
    log.debug(stdin)
    code, out, err = execute(command, stdin=stdin)
    if code != 0:
        log.error("Exit code: %d. Error: %s Stdout: %s",
                  code, err, out)
        return False
