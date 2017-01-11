#    Copyright 2015 Mirantis, Inc.
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

import os
import shutil
import tempfile
import unittest

import mock
import yaml

from fuelmenu import settings as settings_module


class TestDictMege(unittest.TestCase):
    def test_dict_merge_simple(self):
        a = {'a': 1}
        b = {'b': 2}
        data = settings_module.dict_merge(a, b)
        self.assertEqual({'a': 1, 'b': 2}, data)

    def test_dict_merge_intended_behavior(self):
        """If b is not a dict, it is the result."""

        a = {'a': 1}
        b = None
        data = settings_module.dict_merge(a, b)
        self.assertEqual(None, data)

    def test_dict_merge_bad_data(self):
        """If a is not a dict, it should raise TypeError."""
        a = {'a': 1}
        b = None
        c = 1
        d = (1, 2, 3)
        e = {'A', 'B', 'C'}
        self.assertRaises(TypeError, settings_module.dict_merge, b, a)
        self.assertRaises(TypeError, settings_module.dict_merge, c, a)
        self.assertRaises(TypeError, settings_module.dict_merge, d, a)
        self.assertRaises(TypeError, settings_module.dict_merge, e, a)

    def test_dict_merge_override(self):
        a = {'a': {'c': 'val'}}
        b = {'b': 2, 'a': 'notval'}
        data = settings_module.dict_merge(a, b)
        self.assertEqual({'a': 'notval', 'b': 2}, data)


class TestSettings(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()

        yaml_file = os.path.join(self.directory, "__yamlfile.yaml")
        open(yaml_file, 'w').write("""
sample:
  one:
    a: b
    c: d
""")
        self.settings = settings_module.Settings()
        self.settings.load(yaml_file)

    def tearDown(self):
        shutil.rmtree(self.directory, ignore_errors=True)

    def test_read_settings(self):
        self.assertEqual(self.settings, {
            'sample': {
                'one': {
                    'a': 'b',
                    'c': 'd',
                }
            }
        })

    def test_merge_settings(self):
        yaml_file = os.path.join(self.directory, "yamlfile.yaml")
        open(yaml_file, 'w').write("""{sample: {one: {a: 666}}}""")

        self.settings.load(yaml_file)

        self.assertEqual(self.settings, {
            'sample': {
                'one': {
                    'a': 666,
                    'c': 'd',
                }
            }
        })

    @mock.patch('__builtin__.open', side_effect=Exception('Error'))
    def test_read_settings_with_error(self, _):
        data = settings_module.Settings()
        data.load('some_path')
        self.assertEqual(data, {})

    def test_write_settings(self):
        outfile = os.path.join(self.directory, 'out.yaml')
        self.settings.write(outfile)

        self.assertTrue(os.path.exists(outfile))
        self.assertTrue(yaml.safe_load(open(outfile)) == self.settings)
