# -*- coding: utf-8 -*-
from __future__ import with_statement

from oktest import ok, not_ok, run, spec
import keight as k8
from keight import Router, Handler, dummy_env, Request, Response, Http404NotFound, Http405MethodNotAllowed


class K8HandlerTest(object):

    def test___init__(self):
        with spec("takes request and response"):
            env = dummy_env('/')
            req = Request(env)
            res = Response(env)
            handler = Handler(req, res)
            ok (handler.request) == req
            ok (handler.response) == res

    def test_handle(self):
        class CommentsHandler(Handler):
            def do_show(self, *args):
                return "<p>CommentsHandler#do_show: %r</p>" % (args, )
            router = Router()
            router.map(r"/(\d+)", GET=do_show)
        class BooksHandler(Handler):
            def do_index(self, *args):
                return "<p>do_index: %r</p>" % (args, )
            def do_show(self, *args):
                return "<p>do_show: %r</p>" % (args, )
            def do_update(self, *args):
                return "<p>do_update: %r</p>" % (args, )
            router = Router()
            router.map(r'', GET=do_index)
            router.map(r'/(\d+)', GET=do_show, PUT=do_update)
            #router.mount(r'/(\d+)/comments', CommentsHandler)
        BooksHandler.router.mount(r'/(\d+)/comments', CommentsHandler)
        BooksHandler.router.set_base_path('/books')
        #
        def _r(*args, **kwargs):
            env = dummy_env(*args, **kwargs)
            return (Request(env), Response(env))
        #
        with spec("if request is matched to action method then creates instance object and invoke action method"):
            actual = BooksHandler.handle(*_r('GET', '/books'))
            ok (actual) == "<p>do_index: ()</p>"
            #
            actual = BooksHandler.handle(*_r('GET', '/books/123'))
            ok (actual) == "<p>do_show: ('123',)</p>"
            #
            actual = BooksHandler.handle(*_r('PUT', '/books/123'))
            ok (actual) == "<p>do_update: ('123',)</p>"
        with spec("if request is matched to handler class then delete to it"):
            ok (CommentsHandler._current) == None
            actual = BooksHandler.handle(*_r('GET', '/books/123/comments/999'))
            ok (CommentsHandler._current).is_a(CommentsHandler)
            ok (actual) == "<p>CommentsHandler#do_show: ('123', '999')</p>"
        with spec("if request path is not matched then raises Http404NotFound"):
            def f():
                actual = BooksHandler.handle(*_r('GET', '/books/'))
            ok (f).raises(Http404NotFound)
            ok (f.exception.to_html()) == "<h2>404 Not Found</h2>\n<p>/books/: not found.</p>\n"
        with spec("if request method is not matched then raises Http405MethodNotAllowed"):
            def f():
                actual = BooksHandler.handle(*_r('POST', '/books/123'))
            ok (f).raises(Http405MethodNotAllowed)
            ok (f.exception.to_html()) == "<h2>405 Method Not Allowed</h2>\n<p>POST: method not allowed.</p>\n"


if __name__ == '__main__':
    run(K8HandlerTest)
