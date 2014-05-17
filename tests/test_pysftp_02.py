'''test pysftp module - set 2 - uses py.test'''

# the following 3 lines let py.test find the module
import sys, os
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MYPATH + '/../')

# from io import BytesIO
from stat import S_ISLNK
from time import sleep

import pysftp

from dhp.test import tempfile_containing
# from mock import Mock, call
import pytest

# pylint: disable=E1101
# pylint: disable = W0142
SFTP_PUBLIC = {'host':'test.rebex.net', 'username':'demo',
               'password':'password'}
SFTP_LOCAL = {'host':'localhost', 'username':'test', 'password':'test1357'}
 #can only reach public, read-only server from CI platform, only test locally
 # if environment variable CI is set  to something to disable local tests
 # the CI env var is set to true by both drone-io and travis
skip_if_ci = pytest.mark.skipif(os.getenv('CI', '')>'', reason='Not Local')


@skip_if_ci
def test_chown_uid():
    '''test changing just the uid'''
    with tempfile_containing('contents') as fname:
        base_fname = base_fname = os.path.split(fname)[1]
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            org_attrs = sftp.put(fname)
            uid = org_attrs.st_uid  # - 1
            sftp.chown(base_fname, uid=uid)
            new_attrs = sftp.stat(base_fname)
            sftp.remove(base_fname)
    assert new_attrs.st_uid == uid
    assert new_attrs.st_gid == org_attrs.st_gid  # confirm no change to gid

@skip_if_ci
def test_chown_gid():
    '''test changing just the gid'''
    with tempfile_containing('contents') as fname:
        base_fname = base_fname = os.path.split(fname)[1]
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            org_attrs = sftp.put(fname)
            gid = org_attrs.st_gid  # - 1
            sftp.chown(base_fname, gid=gid)
            new_attrs = sftp.stat(base_fname)
            sftp.remove(base_fname)
    assert new_attrs.st_gid == gid
    assert new_attrs.st_uid == org_attrs.st_uid  # confirm no change to uid

@skip_if_ci
def test_chown_none():
    '''call .chown with no gid or uid specified'''
    with tempfile_containing('contents') as fname:
        base_fname = base_fname = os.path.split(fname)[1]
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            org_attrs = sftp.put(fname)
            sftp.chown(base_fname)
            new_attrs = sftp.stat(base_fname)
            sftp.remove(base_fname)
    assert new_attrs.st_gid == org_attrs.st_gid
    assert new_attrs.st_uid == org_attrs.st_uid  # confirm no change to uid

@skip_if_ci
def test_chown_not_exist():
    '''call .chown on a non-existing path'''
    with pytest.raises(IOError):
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            sftp.chown('i-do-not-exist.txt', 666)

def test_chown_ro_server():
    '''call .chown against path on read-only server'''
    with pytest.raises(IOError):
        with pysftp.Connection(**SFTP_PUBLIC) as sftp:
            sftp.chown('readme.txt', gid=1000, uid=1000)

@skip_if_ci
def test_chmod_not_exist():
    '''verify error if trying to chmod something that isn't there'''
    with pytest.raises(IOError):
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            sftp.chmod('i-do-not-exist.txt', 666)

@skip_if_ci
def test_chmod_simple():
    '''test basic chmod'''
    new_mode = 711
    with tempfile_containing('') as fname:
        base_fname = os.path.split(fname)[1]
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            org_attrs = sftp.put(fname)
            sftp.chmod(base_fname, new_mode)
            new_attrs = sftp.stat(base_fname)
            sftp.remove(base_fname)
    # that the new mod 711 is as we wanted
    assert pysftp.st_mode_to_int(new_attrs.st_mode) == new_mode
    # that we actually changed something
    assert new_attrs.st_mode != org_attrs.st_mode

def test_path_retreat():
    '''test path_retreat generator'''
    pth = 'foo/bar/baz'
    assert list(pysftp.path_retreat(pth)) == ['foo/bar/baz',
                                              'foo/bar',
                                              'foo']
    pth = '/foo/bar/baz'
    assert list(pysftp.path_retreat(pth)) == ['/foo/bar/baz',
                                              '/foo/bar',
                                              '/foo']

def test_path_advance():
    '''test path_advance generator'''
    pth = 'foo/bar/baz'
    assert list(pysftp.path_advance(pth)) == ['foo',
                                              'foo/bar',
                                              'foo/bar/baz']
    pth = '/foo/bar/baz'
    assert list(pysftp.path_advance(pth)) == ['/foo',
                                              '/foo/bar',
                                              '/foo/bar/baz']

