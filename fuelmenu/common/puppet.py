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
import re
import subprocess

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
    for cls in classes:
        if cls['type'] == "resource":
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
    output = ""
    try:
        proc, out, err = execute(command, stdin=' '.join(input))
    except subprocess.CalledProcessError as e:
        pattern = re.compile('(err:|\(err\):)')
        if pattern.match(output):
            log.error("Exit code: {0}. Output: {1}".format(e.returncode,
                                                           e.output))
            log.exception("Puppet apply errored")
        else:
            log.exception("Puppet apply failed for unknown reason")
        return False
