# -*- coding: utf-8 -*-
from __future__ import with_statement

import oktest
from oktest import ok, not_ok, run, spec
import keight as k8
from keight import Router, Handler, dummy_env, Request, Response, Http404NotFound, Http405MethodNotAllowed, Http301MovedPermanently


def _r(*args, **kwargs):
    env = dummy_env(*args, **kwargs)
    return (k8.REQUEST(env), k8.RESPONSE())


class HandlerTest(object):

    def test___init__(self):
        with spec("takes request and response"):
            req, res = _r()
            handler = Handler(req, res)
            ok (handler.request) == req
            ok (handler.response) == res

    def test_invoke(self):
        class DummyHandler(k8.Handler):
            _error_class = False
            def before(self):  self._before_called  = True
            def after(self):   self._after_called   = True
            def destroy(self): self._destroy_called = True
            def do_index(self, *args):
                if self._error_class:
                    raise self._error_class("error")
                return "args=%r" % (args, )
            def will_raise(self, error_class=Exception):
                self._error_class = error_class
                return self
        with spec("returns result of action method"):
            handler = DummyHandler(*_r())
            ret = handler.invoke(DummyHandler.do_index)
            ok (ret) == 'args=()'
        with spec("args are passed to action method"):
            handler = DummyHandler(*_r())
            ret = handler.invoke(DummyHandler.do_index)
            ok (ret) == "args=()"
            ret = handler.invoke(DummyHandler.do_index, ('foo', '123'))
            ok (ret) == "args=('foo', '123')"
        with spec("calls before() before invoking action method"):
            handler = DummyHandler(*_r())
            handler.invoke(DummyHandler.do_index)
            ok (handler._before_called) == True
        with spec("calls after() after action method is invoked, even when error raised"):
            handler = DummyHandler(*_r())
            handler.invoke(DummyHandler.do_index)
            ok (handler._after_called) == True
            #
            handler = DummyHandler(*_r()).will_raise(Exception)
            ok (lambda: handler.invoke(DummyHandler.do_index)).raises(Exception)
            ok (handler._after_called) == True
        with spec("calls destroy() method to release circular reference"):
            handler = DummyHandler(*_r())
            handler.invoke(DummyHandler.do_index)
            ok (handler._destroy_called) == True
            #
            handler = DummyHandler(*_r()).will_raise(Exception)
            ok (lambda: handler.invoke(DummyHandler.do_index)).raises(Exception)
            ok (handler._destroy_called) == True

    def test_handle(self):
        class CommentsHandler(k8.Handler):
            def do_show(self, *args):
                return "<p>CommentsHandler#do_show: %r</p>" % (args, )
            router = Router().map(r"/(\d+)", GET=do_show)
            _current = None
            def invoke(self, *args):
                self.__class__._current = self
                return k8.Handler.invoke(self, *args)
        class BooksHandler(k8.Handler):
            def do_index(self, *args):
                return "<p>do_index: %r</p>" % (args, )
            def do_show(self, *args):
                return "<p>do_show: %r</p>" % (args, )
            def do_update(self, *args):
                return "<p>do_update: %r</p>" % (args, )
            router = Router().map(r'', GET=do_index)\
                             .map(r'/(\d+)', GET=do_show, PUT=do_update)
        BooksHandler.router.mount(r'/(\d+)/comments', CommentsHandler)
        BooksHandler.router.set_base_path('/books')
        #
        with spec("if request is matched to unbond function then mapped then invokes it with new instance object"):
            actual = BooksHandler.handle(*_r('GET', '/books'))
            ok (actual) == "<p>do_index: ()</p>"
            #
            actual = BooksHandler.handle(*_r('GET', '/books/123'))
            ok (actual) == "<p>do_show: ('123',)</p>"
            #
            actual = BooksHandler.handle(*_r('PUT', '/books/123'))
            ok (actual) == "<p>do_update: ('123',)</p>"
        with spec("if request is matched to other handler class then delegates request and response to it"):
            ok (CommentsHandler._current) == None
            actual = BooksHandler.handle(*_r('GET', '/books/123/comments/999'))
            ok (CommentsHandler._current).is_a(CommentsHandler)
            ok (actual) == "<p>CommentsHandler#do_show: ('123', '999')</p>"
        with spec("if request path is not matched then raises Http404NotFound"):
            def f(): actual = BooksHandler.handle(*_r('GET', '/books/'))
            ok (f).raises(Http404NotFound)
            ok (f.exception.to_html()) == "<h2>404 Not Found</h2>\n<p>/books/: not found.</p>\n"
        with spec("if request path is matched but method is not matched then raises Http405MethodNotAllowed"):
            req, res = _r('POST', '/books/123')
            def f(): actual = BooksHandler.handle(req, res)
            ok (f).raises(Http405MethodNotAllowed)
            ok (f.exception.to_html()) == "<h2>405 Method Not Allowed</h2>\n<p>POST: method not allowed.</p>\n"
        with spec("if request method is POST and _method param is specified then use it as request method value"):
            req, res = _r('POST', '/books/123', body='_method=PUT')
            actual = BooksHandler.handle(req, res)
            ok (actual) == "<p>do_update: ('123',)</p>"
            ok (req.method) == 'PUT'
        #with spec("if '/' is specified but '' is not then request to '' is redirected to '/' with QUERY_STRING"):
        with spec("if 301 is mapped then raises Http301MovedPermanently with current request path and query string"):
            class FooHandler(Handler):
                def do_foo(self): pass
                router = Router()
                router.map('/', GET=do_foo)
            FooHandler.router.set_base_path('/foo')
            def f():
                FooHandler.handle(*_r('GET', '/foo', QUERY_STRING='a=1&b=2'))
            ok (f).raises(Http301MovedPermanently)
            ok (f.exception.location) == '/foo/?a=1&b=2'


if __name__ == '__main__':
    oktest.run()
