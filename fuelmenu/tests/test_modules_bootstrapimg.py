#    Copyright 2017 Mirantis, Inc.
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

from mock import patch
from requests import adapters

from fuelmenu.modules import bootstrapimg
from fuelmenu.tests import base


class TestBootstrapImg(base.BaseModuleTests):

    def setUp(self, responses=None):
        super(TestBootstrapImg, self).setUp()
        if responses:
            self.responses = responses
        self.module = bootstrapimg.BootstrapImage(self.parent)
        # unset proxy settings before start
        os.environ['HTTP_PROXY'] = ''
        os.environ['NO_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''

    @patch.object(adapters.HTTPAdapter, 'send')
    def test_check_url_without_proxies(self, send_mock):
        self.module.check_url('http://some_url')
        # send_mock = mock.MagicMock()

        call_args = send_mock.call_args_list
        self.assertEqual(1, len(call_args))
        call_args = call_args[0]

        args, kwargs = call_args
        self.assertIn('proxies', kwargs)
        self.assertNotIn('http', kwargs['proxies'])
        self.assertNotIn('https', kwargs['proxies'])

    @patch.object(adapters.HTTPAdapter, 'send')
    def test_check_url_with_proxies(self, send_mock):
        http_proxy_url = 'http://http_proxy_url'
        https_proxy_url = 'https://https_proxy_url'
        os.environ['HTTP_PROXY'] = http_proxy_url
        os.environ['HTTPS_PROXY'] = https_proxy_url
        self.module.check_url('http://some_url')
        # send_mock = mock.MagicMock()

        call_args = send_mock.call_args_list
        self.assertEqual(1, len(call_args))
        call_args = call_args[0]

        args, kwargs = call_args
        self.assertIn('proxies', kwargs)
        self.assertIn('http', kwargs['proxies'])
        self.assertIn('https', kwargs['proxies'])
        self.assertEqual(kwargs['proxies']['http'],
                         http_proxy_url)
        self.assertEqual(kwargs['proxies']['https'],
                         https_proxy_url)

    @patch.object(adapters.HTTPAdapter, 'send')
    def test_check_url_with_no_proxy(self, send_mock):
        http_proxy_url = 'http://http_proxy_url'
        https_proxy_url = 'https://https_proxy_url'
        os.environ['HTTP_PROXY'] = http_proxy_url
        os.environ['HTTPS_PROXY'] = https_proxy_url
        os.environ['NO_PROXY'] = 'direct_url'
        self.module.check_url('http://direct_url')
        # send_mock = mock.MagicMock()

        call_args = send_mock.call_args_list
        self.assertEqual(1, len(call_args))
        call_args = call_args[0]

        args, kwargs = call_args
        self.assertIn('proxies', kwargs)
        self.assertNotIn('http', kwargs['proxies'])
        self.assertNotIn('https', kwargs['proxies'])
