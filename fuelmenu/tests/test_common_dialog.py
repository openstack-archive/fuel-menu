from fuelmenu.common.dialog import display_dialog
from fuelmenu.common.dialog import ModalDialog
from mock import Mock
from mock import patch
import unittest


class TestModalDialogBase(unittest.TestCase):
    def setUp(self):
        super(TestModalDialogBase, self).setUp()
        self.body = 'body'
        self.title = 'title'
        self.escape_key = 'escape-key'


class TestModalDialog(TestModalDialogBase):
    def setUp(self):
        super(TestModalDialog, self).setUp()
        self.previous_widget = Mock()
        self.loop = Mock()
        self.dialog = ModalDialog(self.title, self.body, self.escape_key,
                                  self.previous_widget, self.loop)

    def test_repr(self):
        self.assertEqual(
            repr(self.dialog),
            "<ModalDialog title='%s' at %s>" % (
                self.title, hex(id(self.dialog))))

    @patch('urwid.emit_signal')
    def test_close(self, m_emit):
        self.dialog.close(None)
        m_emit.assert_called_once_with(self.dialog, 'close')
        self.assertEqual(self.dialog.keep_open, False)
        self.assertEqual(self.dialog.loop.widget, self.previous_widget)


class TestDisplayDialog(TestModalDialogBase):
    def setUp(self):
        super(TestDisplayDialog, self).setUp()
        self.object = Mock(parent=Mock(mainloop=Mock(widget=Mock())))

    @patch('fuelmenu.common.dialog.ModalDialog', return_value=Mock())
    @patch('urwid.Pile', return_value=Mock())
    def test_display_dialog(self, m_pile, m_dialog):
        original_widget = self.object.parent.mainloop.widget
        self.assertEqual(
            m_dialog.return_value,
            display_dialog(self.object, self.body, self.title, self.escape_key)
        )

        m_pile.assert_called_once_with([self.body])
        m_dialog.assert_called_once_with(
            self.title, m_pile.return_value, self.escape_key,
            original_widget, self.object.parent.mainloop)
        self.assertEqual(
            self.object.parent.mainloop.widget, m_dialog.return_value)
