# Copyright 2016 Mirantis, Inc.
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

import mock
import unittest

from fuelmenu.common import replace


def custom_mock_open(lines):
    """Customizing mock open

    :param lines: list of lines
    :return: mock object
    """
    m_open = mock.mock_open()
    m_open.return_value.readlines.return_value = [
        '{}\n'.format(line) for line in lines
    ]
    return m_open


class TestReplace(unittest.TestCase):
    def setUp(self):
        super(TestReplace, self).setUp()
        self.data = ['line1', 'line2', 'line3']

    def test_replace(self):
        filename = 'filename'
        with mock.patch('__builtin__.open', custom_mock_open(self.data)) \
                as m_open:
            replace.replaceInFile(filename, 'line2', 'line4')
            self.assertEqual(m_open.call_args_list,
                             [mock.call(filename), mock.call(filename, 'w')])
            m_open.return_value.write.assert_called_once_with(
                'line1\nline4\nline3\n')
