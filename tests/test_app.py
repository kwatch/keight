# -*- coding: utf-8 -*-
from __future__ import with_statement

import sys, os, re
from oktest import ok, not_ok, run, spec
from oktest.helper import dummy_environ_vars
import keight as k8
from keight import MainApplication, Handler, Router, dummy_env, Request, Response


class OnDemandHandler(Handler):
    def do_show(self, *args):
        return "OnDemandHandler#do_show: %r" % (args, )
    def do_update(self, *args):
        return "OnDemandHandler#do_update: %r" % (args, )
    router = Router()
    router.map("/(\d+)", GET=do_show, PUT=do_update)

mod1 = type(sys)('my')
mod2 = type(sys)('my.handlers')
mod1.handlers = mod2
mod2.OnDemandHandler = OnDemandHandler
sys.modules['my'] = mod1
sys.modules['my.handlers'] = mod2


class ApplicationTest(object):

    def test___call__(self):
        class DummyApplication(k8.Application):
            def __init__(self, content):
                self.content = content
            def find_handler(self, request):
                def f(request, response):
                    self._request = request
                    self._response = response
                    return self.content
                return f
        _env = k8.dummy_env
        _res = k8.StartResponse
        with spec("creates request and response objects"):
            app = DummyApplication("hello")
            ret = app(_env(), _res())
            ok (app._request).is_a(k8.REQUEST)
            ok (app._response).is_a(k8.RESPONSE)
            req, res = app._request, app._response
            ret = app(_env(), _res())
            not_ok (app._request).is_(req)
            not_ok (app._response).is_(res)
        with spec("handles request and get content"):
            ok (ret) == [app.content]
        with spec("converts content into iterable object"):
            app = DummyApplication("str")
            ok (app(_env(), _res())) == ["str"]
            app = DummyApplication(u"unicode")
            ok (app(_env(), _res())) == ["unicode"]
            app = DummyApplication(None)
            ok (app(_env(), _res())) == [""]
            app = DummyApplication(('A', 'B', 'C'))
            ok (app(_env(), _res())) == ('A', 'B', 'C')
        with spec("calls start_response"):
            start_resp = k8.StartResponse()
            assert start_resp.status is None
            assert start_resp.headers is None
            app(_env(), start_resp)
            ok (start_resp.status) == '200 OK'
            ok (start_resp.headers) == [ ('Content-Type', 'text/html; charset=utf-8') ]
        with spec("releases request and response objects"):
            ok (len(app._request.__dict__)) == 0
            ok (len(app._response.__dict__)) == 0
        with spec("returns iterable object"):
            ret = app(_env(), start_resp)
            ok (hasattr(ret, '__iter__')) == True

    def test_run(self):
        class DummyCGIHandler(object):
            _instance = None
            def __init__(self):
                self.__class__._instance = self
            def run(self, app):
                self.app = app
        k8._CGIHandler = DummyCGIHandler
        with spec("if debug is False then wraps by ProductionMiddleware"):
            app = k8.Application()
            ok (app.run()).is_a(k8.ProductionMiddleware)
        with spec("if debug is True then wraps by DevelopmentMiddleware"):
            app = k8.Application()
            ok (app.run(debug=True)).is_a(k8.DevelopmentMiddleware)
        with spec("invokes wsgiref.handlers.CGIHandler().run(app)"):
            DummyCGIHandler._instance = None
            app = k8.Application().run()
            ok (DummyCGIHandler._instance.app).is_(app)


