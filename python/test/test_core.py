# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

import sys, re
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO

import oktest
from oktest import ok, not_ok
import keight as k8

class KeightRequestTest(object):

    def test___init__(self):
        if "called then sets attributes":
            body = 'name=Keight'
            env = k8.dummy_env('GET', '/hello', qs='name=World', body=body)
            req = k8.Request(env)
            ok (req.env).is_(env)
            ok (req.method) == 'GET'
            ok (req.uri) == '/hello?name=World'
            ok (req.path) == '/hello'
            ok (req.content_length) == len(body)
        if "request body is empty then content length is None":
            env = k8.dummy_env('GET', body='')
            req = k8.Request(env)
            ok (req.content_length) == None
        if "GET method then only query string is parsed":
            env = k8.dummy_env('GET', qs='name=World', body='name=Keight')
            req = k8.Request(env)
            ok (req.params).is_a(k8.Params)
            ok (req.params.values) == {'name': 'World'}
        if "GET method then only query string is parsed":
            env = k8.dummy_env('GET', qs='name1=World', body='name2=Keight')
            req = k8.Request(env)
            ok (req.params).is_a(k8.Params)
            ok (req.params.values) == {'name1': 'World'}
        if "POST or PUT method then only request body is parsed":
            env = k8.dummy_env('POST', qs='name1=World', body='name2=Keight')
            req = k8.Request(env)
            ok (req.params).is_a(k8.Params)
            ok (req.params.values) == {'name2': 'Keight'}

    def test__parse_query_string(self):
        f = k8.Request.parse_query_string
        if "called then returns dict":
            ok (f("a=10&b=20")) == {'a': '10', 'b': '20'}
        if "separater is ';' then parsed as well as '&'":
            ok (f("a=10;b=20")) == {'a': '10', 'b': '20'}
        if "url escaped then unescape it":
            ok (f("%5Barr%5D=%5b123%5d")) == {'[arr]': '[123]'}
        if "param name ends with '[]' then value is list":
            ok (f("a%5B%5D=111&a%5B%5D=222")) == {'a[]': ['111','222']}
            ok (f("a%5B%5D=111&a%5B%5D=222")) == {'a[]': ['111','222']}
        if "value is omitted then empty string is assumed":
            ok (f("a=&b=")) == {'a': '', 'b': ''}
            ok (f("a%5B%5D=")) == {'a[]': ['']}
        if "'=' is missing then value is empty string":
            ok (f("abc")) == {'abc': ''}
            ok (f("a%5B%5D")) == {'a[]': ['']}


class KeightResponseTest(object):

    def before(self):
        self.res = k8.Response()

    def test___init__(self):
        if "created then set status code to 200":
            ok (self.res.status) == 200
        if "created then content type is set to 'text/html; charset=utf-8'":
            ok (self.res.headers[0]) == ('Content-Type', 'text/html; charset=utf-8')

    def test_set_status(self):
        if "status_code is valid then set it to attr":
            self.res.set_status(404)
            ok (self.res.status) == 404
        if "status_code is unknown then raises ValueError":
            def f():
                self.res.set_status(999)
            ok (f).raises(ValueError, '999: unknown status code.')

    def test_get_status_str(self):
        if "called then status code and message":
            ok (self.res.get_status_str()) == '200 OK'
            self.res.set_status(404)
            ok (self.res.get_status_str()) == '404 Not Found'

    def test_set_content_type(self):
        if "called then sets content type":
            self.res.set_content_type('text/plain')
            ok (self.res.headers[0]) == ('Content-Type', 'text/plain')

    def test_get_content_type(self):
        if "called then returns content type":
            ok (self.res.get_content_type()) == 'text/html; charset=utf-8'
            self.res.set_content_type('text/plain')
            ok (self.res.get_content_type()) == 'text/plain'

    def test_set_encoding(self):
        if "called then set encoding and changes content type":
            self.res.set_encoding('ISO8859-1')
            ok (self.res.encoding) == 'ISO8859-1'
            ok (self.res.headers[0][1]) == 'text/html; charset=ISO8859-1'

    def test_add_header(self):
        if "called then add header":
            ok (len(self.res.headers)) == 1
            self.res.add_header('Content-Length', '100')
            ok (len(self.res.headers)) == 2
            ok (self.res.headers[1]) == ('Content-Length', '100')

    def test_add_cookie(self):
        ## TODO
        pass

    def test_set_redirect(self):
        url = 'http://localhost/login'
        if "called then set status code to 301 or 302":
            self.res.set_redirect(url)
            ok (self.res.status) == 302
            self.res.set_redirect(url, True)
            ok (self.res.status) == 301
        if "called then set Location header":
            ok (self.res.headers[1]) == ('Location', url)

    def test_build(self):
        if "called then returns http response string":
            ok (self.res.build()) == """Status: 200 OK\r
Content-Type: text/html; charset=utf-8\r
\r\n"""
            url = 'http://localhost/login'
            self.res.set_redirect(url)
            ok (self.res.build()) == """Status: 302 Found\r
Content-Type: text/html; charset=utf-8\r
Location: %s\r
\r\n""" % url