@skip_if_ci
def test_makedirs():
    '''test makedirs simple, testing 2 things, oh well'''
    rdir = 'foo/bar/baz'
    rdir2 = 'foo/bar'
    with pysftp.Connection(**SFTP_LOCAL) as sftp:
        assert sftp.exists(rdir) == False
        sftp.makedirs(rdir)
        is_dir = sftp.isdir(rdir)
        sftp.rmdir(rdir)
        sftp.rmdir(rdir2)
        sftp.makedirs(rdir)     # try partially existing path
        is_dir_partial = sftp.isdir(rdir)
        for rpath in pysftp.path_retreat(rdir):
            sftp.rmdir(rpath)
    assert is_dir
    assert is_dir_partial

def test_isfile():
    '''test .isfile() functionality'''
    rfile = 'readme.txt'
    rdir = 'pub'
    with pysftp.Connection(**SFTP_PUBLIC) as sftp:
        assert sftp.isfile(rfile) == True
        assert sftp.isfile(rdir) == False

@skip_if_ci
def test_isfile_2():
    '''test .isfile() functionality against a symlink'''
    rsym = 'my-link.txt'
    with tempfile_containing(contents=8192*'*') as fname:
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            sftp.put(fname)
            sftp.symlink(fname, rsym)
            is_file = sftp.isfile(rsym)
            sftp.remove(rsym)
            sftp.remove(os.path.split(fname)[1])
    assert is_file == True

def test_isdir():
    '''test .isdir() functionality'''
    rfile = 'readme.txt'
    rdir = 'pub'
    with pysftp.Connection(**SFTP_PUBLIC) as sftp:
        assert sftp.isdir(rfile) == False
        assert sftp.isdir(rdir) == True

@skip_if_ci
def test_isdir_2():
    '''test .isdir() functionality against a symlink'''
    rsym = 'my-link.txt'
    with tempfile_containing(contents=8192*'*') as fname:
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            sftp.put(fname)
            sftp.symlink(fname, rsym)
            is_dir = sftp.isdir(rsym)
            sftp.remove(rsym)
            sftp.remove(os.path.split(fname)[1])
    assert is_dir == False

@skip_if_ci
def test_lexists_symbolic():
    '''test .lexists() vs. symbolic link'''
    rdest = 'honey-boo-boo'
    with tempfile_containing(contents=8192*'*') as fname:
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            sftp.put(fname)
            sftp.symlink(fname, rdest)
            sftp.remove(os.path.split(fname)[1])
            found = sftp.lexists(rdest) == True
            sftp.remove(rdest)
    assert found

@skip_if_ci
def test_symlink():
    '''test symlink creation'''
    rdest = 'honey-boo-boo'
    with tempfile_containing(contents=8192*'*') as fname:
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            sftp.put(fname)
            sftp.symlink(fname, rdest)
            rslt = sftp.lstat(rdest)
            is_link = S_ISLNK(rslt.st_mode) == True
            sftp.remove(rdest)
            sftp.remove(os.path.split(fname)[1])
    assert is_link

def test_exists():
    '''test .exists() fuctionality'''
    rfile = 'readme.txt'
    rbad = 'pee-a-boo.txt'
    with pysftp.Connection(**SFTP_PUBLIC) as sftp:
        assert sftp.exists(rfile) == True
        assert sftp.exists(rbad) == False
        assert sftp.exists('pub') == True

def test_lexists():
    '''test .lexists() functionality'''
    rfile = 'readme.txt'
    rbad = 'pee-a-boo.txt'
    with pysftp.Connection(**SFTP_PUBLIC) as sftp:
        assert sftp.lexists(rfile) == True
        assert sftp.lexists(rbad) == False
        assert sftp.lexists('pub') == True

def test_get_preserve_mtime():
    '''test that m_time is preserved from local to remote, when get'''
    rfile = 'readme.txt'
    with pysftp.Connection(**SFTP_PUBLIC) as sftp:
        with tempfile_containing('') as localfile:
            r_stat = sftp.stat(rfile)
            sftp.get(rfile, localfile, preserve_mtime=True)
            assert r_stat.st_mtime == os.stat(localfile).st_mtime

@skip_if_ci
def test_put_preserve_mtime():
    '''test that m_time is preserved from local to remote, when put'''
    with tempfile_containing(contents=8192*'*') as fname:
        base_fname = os.path.split(fname)[1]
        base = os.stat(fname)
        with pysftp.Connection(**SFTP_LOCAL) as sftp:
            result1 = sftp.put(fname, preserve_mtime=True)
            sleep(2)
            result2 = sftp.put(fname, preserve_mtime=True)
            # clean up
            sftp.remove(base_fname)
    # see if times are modified
    # assert base.st_atime == result1.st_atime
    assert base.st_mtime == result1.st_mtime
    # assert result1.st_atime == result2.st_atime
    assert result1.st_mtime == result2.st_mtime

