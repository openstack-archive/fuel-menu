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
import netifaces
import unittest

from fuelmenu.common import modulehelper


def custom_mock_open(lines):
    """Customizing mock open, add __iter__

    :param lines: list of lines
    :return: mock object
    """
    m_open = mock.mock_open()
    m_open.return_value.__iter__.return_value = iter(lines)
    m_open.return_value.readlines.return_value = lines
    return m_open


class TestModuleHelperBase(unittest.TestCase):
    def setUp(self):
        super(TestModuleHelperBase, self).setUp()
        self.helper = modulehelper.ModuleHelper()
        self.modobj = mock.Mock()
        self.default_data = {
            'label': 'label1'
        }

    def _check(self, method, expected, *args, **kwargs):
        self.assertEqual(
            getattr(self.helper, method)(*args, **kwargs),
            expected)

    def _run(self, method, *args, **kwargs):
        self._check(method, None, *args, **kwargs)

    def _check_raise(self, method, exception, *args, **kwargs):
        self.assertRaises(
            exception,
            getattr(self.helper, method), *args, **kwargs)


class TestModuleHelperGet(TestModuleHelperBase):
    def setUp(self):
        super(TestModuleHelperGet, self).setUp()
        self.settings = {'key1': {'key2': 'value'}}

    def test_get_setting(self):
        cases = [
            ('key1', {'key2': 'value'}),
            ('key1/key2', 'value')
        ]
        for key, result in cases:
            self._check('get_setting', result, self.settings, key)

    def test_get_setting_incorrect_path(self):
        cases = (
            '',
            'incorrect_key',
            'key1/incorrect_key',
            'key1/key2/key3'
        )
        for incorrect_key in cases:
            self._check_raise('get_setting', KeyError,
                              self.settings, incorrect_key)


@mock.patch('fuelmenu.settings.Settings.read', side_effect=lambda x: x)
@mock.patch('fuelmenu.common.modulehelper.ModuleHelper.get_setting',
            return_value='loaded')
class TestModuleHelperLoad(TestModuleHelperBase):
    def setUp(self):
        super(TestModuleHelperLoad, self).setUp()
        self.modobj.defaults = dict()
        self.modobj.parent = mock.Mock()
        self.modobj.parent.defaultsettingsfile = {'key1': 'value1'}
        self.modobj.parent.settingsfile = {'key2': 'value2'}

    def test_load_types_skipping(self, *_):
        widget_types = {
            modulehelper.WidgetType.BUTTON: 'skipped',
            modulehelper.WidgetType.CHECKBOX: 'loaded',
            modulehelper.WidgetType.LABEL: 'skipped',
            modulehelper.WidgetType.LIST: 'loaded',
            modulehelper.WidgetType.RADIO: 'loaded',
            modulehelper.WidgetType.TEXT_FIELD: 'loaded'
        }

        for index, widget_type in enumerate(widget_types):
            self.modobj.defaults.update({
                index: {
                    'type': widget_type,
                    'value': 'skipped'
                },
            })

        self._check('load', {'key2': 'value2', 'key1': 'value1'},
                    self.modobj)
        for _, setting in self.modobj.defaults.items():
            self.assertEqual(
                widget_types[setting['type']], setting['value'],
                'Widget type with id "{0}" should be {1}'.format(
                    setting['type'], widget_types[setting['type']]))

    def test_load_ignored_params(self, *_):
        self.modobj.defaults.update({
            1: {'value': 'skipped', 'should': 'skipped'},
            2: {'value': 'skipped', 'should': 'loaded'},
            3: {'value': 'skipped', 'should': 'skipped'},
        })
        ignores = [1, 3]
        self._check('load', {'key2': 'value2', 'key1': 'value1'},
                    self.modobj, ignores)

        for _, setting in self.modobj.defaults.items():
            self.assertEqual(setting['value'], setting['should'])

    @mock.patch('logging.Logger.warning')
    def test_load_value_from_settings_failed(
            self, m_warning, m_get_setting, *_):
        m_get_setting.side_effect = KeyError
        self.modobj.defaults.update({'key': {'value': ''}})
        self._check('load', {'key2': 'value2', 'key1': 'value1'},
                    self.modobj)
        self.assertEqual(self.modobj.defaults['key']['value'], '')
        m_warning.assert_called_once_with(
            "Failed to load %s value from settings", 'key')

    def test_load_settings(self, *_):
        self._check('load', {'key1': 'value1', 'key2': 'value2'}, self.modobj)


