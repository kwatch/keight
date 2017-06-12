# -*- coding: utf-8 -*-

import sys, os, re

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end

import keight as k8
from keight import on, mapping
from keight import PY3, PY2


def provide_name(self):
    return "tmp1"


def create_pyfiles(name):
    import shutil
    if os.path.exists(name):
        shutil.rmtree(name)
    os.mkdir(name)
    os.mkdir(name+"/api")
    with open(name+"/__init__.py", 'w') as f:
        f.write("")
    with open(name+"/api/__init__.py", 'w') as f:
        f.write("")
    with open(name+"/api/hello.py", 'w') as f:
        f.write(r"""
import keight as k8
class HelloAPI(k8.Action):
  k8.on('GET', r'')
  def do_index(self): pass
#
class HelloAPI2(object):
  k8.on('GET', r'')
  def do_index(self): pass
#
class HelloAPI3(k8.Action):
  def do_index(self): pass
""")
    with open(name+"/api/items.py", 'w') as f:
        f.write(r"""
from keight import on, Action
class ItemsAction(Action):
    @on('GET', r'')
    def do_index(self):
        return "<p>index</p>"
    @on('POST', r'')
    def do_create(self):
        return "<p>create</p>"
    @on('GET', r'/{id}')
    def do_show(self, id):
        return "<p>show(%r)</p>" % id
    @on('PUT', r'/{id}')
    def do_update(self, id):
        return "<p>update(%r)</p>" % id
    @on('DELETE', r'/{id}')
    def do_delete(self, id):
        return "<p>delete(%r)</p>" % id
""")
    with open(name+"/api/news.py", 'w') as f:
        f.write(r"""
from keight import on, Action
class NewsAction(Action):
    @on('GET', r'')
    def do_index(self):
        return "<p>index</p>"
    @on('POST', r'')
    def do_create(self):
        return "<p>create</p>"
    @on('GET', r'/{id}')
    def do_show(self, id):
        return "<p>show(%r)</p>" % id
    @on('PUT', r'/{id}')
    def do_update(self, id):
        return "<p>update(%r)</p>" % id
    @on('DELETE', r'/{id}')
    def do_delete(self, id):
        return "<p>delete(%r)</p>" % id
""")
    with open(name+"/api/hello9.py", 'w') as f:
        f.write(r"""
import keight as k8, on   #=> ImportError: No module named 'on'

class Hello9Action(k8.Action):
    @on('GET', r'')
    def do_hello(self):
        return "<p>hello</p>"
""")
    return name

def remove_pyfiles(name):
    import os, shutil
    if os.path.exists(name):
        shutil.rmtree(name)

def clear_modules(name):
    for key in list(sys.modules.keys()):
        if key.startswith(name):
            del sys.modules[key]

def clear_module_cache():
    import importlib
    try:
        importlib.invalidate_caches()   # Python 3.3 or later
    except AttributeError:
        pass


##
create_pyfiles("tmp1")
import atexit
#atexit.register(lambda: remove_pyfiles("tmp1"))   # error in Py2.7 (why?)
atexit.register(lambda fn=remove_pyfiles: fn("tmp1"))
##


def validate_lookup(am, lazy=False, argstype=dict):
    from tmp1.api.items import ItemsAction
    from tmp1.api.news  import NewsAction
    items_d = ItemsAction.__dict__
    news_d  = NewsAction.__dict__
    #
    t = am.lookup('/api/items')
    ok (t).is_a(tuple).length(3)
    ok (t[0]) == ItemsAction
    ok (t[1]) == {'GET': items_d['do_index'], 'POST': items_d['do_create']}
    ok (t[2]) == {} if argstype is dict else ()
    #
    t = am.lookup('/api/news')
    ok (t).is_a(tuple).length(3)
    ok (t[0]) == NewsAction
    ok (t[1]) == {'GET': news_d['do_index'], 'POST': news_d['do_create']}
    ok (t[2]) == {} if argstype is dict else ()
    #
    t = am.lookup('/api/items/123')
    ok (t).is_a(tuple).length(3)
    ok (t[0]) == ItemsAction
    ok (t[1]) == {'GET': items_d['do_show'], 'PUT': items_d['do_update'], 'DELETE': items_d['do_delete']}
    ok (t[2]) == {'id': '123'} if argstype is dict else [123]
    #
    t = am.lookup('/api/news/456')
    ok (t).is_a(tuple).length(3)
    ok (t[0]) == NewsAction
    ok (t[1]) == {'GET': news_d['do_show'], 'PUT': news_d['do_update'], 'DELETE': news_d['do_delete']}
    ok (t[2]) == {'id': '456'} if argstype is dict else [456]



