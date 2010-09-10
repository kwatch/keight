# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

from __future__ import with_statement

import sys, os, re, time, glob, shutil
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import oktest
from oktest import ok, not_ok, run, spec
import keight as k8


orig_secret_key = k8.config.secret_key
secret_key = 'd00c3c7a5948ff63a474613bd9b52ae0'



class _SessionTest(object):

    @classmethod
    def before_all(cls):
        k8.config.secret_key = secret_key

    @classmethod
    def after_all(cls):
        k8.config.secret_key = orig_secret_key



def _r(**kwargs):
    request = k8.Request(k8.dummy_env(**kwargs))
    response = k8.Response()
    return request, response


class SessionTest(_SessionTest):

    def _sess(self):
        return k8.Session(*_r())

    def test___init__(self):
        with spec("takes request and response objects"):
            req, res = _r()
            sess = k8.Session(req, res)
            ok (sess.request).is_(req)
            ok (sess.response).is_(res)

    def test_get(self):
        sess = self._sess()
        sess.values['foo'] = 'FOO'
        with spec("returns corresponding value in self.values"):
            ok (sess.get('foo')) == 'FOO'
            ok (sess.get('foo', 9)) == 'FOO'
        with spec("if key not found then returns default value"):
            ok (sess.get('bar')) == None
            ok (sess.get('bar', 9)) == 9

    def test___getitem__(self):
        sess = self._sess()
        sess.values['foo'] = 'FOO'
        with spec("returns corresponding value in self.values"):
            ok (sess['foo']) == 'FOO'
        with spec("if key is not found then raises KeyError"):
            def f():
                sess['bar']
            ok (f).raises(KeyError, "'bar'")

    def test___setitem__(self):
        sess = self._sess()
        with spec("sets corresponding value into self.values"):
            ok (sess.values.get('foo')) == None
            sess['foo'] = 'FOO'
            ok (sess.values.get('foo')) == 'FOO'

    def test___contains__(self):
        sess = self._sess()
        sess.values['foo'] = 'FOO'
        with spec("returns True if key is in self.values"):
            ok ('foo' in sess) == True
        with spec("returns False if key is not in self.values"):
            ok ('bar' in sess) == False

    def test_set_id(self):
        with spec("sets session id"):
            sess = self._sess()
            sess.set_id('123')
            ok (sess.id) == '123'
            ok (sess.values['_id']) == '123'

    def test_new_id(self):
        with spec("returns new session id"):
            id1 = k8.Session.new_id()
            ok (id1).matches('^[a-f0-9]+$')
            ok (len(id1)) == 40    # sha1 hash length
            ok (k8.Session.new_id()) != id1


class CookieSessionTest(_SessionTest):

    def _sess(self):
        return k8.CookieSession(*_r())

    def test___init__(self):
        with spec("creates a cookie object"):
            sess = self._sess()
            ok (sess.cookie).is_a(k8.COOKIE)
            klass = k8.CookieSession
            ok (sess.cookie.name)    == klass.cookie_name
            ok (sess.cookie.path)    == klass.cookie_path
            ok (sess.cookie.domain)  == klass.cookie_domain
            ok (sess.cookie.expires) == klass.cookie_expires
            ok (sess.cookie.secure)  == klass.cookie_secure

    def test_expire(self):
        with spec("sets 'expires' attr of cookie object to old timestamp"):
            sess = self._sess()
            sess.expire()
            ok (sess.cookie.expires) == time.gmtime(0)



orig_session_file_dir = k8.config.session_file_dir
session_file_dir = os.path.join(os.getcwd(), '_sessions')