@mock.patch('fuelmenu.common.modulehelper.ModuleHelper.set_setting',
            return_value='')
class TestModuleHelperSave(TestModuleHelperBase):
    def setUp(self):
        super(TestModuleHelperSave, self).setUp()
        self.modobj.oldsettings = mock.Mock()

    def test_save(self, m_set_setting):
        responses = {
            'key1': 'value1',
            'key2': 'value2'
        }
        self._check('save', {}, self.modobj, responses)
        for key, value in responses.items():
            m_set_setting.assert_any_call(
                {}, key, value, self.modobj.oldsettings)


class TestModuleHelperCancel(TestModuleHelperBase):
    def setUp(self):
        super(TestModuleHelperCancel, self).setUp()
        self.modobj.fields = ['some_field']
        self.modobj.defaults = {'some_field': {'value': 'some_field'}}
        self.edit = mock.Mock()
        self.edit.set_edit_text = mock.Mock()
        self.modobj.edits = [self.edit, self.edit]

    def test_cancel(self):
        self._run('cancel', self.modobj)
        self.edit.set_edit_text.assert_called_once_with(
            self.modobj.defaults['some_field']['value'])

    @mock.patch('logging.Logger.warning')
    def test_cancel_attribute_error(self, m_warning):
        self.edit.set_edit_text.side_effect = AttributeError
        self._run('cancel', self.modobj)
        m_warning.assert_called_once_with(
            "Field %s unable to reset text", self.modobj.fields[0])

    def test_cancel_skipping_fields(self):
        self.modobj.fields = [modulehelper.BLANK_KEY, 'label1']
        self.modobj.defaults = {
            modulehelper.BLANK_KEY: {'value': 'blank'},
            'label1': {'value': 'label1'}}

        self._run('cancel', self.modobj)
        self.assertFalse(self.edit.set_edit_text.called)


@mock.patch('fuelmenu.common.urwidwrapper.SimpleListWalker',
            return_value=mock.Mock())
@mock.patch('fuelmenu.common.urwidwrapper.WalkerStoredListBox',
            return_value=mock.Mock())
@mock.patch('urwid.BoxAdapter', return_value=mock.Mock())
@mock.patch('fuelmenu.common.modulehelper.ModuleHelper._create_widget',
            return_value=mock.Mock(rows=mock.Mock(return_value=0)))
@mock.patch('urwid.Text',
            return_value=mock.Mock(rows=mock.Mock(return_value=0)))
class TestModuleHelperCreateListWidget(TestModuleHelperBase):
    def setUp(self):
        super(TestModuleHelperCreateListWidget, self).setUp()
        self.toolbar = mock.Mock()
        modulehelper.blank = mock.Mock()
        modulehelper.blank.rows = mock.Mock(return_value=0)

    def test_create_list_widget(
            self, m_text, m_create_widget, m_box, m_listbox, m_walker):
        self.default_data.update({
            'value': [{'l1': 'vl1'}, {'l1': 'vl2'}],
            'value_scheme': {'l1': {'value': ''}}
        })

        self._check('_create_list_widget', m_box.return_value,
                    self.default_data, self.toolbar)
        m_text.assert_called_once_with(self.default_data['label'])
        # Called twice for two elements
        m_create_widget.assert_has_calls([
            mock.call('l1', {'value': 'vl1'}, self.toolbar),
            mock.call('l1', {'value': 'vl2'}, self.toolbar)
        ])
        # Called twice for two elements and third on exit
        m_listbox.assert_has_calls(
            [mock.call(m_walker.return_value)] * 3
        )
        # Called twice for two elements and third on exit
        m_walker.assert_has_calls(
            [mock.call([m_create_widget.return_value, modulehelper.blank])] * 2
            + [mock.call([m_text.return_value] + [m_box.return_value] * 2)]
        )
        # Called twice for two elements and third on exit
        m_box.assert_has_calls([mock.call(m_listbox.return_value, 0)] * 3)

    def test_create_list_widget_default(
            self, m_text, m_create_widget, m_box, m_listbox, m_walker):
        self._check('_create_list_widget', m_box.return_value,
                    {}, self.toolbar)
        self.assertFalse(m_text.called)
        self.assertFalse(m_create_widget.called)
        # Called once in the end
        m_listbox.assert_called_once_with(m_walker.return_value)
        m_walker.assert_called_once_with([])
        m_box.assert_called_once_with(m_listbox.return_value, 0)