class K8_Test(object):

    def after(self):
        clear_module_cache()


    with subject('mapping()'):

        @test("[!zfrv6] maps urlpath pattern with action methods.")
        def _(self):
            class HelloAction(k8.Action):
                def do_show(self, id):    return "..."
                def do_update(self, id):  return "..."
                def do_delete(self, id):  return "..."
                #
                mapping(r'/{id}', GET=do_show, PUT=do_update, DELETE=do_delete)
            #
            ok (HelloAction.__mapping__) == [
                (r'/{id}', {'GET'    : HelloAction.__dict__['do_show'],
                            'PUT'    : HelloAction.__dict__['do_update'],
                            'DELETE' : HelloAction.__dict__['do_delete'],
                           }
                 )
            ]

class HelloAction(k8.Action):
    def do_index(self): pass
    def do_create(self): pass
    def do_show(self, id): pass
    def do_update(self, id): pass
    def do_delete(self, id): pass
    def do_any(self, id): pass


class HelloActionMapping(k8.ActionMapping):
    _mapping = {
        '/'    :  (
            HelloAction,
            {
                'GET':  HelloAction.__dict__['do_index'],
                'POST': HelloAction.__dict__['do_create'],
            },
            (),
        ),
        '/123' :  (
            HelloAction,
            {
                'GET':  HelloAction.__dict__['do_show'],
                'PUT':  HelloAction.__dict__['do_update'],
            },
            (123,),
        ),
        '/999' :  (
            HelloAction,
            {
                'GET':  HelloAction.__dict__['do_show'],
                'ANY':  HelloAction.__dict__['do_any'],
            },
            (999,),
        ),
    }
    def lookup(self, req_path):
        if req_path.endswith('/123'):
            return self._mapping['/123']
        if req_path.endswith('/999'):
            return self._mapping['/999']
        if req_path.endswith('/hello/'):
            return self._mapping['/']
        return None


