# -*- coding: utf-8 -*-

import sys

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end

import keight as k8


class BaseAction_Test(object):

    class HelloAction(k8.BaseAction):
        _called = None
        #
        def before_action(self, *a, **kw):
            self._called = []
            self._called.append(('before_action', a, kw))
        #
        def after_action(self, *a, **kw):
            self._called.append(('after_action', a, kw))
        #
        def handle_content(self, *a, **kw):
            self._called.append(('handle_content', a, kw))
            return list(a)
        #
        def hello(self, x, y):
            self._called.append(("hello", (x, y), {}))
            return "<p>x=%r, y=%r</p>" % (x, y)

    def provide_action_class(self):
        return self.HelloAction

    def provide_action_func(self, action_class):
        return action_class.__dict__['hello']

    def provide_action(self, action_class, req="dummy-req", resp="dummy-resp"):
        action = action_class(req, resp)
        return action


    with subject('__init__()'):

        @test("[!accud] takes request and response objects.")
        def _(self, action_class):
            action = action_class("dummy-req", "dummy-resp")
            ok (action.req)  == "dummy-req"
            ok (action.resp) == "dummy-resp"


    with subject('run_request()'):

        @test("[!5rm14] saves current action func into attribute.")
        def _(self, action, action_func):
            args = (123, "foo")
            action.run_action(action_func, args)
            ok (action.action_func).is_(action_func)

        @test("[!23um7] invokes 'before_action()' at first.")
        def _(self, action, action_func):
            args = (123, "foo")
            ok (action._called) == None
            action.run_action(action_func, args)
            ok (action._called[0]) == ('before_action', (), {})

        @test("[!0evnh] calles action function with arguments.")
        def _(self, action, action_func):
            args = (123, "foo")
            ok (action._called) == None
            action.run_action(action_func, args)
            ok (action._called[1]) == ('hello', (123, "foo"), {})

        @test("[!pzf14] invokes 'handle_content()' and returns result of it.")
        def _(self, action, action_func):
            args = (123, "foo")
            ok (action._called) == None
            ret = action.run_action(action_func, args)
            ok (action._called) != None
            ok (action._called[2]) == ('handle_content', ("<p>x=123, y='foo'</p>",), {})
            ok (ret) == ["<p>x=123, y='foo'</p>"]

        @test("[!2cfff] invokes 'after_action()' at end.")
        def _(self, action, action_func):
            ok (action._called) == None
            action.run_action(action_func, (123, "foo"))
            ok (action._called) != None
            ok (action._called[3]) == ('after_action', (None,), {})

        @test("[!khqsv] invokes 'after_action()' even if exception raised.")
        def _(self, action):
            ok (action._called) == None
            action_func = lambda self: 1/0   # raises ZeroDivisionError
            pr = lambda: action.run_action(action_func, ())
            ok (pr).raises(ZeroDivisionError)
            ok (action._called[-1]) == ('after_action', (pr.exception,), {})

        @test("[!onkcb] if exception raised, it will be passed to after_action().")
        def _(self, action):
            ok (action._called) == None
            action_func = lambda self: 1/0   # raises ZeroDivisionError
            pr = lambda: action.run_action(action_func, ())
            ok (pr).raises(ZeroDivisionError)
            ok (action._called) != None
            ok (action._called[-1]) == ('after_action', (pr.exception,), {})