class FileStoreSessionTest(_SessionTest):

    DIR   = session_file_dir
    SID   = 'e3ce3e735326735f3861c4a18110c34d8c241bc2'
    FPATH = os.path.join(session_file_dir, 'e3', 'ce', SID)
    HTTP_COOKIE = '%s=%s' % (k8.FileStoreSession.cookie_name, SID)
    VALUES = { 'arr': [1, 2, 3] }

    @classmethod
    def before_all(cls):
        _SessionTest.before_all()
        k8.config.session_file_dir = cls.DIR
        if os.path.exists(cls.DIR):
            shutil.rmtree(cls.DIR)
        os.mkdir(cls.DIR)

    @classmethod
    def after_all(cls):
        _SessionTest.after_all()
        k8.config.session_file_dir = orig_session_file_dir
        shutil.rmtree(session_file_dir)

    def after(self):
        self._clear_dir()

    def _clear_dir(self):
        for fpath in glob.glob(os.path.join(self.DIR, '*')):
            if os.path.isdir(fpath):
                shutil.rmtree(fpath)
            elif os.path.isfile(fpath):
                os.unlink(fpath)

    def _sess(self, **kwargs):
        return k8.FileStoreSession(*_r(**kwargs))

    def _create_session_file(self):
        sess = self._sess()
        sess.id = self.SID
        sess.values = self.VALUES
        sess.save()
        return self.FPATH

    def test___init__(self):
        with spec("if session file doesn't exist then session id is not restored from cookie and values is empty"):
            with oktest.dummy_attrs(k8.config, logging=False):
                not_ok (self.FPATH).is_file()
                sess = self._sess(HTTP_COOKIE=self.HTTP_COOKIE)
                ok (sess.id) != self.SID
                ok (sess.values) == {}
                ok (sess._fpath) == None
        with spec("if session file exists then restore session id from cookie and session values from session file"):
            #_ = os.path.dirname
            #os.mkdir(_(_(self.FPATH)))
            #os.mkdir(_(self.FPATH))
            #sess._dump_values(self.FPATH, self.VALUES)
            try:
                self._create_session_file()
                ok (self.FPATH).is_file()
                sess = self._sess(HTTP_COOKIE=self.HTTP_COOKIE)
                ok (sess.id) == self.SID
                ok (sess.values) == self.VALUES
                ok (sess._fpath) == self.FPATH
            finally:
                #self._clear_dir()
                pass

    def test_save(self):
        with spec("[b] if k8.config.session_file_dir is not specified then raise ValueError"):
            with oktest.dummy_attrs(k8.config, session_file_dir=''):
                assert k8.config.session_file_dir == ''
                sess = k8.FileStoreSession(*_r())
                def f(): sess.save()
                ok (f).raises(ValueError, "'config.session_file_dir' should be set.")
            assert k8.config.session_file_dir == session_file_dir
        with spec("[b] if directory doesn't exist then create it recursively"):
            #self._clear_dir()
            d = os.path.dirname(self.FPATH)
            not_ok (d).exists()
            sess = self._sess()
            sess.id = self.SID
            sess.values = self.VALUES
            sess.save()
            ok (d).exists()
            ok (d).is_dir()
        with spec("creates session file"):
            ok (self.FPATH).is_file()
            # check session file content
            ok (sess._load_values(self.FPATH)) == self.VALUES
            sess = self._sess(HTTP_COOKIE=self.HTTP_COOKIE)
            ok (sess.id) == self.SID
            ok (sess.values) == self.VALUES
            ok (sess._fpath) == self.FPATH
        with spec("if session is expired then do nothing"):
            ok (self.FPATH).is_file()
            sess.expire()
            not_ok (self.FPATH).exists()
            sess.save()
            not_ok (self.FPATH).exists()

    def test_expire(self):
        with spec("remove session file"):
            self._create_session_file()
            sess = None
            sess = self._sess(HTTP_COOKIE=self.HTTP_COOKIE)
            ok (self.FPATH).is_file()
            sess.expire()
            not_ok (self.FPATH).exists()
            #ok (sess.id) == None
            ok (sess._expired) == True
            #self._clear_dir()

    def test__get_fpath(self):
        with spec("[p] if k8.config.session_file_dir is not specified then raise ValueError"):
            with oktest.dummy_attrs(k8.config, session_file_dir=''):
                assert k8.config.session_file_dir == ''
                sess = k8.FileStoreSession(*_r())
                def f(): sess._get_fpath('12345')
                ok (f).raises(ValueError, "'config.session_file_dir' should be set.")
            assert k8.config.session_file_dir == session_file_dir
        with spec("[p] if directory doesn't exist then create it recursively"):
            d = os.path.dirname(self.FPATH)
            sess = self._sess()
            assert not os.path.exists(d)
            sess._get_fpath(self.SID, forced=True)
            ok (d).exists()
            ok (d).is_dir()

    def test__load_values(self):
        values = {'A':10, 'B':[20,30]}
        with spec("load dumped file and returns undumped values"):
            import pickle
            data = pickle.dumps(values, protocol=2)
            fpath = os.path.join(self.DIR, 'hoge.dump')
            open(fpath, 'wb').write(data)
            ret = self._sess()._load_values(fpath)
            ok (ret) == values

    def test__dump_values(self):
        values = {'A':10, 'B':[20,30]}
        with spec("saves dumped data into file."):
            fpath = os.path.join(self.DIR, 'foo.dump')
            assert not os.path.exists(fpath)
            self._sess()._dump_values(fpath, values)
            ok (fpath).is_file()
        with spec("dumped file is loadable by _load_values()."):
            ret = self._sess()._load_values(fpath)
            ok (ret) == values


