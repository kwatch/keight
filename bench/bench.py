# -*- coding: utf-8 -*-

import sys
from collections import OrderedDict
from string import ascii_lowercase
from wsgiref.util import setup_testing_defaults

from benchmarker import Benchmarker, Skip


API_ENTRIES = [ "%s%02d" % (c * 3, i) for i, c in enumerate(ascii_lowercase, 1) ]
URLPATHS    = ["/api/aaa01", "/api/aaa01/123", "/api/zzz26", "/api/zzz26/789"]
VERSIONS    = OrderedDict()


##
## Keight
##
try:
    import keight
    VERSIONS['keight'] = keight.__release__
except ImportError:
    keight = None
    VERSIONS['keight'] = ""

def build_keight_app(**kwargs):
    if keight is None:
        return None
    k8 = keight
    on = keight.on

    class HelloAction(k8.Action):

        with on.path(r''):

            @on('GET')
            def do_index(self):
                return "<h1>index</h1>"
            @on('POST')
            def do_create(self):
                return "<h1>create</h1>"

        with on.path(r'/new'):

            @on('GET')
            def do_new(self):
                return "<h1>new</h1>"

        with on.path(r'/{id}'):

            @on('GET')
            def do_show(self, id):
                return "<h1>show</h1>"
            @on('PUT')
            def do_update(self, id):
                return "<h1>update</h1>"
            @on('DELETE')
            def do_delete(self, id):
                return "<h1>delete</h1>"

        with on.path(r'/{id}/edit'):

            @on('GET')
            def do_edit(self, id):
                return "<h1>edit</h1>"

    mapping = [
        (r'/api', [ ("/"+x, HelloAction) for x in API_ENTRIES ]),
    ]
    app = k8.wsgi.Application(mapping, **kwargs)
    return app


##
## Falcon
##
try:
    import falcon
    VERSIONS['falcon'] = falcon.__version__
except ImportError:
    falcon = None
    VERSIONS['falcon'] = ""

def build_falcon_app():
    if falcon is None:
        return None

    class HelloResource1(object):
        def on_get(self, req, resp):
            resp.body = "<h1>index</h1>"
        def on_post(self, req, resp):
            resp.body = "<h1>create</h1>"

    class HelloResource2(object):
        def on_get(self, req, resp):
            resp.body = "<h1>new</h1>"

    class HelloResource3(object):
        def on_get(self, req, resp, id):
            resp.body = "<h1>show</h1>"
        def on_put(self, req, resp, id):
            resp.body = "<h1>update</h1>"
        def on_delete(self, req, resp, id):
            resp.body = "<h1>delete</h1>"

    class HelloResource4(object):
        def on_get(self, req, resp, id):
            resp.body = "<h1>edit</h1>"

    app = falcon.API()
    for x in API_ENTRIES:
        app.add_route(r'/api/%s' % x          , HelloResource1())
        app.add_route(r'/api/%s/new' % x      , HelloResource2())
        app.add_route(r'/api/%s/{id}' % x     , HelloResource3())
        app.add_route(r'/api/%s/{id}/edit' % x, HelloResource4())
    return app


##
## Bottle
##
try:
    import bottle
    VERSIONS['bottle'] = bottle.__version__
except ImportError:
    bottle = None
    VERSIONS['bottle'] = ""

def build_bottle_app():
    if bottle is None:
        return None

    def add_handlers(app, item):
        @app.get('/api/%s' % item)
        def bottle_index():
            return "<h1>index</h1>"
        @app.post('/api/%s' % item)
        def bottle_create():
            return "<h1>create</h1>"
        @app.post('/api/%s/new' % item)
        def bottle_new():
            return "<h1>new</h1>"
        @app.get('/api/%s/<id>' % item)
        def bottle_show(id):
            return "<h1>show</h1>"
        @app.post('/api/%s/<id>' % item)
        def bottle_update(id):
            return "<h1>update</h1>"
        @app.post('/api/%s/<id>' % item)
        def bottle_delete(id):
            return "<h1>delete</h1>"
        @app.post('/api/%s/<id>/edit' % item)
        def bottle_delete(id):
            return "<h1>edit</h1>"

    app = bottle.Bottle()
    for item in API_ENTRIES:
        add_handlers(app, item)
    return app


##
## Tornado
##
try:
    import tornado
    import tornado.wsgi
    VERSIONS['tornado'] = tornado.version
