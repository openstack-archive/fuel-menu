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

from fuelmenu import consts

import logging
import subprocess

log = logging.getLogger('fuelmenu.common.utils')


def get_deployment_mode():
    """Report if any fuel containers are already created."""
    command = ['docker', 'ps', '-a']
    try:
        _, output, _ = execute(command)
        if "fuel" in output.lower():
            return consts.POST_DEPLOYMENT_MODE
        else:
            return consts.PRE_DEPLOYMENT_MODE
    except OSError:
        log.warning('Unable to check deployment mode via docker. Assuming'
                    ' pre-deployment stage.')
        return consts.PRE_DEPLOYMENT_MODE


def is_pre_deployment():
    """Return True if current deployment mode is pre."""
    return get_deployment_mode() == consts.PRE_DEPLOYMENT_MODE


def is_post_deployment():
    """Return True if current deployment mode is post."""
    return get_deployment_mode() == consts.POST_DEPLOYMENT_MODE


def get_fuel_version(versionfile=consts.RELEASE_FILE):
    """Read version from versionfile or return empty string."""
    try:
        with open(versionfile, 'r') as f:
            return f.read().strip()
    except IOError:
        log.error("Unable to set Fuel version from %s" % versionfile)
        return ""


def execute(command, stdin=None, shell=False):
    """Executes commands

    :param command: A list of shell lexemes
    :param shell: Specify shell parameter for subprocess.Popen (optional)
    :param stdin: String input for stdin (optional)

    :returns: Tuple of (return_code, stdout, stderr)
    """

    log.debug('Executing command: {0}'.format(' '.join(command)))
    proc = subprocess.Popen(command,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=shell)
    out, err = proc.communicate(input=stdin)
    code = proc.poll()
    log.debug('Command executed with exit code: {0}'.format(str(code)))
    return code, out, err
