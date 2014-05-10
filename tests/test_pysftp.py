'''test pysftp module - uses py.test'''

# the following 3 lines let py.test find the module
import sys, os
MYPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MYPATH + '/../')

import pysftp

from dhp.test import tempfile_containing
import pytest

def test_connection_bad():
    '''attempt connection to a non-existing server'''
    with pytest.raises(pysftp.SSHException):
        sftp = pysftp.Connection(host='nota.realserver.pri',
                                 username='demo',
                                 password='password')
        sftp.close()

def test_connection_good():
    '''connect to a public sftp server'''
    sftp = pysftp.Connection(host='test.rebex.net',
                             username='demo',
                             password='password')
    sftp.close()


def test_listdir():
    '''try and connect to localhost'''
    sftp = pysftp.Connection(host='test.rebex.net',
                             username='demo',
                             password='password')
    assert sftp.listdir() == ['pub', 'readme.txt']
    sftp.close()


def test_cwd():
    '''try and connect to localhost'''
    sftp = pysftp.Connection(host='test.rebex.net',
                             username='demo',
                             password='password')
    assert sftp.getcwd() == None
    sftp.chdir('pub')
    assert sftp.getcwd() == '/pub'
    sftp.close()

def test_get():
    '''download a file'''
    sftp = pysftp.Connection(host='test.rebex.net',
                             username='demo',
                             password='password')
    with tempfile_containing('') as fname:
        sftp.get('readme.txt', fname)
        sftp.close()
        assert open(fname, 'rb').read()[0:7] == 'Welcome'