@mock.patch('fuelmenu.common.urwidwrapper.TextLabel',
            return_value='text_label')
@mock.patch('fuelmenu.common.urwidwrapper.ChoicesGroup',
            return_value=mock.Mock())
@mock.patch('fuelmenu.common.urwidwrapper.Columns', return_value=mock.Mock())
class TestModuleHelperCreateRadioButtonWidget(TestModuleHelperBase):
    def test_create_radiobutton_widget(
            self, m_columns, m_choices, m_label):
        self.default_data.update({
            'callback': 'my_callback',
            'choices': ["Apply", "Cancel"],
        })
        self._check('_create_radiobutton_widget', m_columns.return_value,
                    self.default_data)
        m_label.assert_called_once_with(self.default_data['label'])
        m_choices.assert_called_once_with(
            self.default_data['choices'],
            default_value=self.default_data['choices'][0],
            fn=self.default_data['callback'])
        m_columns.assert_called_once_with(
            [('weight', 2, m_label.return_value),
             ('weight', 3, m_choices.return_value)])

    def test_create_radiobutton_widget_default_choices_and_callback(
            self, m_columns, m_choices, m_label):
        self._check('_create_radiobutton_widget', m_columns.return_value,
                    self.default_data)
        m_label.assert_called_once_with(self.default_data['label'])
        m_choices.assert_called_once_with(
            ['Yes', 'No'],
            default_value='Yes',
            fn=None)
        m_columns.assert_called_once_with(
            [('weight', 2, m_label.return_value),
             ('weight', 3, m_choices.return_value)])


@mock.patch('fuelmenu.common.urwidwrapper.Button', return_value=mock.Mock())
@mock.patch('fuelmenu.common.urwidwrapper.Columns', return_value=mock.Mock())
class TestModuleHelperCreateButtonWidget(TestModuleHelperBase):
    def test_create_button_widget(self, m_columns, m_button):
        self.default_data.update(callback='my_callback')
        self._check('_create_button_widget', m_columns.return_value,
                    self.default_data)
        m_button.assert_called_once_with(
            self.default_data['label'],
            self.default_data['callback'])
        m_columns.assert_called_once_with([m_button.return_value])

    def test_create_button_widget_default(self, m_columns, m_button):
        self._check('_create_button_widget', m_columns.return_value, {})
        m_button.assert_called_once_with('', None)
        m_columns.assert_called_once_with([m_button.return_value])


@mock.patch('fuelmenu.common.urwidwrapper.CheckBox', return_value=mock.Mock())
class TestModuleHelperCreateCheckBoxWidget(TestModuleHelperBase):
    def test_create_checkbox_widget(self, m_checkbox):
        self.default_data.update({
            'callback': 'my_callback',
            'value': True,
        })
        self._check('_create_checkbox_widget', m_checkbox.return_value,
                    self.default_data)
        m_checkbox.assert_called_once_with(
            self.default_data['label'],
            state=self.default_data['value'],
            callback=self.default_data['callback'])

    def test_create_checkbox_widget_state_false_without_callback(
            self, m_checkbox):
        self._check('_create_checkbox_widget', m_checkbox.return_value,
                    self.default_data)
        m_checkbox.assert_called_once_with(
            self.default_data['label'], state=False, callback=None)


@mock.patch('fuelmenu.common.urwidwrapper.TextField', return_value=mock.Mock())
class TestModuleHelperCreateTextWidget(TestModuleHelperBase):
    def setUp(self):
        super(TestModuleHelperCreateTextWidget, self).setUp()
        self.toolbar = mock.Mock()

    def test_create_widget_text_field(self, m_text_label):
        key = 'password'
        self.default_data.update({
            'value': 'value1',
            'tooltip': 'tooltip1'
        })
        self._check('_create_widget', m_text_label.return_value,
                    key, self.default_data, self.toolbar)
        m_text_label.assert_called_once_with(
            key, self.default_data['label'],
            width=23,
            default_value=self.default_data['value'],
            tooltip=self.default_data['tooltip'],
            toolbar=self.toolbar,
            ispassword=True)

    def test_create_widget_text_field_default(self, m_text_label):
        key = ''
        default_data = {}
        self._check('_create_widget', m_text_label.return_value,
                    key, default_data, self.toolbar)
        m_text_label.assert_called_once_with(
            key, '',
            width=23,
            default_value='',
            tooltip='',
            toolbar=self.toolbar,
            ispassword=False)


