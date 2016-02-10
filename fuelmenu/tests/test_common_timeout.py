#    Copyright 2016 Mirantis, Inc.
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

import mock
import time
import unittest

from fuelmenu.common import timeout


class TestRunWithTimeout(unittest.TestCase):
    def test_run_with_timeout_default(self):
        method = mock.Mock(return_value='result')
        self.assertEqual('result', timeout.run_with_timeout(method))
        method.assert_called_once_with()

    def test_run_with_params(self):
        method = mock.Mock(return_value='result')
        self.assertEqual(
            'result', timeout.run_with_timeout(method, ('a1',), {'k1': 'v1'}))
        method.assert_called_once_with('a1', k1='v1')

    def test_run_with_timeout_reached(self):
        self.assertEqual(
            'result',
            timeout.run_with_timeout(
                time.sleep, (2,), timeout=1, default='result'))

    def test_run_with_zero_timeout(self):
        method = mock.Mock(return_value='result')
        self.assertEqual('result', timeout.run_with_timeout(method, timeout=0))
        method.assert_called_once_with()