class ActionMapping_Test(object):

    def after(self):
        clear_module_cache()

    def provide_am(self):
        return HelloActionMapping()


    with subject('._validate_request_method()'):

        @test("[!548rp] raises ActionMappingError when request method is unknown.")
        def _(self):
            fn = lambda: k8.ActionMapping._validate_request_method('LOCK')
            ok (fn).raises(k8.ActionMappingError, "LOCK: unknown request method.")

        @test("[!trjzz] not raises when request method is known.")
        def _(self):
            for meth in ['GET', 'POST', 'PUT', 'DELETE', 'HEAD', 'TRACE', 'OPTIONS']:
                fn = lambda: k8.ActionMapping._validate_request_method(meth)
                ok (fn).not_raise(Exception)

        @test("[!jsu98] not raises when request method is 'ANY'.")
        def _(self):
            fn = lambda: k8.ActionMapping._validate_request_method('ANY')
            ok (fn).not_raise(Exception)


    with subject('#lookup()'):

        @test("[!wwvec] raises NotImplementedError.")
        def _(self):
            am = k8.ActionMapping()
            fn = lambda: am.lookup('/api/hello')
            ok (fn).raises(NotImplementedError, "ActionMapping.lookup(): not implemented yet.")


    with subject('#dispatch()'):

        @test("[!akpxj] returns action class, action func, and urlpath param values.")
        def _(self, am):
            t = am.dispatch('GET', '/api/hello/')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == HelloAction
            ok (t[1]) == HelloAction.__dict__['do_index']
            ok (t[2]) == ()
            #
            t = am.dispatch('PUT', '/api/hello/123')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == HelloAction
            ok (t[1]) == HelloAction.__dict__['do_update']
            ok (t[2]) == (123,)

        @test("[!j3hfh] raises 405 Method Not Allowed when no action method corresponding to request method.")
        def _(self, am):
            fn = lambda: am.dispatch('PUT', '/api/hello/')
            ok (fn).raises(k8.HttpException)
            ok (fn.exception.status) == 405
            #
            fn = lambda: am.dispatch('POST', '/api/hello/123')
            ok (fn).raises(k8.HttpException)
            ok (fn.exception.status) == 405

        @test("[!thk18] falls back to GET method when HEAD method is not provided.")
        def _(self, am):
            t = am.dispatch('HEAD', '/api/hello/')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == HelloAction
            ok (t[1]) == HelloAction.__dict__['do_index']
            ok (t[2]) == ()
            #
            t = am.dispatch('HEAD', '/api/hello/123')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == HelloAction
            ok (t[1]) == HelloAction.__dict__['do_show']
            ok (t[2]) == (123,)

        @test("[!rdfcv] falls back to ANY method when corresponding method is not provided.")
        def _(self, am):
            t = am.dispatch('GET', '/api/hello/999')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == HelloAction
            ok (t[1]) == HelloAction.__dict__['do_show']
            ok (t[2]) == (999,)
            #
            t = am.dispatch('POST', '/api/hello/999')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == HelloAction
            ok (t[1]) == HelloAction.__dict__['do_any']
            ok (t[2]) == (999,)

        @test("[!oureu] raises 404 Not Found when request path not found.")
        def _(self, am):
            fn = lambda: am.dispatch('GET', '/api/hello/0')
            ok (fn).raises(k8.HttpException)
            ok (fn.exception.status) == 404

        @test("[!g9k0i] raises 301 Found when '/foo' not found but '/foo/' exists.")
        def _(self, am):
            for meth in ['GET', 'HEAD']:
                fn = lambda: am.dispatch(meth, '/api/hello')
                ok (fn).raises(k8.HttpException)
                ok (fn.exception.status) == 301
                ok (fn.exception.headers) == {'Location': '/api/hello/'}

        @test("[!c9dsj] raises 301 Found when '/foo/' not found but '/foo' exists.")
        def _(self, am):
            for meth in ['GET', 'HEAD']:
                fn = lambda: am.dispatch(meth, '/api/hello/123/')
                ok (fn).raises(k8.HttpException)
                ok (fn.exception.status) == 301
                ok (fn.exception.headers) == {'Location': '/api/hello/123'}

        @test("[!u6sqo] redirects between '/foo' <=> '/foo/' only on GET or HEAD method.")
        def _(self, am):
            fn = lambda: am.dispatch('POST', '/api/hello')
            ok (fn).raises(k8.HttpException)
            ok (fn.exception.status) == 404
            #
            fn = lambda: am.dispatch('PUT', '/api/hello/123/')
            ok (fn).raises(k8.HttpException)
            ok (fn.exception.status) == 404


    with subject('#_upath_pat2rexp()'):

        @test("[!r1xu6] ex: _upath_pat2rexp(r'/x.gz', '^', '$') => r'^/x\.gz$'")
        def _(self, am):
            ok (am._upath_pat2rexp(r'/x.gz', '^', '$')) == r'^/x\.gz$'

        @test("[!locca] ex: _upath_pat2rexp(r'/{code}', '^', '$', True) => r'^/(?P<code>[^/]+)$'")
        def _(self, am):
            ok (am._upath_pat2rexp(r'/{code}', '^', '$', True)) == r'^/(?P<code>[^/]+)$'

        @test("[!iibcp] ex: _upath_pat2rexp(r'/{code}', '^', '$', False) => r'^/(?:<code>[^/]+)$'")
        def _(self, am):
            ok (am._upath_pat2rexp(r'/{code}', '^', '$', False)) == r'^/(?:[^/]+)$'

        @test("[!t8u2o] ex: _upath_pat2rexp(r'/{code:\d+}', '^', '$', True) => r'^/(?P<code:\d+>[^/]+)$'")
        def _(self, am):
            ok (am._upath_pat2rexp(r'/{code:\d+}', '^', '$', True)) == r'^/(?P<code>\d+)$'

        @test("[!9i3gn] ex: _upath_pat2rexp(r'/{code:\d+}', '^', '$', False) => r'^/(?:<code:\d+>[^/]+)$'")
        def _(self, am):
            ok (am._upath_pat2rexp(r'/{code:\d+}', '^', '$', False)) == r'^/(?:\d+)$'


    with subject('#_upath_pat2func()'):

        @test("[!1heks] builds function object from urlpath pattern and returns it.")
        def _(self, am):
            def args(fn):
                if PY3:
                    code = fn.__code__
                elif PY2:
                    code = fn.func_code
                return code.co_varnames[:code.co_argcount]
            fn = am._upath_pat2func('/api/books')
            ok (fn()) == "/api/books"
            ok (args(fn)) == ()
            fn = am._upath_pat2func('/api/books/{id}')
            ok (fn(123)) == "/api/books/123"
            ok (args(fn)) == ('id',)
            fn = am._upath_pat2func('/api/books/{book_id}/comments/{comment_id}')
            ok (fn(123, 999)) == "/api/books/123/comments/999"
            ok (args(fn)) == ('book_id', 'comment_id')

        @test("[!lelrm] can handle '%' correctly.")
        def _(self, am):
            fn = am._upath_pat2func('/api/%3A/{book_id}/%3B')
            ok (fn(123)) == "/api/%3A/123/%3B"


    with subject('#_load_action_class()'):

        def provide_classstr(self):
            return "gzlsn.api.hello.HelloAPI"

        @test("[!gzlsn] converts string (ex: 'my.api.HelloAction') into class object (ex: my.api.HelloAction).")
        def _(self, am, classstr):
            assert os.path.isfile("tmp1/api/hello.py")
            val = am._load_action_class("tmp1.api.hello.HelloAPI")
            ok (val).is_a(type)
            ok (issubclass(val, k8.Action)) == True
            ok (val.__name__) == "HelloAPI"

        @test("[!7iso7] raises ValueError when specified module or class not found")
        def _(self, am):
            fn = lambda: am._load_action_class("xxx.api.hello.HelloAPI")
            ok (fn).raises(ValueError, "xxx.api.hello.HelloAPI: No such module or class.")
            fn = lambda: am._load_action_class("tmp1.api.hello.HelloAPIxxx")
            ok (fn).raises(ValueError, "tmp1.api.hello.HelloAPIxxx: No such module or class.")

        @test("[!bv2ps] don't catch ImportError raised in specified module.")
        def _(self, am):
            fn = lambda: am._load_action_class("tmp1.api.hello9.HelloAPI")
            if PY3:
                ok (fn).raises(ImportError, "No module named 'on'")
            elif PY2:
                ok (fn).raises(ImportError, "No module named on")

        @test("[!4ci2t] raises TypeError when value is not a class.")
        def _(self, am, classstr):
            fn = lambda: am._load_action_class("tmp1.api.hello.k8")
            ok (fn).raises(TypeError, re.compile(r"^tmp1\.api\.hello\.k8: Action class expected but got <module 'keight' from '.*?'>.$"))

        @test("[!9861d] raises TypeError when value is not a subclass of BaseAction class.")
        def _(self, am, classstr):
            fn = lambda: am._load_action_class("tmp1.api.hello.HelloAPI2")
            ok (fn).raises(TypeError, "tmp1.api.hello.HelloAPI2: Action class expected.")

        @test("[!e3qw0] raises ValueError when no action mehtods.")
        def _(self, am, classstr):
            fn = lambda: am._load_action_class("tmp1.api.hello.HelloAPI3")
            ok (fn).raises(TypeError, "tmp1.api.hello.HelloAPI3: No action methods.")