@mock.patch('fuelmenu.common.urwidwrapper.Columns', return_value=mock.Mock())
@mock.patch('fuelmenu.common.urwidwrapper.Button', return_value=mock.Mock())
class TestModuleHelperCheckColumns(TestModuleHelperBase):
    def setUp(self):
        super(TestModuleHelperCheckColumns, self).setUp()
        self.modobj.check = mock.Mock()
        self.modobj.cancel = mock.Mock()
        self.modobj.apply = mock.Mock()
        self.modobj.parent = mock.Mock(globalsave=False)
        modulehelper.blank = mock.Mock()

    def test_get_check_column_all_buttons(self, m_button, m_columns):
        self._check('_get_check_column', m_columns.return_value,
                    self.modobj, True)
        m_button.assert_has_calls(
            [
                mock.call("Check", self.modobj.check),
                mock.call("Cancel", self.modobj.cancel),
                mock.call("Apply", self.modobj.apply)
            ],
            any_order=False
        )
        m_columns.assert_called_once_with(
            [m_button.return_value] * 3 +
            [('weight', 2, modulehelper.blank)]
        )

    def test_get_check_column_global_save_true(
            self, m_button, m_columns):
        self.modobj.parent.globalsave = True
        self._check('_get_check_column', m_columns.return_value,
                    self.modobj, False)
        m_button.assert_called_once_with("Check", self.modobj.check)
        m_columns.assert_called_once_with([m_button.return_value])


class TestModuleHelper(TestModuleHelperBase):
    def test_set_setting(self):
        cases = [
            (
                {}, 'key1', 'value1',
                {'key1': 'value1'}
            ),
            (
                {}, 'key1/key2', 'value2',
                {'key1': {'key2': 'value2'}}
            ),
            (
                {'key1': {}}, 'key1/key2', 'value2',
                {'key1': {'key2': 'value2'}}
            )
        ]
        for settings, key, value, expected in cases:
            self._run('set_setting', settings, key, value)
            self.assertEqual(settings, expected)

    def test_set_settings_fails(self):
        cases = [
            ({'key1': 'value'}, 'key1/key2', ''),
            ('key1_string', 'key1/key2', ''),
            ('key1_string', 'key1', ''),
        ]
        for settings, key, value in cases:
            self._check_raise('set_setting', TypeError, settings, key, value)

    def test_set_setting_with_default(self):
        settings = dict()
        self._run('set_setting', settings, 'key1/key2', 'new_value',
                  {'key1': {'key2': 'value2', 'key3': 'value3'}})
        self.assertEqual(
            settings, {'key1': {'key2': 'new_value', 'key3': 'value3'}})

    def test_set_setting_with_default_failed(self):
        settings = dict()
        self._check_raise('set_setting', TypeError,
                          settings, 'key1/key2', 'new_value', 'key1_string')

    def test_create_widget(self):
        toolbar = mock.Mock()
        key = 'password'
        cases = [
            (
                modulehelper.WidgetType.CHECKBOX,
                'modulehelper.ModuleHelper._create_checkbox_widget',
                (self.default_data,)
            ),
            (
                modulehelper.WidgetType.RADIO,
                'modulehelper.ModuleHelper._create_radiobutton_widget',
                (self.default_data,)
            ),
            (
                modulehelper.WidgetType.LABEL,
                'urwidwrapper.TextLabel',
                (self.default_data['label'],)
            ),
            (
                modulehelper.WidgetType.LIST,
                'modulehelper.ModuleHelper._create_list_widget',
                (self.default_data, toolbar)
            ),
            (
                modulehelper.WidgetType.BUTTON,
                'modulehelper.ModuleHelper._create_button_widget',
                (self.default_data,)
            ),
        ]

        for widget_type, mock_function, arguments in cases:
            with mock.patch('fuelmenu.common.%s' % mock_function,
                            return_value=mock.Mock()) as m_function:
                self.default_data['type'] = widget_type
                self._check('_create_widget', m_function.return_value,
                            key, self.default_data, toolbar)
                m_function.assert_called_once_with(*arguments)

    @mock.patch('fuelmenu.common.urwidwrapper.TextLabel', return_value='txt')
    @mock.patch('fuelmenu.common.dialog.display_dialog')
    def test_display_dialog(self, m_display_dialog, m_text_label):
        error_msg = 'error'
        title = 'tittle'
        self._run('display_dialog', self.modobj, error_msg, title)
        m_text_label.assert_called_once_with(error_msg)
        m_display_dialog.assert_called_once_with(self.modobj, 'txt', title)

    @mock.patch('fuelmenu.common.modulehelper.ModuleHelper.display_dialog')
    def test_display_failed_check_dialog(self, m_display_dialog):
        self.modobj.name = 'modname'
        errors = ['error1', 'error2']
        self._run('display_failed_check_dialog', self.modobj, errors)
        m_display_dialog.assert_called_once_with(
            self.modobj,
            "Errors:\n  error1\n  error2",
            "Check failed in module modname")

    def test_create_widget_blank(self):
        modulehelper.blank = mock.Mock()
        self._check('_create_widget', modulehelper.blank,
                    modulehelper.BLANK_KEY, {}, None)

    @mock.patch('urwid.Text', return_value=mock.Mock())
    def test_get_header_content(self, m_text):
        other = mock.Mock()
        header_text = ['text', other]
        self._check(
            '_get_header_content', [m_text.return_value, other], header_text)

    @mock.patch('fuelmenu.common.modulehelper.ModuleHelper._create_widget',
                return_value=mock.Mock())
    def test_setup_widgets(self, m_create_widget):
        toolbar = mock.Mock()
        fields = ['key1', 'key2']
        value = mock.Mock()
        defaults = {'key1': value}
        self._check(
            'setup_widgets',
            [m_create_widget.return_value] * 2,
            toolbar, fields, defaults)

        m_create_widget.assert_has_calls([
            mock.call('key1', value, toolbar),
            mock.call('key2', {}, toolbar)])

    @mock.patch('netifaces.ifaddresses')
    def test_get_iface_info(self, m_ifaddresses):
        iface = 'eth0'
        address_family = 'AF1'
        m_ifaddresses.return_value = {address_family: ['value']}
        self._check('_get_iface_info', 'value', iface, address_family)
        m_ifaddresses.assert_called_once_with(iface)


