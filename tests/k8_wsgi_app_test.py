# -*- coding: utf-8 -*-

import sys

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end
from oktest.helper import dummy_io

import keight as k8
from keight import on


class WelcomeAction(k8.Action):

    @on('GET', r'')
    def do_welcome(self):
        return "<h1>Welcome</h1>"


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
        if int(id) == 123:
            return "<p>show(%r)</p>" % id
        else:
            raise k8.HttpException(404)

    @on('PUT', r'/{id}')
    def do_update(self, id):
        return "<p>update(%r)</p>" % id

    @on('DELETE', r'/{id}')
    def do_delete(self, id):
        #return "<p>delete(%r)</p>" % id
        if int(id) == 999:
            raise KeyboardInterrupt()
        elif int(id) == 0:
            x = 1/0   # raise ZeroDivisionError
        else:
            raise k8.HttpException(401)



class Application_Test(object):

    def provide_mapping_list(self):
        return [
            (r'/',            WelcomeAction),
            (r'/api', [
                ('/books',    BooksAction),
                ('/authors',  AuthorsAction),
            ]),
        ]

    def provide_app(self, mapping_list):
        return k8.wsgi.Application(mapping_list)


    with subject('__init__()'):

        @test("[!us151] accepts mapping list and creates ActionMapping object.")
        def _(self, mapping_list):
            app = k8.wsgi.Application(mapping_list)
            ok (app._mapping).is_a(k8.ActionRexpMapping)
            #
            app = k8.wsgi.Application(mapping_list, lazy=True)
            ok (app._mapping).is_a(k8.ActionRexpLazyMapping)
            #
            app = k8.wsgi.Application(mapping_list, engine='statemachine')
            ok (app._mapping).is_a(k8.ActionTrieMapping)
            #
            app = k8.wsgi.Application(mapping_list, lazy=True, engine='statemachine')
            ok (app._mapping).is_a(k8.ActionTrieLazyMapping)

        @test("[!ah3gh] if mapping_list is an ActionMapping object, use it as is.")
        def _(self, mapping_list):
            mapping_obj = k8.ActionTrieLazyMapping(mapping_list)
            app = k8.wsgi.Application(mapping_obj)
            ok (app._mapping).is_(mapping_obj)


    with subject('#lookup()'):

        @test("[!1rmcr] returns action class, action methods, and urlpath arguments.")
        def _(self, app):
            t = app.lookup('/')
            ok (t) == (WelcomeAction,
                       {"GET": WelcomeAction.__dict__['do_welcome']},
                       {})
            #
            t = app.lookup('/api/books/123')
            ok (t) == (BooksAction,
                       {"GET"   : BooksAction.__dict__['do_show'],
                        "PUT"   : BooksAction.__dict__['do_update'],
                        "DELETE": BooksAction.__dict__['do_delete'],
                        },
                       {"id": "123"})

    with subject('#dispatch()'):

        @test("[!wtp8c] returns action class, action func, and urlpath arguments.")
        def _(self, app):
            t = app.dispatch('GET', '/')
            ok (t) == (WelcomeAction,
                       WelcomeAction.__dict__['do_welcome'],
                       {})
            #
            t = app.dispatch('PUT', '/api/books/123')
            ok (t) == (BooksAction,
                       BooksAction.__dict__['do_update'],
                       {"id": "123"})


    with subject('#each_mapping()'):

        @test("[!rfx5n] iterates urlpath pattern, action class and action methods.")
        def _(self, app):
            arr = [ t for t in app.each_mapping() ]
            ok (arr) == [
                ('/',
                 WelcomeAction,
                 {'GET':    WelcomeAction.__dict__['do_welcome']},
                 ),
                ('/api/books',
                 BooksAction,
                 {'GET':    BooksAction.__dict__['do_index'],
                  'POST':   BooksAction.__dict__['do_create']},
                 ),
                ('/api/books/{id}',
                 BooksAction,
                 {'GET':    BooksAction.__dict__['do_show'],
                  'PUT':    BooksAction.__dict__['do_update'],
                  'DELETE': BooksAction.__dict__['do_delete']},
                 ),
                ('/api/authors',
                 AuthorsAction,
                 {'GET':    AuthorsAction.__dict__['do_index'],
                  'POST':   AuthorsAction.__dict__['do_create']},
                 ),
                ('/api/authors/{id}',
                 AuthorsAction,
                 {'GET':    AuthorsAction.__dict__['do_show'],
                  'PUT':    AuthorsAction.__dict__['do_update'],
                  'DELETE': AuthorsAction.__dict__['do_delete']},
                 ),
            ]


    with subject('#__call__()'):

        @test("[!8lx2o] invokes action corresponding to request path and method.")
        def _(self, app):
            env = k8.wsgi.mock_env('GET', '/')
            body = app(env, k8.wsgi.StartResponse())
            ok (body) == [b'<h1>Welcome</h1>']
            #
            env = k8.wsgi.mock_env('GET', '/api/authors/123')
            body = app(env, k8.wsgi.StartResponse())
            ok (body) == [b"<p>show('123')</p>"]

        @test("[!huptr] calls start_response and returns response body.")
        def _(self, app):
            env = k8.wsgi.mock_env('GET', '/')
            start_response = k8.wsgi.StartResponse()
            body = app(env, start_response)
            ok (body) == [b'<h1>Welcome</h1>']
            ok (start_response.status) == "200 OK"
            ok (start_response.headers) == [('Content-Type', "text/html;charset=utf-8"),
                                            ('Content-Length', "16")]
            #
            env = k8.wsgi.mock_env('GET', '/api/authors/123')
            start_response = k8.wsgi.StartResponse()
            body = app(env, start_response)
            ok (body) == [b"<p>show('123')</p>"]
            ok (start_response.status) == "200 OK"
            ok (start_response.headers) == [('Content-Type', "text/html;charset=utf-8"),
                                            ('Content-Length', "18")]

        @test("[!2z6xr] raises UnknownHttpStatusCodeError when status code is unknown.")
        def _(self, app):
            env = k8.wsgi.mock_env('GET', '/')
            start_response = k8.wsgi.StartResponse()
            body = app(env, start_response)
            ok (body) == [b'<h1>Welcome</h1>']
            ok (start_response.status) == "200 OK"
            ok (start_response.headers) == [('Content-Type', "text/html;charset=utf-8"),
                                            ('Content-Length', "16")]


    with subject('#handle_request()'):

        @test("[!0cd7m] handles request.")
        def _(self, app):
            env = k8.wsgi.mock_env('GET', '/api/books/123')
            t = app.handle_request(env)
            ok (t) == (200,
                       [('Content-Type',   "text/html;charset=utf-8"),
                        ('Content-Length', "18")],
                       [b"<p>show('123')</p>"])

        @test("[!f66z9] handles http exception.")
        def _(self, app):
            env = k8.wsgi.mock_env('DELETE', '/api/authors/123')
            t = app.handle_request(env)
            ok (t) == (401,
                       [('Content-Type',   "text/plain;charset=utf-8"),
                        ('Content-Length', "16")],
                       [b"401 Unauthorized"])

        @test("[!ewqep] don't catch KeyboardInterrupt error.")
        def _(self, app):
            env = k8.wsgi.mock_env('DELETE', '/api/authors/999')
            fn = lambda: app.handle_request(env)
            ok (fn).raises(KeyboardInterrupt)

        @test("[!tn8yy] returns 500 Internal Server Error when exception raised.")
        def _(self, app):
            with dummy_io() as io:
                env = k8.wsgi.mock_env('DELETE', '/api/authors/0')
                t = app.handle_request(env)
            ok (t) == (500,
                       [('Content-Type',   "text/html;charset=utf-8"),
                        ('Content-Length', "34")],
                       [b"<h2>500 Internal Server Error</h2>"])


    with subject('#handle_exception()'):

        @test("[!7qgls] writes traceback to stderr.")
        def _(self, app):
            with dummy_io() as io:
                env = k8.wsgi.mock_env('DELETE', '/api/authors/0')
                t = app.handle_request(env)
            #
            stdout, stderr = io
            ok (stdout) == ""
            ok (stderr) == ""
            #
            s = env['wsgi.errors'].getvalue()
            lines = s.splitlines(True)
            ok (lines[0])  == "Traceback (most recent call last):\n"
            #ok (lines[-1]) == "ZeroDivisionError: division by zero\n"
            ok (lines[-1]).in_([
                "ZeroDivisionError: integer division or modulo by zero\n", # Py2.7
                "ZeroDivisionError: division by zero\n",
            ])



if __name__ == '__main__':
    oktest.main()
