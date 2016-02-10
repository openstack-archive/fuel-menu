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

from fuelmenu.common.replace import replaceInFile
from mock import patch
from unittest import TestCase


@patch('fuelmenu.common.replace.logging')
@patch('fuelmenu.common.replace.execute')
class TestReplace(TestCase):
    def setUp(self):
        super(TestReplace, self).setUp()
        self.filename = 'filename'
        self.command = ['sed', 's/line1/line2/g', '-i', self.filename]

    def _check(self, m_execute, args):
        m_execute.return_value = args
        self.assertEqual(replaceInFile(self.filename, 'line1', 'line2'), None)
        m_execute.assert_called_once_with(self.command)

    def test_replace(self, m_execute, m_log):
        self._check(m_execute, (0, '', ''))
        self.assertFalse(m_log.error.called)

    def test_replace_failure(self, m_execute, m_log):
        self._check(m_execute, (1, '', 'Error'))
        m_log.error.assert_called_once_with(
            'Replacing in file failed. Exit code: %d. Error: %s', 1, 'Error')
