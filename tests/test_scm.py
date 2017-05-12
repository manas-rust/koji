import mock
import unittest

import logging
import shutil
import tempfile

from pprint import pprint

import koji
import koji.daemon

from koji.daemon import SCM


class TestSCM(unittest.TestCase):

    def test_urlcheck(self):
        good = [
            "git://server/foo.git#bab0c73900241ef5c465d7e873e9d8b34c948e67",
            "git+ssh://server2/other/path#bab0c73900241ef5c465d7e873e9d8b34c948e67",
            "svn://server/path/to/code#bab0c73900241ef5c465d7e873e9d8b34c948e67",
            "svn+ssh://server/some/path#bab0c73900241ef5c465d7e873e9d8b34c948e67",
            "cvs://server/some/path#bab0c73900241ef5c465d7e873e9d8b34c948e67",
            "cvs+ssh://server/some/path#bab0c73900241ef5c465d7e873e9d8b34c948e67",
            ]
        bad = [
            "http://localhost/foo.html",
            "foo-1.1-1.src.rpm",
            "https://server/foo-1.1-1.src.rpm",
            ]
        for url in good:
            self.assertTrue(SCM.is_scm_url(url))
        for url in bad:
            self.assertFalse(SCM.is_scm_url(url))

    @mock.patch('logging.getLogger')
    def test_init(self, getLogger):
        bad = [
            "git://user@@server/foo.git#bab0c73900241ef5c465d7e873e9d8b34c948e67",
            "git://user:pass@server/foo.git#bab0c73900241ef5c465d7e873e9d8b34c948e67",
            "git://server/foo.git;params=not_allowed",
            "git://server#asdasd",  # no path
            "git://server/foo.git",  # no fragment
            "http://localhost/foo.html",
            "git://@localhost/foo/?a=bar/",
            "http://localhost/foo.html?a=foo/",
            "foo-1.1-1.src.rpm",
            "git://",
            "https://server/foo-1.1-1.src.rpm",
            ]
        for url in bad:
            with self.assertRaises(koji.GenericError):
                scm = SCM(url)

        url = "git://user@server/foo.git#bab0c73900241ef5c465d7e873e9d8b34c948e67"
        scm = SCM(url)
        self.assertEqual(scm.scheme, 'git://')
        self.assertEqual(scm.user, 'user')
        self.assertEqual(scm.host, 'server')
        self.assertEqual(scm.repository, '/foo.git')
        self.assertEqual(scm.module, '')
        self.assertEqual(scm.revision, 'bab0c73900241ef5c465d7e873e9d8b34c948e67')
        self.assertEqual(scm.use_common, True)
        self.assertEqual(scm.source_cmd, ['make', 'sources'])
        self.assertEqual(scm.scmtype, 'GIT')


    @mock.patch('logging.getLogger')
    def test_allowed(self, getLogger):
        allowed = '''
            goodserver:*:no
            !badserver:*
            !maybeserver:/badpath/*
            maybeserver:*:no
            '''
        good = [
            "git://goodserver/path1#1234",
            "git+ssh://maybeserver/path1#1234",
            ]
        bad = [
            "cvs://badserver/projects/42#ref",
            "svn://badserver/projects/42#ref",
            ]
        for url in good:
            scm = SCM(url)
            scm.assert_allowed(allowed)
        for url in bad:
            scm = SCM(url)
            with self.assertRaises(koji.BuildError):
                scm.assert_allowed(allowed)

    @mock.patch('logging.getLogger')
    def test_badrule(self, getLogger):
        allowed = '''
            bogus-entry-should-be-ignored
            goodserver:*:no
            !badserver:*
            '''
        url = "git://goodserver/path1#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)

    @mock.patch('logging.getLogger')
    def test_opts(self, getLogger):
        allowed = '''
            default:*
            nocommon:*:no
            srccmd:*:no:fedpkg,sources
            nosrc:*:no:
            mixed:/foo/*:no
            mixed:/bar/*:yes
            mixed:/baz/*:no:fedpkg,sources
            '''

        url = "git://default/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, True)
        self.assertEqual(scm.source_cmd, ['make', 'sources'])

        url = "git://nocommon/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, False)
        self.assertEqual(scm.source_cmd, ['make', 'sources'])

        url = "git://srccmd/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, False)
        self.assertEqual(scm.source_cmd, ['fedpkg', 'sources'])

        url = "git://nosrc/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, False)
        self.assertEqual(scm.source_cmd, None)

        url = "git://mixed/foo/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, False)
        self.assertEqual(scm.source_cmd, ['make', 'sources'])

        url = "git://mixed/bar/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, True)
        self.assertEqual(scm.source_cmd, ['make', 'sources'])

        url = "git://mixed/baz/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, False)
        self.assertEqual(scm.source_cmd, ['fedpkg', 'sources'])

        url = "git://mixed/koji.git#1234"
        scm = SCM(url)
        with self.assertRaises(koji.BuildError):
            scm.assert_allowed(allowed)

        url = "git://mixed/foo/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, False)
        self.assertEqual(scm.source_cmd, ['make', 'sources'])

        url = "git://mixed/bar/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, True)
        self.assertEqual(scm.source_cmd, ['make', 'sources'])

        url = "git://mixed/baz/koji.git#1234"
        scm = SCM(url)
        scm.assert_allowed(allowed)
        self.assertEqual(scm.use_common, False)
        self.assertEqual(scm.source_cmd, ['fedpkg', 'sources'])

        url = "git://mixed/koji.git#1234"
        scm = SCM(url)
        with self.assertRaises(koji.BuildError):
            scm.assert_allowed(allowed)


