# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

from __future__ import with_statement

import sys, re
import oktest
from oktest import ok, not_ok, spec
from oktest.helper import using
import keight as k8


class DebugTest(object):
    pass


with using(DebugTest):

    def test_dummy_env(self):
        env = k8.dummy_env('GET', '/hello', {'x':1})
        with spec("returns dict object"):
            ok (env).is_a(dict)
        with spec("sets keys and values automatically"):
            ok (env['REQUEST_METHOD']) == 'GET'
            ok (env['PATH_INFO'])      == '/hello'
            ok (env['QUERY_STRING'])   == 'x=1'
            ok (env['REQUEST_URI'])    == '/hello?x=1'
            ok (env['wsgi.input']).is_a(k8._StringIO("").__class__)
            ok (env['wsgi.errors']).is_a(k8._StringIO().__class__)
        with spec("if qs is dict then converts it into query string"):
            env = k8.dummy_env('GET', qs=dict(x=1, y='&=[]'))
            ok (env['QUERY_STRING']).in_(['x=1&y=%26%3D%5B%5D', 'y=%26%3D%5B%5D&x=1'])
        with spec("if body is dict then converts it into query string"):
            env = k8.dummy_env('GET', body=dict(x=1, y='&=[]'))
            ok (env['wsgi.input'].getvalue()).in_(['x=1&y=%26%3D%5B%5D', 'y=%26%3D%5B%5D&x=1'])
        with spec("if POST and CONTENT_TYPE is not set then set it automatically"):
            env = k8.dummy_env('POST', body={'x':1})
            ok (env['REQUEST_METHOD']) == 'POST'
            ok (env['CONTENT_TYPE'])   == 'application/x-www-form-urlencoded'
            ok (env['wsgi.input'].getvalue()) == 'x=1'
        with spec("if POST and CONTENT_TYPE is already set then don't change it"):
            env = k8.dummy_env('POST', body="foo", CONTENT_TYPE="text/plain")
            ok (env['REQUEST_METHOD']) == 'POST'
            ok (env['CONTENT_TYPE'])   == 'text/plain'
            ok (env['wsgi.input'].getvalue()) == 'foo'
        with spec("if request body is specified then set CONTENT_LENGTH as string"):
            env = k8.dummy_env('POST', body={'x':1})
            ok (env['CONTENT_LENGTH']) == '3'
        with spec("if keyword args specified then adds them into env"):
            env = k8.dummy_env(REMOTE_ADDR='123.45.67.8')
            ok (env['REMOTE_ADDR'])    == '123.45.67.8'


if __name__ == '__main__':
    oktest.run()
