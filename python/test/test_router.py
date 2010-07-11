# -*- coding: utf-8 -*-
from __future__ import with_statement

import sys, re
from oktest import ok, not_ok, run, spec
import keight as k8
from keight import Router, Handler, OnDemandLoader


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


class K8RouterTest(object):

    def test_set_base_path(self):
        with spec("set arg into self.base_path"):
            r = Router()
            r.set_base_path("/hello")
            ok (r.base_path) == "/hello"
            ok (r._base_path_rexp) == None
        with spec("self._base_path_rexp is set only when arg is pattern"):
            r = Router()
            r.set_base_path("/hello/(\d+)")
            ok (r.base_path) == "/hello/(\d+)"
            ok (r._base_path_rexp) == re.compile("/hello/(\d+)")
        with spec("sets path function and request method to each action method"):
            def do_index(): pass
            def do_show(): pass
            def do_update(): pass
            r = Router()
            r.map('/', GET=do_index)
            r.map('/(\d+)', GET=do_show, PUT=do_update)
            class CommentsHandler(Handler):
                def do_show(): pass
                router = Router()
                router.map('/(\d+)', GET=do_show)
            r.mount('/(\d+)/comments', CommentsHandler)
            #
            r.set_base_path('/books')
            #
            ok (hasattr(do_index, 'path')) == True
            ok (do_index.path()) == '/books/'
            ok (getattr(do_index, 'method')) == 'GET'
            #
            ok (hasattr(do_show, 'path')) == True
            ok (do_show.path(123)) == '/books/123'
            ok (getattr(do_show, 'method')) == 'GET'
            #
            ok (hasattr(do_update, 'path')) == True
            ok (do_update.path(123)) == '/books/123'
            ok (getattr(do_update, 'method')) == 'PUT'
            #
            ok (CommentsHandler.router.base_path) == '/books/(\d+)/comments'
            ok (hasattr(CommentsHandler.do_show, 'path')) == True
            ok (CommentsHandler.do_show.path(123, 999)) == '/books/123/comments/999'
            ok (getattr(CommentsHandler.do_show, 'method')) == 'GET'
        with spec("if handler class is string then create OnDemandLoader object with callback"):
            r = Router()
            r.mount("/bar", "my.handlers.OnDemandHandler")
            ok (r._mapping_list[0][0]) == "/bar"
            ok (r._mapping_list[0][1]) == None
            ok (r._mapping_list[0][2]) == None
            ok (r._mapping_list[0][3]) == "my.handlers.OnDemandHandler"
            r.set_base_path("/foo")
            ok (r._mapping_list[0][0]) == "/bar"
            ok (r._mapping_list[0][1]) == None
            ok (r._mapping_list[0][2]) == None
            ok (r._mapping_list[0][3]).is_a(OnDemandLoader)
            ok (r._mapping_list[0][3].load()) == OnDemandHandler
            ok (r._mapping_list[0][0]) == "/bar"
            ok (r._mapping_list[0][1]) == None
            ok (r._mapping_list[0][2]) == None
            ok (r._mapping_list[0][3]) == OnDemandHandler

    def tet__build_path_func(self):
        r = Router()
        with spec("returns path function with no argument"):
            func = r._build_path_func('/books')
            ok (func()) == '/books'
        with spec("returns path function with 1 arg"):
            func = r._build_path_func('/books/(\d+)')
            ok (func(123)) == '/books/123'
        with spec("retourns path function with 2 args"):
            func = r._build_path_func('/books/(\d+)/comments(\d+)')
            ok (func(123, 999)) == '/books/123/comments/999'

    def test_map(self):
        r = Router()
        def do_index(): pass
        with spec("if path arg is not pattern then added to self._mapping_dict"):
            ok (r._mapping_dict) == {}
            r.map(r"/new", GET=do_index)
            ok (r._mapping_dict) == {"/new": ({"GET": do_index}, None)}
        with spec("if path arg is pattern then added to self._mapping_list"):
            ok (r._mapping_list) == []
            r.map(r"/(\d+)", GET=do_index)
            ok (r._mapping_list) == [(r"/(\d+)", re.compile(r"/(\d+)"), {'GET': do_index}, None)]

    def test_mount(self):
        class CommentsHandler(Handler): pass
        with spec("if path arg is not pattern then added to self._mapping_list"):
            r = Router()
            ok (r._mapping_list) == []
            r.mount(r"/comments", CommentsHandler)
            ok (r._mapping_list) == [(r"/comments", None, None, CommentsHandler)]
        with spec("if path arg is pattern then added to self._mapping_list"):
            r = Router()
            ok (r._mapping_list) == []
            r.mount(r"/books/(\d+)/commnts/(\d+)", CommentsHandler)
            ok (r._mapping_list) == [(r"/books/(\d+)/commnts/(\d+)", re.compile(r"/books/(\d+)/commnts/(\d+)"), None, CommentsHandler)]

    def test_route(self):
        def do_index(): pass
        def do_create(): pass
        def do_new(): pass
        def do_show(): pass
        def do_update(): pass
        def do_edit(): pass
        def do_delete(): pass
        r = Router()
        r.map(r'', GET=do_index, POST=do_create)
        r.map(r'/new', GET=do_new)
        r.map(r'/(\d+)', GET=do_show, PUT=do_update, DELETE=do_delete)
        r.map(r'/(\d+)/edit', GET=do_edit)
        #
        class CommentsHandler(Handler):
            def do_show(): pass
            router = Router()
            router.map('/(\d+)', GET=do_show)
        r.mount(r'/(\d+)/comments', CommentsHandler)
        #
        r.mount(r'/(\d+)/lazy', 'my.handlers.OnDemandHandler')
        #
        with spec("if base path is not set then raises ValueError"):
            def f():
                r.route('/books/new', 'GET')
            ok (f).raises(ValueError, "base path is not set to router object (do you forget to mount handler class?)")
        #
        r.set_base_path('/books')
        #
        with spec("if matched path is found then returns function and arguments"):
            ok (r.route('/books', 'GET')) == (do_index, ())
            ok (r.route('/books', 'POST')) == (do_create, ())
            ok (r.route('/books/new', 'GET')) == (do_new, ())
            ok (r.route('/books/123', 'GET')) == (do_show, ('123',))
            ok (r.route('/books/123', 'PUT')) == (do_update, ('123',))
            ok (r.route('/books/123', 'DELETE')) == (do_delete, ('123',))
        with spec("if matched handler class is found then returns it and args"):
            ok (r.route('/books/123/comments/999', 'GET')) == (CommentsHandler, ('123',))
        with spec("if not matched to function nor class then returns None (means 404)"):
            ok (r.route('/books/', 'GET')) == (None, '/')
        with spec("if method is not allowed then returns False (means 405)"):
            ok (r.route('/books/123', 'POST')) == (False, '/123')
        with spec("if mapped object is OnDemandLoader then call load()"):
            ok (r._mapping_list[-1][0]) == r"/(\d+)/lazy"
            ok (r._mapping_list[-1][1]) == re.compile(r"/(\d+)/lazy")
            ok (r._mapping_list[-1][2]) == None
            ok (r._mapping_list[-1][3]).is_a(OnDemandLoader)
            ok (r._mapping_list[-1][3].name) == "my.handlers.OnDemandHandler"
            ok (r.route("/books/123/lazy/999", 'PUT')) == (OnDemandHandler, ('123',))
            ok (r._mapping_list[-1][3]) == OnDemandHandler

    def test__match_to_base_path(self):
        with spec("returns rest_path and args in case path is not pattern"):
            r = Router()
            r.set_base_path('/books')
            ok (r._match_to_base_path('/books')) == ('', ())
            ok (r._match_to_base_path('/books/')) == ('/', ())
            ok (r._match_to_base_path('/books/123')) == ('/123', ())
        with spec("returns rest_path and args in case path is pattern"):
            r = Router()
            r.set_base_path('/books/(\d+)/comments')
            ok (r._match_to_base_path('/books/123/comments')) == ('', ('123',))
            ok (r._match_to_base_path('/books/123/comments/')) == ('/', ('123',))
            ok (r._match_to_base_path('/books/123/comments/new')) == ('/new', ('123',))


if __name__ == '__main__':
    run(K8RouterTest)
