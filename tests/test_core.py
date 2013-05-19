# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

from __future__ import with_statement

import sys, re, time
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

from oktest import ok, not_ok, run, spec
import keight as k8
from keight import Request, Response, Params, dummy_env


class RequestTest(object):

    def test___init__(self):
        with spec("sets attributes"):
            body = 'name=Keight'
            env = dummy_env('GET', '/hello', qs='name=World', body=body)
            req = Request(env)
            ok (req.env).is_(env)
            ok (req.method) == 'GET'
            ok (req.uri) == '/hello?name=World'
            ok (req.path) == '/hello'
            ok (req.content_length) == len(body)
        with spec("if request body is empty then content length is None"):
            env = dummy_env('GET', body='')
            req = Request(env)
            ok (req.content_length) == None
        with spec("if GET method then only query string is parsed"):
            env = dummy_env('GET', qs='x=1', body='y=2')
            req = Request(env)
            ok (req.params).is_a(Params)
            ok (req.params.values) == {'x': '1'}
        with spec("if POST or PUT method then only request body is parsed"):
            env = dummy_env('POST', qs='x=1', body='y=2')
            req = Request(env)
            ok (req.params).is_a(Params)
            ok (req.params.values) == {'y': '2'}
        with spec("parses cookie"):
            pass  ## TODO

    def test_parse_query_string(self):
        f = Request(False).parse_query_string
        with spec("returns a dict"):
            ok (f("a=10&b=20")) == {'a': '10', 'b': '20'}
        with spec("if separater is ';' then parsed as well as '&'"):
            ok (f("a=10;b=20")) == {'a': '10', 'b': '20'}
        with spec("if url-escaped then unescape it"):
            ok (f("%5Barr%5D=%5b123%5d")) == {'[arr]': '[123]'}
        with spec("if param name ends with '[]' then value is list"):
            ok (f("a%5B%5D=111&a%5B%5D=222")) == {'a[]': ['111','222']}
            ok (f("a%5B%5D=111&a%5B%5D=222")) == {'a[]': ['111','222']}
        with spec("if value is omitted then empty string is assumed"):
            ok (f("a=&b=")) == {'a': '', 'b': ''}
            ok (f("a%5B%5D=")) == {'a[]': ['']}
        with spec("if '=' is missing then value is empty string"):
            ok (f("abc")) == {'abc': ''}
            ok (f("a%5B%5D")) == {'a[]': ['']}


class ResponseTest(object):

    def before(self):
        self.res = Response()

    def test___init__(self):
        with spec("set status code to 200"):
            ok (self.res.status) == 200
        with spec("content type is set to 'text/html; charset=utf-8'"):
            ok (self.res.headers[0]) == ('Content-Type', 'text/html; charset=utf-8')

    def test_set_status(self):
        with spec("if status_code is valid then set it to attr"):
            self.res.set_status(404)
            ok (self.res.status) == 404
        with spec("if status_code is unknown then raises ValueError"):
            def f():
                self.res.set_status(999)
            ok (f).raises(ValueError, '999: unknown status code.')

    def test_get_status_str(self):
        with spec("returns status code and message"):
            ok (self.res.get_status_str()) == '200 OK'
            self.res.set_status(404)
            ok (self.res.get_status_str()) == '404 Not Found'

    def test_set_content_type(self):
        with spec("sets content type"):
            self.res.set_content_type('text/plain')
            ok (self.res.headers[0]) == ('Content-Type', 'text/plain')

    def test_get_content_type(self):
        with spec("returns content type"):
            ok (self.res.get_content_type()) == 'text/html; charset=utf-8'
            self.res.set_content_type('text/plain')
            ok (self.res.get_content_type()) == 'text/plain'

    def test_set_encoding(self):
        with spec("sets encoding and changes content type"):
            self.res.set_encoding('ISO8859-1')
            ok (self.res.encoding) == 'ISO8859-1'
            ok (self.res.headers[0][1]) == 'text/html; charset=ISO8859-1'

    def test_add_header(self):
        with spec("adds header"):
            ok (len(self.res.headers)) == 1
            self.res.add_header('Content-Length', '100')
            ok (len(self.res.headers)) == 2
            ok (self.res.headers[1]) == ('Content-Length', '100')

    def test_add_cookie(self):
        ## TODO
        pass

    def test_set_redirect(self):
        url = 'http://localhost/login'
        with spec("if permantently is False then sets status code to 302"):
            self.res.set_redirect(url)
            ok (self.res.status) == 302
        with spec("if permantently is True then sets status code to 301"):
            self.res.set_redirect(url, True)
            ok (self.res.status) == 301
        with spec("set Location header"):
            ok (self.res.headers[1]) == ('Location', url)

    def test_build(self):
        with spec("returns http response string"):
            ok (self.res.build()) == """Status: 200 OK\r
Content-Type: text/html; charset=utf-8\r
\r\n"""
            url = 'http://localhost/login'
            self.res.set_redirect(url)
            ok (self.res.build()) == """Status: 302 Found\r
Content-Type: text/html; charset=utf-8\r
Location: %s\r
\r\n""" % url


class CookieTest(object):

    def test___init__(self):
        with spec("takes name, value, path, domain, expires, and secore args"):
            cookie = k8.Cookie('x', 'y', '/', 'example.com', 30, True)
            ok (cookie.name) == 'x'
            ok (cookie.value) == 'y'
            ok (cookie.path) == '/'
            ok (cookie.domain) == 'example.com'
            ok (cookie.expires) == 30
            ok (cookie.secure) == True

    def test___str__(self):
        with spec("converts into str"):
            cookie = k8.Cookie('x', 'y', '/', 'example.com', time.gmtime(1), True)
            ok (str(cookie)) == 'x=y; path=/; domain=example.com; expires=Thu, 01 Jan 1970 00:00:01 GMT; secure'
        with spec("if 'expires' is integer then regard it as seconds"):
            cookie = k8.Cookie('x', 'y', expires=30)
            while True:
                t1 = time.time()
                actual = str(cookie)
                t2 = time.time()
                if int(t1) == int(t2):
                    break
            ok (actual) == 'x=y; expires=' + k8.rfc1123_gmt(time.gmtime(t1 + 30))
        with spec("quotes name and value"):
            cookie = k8.Cookie('x[1]', 'AAA<&> BBB')
            ok (str(cookie)) == 'x%5B1%5D=AAA%3C%26%3E%20BBB'
        with spec("handles unicode object"):
            cookie = k8.Cookie(u'名前', u'値')
            ok (str(cookie)) == '%540D%524D=%5024'

    def test__calc_expires(self):
        with spec("if 'expires' is not an int then returns it"):
            cookie = k8.Cookie('x', 'y', expires=time.gmtime(0))
            ok (cookie._calc_expires()) == time.gmtime(0)
            cookie.expires = None
            ok (cookie._calc_expires()) == None
        with spec("if 'expires' is int then returns time.gmtime(time.time()+expires)"):
            cookie = k8.Cookie('x', 'y', expires=30)
            while True:
                t1 = time.time()
                actual = str(cookie)
                t2 = time.time()
                if int(t1) == int(t2):
                    break
            ok (cookie.expires) == 30
            ok (cookie._calc_expires()) == time.gmtime(t1+30)



if __name__ == '__main__':
    run()
