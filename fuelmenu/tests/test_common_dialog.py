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

from fuelmenu.common import dialog


class TestModalDialogBase(unittest.TestCase):
    def setUp(self):
        super(TestModalDialogBase, self).setUp()
        self.body = 'body'
        self.title = 'title'
        self.escape_key = 'escape-key'


class TestModalDialog(TestModalDialogBase):
    def setUp(self):
        super(TestModalDialog, self).setUp()
        self.previous_widget = mock.Mock()
        self.loop = mock.Mock()
        self.dialog = dialog.ModalDialog(
            self.title, self.body, self.escape_key,
            self.previous_widget, self.loop)

    def test_repr(self):
        self.assertEqual(
            repr(self.dialog),
            "<ModalDialog title='%s' at %s>" % (
                self.title, hex(id(self.dialog))))

    @mock.patch('urwid.emit_signal')
    def test_close(self, m_emit):
        self.dialog.close(None)
        m_emit.assert_called_once_with(self.dialog, 'close')
        self.assertEqual(self.dialog.keep_open, False)
        self.assertEqual(self.dialog.loop.widget, self.previous_widget)


class TestDisplayDialog(TestModalDialogBase):
    def setUp(self):
        super(TestDisplayDialog, self).setUp()
        self.object = mock.Mock(
            parent=mock.Mock(mainloop=mock.Mock(widget=mock.Mock())))

    @mock.patch('fuelmenu.common.dialog.ModalDialog', return_value=mock.Mock())
    @mock.patch('urwid.Pile', return_value=mock.Mock())
    def test_display_dialog(self, m_pile, m_dialog):
        original_widget = self.object.parent.mainloop.widget
        self.assertEqual(
            m_dialog.return_value,
            dialog.display_dialog(
                self.object, self.body, self.title, self.escape_key)
        )

        m_pile.assert_called_once_with([self.body])
        m_dialog.assert_called_once_with(
            self.title, m_pile.return_value, self.escape_key,
            original_widget, self.object.parent.mainloop)
        self.assertEqual(
            self.object.parent.mainloop.widget, m_dialog.return_value)