@mock.patch('fuelmenu.common.modulehelper.log.debug')
@mock.patch('fuelmenu.common.modulehelper.ModuleHelper._get_header_content',
            return_value=['header'])
@mock.patch('fuelmenu.common.modulehelper.ModuleHelper.setup_widgets',
            return_value=['edit'])
@mock.patch('fuelmenu.common.urwidwrapper.TabbedListWalker',
            return_value=mock.Mock())
@mock.patch('urwid.ListBox', return_value=mock.Mock())
@mock.patch('fuelmenu.common.modulehelper.ModuleHelper._get_check_column',
            return_value='buttons')
class TestScreenUI(TestModuleHelperBase):
    def setUp(self):
        super(TestScreenUI, self).setUp()
        self.modobj.name = 'test'
        self.modobj.parent = mock.Mock(footer=mock.Mock())
        self.header_text = mock.Mock()
        self.fields = mock.Mock()
        self.defaults = mock.Mock()
        modulehelper.blank = 'blank'

    def test_screen_ui(
            self, m_get_check_column, m_list_box, m_list_walker,
            m_setup_widgets, m_get_header_content, m_debug):
        self._check(
            'screenUI',
            m_list_box.return_value,
            self.modobj,
            self.header_text,
            self.fields,
            self.defaults
        )
        self.assertEqual(self.modobj.edits, m_setup_widgets.return_value)
        self.assertEqual(self.modobj.walker, m_list_walker.return_value)
        self.assertEqual(
            self.modobj.listbox_content,
            ['header', 'blank', 'edit', 'blank', 'buttons'])

        m_debug.assert_called_once_with(
            "Preparing screen UI for %s", self.modobj.name)
        m_get_header_content.assert_called_once_with(self.header_text)
        m_setup_widgets.assert_called_once_with(
            self.modobj.parent.footer, self.fields, self.defaults)
        m_get_check_column.assert_called_once_with(self.modobj, False)
        m_list_walker.assert_called_once_with(self.modobj.listbox_content)
        m_list_box.assert_called_once_with(m_list_walker.return_value)

    def test_screen_ui_buttons_visible_false(self, m_get_check_column,
                                             m_list_box, *_):
        self._check('screenUI', m_list_box.return_value,
                    self.modobj,
                    self.header_text,
                    self.fields,
                    self.defaults,
                    buttons_visible=False)
        self.assertFalse(m_get_check_column.called)


