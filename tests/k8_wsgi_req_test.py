# -*- coding: utf-8 -*-

import sys, os

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end

import keight as k8
from keight import S


class Request_Test(object):

    def provide_req(self):
        return k8.wsgi.Request(k8.wsgi.mock_env("GET", "/123"))

    def provide_data_dir(self):
        return os.path.join(os.path.dirname(__file__), "data")

    def provide_multipart_env(self, data_dir):
        with open(data_dir + "/multipart.form", 'rb') as f:
            input = f.read()
        boundary = S(input[2:input.index(b'\r\n')])
        cont_type = "multipart/form-data;boundary=%s" % boundary
        env = k8.wsgi.mock_env("POST", "/", input=input, env={"CONTENT_TYPE": cont_type})
        return env


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


    with subject('#params_query'):

        @test("[!6ezqw] parses QUERY_STRING and returns it as Hash/dict object.")
        def _(self):
            qstr = "x=1&y=2"
            env = k8.wsgi.mock_env("GET", "/", env={"QUERY_STRING": qstr})
            req = k8.wsgi.Request(env)
            ok (req.params_query) == {"x": "1", "y": "2"}

        @test("[!o0ws7] unquotes both keys and values.")
        def _(self):
            qstr = "arr%5Bxxx%5D=%3C%3E+%26%3B"
            env = k8.wsgi.mock_env("GET", "/", env={'QUERY_STRING': qstr})
            req = k8.wsgi.Request(env)
            ok (req.params_query) == {"arr[xxx]": "<> &;"}


    with subject('#params_form'):

        @test("[!q88w9] raises 400 error when content length is missing.")
        def _(self):
            env = k8.wsgi.mock_env("POST", "/", form="x=1")
            env['CONTENT_LENGTH'] = None
            req = k8.wsgi.Request(env)
            def fn(): req.params_form
            ok (fn).raises(k8.HttpException)
            ok (fn.exception.status) == 400
            ok (fn.exception.content) == "Content-Length header expected."

        @test("[!gi4qq] raises 400 error when content length is invalid.")
        def _(self):
            env = k8.wsgi.mock_env("POST", "/", form="x=1")
            env['CONTENT_LENGTH'] = "abc"
            req = k8.wsgi.Request(env)
            def fn(): req.params_form
            ok (fn).raises(k8.HttpException)
            ok (fn.exception.status) == 400
            ok (fn.exception.content) == "Content-Length should be an integer."

        @test("[!59ad2] parses form parameters and returns it as Hash/dict object when form requested.")
        def _(self):
            form = "x=1&y=2&arr%5Bxxx%5D=%3C%3E+%26%3B"
            env = k8.wsgi.mock_env("POST", "/", form=form)
            req = k8.wsgi.Request(env)
            ok (req.params_form) == {"x": "1", "y": "2", "arr[xxx]": "<> &;"}

        @test("[!puxlr] raises 400 error when content length is too large (> 10MB).")
        def _(self):
            env = k8.wsgi.mock_env("POST", "/", form="x=1")
            env['CONTENT_LENGTH'] = str(10*1024*1024 + 1)
            req = k8.wsgi.Request(env)
            def fn(): req.params_form
            ok (fn).raises(k8.HttpException)
            ok (fn.exception.status) == 400
            ok (fn.exception.content) == "Content-Length is too large."


    with subject('#params_multipart'):

        @test("[!y1jng] parses multipart when multipart form requested.")
        def _(self, multipart_env, data_dir):
            env = multipart_env
            req = k8.wsgi.Request(env)
            form, files = req.params_multipart
            ok (form) == {
                "text1": "test1",
                "text2": "日本語\r\nあいうえお\r\n",
                "file1": "example1.png",
                "file2": "example1.jpg",
            }
            ok (files).is_a(dict)
            ok (set(files.keys())) == set(["file1", "file2"])
            #
            ok (files['file1']).is_a(k8.UploadedFile)
            ok (files['file1'].filename)     == "example1.png"
            ok (files['file1'].content_type) == "image/png"
            ok (files['file1'].tmp_filepath).is_file()
            with open(data_dir + "/example1.png", 'rb') as f:
                expected = f.read()
            with open(files['file1'].tmp_filepath, 'rb') as f:
                actual   = f.read()
            ok (actual) == expected
            #
            ok (files['file2']).is_a(k8.UploadedFile)
            ok (files['file2'].filename)     == "example1.jpg"
            ok (files['file2'].content_type) == "image/jpeg"
            ok (files['file2'].tmp_filepath).is_file()
            with open(data_dir + "/example1.jpg", 'rb') as f:
                expected = f.read()
            with open(files['file2'].tmp_filepath, 'rb') as f:
                actual   = f.read()
            ok (actual) == expected

        @test("[!mtx6t] raises 400 error when content length of multipart is too large (> 100MB).")
        def _(self, multipart_env):
            env = multipart_env
            env['CONTENT_LENGTH'] = str(100*1024*1024 + 1)
            req = k8.wsgi.Request(env)
            def fn(): req.params_multipart
            ok (fn).raises(k8.HttpException)
            ok (fn.exception.status) == 400
            ok (fn.exception.content) == "Content-Length of multipart is too large."


    with subject('#params_json'):

        @test("[!ugik5] parses ajson data and returns it as hash object when json data is sent.")
        def _(self):
            data = '{"x":1,"y":2,"arr":["a","b","c"]}'
            env = k8.wsgi.mock_env("POST", "/", json=data)
            req = k8.wsgi.Request(env)
            ok (req.params_json) == {"x": 1, "y": 2, "arr": ["a", "b", "c"]}


    with subject('#params'):

        @test("[!erlc7] parses QUERY_STRING when request method is GET or HEAD.")
        def _(self):
            qstr = "a=8&b=9"
            form = "x=1&y=2"
            env = k8.wsgi.mock_env('GET', '/', query=qstr, form=form)
            req = k8.wsgi.Request(env)
            ok (req.params) == {"a": "8", "b": "9"}

        @test("[!cr0zj] parses JSON when content type is 'application/json'.")
        def _(self):
            qstr = "a=8&b=9"
            json = '{"n":123}'
            env = k8.wsgi.mock_env('POST', '/', query=qstr, json=json)
            req = k8.wsgi.Request(env)
            ok (req.params) == {"n": 123}

        @test("[!j2lno] parses form parameters when content type is 'application/x-www-form-urlencoded'.")
        def _(self):
            qstr = "a=8&b=9"
            form = "x=1&y=2"
            env = k8.wsgi.mock_env('POST', '/', query=qstr, form=form)
            req = k8.wsgi.Request(env)
            ok (req.params) == {"x": "1", "y": "2"}

        @test("[!4rmn9] parses multipart when content type is 'multipart/form-data'.")
        @todo
        def _(self):
            assert False



if __name__ == '__main__':
    oktest.main()
