# coding=utf-8
from __future__ import absolute_import

import unittest

import mock
import six

import koji
from koji_cli.commands import handle_edit_channel
from . import utils


class TestEditChannel(utils.CliTestCase):

    def setUp(self):
        self.options = mock.MagicMock()
        self.session = mock.MagicMock()
        self.channel_old = 'test-channel'
        self.channel_new = 'test-channel-new'
        self.description = 'description'
        self.channel_info = {
            'id': 123,
            'name': self.channel_old,
            'description': self.description,
        }
        self.maxDiff = None

    def tearDown(self):
        mock.patch.stopall()

    def test_handle_edit_channel_help(self):
        self.assert_help(
            handle_edit_channel,
            """Usage: %s edit-channel [options] <old-name>
(Specify the --help global option for a list of other help options)

Options:
  -h, --help            show this help message and exit
  --name=NAME           New channel name
  --description=DESCRIPTION
                        Description of channel
  --comment=COMMENT     Comment of channel
""" % self.progname)

    @mock.patch('sys.stderr', new_callable=six.StringIO)
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_edit_channel_without_args(self, activate_session_mock, stderr):
        with self.assertRaises(SystemExit) as ex:
            handle_edit_channel(self.options, self.session, [])
        self.assertExitCode(ex, 2)
        actual = stderr.getvalue()
        expected_stderr = """Usage: %s edit-channel [options] <old-name>
(Specify the --help global option for a list of other help options)

%s: error: Incorrect number of arguments
""" % (self.progname, self.progname)
        self.assertMultiLineEqual(actual, expected_stderr)
        activate_session_mock.assert_not_called()

    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_edit_channel(self, activate_session_mock):
        handle_edit_channel(self.options, self.session,
                            [self.channel_old, '--name', self.channel_new,
                             '--description', self.description])
        activate_session_mock.assert_called_once_with(self.session, self.options)
        self.session.editChannel.assert_called_once_with(self.channel_old, name=self.channel_new,
                                                         description=self.description)

    @mock.patch('sys.stderr', new_callable=six.StringIO)
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_edit_channel_older_hub(self, activate_session_mock, stderr):
        expected_api = 'Invalid method: editChannel'
        expected = 'editChannel is available on hub from Koji 1.26 version, your version ' \
                   'is 1.25.1\n'
        self.session.getKojiVersion.return_value = '1.25.1'

        self.session.editChannel.side_effect = koji.GenericError(expected_api)
        with self.assertRaises(SystemExit) as ex:
            handle_edit_channel(self.options, self.session,
                                [self.channel_old, '--name', self.channel_new,
                                 '--description', self.description])
        self.assertExitCode(ex, 1)
        actual = stderr.getvalue()
        self.assertMultiLineEqual(actual, expected)
        activate_session_mock.assert_called_once_with(self.session, self.options)
        self.session.editChannel.assert_called_once_with(self.channel_old, name=self.channel_new,
                                                         description=self.description)

    @mock.patch('sys.stderr', new_callable=six.StringIO)
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_edit_channel_non_exist_channel(self, activate_session_mock, stderr):
        expected = 'No such channel: %s\n' % self.channel_old
        channel_info = None
        self.session.getChannel.return_value = channel_info
        with self.assertRaises(SystemExit) as ex:
            handle_edit_channel(self.options, self.session,
                                [self.channel_old, '--name', self.channel_new,
                                 '--description', self.description])
        self.assertExitCode(ex, 1)
        actual = stderr.getvalue()
        self.assertMultiLineEqual(actual, expected)
        activate_session_mock.assert_called_once_with(self.session, self.options)
        self.session.editChannel.assert_not_called()

    @mock.patch('sys.stderr', new_callable=six.StringIO)
    @mock.patch('koji_cli.commands.activate_session')
    def test_handle_edit_channel_non_result(self, activate_session_mock, stderr):
        expected = 'No changes made, please correct the command line\n'
        self.session.getChannel.return_value = self.channel_info
        self.session.editChannel.return_value = None
        with self.assertRaises(SystemExit) as ex:
            handle_edit_channel(self.options, self.session,
                                [self.channel_old, '--name', self.channel_new,
                                 '--description', self.description])
        self.assertExitCode(ex, 1)
        actual = stderr.getvalue()
        self.assertMultiLineEqual(actual, expected)
        activate_session_mock.assert_called_once_with(self.session, self.options)
        self.session.editChannel.assert_called_once_with(self.channel_old, name=self.channel_new,
                                                         description=self.description)


if __name__ == '__main__':
    unittest.main()
