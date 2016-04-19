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

import os
import signal
import tempfile

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
        os_mock.path.isdir.return_value = False
        mode = utils.get_deployment_mode()
        self.assertEqual('pre', mode)

    @mock.patch('fuelmenu.common.utils.os')
    def test_get_deployment_mode_post(self, os_mock):
        os_mock.path.isdir.return_value = True
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

    def test_lock_running(self):
        lock_file = tempfile.mktemp()
        self.assertTrue(utils.lock_running(lock_file))

    def test_lock_running_fail(self):

        def handler(signum, frame):
            raise Exception("Timeout occured while running unit test "
                            "test_lock_running_fail")

        # set an alarm, because test may hang
        signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, 3)

        lock_file = tempfile.mktemp()

        read_fd1, write_fd1 = os.pipe()
        read_fd2, write_fd2 = os.pipe()
        pid = os.fork()
        if pid == 0:
            # Run lock_running in child first
            os.close(read_fd1)
            os.close(write_fd2)
            write_f1 = os.fdopen(write_fd1, 'w')
            read_f2 = os.fdopen(read_fd2, 'r')

            utils.lock_running(lock_file)

            write_f1.write('x')
            write_f1.close()
            read_f2.read()

            # exit from child by issuing execve, so that unit
            # testing framework will not finish in two instances
            os.execlp('true', 'true')
        else:
            # then in parent
            os.close(write_fd1)
            os.close(read_fd2)
            read_f1 = os.fdopen(read_fd1, 'r')
            write_f2 = os.fdopen(write_fd2, 'w')
            read_f1.read()

            # child is holding lock at this point
            self.assertFalse(utils.lock_running(lock_file))

            write_f2.write('x')
            write_f2.close()

            signal.alarm(0)
