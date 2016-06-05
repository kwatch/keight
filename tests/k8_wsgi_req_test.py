# -*- coding: utf-8 -*-

import sys

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end

import keight as k8


class Request_Test(object):


    with subject('#__init__()'):

        @test("[!ualzp] accepts environ object.")
        def _(self):
            env = k8.wsgi.mock_env('PUT', '/api/books/123')
            req = k8.wsgi.Request(env)
            ok (req.env) == env

        @test("[!841wq] sets method and path attributes.")
        def _(self):
            env = k8.wsgi.mock_env('PUT', '/api/books/123')
            req = k8.wsgi.Request(env)
            ok (req.method) == 'PUT'
            ok (req.path)   == '/api/books/123'


    with subject('#content_type'):

        @test("[!l88e2] returns CONTENT_TYPE value in environ object.")
        def _(self):
            env = k8.wsgi.mock_env('PUT', '/api/books/123')
            ok (k8.wsgi.Request(env).content_type) == None
            env['CONTENT_TYPE'] = "application/x-www-form-urlencoded"
            ok (k8.wsgi.Request(env).content_type) == "application/x-www-form-urlencoded"


    with subject('#content_length'):

        @test("[!uwj7o] returns CONTENT_LENGTH value in environ object.")
        def _(self):
            env = k8.wsgi.mock_env('GET', '/')
            ok (k8.wsgi.Request(env).content_length) == None
            env['CONTENT_LENGTH'] = "123"
            ok (k8.wsgi.Request(env).content_length) == 123

        @test("[!j39md] returns int value instead of string.")
        def _(self):
            env = k8.wsgi.mock_env('GET', '/')
            env['CONTENT_LENGTH'] = "123"
            ok (k8.wsgi.Request(env).content_length).is_a(int)


    with subject('#headers'):

        @test("[!n45wo] returns header object which wraps environ object.")
        def _(self):
            env = k8.wsgi.mock_env('GET', '/api/books')
            env['CONTENT_TYPE']          = "application/json"
            env['CONTENT_LENGTH']        = "123"
            env['HTTP_ACCEPT_ENCODING']  = "gzip, deflate"
            env['HTTP_X_REQUESTED_WITH'] = "XMLHttpRequest"
            req = k8.wsgi.Request(env)
            ok (req.headers['Content-Type'])     == "application/json"
            ok (req.headers['Content-Length'])   == "123"
            ok (req.headers['Accept-Encoding'])  == "gzip, deflate"
            ok (req.headers['X-Requested-With']) == "XMLHttpRequest"


    with subject('#header()'):

        @test("[!3ymtd] returns header value in environ object.")
        def _(self):
            env = k8.wsgi.mock_env('GET', '/api/books')
            env['CONTENT_TYPE']          = "application/json"
            env['CONTENT_LENGTH']        = "123"
            env['HTTP_ACCEPT_ENCODING']  = "gzip, deflate"
            env['HTTP_X_REQUESTED_WITH'] = "XMLHttpRequest"
            req = k8.wsgi.Request(env)
            ok (req.header('Content-Type'))     == "application/json"
            ok (req.header('Content-Length'))   == "123"
            ok (req.header('Accept-Encoding'))  == "gzip, deflate"
            ok (req.header('X-Requested-With')) == "XMLHttpRequest"



if __name__ == '__main__':
    oktest.main()