class TestNetworkMethodsBase(TestModuleHelperBase):
    def setUp(self):
        super(TestNetworkMethodsBase, self).setUp()
        self.iface = 'eth0'


@mock.patch('fuelmenu.common.modulehelper.ModuleHelper._get_iface_info',)
class TestGetInterfaceSettings(TestNetworkMethodsBase):
    def setUp(self):
        super(TestGetInterfaceSettings, self).setUp()
        self.values = {
            netifaces.AF_INET: {
                'addr': '127.0.0.1',
                'netmask': ''
            },
            netifaces.AF_LINK: {
                'addr': '38:2c:4a:b0:a4:0a'
            }
        }
        self.value_on_succes = {
            'addr': '127.0.0.1',
            'netmask': '',
            'onboot': 'Yes',
            'mac': '38:2c:4a:b0:a4:0a'
        }
        self.value_on_error = {
            'addr': '',
            'netmask': '',
            'onboot': 'no',
            'mac': '38:2c:4a:b0:a4:0a'
        }

    def _check_get_iface_settings(self, m_get_iface_info, expected):
        m_get_iface_info.side_effect = lambda _, x: self.values[x]
        self._check('_get_iface_settings', expected, self.iface)
        m_get_iface_info.assert_has_calls([
            mock.call(self.iface, netifaces.AF_INET),
            mock.call(self.iface, netifaces.AF_LINK)])

    def test_get_iface_settings(self, m_get_iface_info):
        self._check_get_iface_settings(m_get_iface_info, self.value_on_succes)

    def test_get_iface_settings_key_error(self, m_get_iface_info):
        del self.values[netifaces.AF_INET]
        self._check_get_iface_settings(m_get_iface_info, self.value_on_error)

    def test_get_iface_settings_type_error(self, m_get_iface_info):
        self.values[netifaces.AF_INET] = int()
        self._check_get_iface_settings(m_get_iface_info, self.value_on_error)


class TestGetLinkState(TestNetworkMethodsBase):
    def setUp(self):
        super(TestGetLinkState, self).setUp()
        self.addr = '127.0.0.1'
        self.data = ['  down  ']

    def _check_get_link_state(self, expected, open_side_effect=None):
        with mock.patch('__builtin__.open', custom_mock_open(self.data)) \
                as m_open:
            m_open.side_effect = open_side_effect
            self._check('_get_link_state', expected, self.iface, self.addr)
            m_open.assert_called_once_with(
                '/sys/class/net/%s/operstate' % self.iface)

    def _assert_warning(self, m_warning):
        m_warning.assert_called_once_with(
            "Unable to read operstate file for %s", self.iface)

    def test_get_link_state(self):
        self._check_get_link_state('down')

    @mock.patch('fuelmenu.common.modulehelper.log.warning')
    def test_get_link_state_os_error(self, m_warning):
        self._check_get_link_state('up', open_side_effect=IOError)
        self._assert_warning(m_warning)

    @mock.patch('fuelmenu.common.modulehelper.log.warning')
    def test_get_link_state_os_error_and_empty_addr(self, m_warning):
        self.addr = ''
        self._check_get_link_state('unknown', open_side_effect=IOError)
        self._assert_warning(m_warning)


class TestGetBootProto(TestNetworkMethodsBase):
    def setUp(self):
        super(TestGetBootProto, self).setUp()
        self.dhcp_exist = True
        self.data = [
            'HWADDR=0A:00:27:00:00:00',
            'TYPE=Ethernet',
            'BOOTPROTO=bootp',
            'DEFROUTE=yes']

    def _check_get_boot_proto(self, expected, open_side_effect=None):
        with mock.patch('__builtin__.open', custom_mock_open(self.data)) \
                as m_open:
            m_open.side_effect = open_side_effect
            self._check(
                '_get_boot_proto', expected, self.iface, self.dhcp_exist)
            m_open.assert_called_once_with(
                "/etc/sysconfig/network-scripts/ifcfg-%s" % self.iface)

    def test_get_boot_proto(self):
        self._check_get_boot_proto('bootp')

    def test_get_boot_proto_exception(self):
        self._check_get_boot_proto('dhcp', open_side_effect=Exception)

    def test_get_boot_proto_exception_and_no_dhcp(self):
        self.dhcp_exist = False
        self._check_get_boot_proto('none', open_side_effect=Exception)


