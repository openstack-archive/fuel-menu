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


def puppetApply(classes):
    #name should be a string
    #params should be a dict or list of dicts
    '''Runs puppet apply -e "classname {'name': params}".'''
    log = logging
    log.info("Puppet start")

    command = ["puppet", "apply", "-d", "-v", "--logdest",
               "/var/log/puppet/fuelmenu-puppet.log"]
    input = []
    # TODO(mattymo): Convert puppet resource types to consts
    for cls in classes:
        if cls['type'] == "literal":
            input.append(cls["name"])
            continue
        elif cls['type'] == "resource":
            input.extend([cls["class"], "{", '"%s":' % cls["name"]])
        elif cls['type'] == "class":
            input.extend(["class", "{", '"%s":' % cls["class"]])
        else:
            log.error("Invalid type %s" % cls['type'])
            return False
        #Build params
        for key, value in cls["params"].iteritems():
            if type(value) == bool:
                input.extend([key, "=>", '%s,' % str(value).lower()])
            else:
                input.extend([key, "=>", '"%s",' % value])
        input.append('}')

    log.debug(' '.join(command))
    log.debug(' '.join(input))
    code, out, err = execute(command, stdin=' '.join(input))
    if code != 0:
        log.error("Exit code: {0}. Error: {1} Stdout: {1}".format(
            code, err, out))
        return False
