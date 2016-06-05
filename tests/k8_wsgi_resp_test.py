# -*- coding: utf-8 -*-

import sys

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end

import keight as k8


class Response_Test(object):


    with subject('#__init__()'):

        @test("[!3d06t] default status code is 200.")
        def _(self):
            resp = k8.wsgi.Response()
            ok (resp.status) == 200


    with subject('#header()'):

        @test("[!u5pqv] returns header value.")
        def _(self):
            resp = k8.wsgi.Response()
            resp.content_type   = "application/json"
            resp.content_length = 123
            resp.add_header('Location', '/redirect')
            ok (resp.header('Content-Type'))   == "application/json"
            ok (resp.header('Content-Length')) == "123"
            ok (resp.header('Location'))       == "/redirect"


    with subject('#add_header()'):

        @test("[!xeqt9] adds response header.")
        def _(self):
            resp = k8.wsgi.Response()
            resp.add_header('ETag', "abc123")
            ok (resp.header('ETag')) == "abc123"


    with subject('#get_header_list()'):

        @test("[!pducc] returns list of pair header name and value.")
        def _(self):
            resp = k8.wsgi.Response()
            resp.content_type   = "application/json"
            resp.content_length = 100
            resp.add_header('ETag', "abc123")
            resp.add_header('Cache-Control', "no-cache")
            ok (resp.get_header_list()) == [
                ('Content-Type'   , "application/json"),
                ('Content-Length' , "100"),
                ('ETag'           , "abc123"),
                ('Cache-Control'  , "no-cache"),
            ]

        @test("[!zvggv] header list contains Content-Length header if it is set.")
        def _(self):
            resp = k8.wsgi.Response()
            resp.content_type   = "application/json"
            resp.content_length = 100
            ok (resp.get_header_list()) == [
                ('Content-Type'   , "application/json"),
                ('Content-Length' , "100"),
            ]
            #
            resp = k8.wsgi.Response()
            resp.content_length = 100
            ok (resp.get_header_list()) == [
                ('Content-Length' , "100"),
            ]

        @test("[!oij5a] header list contains Content-Type header if it is set.")
        def _(self):
            resp = k8.wsgi.Response()
            resp.content_type   = "application/json"
            resp.content_length = 100
            ok (resp.get_header_list()) == [
                ('Content-Type'   , "application/json"),
                ('Content-Length' , "100"),
            ]
            #
            resp = k8.wsgi.Response()
            resp.content_type   = "application/json"
            ok (resp.get_header_list()) == [
                ('Content-Type'   , "application/json"),
            ]


    with subject('#add_cookie()'):

        @test("[!fw2f5] returns cookie string.")
        def _(self):
            resp = k8.wsgi.Response()
            cookie_str = resp.add_cookie('name1', 'value1')
            ok (cookie_str) == "name1=value1"

        @test("[!eng8x] builds cookie string.")
        def _(self):
            resp = k8.wsgi.Response()
            cookie_str = resp.add_cookie('name1', 'value1',
                                         domain   = "api.example.com",
                                         path     = "/api",
                                         max_age  = "1200",
                                         expires  = "2016-01-01 12:34:56 GMT",
                                         httponly = True,
                                         secure   = True,
                                         )
            ok (cookie_str) == r"name1=value1; Domain=api.example.com; Path=/api; Max-Age=1200; Expires=2016-01-01 12:34:56 GMT; HttpOnly; Secure"

        @test("[!a17wa] adds Set-Cookie header.")
        def _(self):
            resp = k8.wsgi.Response()
            resp.add_cookie('name1', 'value1')
            ok (resp.header('Set-Cookie')) == "name1=value1"
            #
            resp = k8.wsgi.Response()
            resp.add_cookie('name1', 'value1')
            resp.add_cookie('name2', 'value2')
            resp.add_cookie('name3', 'value3')
            ok (resp.get_header_list()) == [
                ('Set-Cookie', "name1=value1"),
                ('Set-Cookie', "name2=value2"),
                ('Set-Cookie', "name3=value3"),
            ]



if __name__ == '__main__':
    oktest.main()