class KeightRouterTest(object):

    def test___init__(self):
        if "called then set base_path":
            router = k8.Router('/hello')
            ok (router.base_path) == '/hello'
        if "called with path pattern then set base_path_rexp too":
            router = k8.Router('/hello/(\d+)')
            ok (router.base_path) == '/hello/(\d+)'
            ok (router.base_path_rexp) == re.compile('/hello/(\d+)')

    def test_map(self):
        def do_index(): pass
        def do_show(): pass
        def do_new(): pass
        def do_create(): pass
        def do_edit(): pass
        def do_update(): pass
        def do_delete(): pass
        if "called then sets mappings":
            r = k8.Router('/hello')
            r.map('/', GET=do_index, POST=do_create)
            r.map('/new', GET=do_new)
            r.map('/(\d+)', GET=do_show, PUT=do_update, DELETE=do_delete)
            r.map('/(\d+)/edit', GET=do_edit)
            L = r.mappings
            x = re.compile
            ok (L[0]) == ('/', x('/$'), dict(GET=do_index, POST=do_create))
            ok (L[1]) == ('/new',x('/new$'), dict(GET=do_new))
            ok (L[2]) == ('/(\d+)', x('/(\d+)$'), dict(GET=do_show, PUT=do_update, DELETE=do_delete))
            ok (L[3]) == ('/(\d+)/edit', x('/(\d+)/edit$'), dict(GET=do_edit))
        if "called then sets path functions":
            t = type(lambda x: x)
            ok (do_index.path).is_a(t)
            ok (do_show.path).is_a(t)
            ok (do_new.path).is_a(t)
            ok (do_create.path).is_a(t)
            ok (do_edit.path).is_a(t)
            ok (do_update.path).is_a(t)
            ok (do_delete.path).is_a(t)
            ok (do_index.path()) == '/hello/'
            ok (do_show.path(123)) == '/hello/123'
            ok (do_new.path()) == '/hello/new'
            ok (do_create.path()) == '/hello/'
            ok (do_edit.path(123)) == '/hello/123/edit'
            ok (do_update.path(123)) == '/hello/123'
            ok (do_delete.path(123)) == '/hello/123'

    def test_route(self):
        def do_index(): pass
        def do_show(): pass
        def do_new(): pass
        def do_create(): pass
        def do_edit(): pass
        def do_update(): pass
        def do_delete(): pass
        r = k8.Router('/hello')
        r.map('/', GET=do_index, POST=do_create)
        r.map('/new', GET=do_new)
        r.map('/(\d+)', GET=do_show, PUT=do_update, DELETE=do_delete)
        r.map('/(\d+)/edit', GET=do_edit)
        if "called then returns mapped object, args, and rest path":
            ok (r.route('GET', '/hello/')) == (do_index, (), '')
            ok (r.route('POST', '/hello/')) == (do_create, (), '')
            ok (r.route('GET', '/hello/new')) == (do_new, (), '')
            ok (r.route('GET', '/hello/123')) == (do_show, ('123',), '')
            ok (r.route('PUT', '/hello/123')) == (do_update, ('123',), '')
            ok (r.route('DELETE', '/hello/123')) == (do_delete, ('123',), '')
            ok (r.route('GET', '/hello/123/edit')) == (do_edit, ('123',), '')
        if "not found then returns None":
            ok (r.route('GET', '/hello/create')) == None
        if "no mappped item then returns False":
            ok (r.route('POST', '/hello/new')) == False

    def test_handle(self):
        pass

    def test_dispatch(self):
        pass


