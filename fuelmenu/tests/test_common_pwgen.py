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

from fuelmenu.common.pwgen import password
import string
from unittest import TestCase


class TestPassword(TestCase):
    def test_password(self):
        chars = string.letters + string.digits
        cases = [
            ('10', 10),
            (None, 8),
            ('test', 8)
        ]

        for arg, length in cases:
            result = password(arg)
            for char in result:
                self.assertIn(char, chars)
            self.assertEqual(len(result), length)
