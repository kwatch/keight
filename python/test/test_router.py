# -*- coding: utf-8 -*-
from __future__ import with_statement

import sys, re
from oktest import ok, not_ok, run, spec
import keight as k8
from keight import Router, Handler, OnDemandLoader, Http404NotFound, Http405MethodNotAllowed


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


class RouterTest(object):

    def test_set_base_path(self):
        with spec("set base_path into self.base_path"):
            r = Router()
            r.set_base_path("/hello")
            ok (r.base_path) == "/hello"
        with spec("if base_path is a pattern then compile and save it"):
            ok (r._base_path_rexp) == None
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

    def test_map(self):
        r = Router()
        def do_index(): pass
        with spec("if path arg is not a pattern then appends into self._mapping_dict"):
            assert r._mapping_dict == {}
            r.map(r"/new", GET=do_index)
            ok (r._mapping_dict) == {"/new": [{"GET": do_index}, None]}
        with spec("if path arg is a pattern then appends into self._mapping_list"):
            assert r._mapping_list == []
            r.map(r"/(\d+)", GET=do_index)
            ok (r._mapping_list) == [[r"/(\d+)", re.compile(r"/(\d+)"), {'GET': do_index}, None]]
        with spec("if path is '/' then prepares to redirect when empty path"):
            assert r._mapping_dict.get('') == None
            r.map(r"/", GET=do_index)
            #ok (r.mappings[-1]) == ('', {"GET": 301}, None)
            ok (r._mapping_dict['']) == [{"GET": 301}, None]
        with spec("store path and kwargs"):
            ok (r.mappings) == [(r'/new', {'GET': do_index}, None),
                                (r'/(\d+)', {'GET': do_index}, None),
                                (r'/', {'GET': do_index}, None)]
        with spec("returns self"):
            ret = r.map(r"/", GET=do_index)
            ok (ret).is_(r)

    def test_mount(self):
        class CommentsHandler(Handler): pass
        r = Router()
        assert r._mapping_list == []
        with spec("if path arg is not a pattern then appends None to self._mapping_list"):
            r.mount(r"/comments", CommentsHandler)
            ok (len(r._mapping_list)) == 1
            ok (r._mapping_list) == [[r"/comments", None, None, CommentsHandler]]
        with spec("if path arg is not a pattern then compile and appends to self._mapping_list"):
            r.mount(r"/books/(\d+)/commnts/(\d+)", CommentsHandler)
            ok (len(r._mapping_list)) == 2
            ok (r._mapping_list) == [[r"/comments", None, None, CommentsHandler],
                                     [r"/books/(\d+)/commnts/(\d+)", re.compile(r"/books/(\d+)/commnts/(\d+)"), None, CommentsHandler]]
        with spec("store path and handler_class"):
            ok (r.mappings) == [(r"/comments", None, CommentsHandler),
                                (r"/books/(\d+)/commnts/(\d+)", None, CommentsHandler)]
        with spec("returns self"):
            ret = r.mount("/", CommentsHandler)
            ok (ret).is_(r)

    def test_route(self):
        def do_index(): pass
        def do_create(): pass
        def do_new(): pass
        def do_show(): pass
        def do_update(): pass
        def do_edit(): pass
        def do_delete(): pass
        def do_something(): pass
        r = Router()
        r.map(r'', GET=do_index, POST=do_create)
        r.map(r'/new', GET=do_new)
        r.map(r'/(\d+)', GET=do_show, PUT=do_update, DELETE=do_delete)
        r.map(r'/(\d+)/edit', GET=do_edit)
        r.map(r'/something', ALL=do_something)
        #
        class CommentsHandler(Handler):
            def do_show(): pass
            router = Router()
            router.map('/(\d+)', GET=do_show)
        r.mount(r'/(\d+)/comments', CommentsHandler)
        #
        r.mount(r'/(\d+)/lazy', 'my.handlers.OnDemandHandler')
        #
        with spec("if base path is not set then raises error"):
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
        #with spec("if not matched to function nor class then returns None (means 404)"):
        #    ok (r.route('/books/', 'GET')) == (None, ())
        with spec("if not matched to function nor class then raises Http404NotFound"):
            ok (lambda: r.route('/books/', 'GET')).raises(Http404NotFound, "/books/: not found.")
        #with spec("if method is not allowed then returns False (means 405)"):
        #    ok (r.route('/books/123', 'POST')) == (False, ('123',))
        with spec("if method is not allowed then raises Http405MethodNotAllowed"):
            ok (lambda: r.route('/books/123', 'POST')).raises(Http405MethodNotAllowed, "POST: method not allowed.")
        with spec("if mapped object is OnDemandLoader then call load()"):
            ok (r._mapping_list[-1][0]) == r"/(\d+)/lazy"
            ok (r._mapping_list[-1][1]) == re.compile(r"/(\d+)/lazy")
            ok (r._mapping_list[-1][2]) == None
            ok (r._mapping_list[-1][3]).is_a(OnDemandLoader)
            ok (r._mapping_list[-1][3].name) == "my.handlers.OnDemandHandler"
            ok (r.route("/books/123/lazy/999", 'PUT')) == (OnDemandHandler, ('123',))
            ok (r._mapping_list[-1][3]) == OnDemandHandler
        with spec("if ALL is specified then returns matched function in any method"):
            ok (r.route('/books/something', 'XXX')) == (do_something, ())

    def test_FUNCTEST_route(self):
        with spec("[F] if '/' is specified but '' is not then request to '' will be redirected"):
            def do_foo1(): pass
            r = Router()
            r.map('/', GET=do_foo1)
            r.set_base_path('/books')
            ret = r.route('/books', 'GET')
            ok (ret[0]) == 301

    def test__match_to_base_path(self):
        with spec("returns rest_path and args in case base_path is a pattern"):
            r = Router()
            r.set_base_path('/books/(\d+)/comments')
            ok (r._match_to_base_path('/books/123/comments')) == ('', ('123',))
            ok (r._match_to_base_path('/books/123/comments/')) == ('/', ('123',))
            ok (r._match_to_base_path('/books/123/comments/new')) == ('/new', ('123',))
        with spec("returns rest_path and args in case base_path is not a pattern"):
            r = Router()
            r.set_base_path('/books')
            ok (r._match_to_base_path('/books')) == ('', ())
            ok (r._match_to_base_path('/books/')) == ('/', ())
            ok (r._match_to_base_path('/books/123')) == ('/123', ())
        with spec("if base_path is not set then raises error"):
            r = Router()
            def f(): r.route('/books/new', 'GET')
            ok (f).raises(ValueError, "base path is not set to router object (do you forget to mount handler class?)")

    def test__find_kwargs_or_handler_class(self):
        def do_index(): pass
        def do_create(): pass
        def do_new(): pass
        def do_show(): pass
        def do_show123(): pass
        def do_update(): pass
        def do_edit(): pass
        def do_delete(): pass
        def do_something(): pass
        r = Router()
        r.map(r'/(\d+)', GET=do_show, PUT=do_update)
        r.map(r'/123',   GET=do_show123)
        assert r._mapping_dict == {'/123': [{'GET': do_show123}, None]}
        assert r._mapping_list == [
            ['/(\\d+)', re.compile(r'/(\d+)'), {'GET': do_show, 'PUT': do_update}, None],
        ]
        with spec("if rest_path is in self._mapping_dict then returns corresponding values"):
            kwargs, handler_class, args = r._find_kwargs_or_handler_class('/123')
            ok (kwargs) == {'GET': do_show123}
            ok (handler_class) == None
        with spec("if rest_path is not in self._mapping_dict then search self._mapping_list"):
            kwargs, handler_class, args = r._find_kwargs_or_handler_class('/12')
            ok (kwargs) == {'GET': do_show, 'PUT': do_update}
            ok (handler_class) == None
        with spec("if not matched then returns Nones"):
            kwargs, handler_class, args = r._find_kwargs_or_handler_class('/')
            ok (kwargs) == None
            ok (handler_class) == None

    def test__config_action_func(self):
        F = k8.Router._config_action_func
        with spec("sets request method"):
            def do_delete(): pass
            F(do_delete, '/books/(\d+)', 'DELETE')
            ok (do_delete.method) == 'DELETE'
        with spec("if path is specified then sets path() function"):
            def do_index(): pass
            F(do_index, '/books', 'GET')
            ok (do_index.path()) == '/books'
            def do_show(): pass
            F(do_show, '/books/(\d+)', 'GET')
            ok (do_show.path(123)) == '/books/123'
            def do_comment(): pass
            F(do_comment, '/books/(\d+)/comment/(\d+)', 'GET')
            ok (do_comment.path(123, 999)) == '/books/123/comment/999'
        with spec("if path is not specified then path() function is empty"):
            def do_index(): pass
            F(do_index, '', 'GET')
            ok (do_index.path()) == ''
            F(do_index, None, 'GET')
            ok (do_index.path()) == None
        with spec("sets hidden_tag() function which returns hidden tag only if request method is not GET nor POST"):
            def do_delete(): pass
            F(do_delete, '/', 'GET')
            ok (do_delete.hidden_tag()) == ''
            F(do_delete, '/', 'POST')
            ok (do_delete.hidden_tag()) == ''
            F(do_delete, '/', 'PUT')
            ok (do_delete.hidden_tag()) == '<input type="hidden" name="_method" value="PUT" />'
            F(do_delete, '/', 'DELETE')
            ok (do_delete.hidden_tag()) == '<input type="hidden" name="_method" value="DELETE" />'


