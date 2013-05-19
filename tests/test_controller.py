# -*- coding: utf-8 -*-
from __future__ import with_statement

import oktest
from oktest import ok, not_ok, run, spec
import keight as k8


def _r(*args, **kwargs):
    env = k8.dummy_env(*args, **kwargs)
    return (k8.REQUEST(env), k8.RESPONSE())

config_secret_key = k8.config.secret_key

class ControllerTest(object):

    @classmethod
    def before_all(cls):
        k8.config.secret_key = 'd00c3c7a5948ff63a474613bd9b52ae0'

    @classmethod
    def after_all(cls):
        k8.config.secret_key = config_secret_key

    def before(self):
        self.controller = k8.Controller(*_r())

    def test___init__(self):
        with spec("calls parent __init__() method"):
            req, res = _r()
            c = k8.Controller(req, res)
            ok (c.request).is_(req)
            ok (c.response).is_(res)
        with spec("creates context object and adds self to it"):
            ok (c.context) == {'self': c}

    def test___getitem__(self):
        with spec("returns context data"):
            c = self.controller
            c.context['A'] = 123
            ok (c['A']) == 123

    def test___setitem__(self):
        with spec("sets context data"):
            c = self.controller
            c['A'] = 999
            ok (c.context.get('A')) == 999

    def test_before(self):
        with spec("if request method is not GET, HEAD nor HEAD then checks CSRF token forcedly"):
            for method in ('GET', 'HEAD', 'OPTIONS'):
                c = k8.Controller(*_r(method, '/'))
                c.before()
                ok ('csrf' not in c.__dict__) == True
            for method in ('POST', 'PUT', 'DELETE'):
                c = k8.Controller(*_r(method, '/'))
                def f(): c.before()
                ok (f).raises(k8.Http403Forbidden, 'Csrf token check failed.')

    def test_after(self):
        with spec("if session object exists then save it"):
            class DummySession(object):
                def save(self):
                    self._saved = True
            c = self.controller
            sess = DummySession()
            c.__dict__['session'] = sess
            c.after()
            ok (sess._saved) == True

    def test__def_getter(self):
        with spec("helps to define properties"):
            c = self.controller
            ok (c.session).is_a(k8.SESSION)
            ok (c.csrf)   .is_a(k8.CSRF)
            ok (c.console).is_a(k8.CONSOLE)

    def test_redirect_to(self):
        with spec("raises Http302Found with location"):
            c = self.controller
            def f(): c.redirect_to('/foo')
            ok (f).raises(k8.Http302Found)
            ok (f.exception.location) == '/foo'

    def test_redirect_permanently_to(self):
        with spec("raises Http301MovedPermanently with location"):
            c = self.controller
            def f(): c.redirect_permanently_to('/bar')
            ok (f).raises(k8.Http301MovedPermanently)
            ok (f.exception.location) == '/bar'

    def test_not_found(self):
        with spec("raises Http404NotFound"):
            c = self.controller
            def f(): c.not_found('foobar')
            ok (f).raises(k8.Http404NotFound)
            ok (str(f.exception)) == 'foobar: not found.'
        with spec("if request_uri is not specified then reports current request uri"):
            c = k8.Controller(*_r('GET', '/foo/bar'))
            def f(): c.not_found()
            ok (f).raises(k8.Http404NotFound)
            ok (f.exception.args[0]) == '/foo/bar: not found.'
            ok (str(f.exception)) == '/foo/bar: not found.'

    def test_url_path(self):
        class DummyController(k8.Controller):
            def do_index(self): return ''
            def do_show(self, id): return ''
            def do_edit(self, id): return ''
            def do_update(self, id): return ''
            router = k8.Router()
            router.map('/', GET=do_index)\
                  .map('/(\d+)', GET=do_show, PUT=do_update)\
                  .map('/(\d+)/edit', GET=do_edit)
        DummyController.router.set_base_path('/books')
        c = DummyController(*_r())
        with spec("builds url path from arg"):
            ok (c.url_path('/')) == '/books/'
            ok (c.url_path('')) == '/books'  # or '/books/' ?
            ok (c.url_path('/123')) == '/books/123'
        with spec("kwargs are regarded as query string"):
            ret = c.url_path('/foo', x=1, y='A=B')
            ok (ret).in_(['/books/foo?x=1&y=A%3DB', '/books/foo?y=A%3DB&x=1'])
        with spec("if current class doesn't have router object then raises error"):
            del DummyController.router
            def f(): c.url_path('/index')
            ok (f).raises(ValueError, 'DummyController.router is not configured.')


if __name__ == '__main__':
    oktest.run()