class MainApplicationTest(object):

    def test_map(self):
        def hello(req, res):
            return "Hello"
        app = k8.MainApplication()
        with spec("if path is None then detect it from $SCRIPT_NAME."):
            v = os.environ.get('SCRIPT_NAME')
            with dummy_environ_vars(SCRIPT_NAME='/aaa/bbb/index.cgi'):
                assert os.environ.get('SCRIPT_NAME') == '/aaa/bbb/index.cgi'
                app.map(None, GET=hello)
                ok (app.router.mappings) == [('/aaa/bbb', {'GET':hello}, None)]
            assert os.environ.get('SCRIPT_NAME') == v
        with spec("returns self"):
            ret = app.map('/foo', GET=hello)
            ok (ret).is_(app)

    def test_mount(self):
        app = k8.MainApplication()
        with spec("sets base_path of handler_class automatically"):
            class HelloHandler1(k8.Handler):
                def do_index(self, *args): return ""
                def do_show(self, *args):  return ""
                router = k8.Router().map("", GET=do_index) \
                                    .map("/(\d+)", GET=do_show)
            assert HelloHandler1.router.base_path is None
            assert not hasattr(HelloHandler1.do_index, 'path')
            assert not hasattr(HelloHandler1.do_index, 'method')
            #
            app.mount("/hello", HelloHandler1)
            ok (HelloHandler1.router.base_path) == '/hello'
            ok (HelloHandler1.do_index.path()) == '/hello'
            ok (HelloHandler1.do_show.path(123)) == '/hello/123'
        with spec("if path is None then detect it from $SCRIPT_NAME."):
            class HelloHandler2(k8.Handler):
                def do_index(self, *args): return ""
                def do_show(self, *args):  return ""
                router = k8.Router().map("/", GET=do_index) \
                                    .map("/(\d+)", GET=do_show)
            #
            v = os.environ.get('SCRIPT_NAME')
            with dummy_environ_vars(SCRIPT_NAME='/A/B/index.cgi'):
                assert os.environ.get('SCRIPT_NAME') == '/A/B/index.cgi'
                app.mount(None, HelloHandler2)
            assert os.environ.get('SCRIPT_NAME') == v
            ok (HelloHandler2.router.base_path) == '/A/B'
            ok (HelloHandler2.do_index.path()) == '/A/B/'
            ok (HelloHandler2.do_show.path(123)) == '/A/B/123'
        with spec("returns self"):
            class HelloHandler3(k8.Handler):
                router = k8.Router()
            ret = app.mount("/foo", HelloHandler3)
            ok (ret).is_(app)

    def test_default_root_path(self):
        with spec("if $SCRIPT_NAME is not set then returns None."):
            assert os.environ.get('SCRIPT_NAME') is None
            ok (k8.MainApplication.default_root_path()) == None
            with dummy_environ_vars(SCRIPT_NAME=''):
                ok (k8.MainApplication.default_root_path()) == None
        with spec("if $SCRIPT_NAME is set then returns it's dirname."):
            v = os.environ.get('SCRIPT_NAME')
            with dummy_environ_vars(SCRIPT_NAME='/x/y/index.cgi'):
                assert os.environ.get('SCRIPT_NAME') == '/x/y/index.cgi'
                ok (k8.MainApplication.default_root_path()) == '/x/y'
            assert os.environ.get('SCRIPT_NAME') == v

    def test_find_handler(self):
        def welcome(req, res):
            return "Welcome!"
        def do_comment(req, res): return ""
        class HelloHandler(k8.Handler):
            def do_index(self, *args):  return "args=%r" % (args, )
            def do_show(self, id): return ""
            router = Router().map("", GET=do_index)\
                             .map("/(\d+)", GET=do_show)
        #
        app = k8.MainApplication()
        app.map(r"/welcome", GET=welcome)
        app.mount(r"/hello", HelloHandler)
        app.map(r"/entry/(\d+)/comment/(\d+)", GET=do_comment)
        #
        with spec("if request is matched to mapped action function then returns it"):
            req = k8.Request(dummy_env('GET', '/welcome'))
            ok (app.find_handler(req)) == welcome
            req = k8.Request(dummy_env('GET', '/entry/123/comment/999'))
            ok (app.find_handler(req)) == do_comment
        with spec("if request is matched to mounted handler class then returns it's handle() method"):
            req = k8.Request(dummy_env('GET', '/hello'))
            ok (app.find_handler(req)) == HelloHandler.handle
        with spec("sets args to request object"):
            req = k8.Request(dummy_env('GET', '/hello/123'))
            app.find_handler(req)
            ok (req.args) == ()   # TODO: should be ('123')?
            req = k8.Request(dummy_env('GET', '/entry/123/comment/999'))
            app.find_handler(req)
            ok (req.args) == ('123', '999')
        with spec("if request path is not found then raises 404 not found"):
            req = k8.Request(dummy_env('GET', '/index'))
            def f(): app.find_handler(req)
            ok (f).raises(k8.Http404NotFound, '/index: not found.')
        with spec("if request method is not matched (to mapped function) then raises 405 method not allowed"):
            req = k8.Request(dummy_env('POST', '/welcome'))
            def f(): app.find_handler(req)
            ok (f).raises(k8.Http405MethodNotAllowed, 'POST: method not allowed.')

    def test_FUNCTEST___call__(self):
        def welcome(req, res):
            return "Welcome!"
        class HelloHandler(Handler):
            def do_index(self, *args):  return "args=%r" % (args, )
            def do_show(self, *args):   return "do_show: %r" % (args, )
            def do_update(self, *args): return "do_update: %r" % (args, )
            def do_edit(self, *args):   return "do_edit: %r" % (args, )
            router = Router()
            router.map("", GET=do_index)
            router.map("/(\d+)", GET=do_show, PUT=do_update)
            router.map("/(\d+)/edit", GET=do_edit)
            router.mount("/(\d+)/lazy", "my.handlers.OnDemandHandler")  # lazy
        #
        app = k8.MainApplication()
        app.map("/welcome", GET=welcome)
        app.mount("/hello", HelloHandler)
        #
        with spec("[F] if request is matched to handler class then calls action function"):
            env = dummy_env('GET', '/welcome')
            start_response = k8.StartResponse()
            ok (app(env, start_response)) == ["Welcome!"]
            ok (start_response.status) == '200 OK'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8')]
        with spec("[F] if request is matched to handler class then instance object is created and request is delegaded to it"):
            env = dummy_env('GET', '/hello')
            start_response = k8.StartResponse()
            ok (app(env, start_response)) == ["args=()"]
            ok (start_response.status) == '200 OK'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8')]
            #
            env = dummy_env('GET', '/hello/123')
            start_response = k8.StartResponse()
            ok (app(env, start_response)) == ["do_show: ('123',)"]
            ok (start_response.status) == '200 OK'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8')]
            #
            env = dummy_env('PUT', '/hello/123')
            start_response = k8.StartResponse()
            ok (app(env, start_response)) == ["do_update: ('123',)"]
            ok (start_response.status) == '200 OK'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8')]
        with spec("[F] if request path is not matched then set status to 404 Not Found"):
            env = dummy_env('POST', '/hello/new')
            start_response = k8.StartResponse()
            ok (app(env, start_response)) == ["<h2>404 Not Found</h2>\n<p>/hello/new: not found.</p>\n"]
            ok (start_response.status) == '404 Not Found'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8'), ]
        with spec("[F] if request method is not matched then set status to 405 Method Not Allowed"):
            env = dummy_env('POST', '/hello/123')
            start_response = k8.StartResponse()
            ok (app(env, start_response)) == ["<h2>405 Method Not Allowed</h2>\n<p>POST: method not allowed.</p>\n"]
            ok (start_response.status) == '405 Method Not Allowed'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8'), ]
        with spec("[F] if lazy load class name is specified then load class on demand"):
            env = dummy_env('PUT', '/hello/123/lazy/999')
            start_response = k8.StartResponse()
            ok (app(env, start_response)) == ["OnDemandHandler#do_update: ('123', '999')"]