class RootRouterTest(object):

    def test_map(self):
        with spec("configure each action functions"):
            def do_hello(req, res): return ""
            r = k8.RootRouter()
            r.map("/hello", GET=do_hello)
            ok (do_hello.method) == 'GET'
            ok (do_hello.path()) == '/hello'

    def test_mount(self):
        with spec("if handler_class has router then set path as base_path of it"):
            class Hello(k8.Handler):
                def do_index(self): return ""
                router = k8.Router().map("/", GET=do_index)
            assert Hello.router.base_path is None
            r = k8.RootRouter()
            r.mount("/hello", Hello)
            ok (Hello.router.base_path) == "/hello"

    def test__match_to_base_path(self):
        with spec("returns passed path and an empty tuple"):
            ok (k8.RootRouter()._match_to_base_path('/foo')) == ('/foo', ())


class OnDemandLoaderTest(object):

    def test_load(self):
        def callback(obj):
            callback.obj = obj
        callback.obj = None
        loader = OnDemandLoader('xml.dom.minidom.Node', callback)
        with spec("loads object with importing module"):
            assert sys.modules.get('xml.dom.minidom') == None
            ret = loader.load()
            ok (sys.modules.get('xml.dom.minidom')) != None
            mod = sys.modules.get('xml.dom.minidom')
            ok (mod).is_a(type(sys))
        with spec("if callback is specified then call it with loaded object"):
            ok (callback.obj).is_(mod.Node)
        with spec("returns loaded object (typically class object)"):
            ok (ret).is_(mod.Node)


if __name__ == '__main__':
    run()
