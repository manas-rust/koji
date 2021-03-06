from __future__ import absolute_import

import unittest

import mock
from six.moves import StringIO

import koji
from koji_cli.commands import anon_handle_list_channels
from . import utils


class TestListChannels(utils.CliTestCase):
    maxDiff = None

    def setUp(self):
        self.options = mock.MagicMock()
        self.options.quiet = True
        self.session = mock.MagicMock()
        self.session.getAPIVersion.return_value = koji.API_VERSION
        self.list_channels = [
            {'id': 1, 'name': 'default', 'enabled': True, 'comment': 'test-comment-1',
             'description': 'test-description-1'},
            {'id': 2, 'name': 'test', 'enabled': False, 'comment': 'test-comment-2',
             'description': 'test-description-2'},
        ]
        self.list_channels_without_enabled = [
            {'id': 1, 'name': 'default', 'comment': 'test-comment-1',
             'description': 'test-description-1'},
            {'id': 2, 'name': 'test', 'comment': 'test-comment-2',
             'description': 'test-description-2'},
        ]

        self.list_hosts_mc = [
            [[
                {'enabled': True, 'ready': True, 'capacity': 2.0, 'task_load': 1.34},
                {'enabled': True, 'ready': False, 'capacity': 2.0, 'task_load': 0.0},
                {'enabled': True, 'ready': False, 'capacity': 2.0, 'task_load': 0.0},
            ]],
            [[
                {'enabled': True, 'ready': True, 'capacity': 2.0, 'task_load': 1.34},
                {'enabled': False, 'ready': True, 'capacity': 2.0, 'task_load': 0.34},
                {'enabled': True, 'ready': False, 'capacity': 2.0, 'task_load': 0.0},
            ]]
        ]

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_not_quiet(self, ensure_connection_mock, stdout):
        self.session.listChannels.return_value = self.list_channels
        self.session.multiCall.return_value = self.list_hosts_mc
        args = []
        self.options.quiet = False

        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = "Channel        Enabled  Ready Disbld   Load    Cap   Perc    \n" \
                   "default              3      1      0      1      6     22%\n" \
                   "test [disabled]      2      2      1      1      6     28%\n"

        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_with_comment(self, ensure_connection_mock, stdout):
        self.session.listChannels.return_value = self.list_channels
        self.session.multiCall.return_value = self.list_hosts_mc
        args = ['--comment']
        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = 'default              3      1      0      1      6     22%   ' \
                   'test-comment-1                                    \n' \
                   'test [disabled]      2      2      1      1      6     28%   ' \
                   'test-comment-2                                    \n'
        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_with_description(self, ensure_connection_mock, stdout):
        self.session.listChannels.return_value = self.list_channels
        self.session.multiCall.return_value = self.list_hosts_mc
        args = ['--description']
        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = 'default              3      1      0      1      6     22%   ' \
                   'test-description-1                                \n' \
                   'test [disabled]      2      2      1      1      6     28%   ' \
                   'test-description-2                                \n'
        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_with_comment_desc_not_quiet(self, ensure_connection_mock, stdout):
        self.session.listChannels.return_value = self.list_channels
        self.session.multiCall.return_value = self.list_hosts_mc
        args = ['--description', '--comment']
        self.options.quiet = False

        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = "Channel        Enabled  Ready Disbld   Load    Cap   Perc    " \
                   "Description                                          " \
                   "Comment                                              \n" \
                   "default              3      1      0      1      6     22%   " \
                   "test-description-1                                   " \
                   "test-comment-1                                    \n" \
                   "test [disabled]      2      2      1      1      6     28%   " \
                   "test-description-2                                   " \
                   "test-comment-2                                    \n"
        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_with_enabled_hub_without_enabled(self, ensure_connection_mock, stdout):
        self.session.listChannels.side_effect = [koji.ParameterError,
                                                 self.list_channels_without_enabled]
        self.session.multiCall.return_value = self.list_hosts_mc
        args = ['--enabled']
        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = 'default      3      1      0      1      6     22%\n' \
                   'test         2      2      1      1      6     28%\n'
        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_with_enabled(self, ensure_connection_mock, stdout):
        list_channel_enabled = [
            {'id': 1, 'name': 'default', 'enabled': True, 'comment': 'test-comment-1',
             'description': 'test-description-1'},
        ]
        list_hosts_mc = [
            [[
                {'enabled': True, 'ready': True, 'capacity': 2.0, 'task_load': 1.34},
                {'enabled': True, 'ready': False, 'capacity': 2.0, 'task_load': 0.0},
                {'enabled': True, 'ready': False, 'capacity': 2.0, 'task_load': 0.0},
            ]]
        ]
        self.session.listChannels.return_value = list_channel_enabled
        self.session.multiCall.return_value = list_hosts_mc
        args = ['--enabled']
        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = 'default      3      1      0      1      6     22%\n'
        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_with_disabled(self, ensure_connection_mock, stdout):
        list_channel_disabled = [
            {'id': 2, 'name': 'test', 'enabled': False, 'comment': 'test-comment-2',
             'description': 'test-description-2'},
        ]
        list_hosts_mc = [
            [[
                {'enabled': True, 'ready': True, 'capacity': 2.0, 'task_load': 1.34},
                {'enabled': False, 'ready': True, 'capacity': 2.0, 'task_load': 0.34},
                {'enabled': True, 'ready': False, 'capacity': 2.0, 'task_load': 0.0},
            ]]
        ]
        self.session.listChannels.return_value = list_channel_disabled
        self.session.multiCall.return_value = list_hosts_mc
        args = ['--disabled']
        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = 'test [disabled]      2      2      1      1      6     28%\n'
        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_with_empty_channels(self, ensure_connection_mock, stdout):
        list_channels = []
        list_hosts_mc = [[[]]]
        self.session.listChannels.return_value = list_channels
        self.session.multiCall.return_value = list_hosts_mc
        args = []
        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = ''
        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_simple_without_quiet(self, ensure_connection_mock, stdout):
        self.session.listChannels.return_value = self.list_channels
        self.session.multiCall.return_value = self.list_hosts_mc
        self.options.quiet = False
        args = ['--simple']

        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = """Channel
default
test [disabled]
"""
        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    @mock.patch('sys.stdout', new_callable=StringIO)
    @mock.patch('koji_cli.commands.ensure_connection')
    def test_list_channels_simple_with_quiet(self, ensure_connection_mock, stdout):
        self.session.listChannels.return_value = self.list_channels
        self.session.multiCall.return_value = self.list_hosts_mc
        args = ['--simple', '--quiet']

        anon_handle_list_channels(self.options, self.session, args)

        actual = stdout.getvalue()
        print(actual)
        expected = """default
test [disabled]
"""
        self.assertMultiLineEqual(actual, expected)
        ensure_connection_mock.assert_called_once_with(self.session, self.options)

    def test_list_channels_help(self):
        self.assert_help(
            anon_handle_list_channels,
            """Usage: %s list-channels [options]
(Specify the --help global option for a list of other help options)

Options:
  -h, --help     show this help message and exit
  --simple       Print just list of channels without additional info
  --quiet        Do not print header information
  --comment      Show comments
  --description  Show descriptions
  --enabled      Limit to enabled channels
  --not-enabled  Limit to not enabled channels
  --disabled     Alias for --not-enabled
""" % self.progname)


if __name__ == '__main__':
    unittest.main()