class Action_TC(object):

    class HelloAction(k8.Action):
        def do_index(self):
            return "<p>Hello World!</p>"
        def do_show(self, name):
            return "<p>Hello %s!</p>" % name

    def provide_action(self):
        req  = k8.wsgi.Request({'REQUEST_METHOD':'GET', 'PATH_INFO':'/'})
        resp = k8.wsgi.Response()
        return self.HelloAction(req, resp)


    with subject('handle_content()'):

        with situation("[!5hs2k] when argument is None..."):

            @test("[!sq6ov] returns empty binary string when content is None.")
            def _(self, action):
                ok (action.handle_content(None)) == [b""]

            @test("[!piocs] don't set content-type.")
            def _(self, action):
                action.handle_content(None)
                ok (action.resp.content_type) == None

            @test("[!s380l] sets content-length as 0.")
            def _(self, action):
                action.handle_content(None)
                ok (action.resp.content_length) == 0

        with situation("[!in858] when argument is a dict object..."):

            @test("[!kk6oy] converts it into JSON binary string.")
            def _(self, action):
                ok (action.handle_content({"status": "ok"})) == [b'{"status":"ok"}']

            @test("[!v5bvs] sets content-type as 'application/json'.")
            def _(self, action):
                action.handle_content({"status": "ok"})
                ok (action.resp.content_type) == "application/json"

            @test("[!15dgy] sets content-length.")
            def _(self, action):
                action.handle_content({"status": "ok"})
                ok (action.resp.content_length) == 15

        with situation("[!58h7f] when argument is a unicode object..."):

            @test("[!k655a] converts unicode string into binary string.")
            def _(self, action):
                binary = b'\xe3\x81\x82\xe3\x81\x84\xe3\x81\x86\xe3\x81\x88\xe3\x81\x8a'
                ok (action.handle_content(u"あいうえお")) == [binary]
                ok (binary.decode('utf-8')) == u"あいうえお"

            @test("[!al4tt] don't touch content-type.")
            def _(self, action):
                action.handle_content(u"あいうえお")
                ok (action.resp.content_type) == None

            @test("[!ari1a] sets content-length.")
            def _(self, action):
                action.handle_content(u"あいうえお")
                ok (action.resp.content_length) == 3*5

        with situation("[!0mejh] when argument is a binary string..."):

            @test("[!9mma6] don't convert binary string.")
            def _(self, action):
                binary = b'\xe3\x81\x82\xe3\x81\x84\xe3\x81\x86\xe3\x81\x88\xe3\x81\x8a'
                ok (action.handle_content(binary)) == [binary]

            @test("[!cj7uu] don't touch content-type.")
            def _(self, action):
                binary = b'\xe3\x81\x82\xe3\x81\x84\xe3\x81\x86\xe3\x81\x88\xe3\x81\x8a'
                action.handle_content(binary)
                ok (action.resp.content_type) == None

            @test("[!mathw] sets content-length.")
            def _(self, action):
                binary = b'\xe3\x81\x82\xe3\x81\x84\xe3\x81\x86\xe3\x81\x88\xe3\x81\x8a'
                action.handle_content(binary)
                ok (action.resp.content_length) == 3*5

        with situation("[!lwlxb] else..."):

            @test("[!zxsbp] returns content as-is, regarding it as iterable object.")
            def _(self, action):
                iterable = ('AA', 'BB', 'CC')
                ok (action.handle_content(iterable)) == iterable

            @test("[!hsj7v] don't touch content-type.")
            def _(self, action):
                iterable = ('AA', 'BB', 'CC')
                action.handle_content(iterable)
                ok (action.resp.content_type) == None

            @test("[!6qall] don't touch content-length.")
            def _(self, action):
                iterable = ('AA', 'BB', 'CC')
                action.handle_content(iterable)
                ok (action.resp.content_length) == None


    with subject('#after_action()'):

        @test("[!rc0qi] set content-type automatically when it is blank.")
        def _(self, action):
            func = lambda self: "<p>yes</p>"
            action.run_action(func, ())
            ok (action.resp.content_type) == u"text/html;charset=utf-8"

        @test("[!r3l7v] guesses content-type from request path if possible.")
        def _(self, action):
            action.req.path = "/api/foo.csv"
            func = lambda self: "1,2,3"
            action.run_action(func, ())
            ok (action.resp.content_type) == u"text/comma-separated-values"


    with subject('#guess_content_type'):

        @test("[!ar80y] returns content-type related to suffix of request path.")
        def _(self, action):
            action.req.path = "/aaa.html"
            ok (action.guess_content_type()) == "text/html"
            action.req.path = "/aaa.jpg"
            ok (action.guess_content_type()) == "image/jpeg"
            action.req.path = "/aaa.csv"
            ok (action.guess_content_type()) == "text/comma-separated-values"

        @test("[!eeimv] returns None when request path has no suffix.")
        def _(self, action):
            action.req.path = "/"
            ok (action.guess_content_type()) == None

        @test("[!qaz00] returns None when suffix of request path is unknown.")
        def _(self, action):
            action.req.path = "/x.html/xxx"
            ok (action.guess_content_type()) == None



if __name__ == '__main__':
    oktest.main()