###

class BooksAction(k8.Action):

    @on('GET', r'')
    def do_index(self):
        return "<p>index</p>"

    @on('POST', r'')
    def do_create(self):
        return "<p>create</p>"

    @on('GET', r'/{id}')
    def do_show(self, id):
        return "<p>show(%r)</p>" % id

    @on('PUT', r'/{id}')
    def do_update(self, id):
        return "<p>update(%r)</p>" % id

    @on('DELETE', r'/{id}')
    def do_delete(self, id):
        return "<p>delete(%r)</p>" % id


class AuthorsAction(k8.Action):

    @on('GET', r'')
    def do_index(self):
        return "<p>index</p>"

    @on('POST', r'')
    def do_create(self):
        return "<p>create</p>"

    @on('GET', r'/{id}')
    def do_show(self, id):
        return "<p>show(%r)</p>" % id

    @on('PUT', r'/{id}')
    def do_update(self, id):
        return "<p>update(%r)</p>" % id

    @on('DELETE', r'/{id}')
    def do_delete(self, id):
        return "<p>delete(%r)</p>" % id



class ActionRexpMapping_Test(object):

    def after(self):
        clear_module_cache()

    def provide_mapping_list(self):
        return [
            ('/api', [
                ('/books',     BooksAction),
                ('/authors',   AuthorsAction),
            ]),
        ]

    def provide_am(self, mapping_list):
        return k8.ActionRexpMapping(mapping_list)


    with subject('#__init__()'):

        @test("[!qm6q0] accepts urlpath mapping list.")
        def _(self, mapping_list):
            fn = lambda: k8.ActionRexpMapping(mapping_list)
            ok (fn).not_raise(Exception)

        @test("[!cgftn] builds regexp representing routing.")
        def _(self, mapping_list):
            am = k8.ActionRexpMapping(mapping_list)
            ok (am).has_attr('_variable_rexp')
            ok (am._variable_rexp).is_a(type(re.compile('x')))
            expected = r'^(?:/api(?:/books/(?:[^/]+)($)|/authors/(?:[^/]+)($)))$'
            ok (am._variable_rexp.pattern) == expected

        @test("[!ta2hs] builds fixed entries.")
        def _(self, mapping_list):
            am = k8.ActionRexpMapping(mapping_list)
            ok (am._fixed_entries).is_a(dict)
            ok (am._fixed_entries) == {
                '/api/authors': (
                    AuthorsAction,
                    {'GET':  AuthorsAction.__dict__['do_index'],
                     'POST': AuthorsAction.__dict__['do_create']},
                    {},
                ),
                '/api/books': (
                    BooksAction,
                    {'GET':  BooksAction.__dict__['do_index'],
                     'POST': BooksAction.__dict__['do_create']},
                    {},
                ),
            }

        @test("[!tzw5a] sets actual 'urlpath()' to action functions.")
        def _(self, mapping_list):
            am = k8.ActionRexpMapping(mapping_list)
            t = am.lookup('/api/authors')
            klass = t[0]
            ok (klass.do_index.urlpath())     == '/api/authors'
            ok (klass.do_create.urlpath())    == '/api/authors'
            ok (klass.do_show.urlpath(123))   == '/api/authors/123'
            ok (klass.do_update.urlpath(123)) == '/api/authors/123'
            ok (klass.do_delete.urlpath(123)) == '/api/authors/123'


    with subject('#lookup()'):

        @test("[!0o1rm] returns action class, action methods and urlpath arguments.")
        def _(self, am):
            books_d   = BooksAction.__dict__
            authors_d = AuthorsAction.__dict__
            #
            t = am.lookup('/api/books')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == BooksAction
            ok (t[1]) == {'GET':  books_d['do_index'], 'POST': books_d['do_create']}
            ok (t[2]) == {}
            #
            t = am.lookup('/api/authors')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == AuthorsAction
            ok (t[1]) == {'GET':  authors_d['do_index'], 'POST': authors_d['do_create']}
            ok (t[2]) == {}
            #
            t = am.lookup('/api/books/123')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == BooksAction
            ok (t[1]) == {'GET':  books_d['do_show'], 'PUT': books_d['do_update'], 'DELETE': books_d['do_delete']}
            ok (t[2]) == {'id': '123'}
            #
            t = am.lookup('/api/authors/123')
            ok (t).is_a(tuple).length(3)
            ok (t[0]) == AuthorsAction
            ok (t[1]) == {'GET':  authors_d['do_show'], 'PUT': authors_d['do_update'], 'DELETE': authors_d['do_delete']}
            ok (t[2]) == {'id': '123'}

        @test("[!wduo6] returns None when not found.")
        def _(self, am):
            ok (am.lookup('/api/book')) == None
            ok (am.lookup('/api/authors/123/456')) == None

        @test("[!viut2] returns None when not matched.")
        def _(self, am):
            class HelloAPI(k8.Action):
                @on('GET', r'')
                def do_index(self): pass
            mapping_list = [
                (r'/api', [
                    (r'/hello', HelloAPI),
                ]),
            ]
            am = self.provide_am(mapping_list)
            ok (am.lookup('/api')) == None


    with subject('#__iter__()'):

        @test("[!gvtd4] yields each urlpath pattern, action class, and action methods.")
        def _(self, am):
            books_d   = BooksAction.__dict__
            authors_d = AuthorsAction.__dict__
            #
            g = iter(am)
            ok (next(g)) == ('/api/books',
                             BooksAction,
                             {'GET': books_d['do_index'], 'POST': books_d['do_create']},
                             )
            ok (next(g)) == ('/api/books/{id}',
                             BooksAction,
                             {'GET': books_d['do_show'], 'PUT': books_d['do_update'], 'DELETE': books_d['do_delete']},
                             )
            ok (next(g)) == ('/api/authors',
                             AuthorsAction,
                             {'GET': authors_d['do_index'], 'POST': authors_d['do_create']},
                             )
            ok (next(g)) == ('/api/authors/{id}',
                             AuthorsAction,
                             {'GET': authors_d['do_show'], 'PUT': authors_d['do_update'], 'DELETE': authors_d['do_delete']},
                             )
            ok (lambda: next(g)).raises(StopIteration)