@mock.patch('fuelmenu.common.modulehelper.ModuleHelper._get_iface_settings',
            return_value=dict(addr='127.0.0.1'))
@mock.patch('fuelmenu.common.modulehelper.ModuleHelper._get_link_state',
            return_value=mock.Mock())
@mock.patch('fuelmenu.common.modulehelper.ModuleHelper._get_boot_proto',
            return_value=mock.Mock())
class TestGetNet(TestNetworkMethodsBase):
    def setUp(self):
        super(TestGetNet, self).setUp()
        self.dhcp_exist = True

    def test_get_net(self, m_get_boot_proto, m_get_link_state,
                     m_get_iface_settings):
        expected = {
            'addr': m_get_iface_settings.return_value['addr'],
            'link': m_get_link_state.return_value,
            'bootproto': m_get_boot_proto.return_value
        }
        self._check('_get_net', expected, self.iface, self.dhcp_exist)
        m_get_iface_settings.assert_called_once_with(self.iface)
        m_get_link_state.assert_called_once_with(
            self.iface, m_get_iface_settings.return_value['addr'])
        m_get_boot_proto.assert_called_once_with(self.iface, self.dhcp_exist)


@mock.patch('fuelmenu.common.network.get_physical_ifaces',
            return_values=['eth0', 'eth1'])
@mock.patch('fuelmenu.common.modulehelper.ModuleHelper._get_net',
            return_value=mock.Mock())
class TestGetNetwork(TestModuleHelperBase):
    def setUp(self):
        super(TestGetNetwork, self).setUp()
        self.modobj.getDHCP = mock.Mock(return_value=mock.Mock())
        self.modobj.netsettings = dict()
        self.modobj.gateway = mock.Mock()
        self.modobj.get_default_gateway_linux = mock.Mock(
            return_value=mock.Mock())

    def test_get_network(self, m_get_net, m_get_physical_ifaces):
        self._run('getNetwork', self.modobj)
        m_get_physical_ifaces.assert_called_once_with()
        self.modobj.getDHCP.assert_has_calls(
            [mock.call(iface) for iface in m_get_physical_ifaces.return_value]
        )
        m_get_net.assert_has_calls(
            [mock.call(iface, self.modobj.getDHCP.return_value)
                for iface in m_get_physical_ifaces.return_value]
        )
        self.assertEqual(
            self.modobj.netsettings,
            {
                iface: m_get_net.return_value
                for iface in m_get_physical_ifaces.return_value
            }
        )


@mock.patch('fuelmenu.common.modulehelper.utils.execute')
class TestGetDhcp(TestNetworkMethodsBase):
    def _check_get_dhcp(self, expected, m_execute):
        self._check('getDHCP', expected, self.iface)
        m_execute.assert_called_once_with(
            ["pgrep", "-f", "dhclient.*{0}".format(self.iface)])

    def test_get_dhcp(self, m_execute):
        m_execute.return_value = (0, mock.Mock(), mock.Mock())
        self._check_get_dhcp(True, m_execute)

    def test_get_dhcp_failure(self, m_execute):
        m_execute.return_value = (1, mock.Mock(), mock.Mock())
        self._check_get_dhcp(False, m_execute)


@mock.patch('socket.inet_ntoa', return_value=mock.Mock())
@mock.patch('struct.pack', return_value=mock.Mock())
class TestGetDefaultGateway(TestModuleHelperBase):
    def setUp(self):
        super(TestGetDefaultGateway, self).setUp()
        self.data = [
            'Iface	Destination	Gateway 	Flags',
            'eth0	00000000	810812AC	0001',
            'eth1	007AA8C0	000110AC	0003',
            'eth2	00000000	0A1012AC	0003']

    def _check_default_gateway(self, expected):
        with mock.patch('__builtin__.open', custom_mock_open(self.data)):
            self._check('get_default_gateway_linux', expected)

    def test_get_default_gateway_linux(self, m_pack, m_inet_ntoa):
        self._check_default_gateway(m_inet_ntoa.return_value)
        m_pack.assert_called_once_with('<L', int('0A1012AC', 16))
        m_inet_ntoa.assert_called_once_with(m_pack.return_value)

    def test_get_default_gateway_linux_not_found(
            self, m_pack, m_inet_ntoa):
        del self.data[3]
        self._check_default_gateway(None)
        self.assertFalse(m_pack.called)
        self.assertFalse(m_inet_ntoa.called)
