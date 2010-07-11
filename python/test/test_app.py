# -*- coding: utf-8 -*-
from __future__ import with_statement

import sys, re
from oktest import ok, not_ok, run, spec
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


class StartResponse(object):

    def __call__(self, status, headers):
        self.status = status
        self.headers = headers


class K8MainApplicationTest(object):

    def test_mount(self):
        def welcome(req, res):
            return "Welcome!"
        class HelloHandler(Handler):
            def do_index(self, *args):
                return "args=%r" % (args, )
            def do_show(self, *args):
                return "do_show(): args=%r" % (args, )
            router = Router()
            router.map("", GET=do_index)
            router.map("/(\d+)", GET=do_show)
        #
        app = MainApplication()
        app.map("/welcome", GET=welcome)
        app.mount("/hello", HelloHandler)
        with spec("keep arguments"):
            #ok (app.mappings) == [
            #    ('/welcome', None, welcome, None),
            #    ('/hello', None, HelloHandler.handle, HelloHandler),
            #]
            pass
        with spec("calls router.set_base_path()"):
            ok (HelloHandler.router.base_path) == '/hello'
            ok (HelloHandler.do_index.path()) == '/hello'
            ok (HelloHandler.do_show.path(123)) == '/hello/123'

    def test___call__(self):
        def welcome(req, res):
            return "Welcome!"
        class HelloHandler(Handler):
            def do_index(self, *args):
                return "args=%r" % (args, )
            def do_show(self, *args):
                return "do_show: %r" % (args, )
            def do_update(self, *args):
                return "do_update: %r" % (args, )
            def do_edit(self, *args):
                return "do_edit: %r" % (args, )
            router = Router()
            router.map("", GET=do_index)
            router.map("/(\d+)", GET=do_show, PUT=do_update)
            router.map("/(\d+)/edit", GET=do_edit)
            router.mount("/(\d+)/lazy", "my.handlers.OnDemandHandler")  # lazy
        #
        app = MainApplication()
        app.map("/welcome", GET=welcome)
        app.mount("/hello", HelloHandler)
        #
        with spec("request mathched to action function then it will be called"):
            env = dummy_env('GET', '/welcome')
            start_response = StartResponse()
            ok (app(env, start_response)) == ["Welcome!"]
            ok (start_response.status) == '200 OK'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8')]
        with spec("request matched to handler class then instance object is created and request is delegaded to it"):
            env = dummy_env('GET', '/hello')
            start_response = StartResponse()
            ok (app(env, start_response)) == ["args=()"]
            ok (start_response.status) == '200 OK'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8')]
            #
            env = dummy_env('GET', '/hello/123')
            start_response = StartResponse()
            ok (app(env, start_response)) == ["do_show: ('123',)"]
            ok (start_response.status) == '200 OK'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8')]
            #
            env = dummy_env('PUT', '/hello/123')
            start_response = StartResponse()
            ok (app(env, start_response)) == ["do_update: ('123',)"]
            ok (start_response.status) == '200 OK'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8')]
        with spec("if request path is not matched then set status to 404 Not Found"):
            env = dummy_env('POST', '/hello/new')
            start_response = StartResponse()
            ok (app(env, start_response)) == ["<h2>404 Not Found</h2>\n<p>/hello/new: not found.</p>\n"]
            ok (start_response.status) == '404 Not Found'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8'), ]
        with spec("if request method is not matched then set status to 405 Method Not Allowed"):
            env = dummy_env('POST', '/hello/123')
            start_response = StartResponse()
            ok (app(env, start_response)) == ["<h2>405 Method Not Allowed</h2>\n<p>POST: method not allowed.</p>\n"]
            ok (start_response.status) == '405 Method Not Allowed'
            ok (start_response.headers) == [('Content-Type', 'text/html; charset=utf-8'), ]
        with spec("if lazy load class name is specified then load class on demand"):
            env = dummy_env('PUT', '/hello/123/lazy/999')
            start_response = StartResponse()
            ok (app(env, start_response)) == ["OnDemandHandler#do_update: ('123', '999')"]

    def test_run(self):
        pass

    def test_find_handler(self):
        def welcome(req, res):
            return "Welcome!"
        class HelloHandler(Handler):
            def do_index(self, *args):
                return "args=%r" % (args, )
            router = Router()
            router.map("", GET=do_index)
        #
        app = MainApplication()
        app.map("/welcome", GET=welcome)
        app.mount("/hello", HelloHandler)
        #
        with spec("returns mapped action function"):
            req = Request(dummy_env('GET', '/welcome'))
            ok (app.find_handler(req)) == welcome
        with spec("returns handle() method of mapped class"):
            req = Request(dummy_env('GET', '/hello'))
            ok (app.find_handler(req)) == HelloHandler.handle
        with spec("if request path not found then raises 404 not found"):
            pass
        with spec("if request method not matched then raises 405 method not allowed"):
            pass


if __name__ == '__main__':
    run(K8MainApplicationTest)
