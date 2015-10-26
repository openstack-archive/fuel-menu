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


def test_dict_merge_simple():
    a = {'a': 1}
    b = {'b': 2}
    data = utils.dict_merge(a, b)
    assert data == {'a': 1, 'b': 2}


def test_dict_merge_none():
    a = {'a': 1}
    b = None
    data = utils.dict_merge(a, b)
    assert data is None


def test_dict_merge_override():
    a = {'a': {'c': 'val'}}
    b = {'b': 2, 'a': 'notval'}
    data = utils.dict_merge(a, b)
    assert data == {'a': 'notval', 'b': 2}