class KeightControllerTest(object):

    def test___init__(self):
        if "called then accept request and response object":
            req = k8.Request(k8.dummy_env())
            res = k8.Response()
            c = k8.Controller(req, res)
            ok (c.request).is_(req)
            ok (c.response).is_(res)

    def test_handle_1(self):
        ## base path is non-pattern string
        class HelloController(k8.Controller):
            def do_index(self):
                return "<p>action_name=%r</p>" % self.action_name
            def do_show(self, id):
                return "<p>action_name=%r, id=%r</p>" % (self.action_name, id)
            def do_update(self, id):
                return "<p>action_name=%r, id=%r</p>" % (self.action_name, id)
            router = k8.Router('/hello')
            router.map('/', GET=do_index)
            router.map('/(\d+)', GET=do_show, PUT=do_update)
        if "case GET /hello/":
            req = k8.Request(k8.dummy_env('GET', '/hello/'))
            res = k8.Response()
            result = HelloController.handle(req, res)
            ok (result) == "<p>action_name='do_index'</p>"
        if "case GET /hello/123":
            req = k8.Request(k8.dummy_env('GET', '/hello/123'))
            res = k8.Response()
            result = HelloController.handle(req, res)
            ok (result) == "<p>action_name='do_show', id='123'</p>"
        if "case PUT /hello/123":
            req = k8.Request(k8.dummy_env('PUT', '/hello/123'))
            res = k8.Response()
            result = HelloController.handle(req, res)
            ok (result) == "<p>action_name='do_update', id='123'</p>"

    def test_handle_2(self):
        ## base path contains '(\d+)' or so
        class CommentsController(k8.Controller):
            def do_index(self, *args):
                return "<p>action_name=%r, args=%r</p>" % (self.action_name, args)
            def do_show(self, *args):
                return "<p>action_name=%r, args=%r</p>" % (self.action_name, args)
            def do_update(self, *args):
                return "<p>action_name=%r, args=%r</p>" % (self.action_name, args)
            router = k8.Router('/posts/(\d+)/comments')
            router.map('', GET=do_index)
            router.map('/(\d+)', GET=do_show, PUT=do_update)
        if "case GET /posts/123/comments":
            req = k8.Request(k8.dummy_env('GET', '/posts/123/comments'))
            res = k8.Response()
            result = CommentsController.handle(req, res)
            ok (result) == "<p>action_name='do_index', args=('123',)</p>"
        if "case GET /posts/123/comments/456":
            req = k8.Request(k8.dummy_env('GET', '/posts/123/comments/456'))
            res = k8.Response()
            result = CommentsController.handle(req, res)
            ok (result) == "<p>action_name='do_show', args=('123', '456')</p>"
        if "case PUT /posts/123/comments/456":
            req = k8.Request(k8.dummy_env('PUT', '/posts/123/comments/456'))
            res = k8.Response()
            result = CommentsController.handle(req, res)
            ok (result) == "<p>action_name='do_update', args=('123', '456')</p>"


if __name__ == '__main__':
    oktest.run('Keight.*Test')
