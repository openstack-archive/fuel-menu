# -*- coding: utf-8 -*-

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

from fuelmenu.common import utils

import mock
from mock import patch
import subprocess
import unittest


class TestUtils(unittest.TestCase):

    def test_dict_merge_simple(self):
        a = {'a': 1}
        b = {'b': 2}
        data = utils.dict_merge(a, b)
        self.assertEqual({'a': 1, 'b': 2}, data)

    def test_dict_merge_intended_behavior(self):
        """If b is not a dict, it is the result."""

        a = {'a': 1}
        b = None
        data = utils.dict_merge(a, b)
        self.assertEqual(None, data)

    def test_dict_merge_bad_data(self):
        """If a is not a dict, it should raise TypeError."""
        a = {'a': 1}
        b = None
        c = 1
        d = (1, 2, 3)
        e = set(['A', 'B', 'C'])
        self.assertRaises(TypeError, utils.dict_merge, b, a)
        self.assertRaises(TypeError, utils.dict_merge, c, a)
        self.assertRaises(TypeError, utils.dict_merge, d, a)
        self.assertRaises(TypeError, utils.dict_merge, e, a)

    def test_dict_merge_override(self):
        a = {'a': {'c': 'val'}}
        b = {'b': 2, 'a': 'notval'}
        data = utils.dict_merge(a, b)
        self.assertEqual({'a': 'notval', 'b': 2}, data)

    def make_process_mock(self, return_code=0, retval=('stdout', 'stderr')):
        process_mock = mock.Mock(
            communicate=mock.Mock(return_value=retval))
        process_mock.stdout = ['Stdout line 1', 'Stdout line 2']
        process_mock.returncode = return_code

        return process_mock

    def test_get_deployment_mode_pre(self):
        process_mock = self.make_process_mock(return_code=0)
        with patch.object(subprocess, 'Popen', return_value=process_mock):
            mode = utils.get_deployment_mode()
            process_mock.communicate.assert_called_once_with()
            self.assertEqual('pre', mode)

    def test_get_deployment_mode_post(self):
        output = 'fuel-core-8.0-rabbitmq'
        process_mock = self.make_process_mock(return_code=0,
                                              retval=(output, ''))
        with patch.object(subprocess, 'Popen', return_value=process_mock):
            mode = utils.get_deployment_mode()
            process_mock.communicate.assert_called_once_with()
            self.assertEqual('post', mode)