except ImportError:
    tornado = None
    VERSIONS['tornado'] = ""

def build_tornado_app():
    if tornado is None:
        return None

    class HelloHandler1(tornado.web.RequestHandler):
        def check_etag_header(self): return False
        def get(self):
            self.write("<h1>index</h1>")
        def post(self):
            self.write("<h1>create</h1>")
    class HelloHandler2(tornado.web.RequestHandler):
        def check_etag_header(self): return False
        def get(self):
            self.write("<h1>new</h1>")
    class HelloHandler3(tornado.web.RequestHandler):
        def check_etag_header(self): return False
        def get(self, id):
            self.write("<h1>show</h1>")
        def put(self, id):
            self.write("<h1>update</h1>")
        def delete(self, id):
            self.write("<h1>delete</h1>")
    class HelloHandler4(tornado.web.RequestHandler):
        def check_etag_header(self): return False
        def get(self, id):
            self.write("<h1>edit</h1>")

    mapping = []
    for x in API_ENTRIES:
        mapping.append(("/api/%s"         % x, HelloHandler1))
        mapping.append(("/api/%s/new"     % x, HelloHandler2))
        mapping.append(("/api/%s/([^/]+)" % x, HelloHandler3))
        mapping.append(("/api/%s/([^/]+)" % x, HelloHandler4))
    application = tornado.web.Application(mapping)
    app = tornado.wsgi.WSGIAdapter(application)
    return app


##
## Flask
##
try:
    from flask import Flask
    VERSIONS['flask'] = falcon.__version__
except ImportError:
    Flask = None
    VERSIONS['flask'] = ""

def build_flask_app():
    if Flask is None:
        return None

    def add_handlers(app, item):
        def flask_index():
            return "<h1>index</h1>"
        def flask_create():
            return "<h1>create</h1>"
        def flask_new():
            return "<h1>new</h1>"
        def flask_show(id):
            return "<h1>show</h1>"
        def flask_update(id):
            return "<h1>update</h1>"
        def flask_delete(id):
            return "<h1>delete</h1>"
        def flask_edit(id):
            return "<h1>edit</h1>"
        #
        flask_index  .__name__ = 'flask_index_'  + item
        flask_create .__name__ = 'flask_create_' + item
        flask_new    .__name__ = 'flask_new_'    + item
        flask_show   .__name__ = 'flask_show_'   + item
        flask_update .__name__ = 'flask_update_' + item
        flask_delete .__name__ = 'flask_delete_' + item
        flask_edit   .__name__ = 'flask_edit_'   + item
        #
        app.route('/api/%s'           % item, methods=['GET']   )(flask_index)
        app.route('/api/%s'           % item, methods=['POST']  )(flask_create)
        app.route('/api/%s/new'       % item, methods=['GET']   )(flask_new)
        app.route('/api/%s/{id}'      % item, methods=['GET']   )(flask_show)
        app.route('/api/%s/{id}'      % item, methods=['PUT']   )(flask_update)
        app.route('/api/%s/{id}'      % item, methods=['DELETE'])(flask_delete)
        app.route('/api/%s/{id}/edit' % item, methods=['GET']   )(flask_edit)

    app = Flask(__name__)
    for x in API_ENTRIES:
        add_handlers(app, x)
    return app


##
## Pyramid
##
try:
    import pyramid
    #VERSIONS['pyramid'] = pyramid.__version__
    import pip
    VERSIONS['pyramid'] = \
        next(( x.version for x in pip.get_installed_distributions()
                           if x.project_name == 'pyramid' ), None)
except ImportError:
    Flask = None
    VERSIONS['pyramid'] = ""