class ActionRexpLazyMapping_Test(object):

    def after(self):
        clear_module_cache()

    def provide_mapping_list(self, name):
        return [
            ('/api', [
                ('/items',     name+".api.items.ItemsAction"),
                ('/news',      name+".api.news.NewsAction"),
            ]),
        ]

    def provide_am(self, mapping_list, name):
        assert os.path.isdir(name)
        return k8.ActionRexpLazyMapping(mapping_list)


    with subject('#__init__()'):

        @test("[!ie7w7] accepts urlpath mapping list.")
        def _(self, mapping_list):
            ok (lambda: k8.ActionRexpLazyMapping(mapping_list)).not_raise(Exception)

        @test("[!hdb1y] builds regexp representing routing.")
        def _(self, mapping_list):
            am = k8.ActionRexpLazyMapping(mapping_list)
            ok (am._urlpath_rexp) != None
            ok (am._urlpath_rexp).is_a(type(re.compile('x')))
            ok (am._urlpath_rexp.pattern) == r'^(?:/api(?:/items((?=[/.]|$))|/news((?=[/.]|$))))(?=[./]|$)'

        @test("[!np9zn] no fixed entries at first.")
        def _(self, mapping_list):
            am = k8.ActionRexpLazyMapping(mapping_list)
            ok (am._fixed_urlpaths) == {}


    with subject('#lookup()'):

        @test("[!8ktv8] loads action class from file when class is a string.")
        def _(self, am, name="tmp1"):
            ok (sys.modules).not_contain("tmp1.api.items")
            ok (sys.modules).not_contain("tmp1.api.news")
            t = am.lookup('/api/items')     # looking up resuls in loading *.py
            ok (sys.modules).contains("tmp1.api.items")   # loaded!
            ok (sys.modules).not_contain("tmp1.api.news")
            t = am.lookup('/api/news/456')  # looking up resuls in loading *.py
            ok (sys.modules).contains("tmp1.api.items")
            ok (sys.modules).contains("tmp1.api.news")    # loaded!

        @test("[!sb5h9] returns action class, action methods and urlpath arguments.")
        def _(self, am, name="tmp1"):
            validate_lookup(am, lazy=False, argstype=dict)

        @test("[!vtgiz] returns None when not found.")
        def _(self, am):
            ok (am.lookup('/api/zzzz')) == None
            ok (am.lookup('/api/news/123/456')) == None


    with subject('#__iter__()'):

        @test("[!u58yc] yields each urlpath pattern, action class, and action methods.")
        def _(self, am, name="tmp1"):
            ts = [ t for t in am ]
            ok (ts).length(4)
            #
            from tmp1.api.items import ItemsAction
            from tmp1.api.news import NewsAction
            items_d = ItemsAction.__dict__
            news_d  = NewsAction.__dict__
            #
            ok (ts[0]) == ('/api/items',
                           ItemsAction,
                           {'GET': items_d['do_index'], 'POST': items_d['do_create']},
                           )
            ok (ts[1]) == ('/api/items/{id}',
                           ItemsAction,
                           {'GET': items_d['do_show'], 'PUT': items_d['do_update'], 'DELETE': items_d['do_delete']},
                           )
            ok (ts[2]) == ('/api/news',
                           NewsAction,
                           {'GET': news_d['do_index'], 'POST': news_d['do_create']},
                           )
            ok (ts[3]) == ('/api/news/{id}',
                           NewsAction,
                           {'GET': news_d['do_show'], 'PUT': news_d['do_update'], 'DELETE': news_d['do_delete']},
                           )



