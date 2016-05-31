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


def make_ordered_mapping(self, node, deep=False):
    if not isinstance(node, yaml.MappingNode):
        msg = 'node has to be an instance of yaml.MappingNode but it is {0}'
        raise yaml.ConstructorError(None,
                                    None,
                                    msg.format(type(node)),
                                    node.start_mark)

    kv = [(self.construct_object(key, deep=deep),
          self.construct_object(value, deep=deep))
          for key, value in node.value]

    first_unhashable = next((key for key, _ in kv
                             if not isinstance(key, collections.Hashable)),
                            None)
    if first_unhashable is not None:
        raise yaml.ConstructorError('During the construction of the mapping',
                                    node.start_mark,
                                    'found at least one unhashable key',
                                    first_unhashable.start_mark)

    return OrderedDict(kv)


def make_ordered_yaml_map(self, node):
    yield OrderedDict(self.construct_mapping(node))


def tell_best_node_style(key, value):

    return isinstance(key, yaml.ScalarNode) and not key.style and\
        isinstance(value, yaml.ScalarNode) and not value.style


def ordered_mapping_to_node(self, tag, mapping, flow_style=None):
    mapping_val = []

    mapping_node = yaml.MappingNode(tag, mapping_val, flow_style=flow_style)
    if self.alias_key is not None:
        self.represented_objects[self.alias_key] = mapping_node

    map_items = list(mapping.items()) if hasattr(mapping, 'items') else mapping

    for key, value in map_items:
        n_key = self.represent_data(key)
        n_value = self.represent_data(value)
        mapping_val.append((n_key, n_value))

        default_or_best = lambda: self.default_flow_style\
            if self.default_flow_style is not None else\
            tell_best_node_style(n_key, n_value)

        mapping_node.flow_style = flow_style if flow_style is not None\
            else default_or_best()

    return mapping_node


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
        except IOError:
            log.info("Unable to read YAML: %s", settings_file)
        except Exception:
            log.error("Malformed YAML: %s", settings_file)

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


yaml.constructor.BaseConstructor.construct_mapping = make_ordered_mapping
yaml.constructor.Constructor.add_constructor('tag:yaml.org,2002:map',
                                             make_ordered_yaml_map)

# Settings object is the instance of OrderedDict, so multi_representer
# of OrderedDict can handle both types (OrderedDict and Settings)
yaml.representer.Representer.add_multi_representer(
    OrderedDict,
    yaml.representer.SafeRepresenter.represent_dict
)
yaml.representer.BaseRepresenter.represent_mapping = ordered_mapping_to_node
