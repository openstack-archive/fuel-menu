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
import logging
import random as _random
import string
import subprocess

from fuelmenu import consts


log = logging.getLogger('fuelmenu.common.utils')
random = _random.SystemRandom()

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


def dict_merge(a, b):
    """Recursively merges values in dicts from b into a

    All values in b override a, even if b is not a dict:
    Example:
    x = {'a': {'b' : 'val'}}
    y = {'a': 'notval'}
    z = {'z': None}
    dict_merge(x, y) returns {'a': 'notval'}
    dict_merge(x, z) returns {'a': {'b': 'val'}, {'z': None}}
    dict_merge(z, x) returns {'z': None, 'a': {'b': 'val'}}

    :param a: the first dict
    :param b: any value
    :returns: resulting value of b merged into a, with b taking precedence
    """
    if not isinstance(a, (dict, OrderedDict)):
        raise TypeError('First parameter is not a dict')

    result = copy.deepcopy(a)
    try:
        for k, v in b.iteritems():
            if k in result and isinstance(result[k],
                                          (dict, OrderedDict)):
                result[k] = dict_merge(result[k], v)
            else:
                result[k] = copy.deepcopy(v)
    except AttributeError:
        # Non-iterable objects should be just returned
        return b
    return result


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


def gensalt():
    """Generate SHA-512 salt for crypt.crypt function."""
    letters = string.ascii_letters + string.digits + './'
    sha512prefix = "$6$"
    random_letters = ''.join(random.choice(letters) for _ in range(16))
    return sha512prefix + random_letters