class CookieStoreSession(_SessionTest):

    SID    = 'b33771760a6701eef934454116ddafff1655d189'
    VALUES = {'_id': SID, 'arr': [1,2,3]}
    #DUMPED = '922f97d82fb14aebe54112918d1dfb645f7a1dbe:KGRwMApTJ2FycicKcDEKKGxwMgpJMQphSTIKYUkzCmFzUydfaWQnCnAzClMnYjMzNzcxNzYwYTY3MDFlZWY5MzQ0NTQxMTZkZGFmZmYxNjU1ZDE4OScKcDQKcy4='  # protocol 0
    #DUMPED = '21a5b6828ff581f159bde0a239bad021eb14c47a:gAJ9cQAoVQNhcnJxAV1xAihLAUsCSwNlVQNfaWRxA1UoYjMzNzcxNzYwYTY3MDFlZWY5MzQ0NTQxMTZkZGFmZmYxNjU1ZDE4OXEEdS4='  # protocol 2
    DUMPED = '5625ed5946a5f39bd2aef3f6e3c609ec5cd1f8f2:gAJ9cQEoVQNhcnJxAl1xAyhLAUsCSwNlVQNfaWRxBFUoYjMzNzcxNzYwYTY3MDFlZWY5MzQ0NTQxMTZkZGFmZmYxNjU1ZDE4OXEFdS4='
    HTTP_COOKIE = k8.CookieStoreSession.cookie_name + '=' + DUMPED

    def _sess(self, **kwargs):
        return k8.CookieStoreSession(*_r(**kwargs))

    def test___init__(self):
        #sess = self._sess()
        with spec("if secret_key is not specified then raises exception"):
            try:
                k8.config.secret_key = ''
                def f():
                    k8.CookieStoreSession(*_r())
                ok (f).raises(ValueError, "'config.secret_key' should be set.")
            finally:
                k8.config.secret_key = secret_key
        with spec("restore session id and values from cookie value"):
            sess = self._sess(HTTP_COOKIE=self.HTTP_COOKIE)
            ok (sess.values) == self.VALUES
            ok (sess.id) == self.SID
        with spec("create empty values if session cookie is not found"):
            sess = self._sess()
            ok (sess.values) == {'_id': sess.id}
            ok (sess.id).is_a(str)
            ok (len(sess.id)) == len(self.SID)

    def test_save(self):
        sess = self._sess()
        sess['foo'] = 'FOO'
        with spec("sets cookie value"):
            cookie_val = sess.cookie.value
            sess.save()
            ok (sess.cookie.value) != cookie_val
            values = sess._load_values(sess.cookie.value)
            ok ('foo' in values) == True
            ok (values['foo']) == 'FOO'

    def test__load_values(self):
        sess = self._sess()
        with spec("load values from str"):
            ok (sess._load_values(self.DUMPED)) == self.VALUES
        with spec("if cookie value is invalid then return None"):
            ok (sess._load_values('x' + self.DUMPED)) == None

    def test__dump_values(self):
        sess = self._sess()
        with spec("dumps values into str"):
            ok (sess._dump_values(self.VALUES)) == self.DUMPED



if __name__ == '__main__':
    oktest.run()
