# -*- coding: utf-8 -*-

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
import unittest

from fuelmenu.common import puppet


@mock.patch('fuelmenu.common.puppet.logging')
@mock.patch('fuelmenu.common.puppet.utils.execute',
            return_value=(0, 'Success', 0))
class TestPuppetApply(unittest.TestCase):
    def setUp(self):
        super(TestPuppetApply, self).setUp()
        self.command = ["puppet", "apply", "-d", "-v", "--logdest",
                        "/var/log/puppet/fuelmenu-puppet.log"]
        self.input = (
            'literal_1 class_1 { "resource_1": resource_k1 => "Resource_v1", }'
            ' class { "class_1": class_k3 => true, }'
        )
        self.classes = [
            {
                'type': 'literal',
                'name': 'literal_1',
                'params': {
                    'literal_k1': 'Literal_v1',
                }
            },
            {
                'type': 'resource',
                'name': 'resource_1',
                'class': 'class_1',
                'params': {
                    'resource_k1': 'Resource_v1',
                }
            },
            {
                'type': 'class',
                'class': 'class_1',
                'params': {
                    'class_k3': True
                }
            }
        ]

    def test_puppet_apply(self, m_execute, m_log):
        self.assertEqual(puppet.puppetApply(self.classes), True)
        m_execute.assert_called_once_with(self.command, stdin=self.input)
        m_log.info.assert_called_once_with('Puppet start')
        self.assertFalse(m_log.error.called)

    def test_incorrect_type(self, m_execute, m_log):
        self.classes.append({
            'type': 'incorrect',
            'name': 'incorrect name',
            'class': 'class_2',
            'params': {}
        })
        self.assertEqual(puppet.puppetApply(self.classes), False)
        self.assertFalse(m_execute.called)
        m_log.error.assert_called_once_with('Invalid type %s', 'incorrect')

    def test_execute_failure(self, m_execute, m_log):
        res = (1, 'Fail', 5)
        m_execute.return_value = res
        self.assertEqual(puppet.puppetApply(self.classes), False)
        m_log.error.assert_called_once_with(
            'Exit code: %d. Error: %s Stdout: %s', res[0], res[2], res[1])