class CGIApplicationTest(object):

    def test___init__(self):
        with spec("if handler is class object but not subclass of Handler then raises error"):
            class DummyHandler1(object):
                @classmethod
                def handle(cls, req, res):
                    return ""
            def f(): k8.CGIApplication(DummyHandler1)
            ok (f).raises(TypeError, "DummyHandler1: Handler subclass is expected.")
        with spec("if function is not found in handler class then raises error"):
            class DummyHandler2(k8.Handler):
                def do_hello(self): return ""
            def f(): k8.CGIApplication(DummyHandler2, GET='do_index')
            ok (f).raises(ValueError, "GET='do_index': function not found in DummyHandler2 class.")
        with spec("if handler is Handler subclass then create new handler function"):
            class DummyHandler3(k8.Handler):
                def do_hello(self): return "do_hello() called."
                def do_create(self): return "do_create() called."
            app = k8.CGIApplication(DummyHandler3, GET='do_hello', POST='do_create')
            ok (app.mapping['GET']).is_a(type(lambda: 0))
            ok (app.mapping['POST']).is_a(type(lambda: 0))
            ok (app.mapping['GET'].func_name) == 'do_hello'
            ok (app.mapping['POST'].func_name) == 'do_create'
            env = k8.dummy_env()
            req = k8.REQUEST(env)
            res = k8.RESPONSE()
            ok (app.mapping['GET'](req, res)) == "do_hello() called."
            ok (app.mapping['POST'](req, res)) == "do_create() called."
        with spec("if handler is function then it will be invoked in any request method"):
            def do_welcome(request, response):
                return "do_welcome() called"
            app = k8.CGIApplication(do_welcome)
            ok (app.mapping['ALL']).is_(do_welcome)
        with spec("if handler is not a function nor a class object then raises error"):
            def f(): k8.CGIApplication([1,2,3])
            ok (f).raises(TypeError, "[1, 2, 3]: handler should be function or Handler subclass.")

    def test_find_handler(self):
        class DummyHandler4(k8.Handler):
            def do_hello(self): return "do_hello() called."
            def do_create(self): return "do_create() called."
        app = k8.CGIApplication(DummyHandler4, GET='do_hello', POST='do_create')
        with spec("if handler is found then returns it"):
            req = k8.REQUEST(dummy_env('GET'))
            ok (app.find_handler(req).func_name) == 'do_hello'
        with spec("if handler is not found then raises Http405MethodNotAllowed"):
            req = k8.REQUEST(dummy_env('DELETE'))
            def f(): app.find_handler(req)
            ok (f).raises(k8.Http405MethodNotAllowed, "DELETE: method not allowed.")
        with spec("finds handler by request method"):
            req = k8.REQUEST(dummy_env('GET'))
            ok (app.find_handler(req).func_name) == 'do_hello'
            req = k8.REQUEST(dummy_env('POST'))
            ok (app.find_handler(req).func_name) == 'do_create'
            #
            def do_welcome(request, response):
                return "do_welcome() called."
            app = k8.CGIApplication(do_welcome)
            req = k8.REQUEST(dummy_env('GET'))
            ok (app.find_handler(req)) == do_welcome
            req = k8.REQUEST(dummy_env('POST'))
            ok (app.find_handler(req)) == do_welcome
            req = k8.REQUEST(dummy_env('DELETE'))
            ok (app.find_handler(req)) == do_welcome


if __name__ == '__main__':
    run()