class TestSCMCheckouts(unittest.TestCase):

    def setUp(self):
        self.symlink = mock.patch('os.symlink').start()
        self.getLogger = mock.patch('logging.getLogger').start()
        self.log_output = mock.patch('koji.daemon.log_output').start()
        self.log_output.return_value = None
        self.tempdir = tempfile.mkdtemp()
        self.session = mock.MagicMock()
        self.uploadpath = mock.MagicMock()
        self.logfile = mock.MagicMock()
        self.allowed = '''
            default:*
            nocommon:*:no
            srccmd:*:no:fedpkg,sources
            nosrc:*:no:
            '''

    def tearDown(self):
        mock.patch.stopall()
        shutil.rmtree(self.tempdir)

    def test_checkout_git_nocommon(self):

        url = "git://nocommon/koji.git#asdasd"
        scm = SCM(url)
        scm.assert_allowed(self.allowed)
        scm.checkout(self.tempdir, session=self.session,
                uploadpath=self.uploadpath, logfile=self.logfile)
        self.assertEqual(scm.use_common, False)
        self.symlink.assert_not_called()
        # expected commands
        cmd = ['git', 'clone', '-n', 'git://nocommon/koji.git',
                self.tempdir + '/koji']
        call1 = mock.call(self.session, cmd[0], cmd, self.logfile,
                        self.uploadpath, cwd=self.tempdir, logerror=1,
                        append=False, env=None)
        cmd = ['git', 'reset', '--hard', 'asdasd']
        call2 = mock.call(self.session, cmd[0], cmd, self.logfile,
                        self.uploadpath, cwd=self.tempdir + '/koji',
                        logerror=1, append=True, env=None)
        self.log_output.assert_has_calls([call1, call2])

    def test_checkout_gitssh_nocommon(self):

        url = "git+ssh://user@nocommon/koji.git#asdasd"
        scm = SCM(url)
        scm.assert_allowed(self.allowed)
        scm.checkout(self.tempdir, session=self.session,
                uploadpath=self.uploadpath, logfile=self.logfile)
        self.assertEqual(scm.use_common, False)
        self.symlink.assert_not_called()
        # expected commands
        cmd = ['git', 'clone', '-n', 'git+ssh://user@nocommon/koji.git',
                self.tempdir + '/koji']
        call1 = mock.call(self.session, cmd[0], cmd, self.logfile,
                        self.uploadpath, cwd=self.tempdir, logerror=1,
                        append=False, env=None)
        cmd = ['git', 'reset', '--hard', 'asdasd']
        call2 = mock.call(self.session, cmd[0], cmd, self.logfile,
                        self.uploadpath, cwd=self.tempdir + '/koji',
                        logerror=1, append=True, env=None)
        self.log_output.assert_has_calls([call1, call2])
