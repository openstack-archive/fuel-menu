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

from copy import deepcopy
import ordereddict


def dict_merge(a, b):
    """Recursively merges values in dicts from b into a

    All values in b override a:
    Example:
    x = {'a': {'b' : 'val'}}
    y = {'a': 'notval'}
    z = {'z': None}
    dict_merge(x, y) returns {'a': 'notval'}
    dict_merge(x, z) returns {'a': {'b': 'val'}, {'z': None}}
    dict_merge(z, x) returns {'z': None, 'a': {'b': 'val'}}

    :param a: the first dict
    :param b: any value
    :returns: the result dict (merge result of a and b)
    """
    if not isinstance(a, (dict, ordereddict.OrderedDict)):
        raise TypeError('First parameter is not a dict')

    result = deepcopy(a)
    try:
        for k, v in b.iteritems():
            if k in result and isinstance(result[k],
                                          (dict, ordereddict.OrderedDict)):
                result[k] = dict_merge(result[k], v)
            else:
                result[k] = deepcopy(v)
    except AttributeError:
        #Non-iterable objects should be just returned
        return b
    return result