def build_pyramid_app():
    if pyramid is None:
        return None

    buf = []
    buf.append(r"""
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPMethodNotAllowed
"""[1:])
    for item in API_ENTRIES:
        buf.append(r"""
@view_config(route_name='{item}_items', renderer='string')
def pyramid_{item}_items(request):
    if request.method in ('GET', 'HEAD'):
        return "<h1>index</h1>"
    elif request.method == 'POST':
        return "<h1>create</h1>"
    else:
        raise HTTPMethodNotAllowed()

@view_config(route_name='{item}_newitem', renderer='string')
def pyramid_{item}_newitem(request):
    if request.method in ('GET', 'HEAD'):
        return "<h1>new</h1>"
    else:
        raise HTTPMethodNotAllowed()

@view_config(route_name='{item}_item', renderer='string')
def pyramid_{item}_item(request):
    if request.method in ('GET', 'HEAD'):
        return "<h1>show</h1>"
    elif request.method == 'PUT':
        return "<h1>update</h1>"
    elif request.method == 'DELETE':
        return "<h1>delete</h1>"
    else:
        raise HTTPMethodNotAllowed()

@view_config(route_name='{item}_edititem', renderer='string')
def pyramid_{item}_edititem(request):
    if request.method in ('GET', 'HEAD'):
        return "<h1>edit</h1>"
    else:
        raise HTTPMethodNotAllowed()
"""[1:].format(item=item))
    exec("".join(buf), globals(), globals())
    from pyramid.config import Configurator
    config = Configurator()
    for x in API_ENTRIES:
        config.add_route('%s_items'    % x, '/api/%s' % x)
        config.add_route('%s_newitem'  % x, '/api/%s/new' % x)
        config.add_route('%s_item'     % x, '/api/%s/{id}' % x)
        config.add_route('%s_edititem' % x, '/api/%s/{id}/edit' % x)
    config.scan()
    app = config.make_wsgi_app()
    return app


##
##
##


def new_environ(method, urlpath):
    environ = {"REQUEST_METHOD": method, "PATH_INFO": urlpath}
    setup_testing_defaults(environ)
    return environ


class StartResponse(object):

    def __call__(self, status, headers):
        self.status  = status
        self.headers = headers


with Benchmarker(loop=100000, cycle=5, extra=2) as bench:

    print("")
    for k, v in VERSIONS.items():
        print("## %-20s: %s" % (k, v or '(not installed)'))
    print("")

    @bench(None)
    def _(bm):
        environ = new_environ('GET', upath)
        start_response = StartResponse()
        status = "200 OK"
        headers = [("Content-Type", "text/html")]
        for _ in bm:
            start_response(status, headers)

    k8rexp_app = build_keight_app(engine='rexp')
    for upath in URLPATHS:
        @bench('keight(rexp): %s' % upath)
        def _(bm, upath=upath, app=k8rexp_app):
            if app is None: raise Skip("not installed")
            environ = new_environ('GET', upath)
            start_response = StartResponse()
            for _ in bm:
                body = app(environ, start_response)

    k8trie_app = build_keight_app(engine='statemachine')
    for upath in URLPATHS:
        @bench('keight(trie): %s' % upath)
        def _(bm, upath=upath, app=k8trie_app):
            if app is None: raise Skip("not installed")
            environ = new_environ('GET', upath)
            start_response = StartResponse()
            for _ in bm:
                body = app(environ, start_response)

    falcon_app = build_falcon_app()
    for upath in URLPATHS:
        @bench('falcon: %s' % upath)
        def _(bm, upath=upath, app=falcon_app):
            if app is None: raise Skip("not installed")
            environ = new_environ('GET', upath)
            start_response = StartResponse()
            for _ in bm:
                body = app(environ, start_response)

    bottle_app = build_bottle_app()
    for upath in URLPATHS:
        @bench('bottle: %s' % upath)
        def _(bm, upath=upath, app=bottle_app):
            if app is None: raise Skip("not installed")
            environ = new_environ('GET', upath)
            start_response = StartResponse()
            for _ in bm:
                body = app(environ, start_response)

    tornado_app = build_tornado_app()
    for upath in URLPATHS:
        @bench('tornado: %s' % upath)
        def _(bm, upath=upath, app=tornado_app):
            if app is None: raise Skip("not installed")
            environ = new_environ('GET', upath)
            start_response = StartResponse()
            for _ in bm:
                body = app(environ, start_response)

    flask_app = build_flask_app()
    for upath in URLPATHS:
        @bench('flask: %s' % upath)
        def _(bm, upath=upath, app=flask_app):
            if app is None: raise Skip("not installed")
            environ = new_environ('GET', upath)
            start_response = StartResponse()
            for _ in bm:
                body = app(environ, start_response)

    pyramid_app = build_pyramid_app()
    for upath in URLPATHS:
        @bench('pyramid: %s' % upath)
        def _(bm, upath=upath, app=pyramid_app):
            if app is None: raise Skip("not installed")
            environ = new_environ('GET', upath)
            start_response = StartResponse()
            for _ in bm:
                body = app(environ, start_response)
