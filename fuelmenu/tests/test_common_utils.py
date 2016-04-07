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
import unittest


class TestUtils(unittest.TestCase):
    def make_process_mock(self, return_code=0, retval=('stdout', 'stderr')):
        process_mock = mock.Mock(
            communicate=mock.Mock(return_value=retval))
        process_mock.stdout = ['Stdout line 1', 'Stdout line 2']
        process_mock.returncode = return_code

        return process_mock

    @mock.patch('fuelmenu.common.utils.os')
    def test_get_deployment_mode_pre(self, os_mock):
        os_mock.path.isfile.return_value = False
        mode = utils.get_deployment_mode()
        self.assertEqual('pre', mode)

    @mock.patch('fuelmenu.common.utils.os')
    def test_get_deployment_mode_post(self, os_mock):
        os_mock.path.isfile.return_value = True
        mode = utils.get_deployment_mode()
        self.assertEqual('post', mode)

    @mock.patch('fuelmenu.common.utils.get_deployment_mode')
    def test_is_pre_deployment(self, utils_mock):
        utils_mock.return_value = "pre"
        data = utils.is_pre_deployment()
        self.assertEqual(data, True)

    @mock.patch('fuelmenu.common.utils.get_deployment_mode')
    def test_is_post_deployment(self, utils_mock):
        utils_mock.return_value = "pre"
        data = utils.is_post_deployment()
        self.assertEqual(data, False)

    def test_get_fuel_version(self):
        output = 'abc.xyz'
        with patch(
                '__builtin__.open',
                mock.mock_open(read_data=output),
                create=True
        ):
            data = utils.get_fuel_version()
            self.assertEqual(output, data)

    def test_get_fuel_version_with_exc(self):
        with patch(
                '__builtin__.open',
                mock.mock_open(),
                create=True
        ) as mocked_open:
            mocked_open.side_effect = IOError()
            data = utils.get_fuel_version()
            self.assertEqual("", data)
