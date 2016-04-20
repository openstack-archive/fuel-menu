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

import collections
import copy
import logging
from string import Template

try:
    from collections import OrderedDict
except Exception:
    # python 2.6 or earlier use backport
    from ordereddict import OrderedDict

import yaml

log = logging.getLogger('fuelmenu.settings')


def construct_ordered_mapping(self, node, deep=False):
    if not isinstance(node, yaml.MappingNode):
        raise yaml.ConstructorError(None, None,
                                    "expected a mapping node, but found %s" %
                                    node.id, node.start_mark)
    mapping = OrderedDict()
    for key_node, value_node in node.value:
        key = self.construct_object(key_node, deep=deep)
        if not isinstance(key, collections.Hashable):
            raise yaml.ConstructorError(
                "while constructing a mapping", node.start_mark,
                "found unhashable key", key_node.start_mark)
        value = self.construct_object(value_node, deep=deep)
        mapping[key] = value
    return mapping
yaml.constructor.BaseConstructor.construct_mapping = construct_ordered_mapping


def construct_yaml_map_with_ordered_dict(self, node):
    data = OrderedDict()
    yield data
    value = self.construct_mapping(node)
    data.update(value)
yaml.constructor.Constructor.add_constructor(
    'tag:yaml.org,2002:map',
    construct_yaml_map_with_ordered_dict)


def represent_ordered_mapping(self, tag, mapping, flow_style=None):
    value = []
    node = yaml.MappingNode(tag, value, flow_style=flow_style)
    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = node
    best_style = True
    if hasattr(mapping, 'items'):
        mapping = list(mapping.items())
    for item_key, item_value in mapping:
        node_key = self.represent_data(item_key)
        node_value = self.represent_data(item_value)
        if not (isinstance(node_key, yaml.ScalarNode) and not node_key.style):
            best_style = False
        if not (isinstance(node_value, yaml.ScalarNode)
                and not node_value.style):
            best_style = False
        value.append((node_key, node_value))
    if flow_style is None:
        if self.default_flow_style is not None:
            node.flow_style = self.default_flow_style
        else:
            node.flow_style = best_style
    return node

# Settings object is the instance of OrderedDict, so multi_representer
# of OrderedDict can handle both types (OrderedDict and Settings)
yaml.representer.Representer.add_multi_representer(
    OrderedDict, yaml.representer.SafeRepresenter.represent_dict)
yaml.representer.BaseRepresenter.represent_mapping = represent_ordered_mapping


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


class Settings(OrderedDict):
    def load(self, settings_file, template_kwargs=None):
        """Load setting from file and merge them to existing object

        settings_file: path to setings.yaml file

        template_kwargs: dict with parameters that will be placed
        instead labeles in settings file before yaml parsing
        """
        try:
            with open(settings_file) as infile:
                settings = yaml.load(Template(
                    infile.read()).safe_substitute(template_kwargs or {}))

                self.merge(settings)
        except Exception:
            log.info("Unable to read YAML: %s", settings_file)

        return self

    def write(self, outfn='mysettings.yaml'):
        """Write settings to file."""
        with open(outfn, 'w') as outfile:
            yaml.dump(self, outfile, default_style='"',
                      default_flow_style=False)
            return True

    def merge(self, other):
        """Merge this settings object with other."""
        self.update(dict_merge(self, other))
