# -*- coding: utf-8 -*-

import sys, os, re, shutil
from datetime import datetime

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end

import keight as k8
from keight import on



class On_Test(object):


    with subject('#path()'):

        @test("[!nhlhs] works with 'with' statement.")
        def _(self):
            ok (on._urlpath_pattern) == None
            with on.path('/foo/{id}'):
                ok (on._urlpath_pattern) == '/foo/{id}'
            ok (on._urlpath_pattern) == None

        @test("[!fl2hd] (UNDOCUMENTED) allows to nest 'with' statement.")
        def _(self):
            ok (on._urlpath_pattern) == None
            with on.path('/foo'):
                ok (on._urlpath_pattern) == '/foo'
                with on.path('/{id}'):
                    ok (on._urlpath_pattern) == '/foo/{id}'
                    with on.path('/comments'):
                        ok (on._urlpath_pattern) == '/foo/{id}/comments'
                    ok (on._urlpath_pattern) == '/foo/{id}'
                ok (on._urlpath_pattern) == '/foo'
            ok (on._urlpath_pattern) == None

        @test("[!nbcq8] clears urlpath data even if exception raised.")
        def _(self):
            ok (on._urlpath_pattern) == None
            try:
                with on.path('/foo'):
                    ok (on._urlpath_pattern) == '/foo'
                    1/0
            except ZeroDivisionError:
                pass
            ok (on._urlpath_pattern) == None


    with subject('#__call__()'):

        @test("[!i47p3] maps request path and urlpath pattern with action method.")
        def _(self):
            class HelloAction(k8.Action):
                @on('GET', r'/{id}')
                def do_show(self, id):
                    return "..."
                @on('PUT', r'/{id}')
                def do_update(self, id):
                    return "..."
            #
            ok (HelloAction.__mapping__) == [
                (r'/{id}', {'GET'    : HelloAction.__dict__['do_show'],
                            'PUT'    : HelloAction.__dict__['do_update'],
                           }
                 )
            ]

        @test("[!a6xv2] sets keyword args to function as options.")
        def _(self):
            class HelloAction(k8.Action):
                @on('POST', r'', csrf=False, tag="new")
                def do_create(self):
                    return "..."
            #
            fn = HelloAction.__dict__['do_create']
            ok (fn).has_attr('options')
            ok (fn.options) == {"csrf": False, "tag": "new"}

        @test("[!2ftjv] @on.GET(), @on.POST(), ... are same as @on('GET'), @on('POST'), ...")
        def _(self):
            class HelloAction(k8.Action):
                @on.GET(r'/{id}')
                def do_get(self, id):
                    return "..."
                @on.POST(r'/{id}')
                def do_post(self, id):
                    return "..."
                @on.PUT(r'/{id}')
                def do_put(self, id):
                    return "..."
                @on.DELETE(r'/{id}')
                def do_delete(self, id):
                    return "..."
                @on.HEAD(r'/{id}')
                def do_head(self, id):
                    return "..."
                @on.OPTIONS(r'/{id}')
                def do_options(self, id):
                    return "..."
                @on.TRACE(r'/{id}')
                def do_trace(self, id):
                    return "..."
                @on.LINK(r'/{id}')
                def do_link(self, id):
                    return "..."
                @on.UNLINK(r'/{id}')
                def do_unlink(self, id):
                    return "..."
            #
            ok (HelloAction.__mapping__) == [
                (r'/{id}', {
                    'GET'    : HelloAction.__dict__['do_get'],
                    'POST'   : HelloAction.__dict__['do_post'],
                    'PUT'    : HelloAction.__dict__['do_put'],
                    'DELETE' : HelloAction.__dict__['do_delete'],
                    'HEAD'   : HelloAction.__dict__['do_head'],
                    'OPTIONS': HelloAction.__dict__['do_options'],
                    'TRACE'  : HelloAction.__dict__['do_trace'],
                    'LINK'   : HelloAction.__dict__['do_link'],
                    'UNLINK' : HelloAction.__dict__['do_unlink'],
                }),
            ]


        @test("[!st0sl] uses urlpath specified by 'on.path()' when 2nd arg is null.")
        def _(self):
            class HelloAction(k8.Action):
                with on.path(r'/{id}'):
                    @on('GET')
                    def do_show(self, id):
                        return "..."
                    @on('PUT')
                    def do_update(self, id):
                        return "..."
            #
            ok (HelloAction.__mapping__) == [
                (r'/{id}', {'GET'    : HelloAction.__dict__['do_show'],
                            'PUT'    : HelloAction.__dict__['do_update'],
                           }
                 )
            ]

        @test("[!kc43q] when both 'on.path()' and 2nd arg are specified, concats them.")
        def _(self):
            class HelloAction(k8.Action):
                with on.path(r'/{id}'):
                    @on('GET', '.html')
                    def do_show_html(self, id):
                        return "..."
                    @on('GET', '.json')
                    def do_show_json(self, id):
                        return "..."
            #
            ok (HelloAction.__mapping__) == [
                (r'/{id}.html', {'GET': HelloAction.__dict__['do_show_html']}),
                (r'/{id}.json', {'GET': HelloAction.__dict__['do_show_json']}),
            ]

        @test("[!6iv0b] raises error when neither 'on.path()' nor 2nd arg specified.")
        def _(self):
            def fn():
                class HelloAction(k8.Action):
                    #with on.path(r'/{id}'):
                        @on('GET', r'/{id}')
                        def do_show(self, id):
                            return "..."
                        @on('PUT')
                        def do_update(self, id):
                            return "..."
            expected = "on('PUT'): requires urlpath pattern as 2nd argument."
            ok (fn).raises(k8.ActionMappingError, expected)



if __name__ == '__main__':
    import oktest
    oktest.main()