class ActionTrieMapping_Test(object):

    def provide_mapping_list(self, name):
        return [
            ('/api', [
                ('/items',     name+".api.items.ItemsAction"),
                ('/news',      name+".api.news.NewsAction"),
            ]),
        ]

    def provide_am(self, mapping_list, name, lazy=True):
        assert os.path.isdir(name)
        return k8.ActionTrieMapping(mapping_list, lazy=lazy)

    def after(self):
        clear_module_cache()
        clear_modules(provide_name(self))


    with subject('#__init__()'):

        @test("[!1gp9m] accepts urlpath mapping list.")
        def _(self, mapping_list):
            am = k8.ActionTrieMapping(mapping_list, lazy=True)
            ok (am._fixed_entries) == {}
            ok (am._variable_entries) == {
                'api': {
                    'items': {
                        0: ("tmp1.api.items.ItemsAction", "/api/items", []),
                    },
                    'news': {
                        0: ("tmp1.api.news.NewsAction", "/api/news", []),
                    },
                },
            }

        @test("[!n9wrs] load classes if lazy=False.")
        def _(self, mapping_list):
            clear_modules("tmp1")
            ok (sys.modules).not_contain("tmp1")
            ok (sys.modules).not_contain("tmp1.api")
            #
            am = k8.ActionTrieMapping(mapping_list, lazy=False)
            ok (sys.modules).contains("tmp1")
            ok (sys.modules).contains("tmp1.api")
            from tmp1.api.items import ItemsAction
            from tmp1.api.news  import NewsAction
            ok (am._fixed_entries) == {
                "/api/items": (ItemsAction,
                               {"GET" : ItemsAction.__dict__["do_index"],
                                "POST": ItemsAction.__dict__["do_create"]},
                               (),
                               ),
                "/api/news":  (NewsAction,
                               {"GET" : NewsAction.__dict__["do_index"],
                                "POST": NewsAction.__dict__["do_create"]},
                               (),
                               ),
            }
            ok (am._variable_entries) == {
                "api": {
                    "items": {
                        1: {
                            None: (ItemsAction,
                                   {"GET"   : ItemsAction.__dict__["do_show"],
                                    "PUT"   : ItemsAction.__dict__["do_update"],
                                    "DELETE": ItemsAction.__dict__["do_delete"]},
                                   ["id"],
                                   ""),
                        },
                    },
                    "news": {
                        1: {
                            None: (NewsAction,
                                   {"GET"   : NewsAction.__dict__["do_show"],
                                    "PUT"   : NewsAction.__dict__["do_update"],
                                    "DELETE": NewsAction.__dict__["do_delete"]},
                                   ["id"],
                                   ""),
                        },
                    },
                },
            }

        @test("[!ifj4v] don't load classes if lazy=True.")
        def _(self, mapping_list):
            clear_modules("tmp1")
            ok (sys.modules).not_contain("tmp1")
            ok (sys.modules).not_contain("tmp1.api")
            #
            am = k8.ActionTrieMapping(mapping_list, lazy=True)
            ok (sys.modules).not_contain("tmp1")
            ok (sys.modules).not_contain("tmp1.api")
            ok (am._fixed_entries) == {}
            ok (am._variable_entries) == {
                "api": {
                    "items": {
                        0: ("tmp1.api.items.ItemsAction", "/api/items", []),
                    },
                    "news": {
                        0: ("tmp1.api.news.NewsAction", "/api/news", []),
                    },
                },
            }

        @test("[!3zjhc] sets actual 'urlpath()' to each action functions.")
        def _(self, mapping_list):
            am = k8.ActionTrieMapping(mapping_list, lazy=False)
            t = am.lookup("/api/items")
            klass = t[0]
            ok (klass.do_index.urlpath())    == '/api/items'
            ok (klass.do_create.urlpath())   == '/api/items'
            ok (klass.do_show.urlpath(10))   == '/api/items/10'
            ok (klass.do_update.urlpath(20)) == '/api/items/20'
            ok (klass.do_delete.urlpath(30)) == '/api/items/30'


    with subject('#lookup()'):

        @test("[!05a7a] loads action classes dinamically if lazy=True.")
        def _(self, am, lazy=True, name="tmp1"):
            clear_modules("tmp1")
            ok (sys.modules).not_contain("tmp1")
            ok (sys.modules).not_contain("tmp1.api")
            ok (sys.modules).not_contain("tmp1.api.items")
            ok (sys.modules).not_contain("tmp1.api.news")
            ok (am._fixed_entries) == {}
            ok (am._variable_entries) == {
                'api': {
                    'items': {
                        0: ("tmp1.api.items.ItemsAction", "/api/items", []),
                    },
                    'news': {
                        0: ("tmp1.api.news.NewsAction", "/api/news", []),
                    },
                },
            }
            #
            am.lookup("/api/items")
            ok (sys.modules).contains("tmp1")              # loaded!
            ok (sys.modules).contains("tmp1.api")          # loaded!
            ok (sys.modules).contains("tmp1.api.items")    # loaded!
            ok (sys.modules).not_contain("tmp1.api.news")  # NOT LOADED YET!
            import tmp1.api.items
            items_d = tmp1.api.items.ItemsAction.__dict__
            ok (am._fixed_entries) == {
                '/api/items': (
                    tmp1.api.items.ItemsAction,
                    {'GET' :  items_d['do_index'],
                     'POST':  items_d['do_create']},
                    (),
                ),
            }
            ok (am._variable_entries) == {
                'api': {
                    'items': {
                        1: {
                            None: (
                                tmp1.api.items.ItemsAction,
                                {'GET':    items_d['do_show'],
                                 'PUT':    items_d['do_update'],
                                 'DELETE': items_d['do_delete']},
                                ["id"],
                                '',
                            ),
                        },
                    },
                    'news': {
                        0: ("tmp1.api.news.NewsAction", "/api/news", []),
                    },
                },
            }
            #
            am.lookup("/api/news/123")
            ok (sys.modules).contains("tmp1")
            ok (sys.modules).contains("tmp1.api")
            ok (sys.modules).contains("tmp1.api.items")
            ok (sys.modules).contains("tmp1.api.news")     # loaded!
            import tmp1.api.news
            news_d = tmp1.api.news.NewsAction.__dict__
            ok (am._fixed_entries) == {
                '/api/items': (
                    tmp1.api.items.ItemsAction,
                    {'GET' :  items_d['do_index'],
                     'POST':  items_d['do_create']},
                    (),
                ),
                '/api/news': (
                    tmp1.api.news.NewsAction,
                    {'GET' :  news_d['do_index'],
                     'POST':  news_d['do_create']},
                    (),
                ),
            }
            ok (am._variable_entries) == {
                'api': {
                    'items': {
                        1: {
                            None: (
                                tmp1.api.items.ItemsAction,
                                {'GET':    items_d['do_show'],
                                 'PUT':    items_d['do_update'],
                                 'DELETE': items_d['do_delete']},
                                ["id"],
                                '',
                            ),
                        },
                    },
                    'news': {
                        1: {
                            None: (
                                tmp1.api.news.NewsAction,
                                {'GET':    news_d['do_show'],
                                 'PUT':    news_d['do_update'],
                                 'DELETE': news_d['do_delete']},
                                ["id"],
                                '',
                            ),
                        },
                    },
                },
            }

        @test("[!u95qz] returns action class, action methods and urlpath arguments.")
        def _(self, am, name="tmp1"):
            validate_lookup(am, lazy=True, argstype=list)

        @test("[!ltatd] returns None when not found.")
        def _(self, am):
            ok (am.lookup('/api/zzzz')) == None
            ok (am.lookup('/api/news/123/456')) == None


    with subject('#__iter__()'):

        @test("[!0sgfj] yields each urlpath pattern, action class, and action methods.")
        @todo
        def _(self, am, name="tmp1"):
            assert False



if __name__ == '__main__':
    oktest.main()
