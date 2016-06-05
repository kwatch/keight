# -*- coding: utf-8 -*-

import sys, os, re
from datetime import datetime

import oktest
from oktest import ok, test, skip, todo, subject, situation, at_end
try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

import keight as k8
from keight import on, mapping
from keight import PY2, PY3

if PY3:
    xrange = range




class util_Test(object):


    with subject('.escape_html()'):

        @test("[!90jx8] escapes '& < > \" \'' into '&amp; &lt; &gt; &quot; &#39;'.")
        def _(self):
            ok (k8.util.escape_html("& < > \" '")) == "&amp; &lt; &gt; &quot; &#39;"


    with subject('.h()'):

        @test("[!a96jo] encodes string into percent encoding format.")
        def _(self):
            ok (k8.util.h("& < > \" '")) == "&amp; &lt; &gt; &quot; &#39;"


    with subject('.parse_query_string()'):

        @test("[!fzt3w] parses query string and returns dict object.")
        def _(self):
            d = k8.util.parse_query_string("x=123&y=456&z=")
            ok (d) == {"x": "123", "y": "456", "z": ""}

        @test("[!engr6] returns empty dict object when query string is empty.")
        def _(self):
            d = k8.util.parse_query_string("")
            ok (d) == {}

        @test("[!t0w33] regards as array of string when param name ends with '[]'.")
        def _(self):
            d = k8.util.parse_query_string("x[]=123&x[]=456")
            ok (d) == {"x[]": ["123", "456"]}


    with subject('.parse_multipart()'):

        def provide_multipart_data(self):
            from os.path import join, dirname
            data_dir = join(dirname(__file__), "data")
            with open(join(data_dir, "multipart.form"), 'rb') as f:
                data = f.read()
            return data

        def provide_boundary(self, multipart_data):
            pos = multipart_data.index(b'\r\n')
            boundary = multipart_data[2:pos]   # ignores '--' at beginning of str
            return boundary

        @test("[!mqrei] parses multipart form data.")
        def _(self, multipart_data, boundary):
            from os.path import join, dirname, getsize
            data = multipart_data
            data_dir = join(dirname(__file__), "data")
            stdin = BytesIO(data)
            try:
                files = None
                params, files = k8.util.parse_multipart(stdin, boundary, len(data))
                ok (params) == {
                    'text1': "test1",
                    'text2': "日本語\r\nあいうえお\r\n",
                    'file1': "example1.png",
                    'file2': "example1.jpg",
                }
                #
                upfile1 = files['file1']
                ok (upfile1).is_a(k8.UploadedFile)
                ok (upfile1.filename)     == "example1.png"
                ok (upfile1.content_type) == "image/png"
                ok (upfile1.tmp_filepath).is_file()
                with open(data_dir + "/example1.png", 'rb') as f:
                    expected_data = f.read()
                with open(upfile1.tmp_filepath, 'rb') as f:
                    actual_data = f.read()
                with open("/tmp/actual1.png", 'wb') as f: f.write(actual_data)
                with open("/tmp/expected1.png", 'wb') as f: f.write(expected_data)
                ok (len(actual_data)) == len(expected_data)
                ok (actual_data) == expected_data
                #
                upfile2 = files['file2']
                ok (upfile2).is_a(k8.UploadedFile)
                ok (upfile2.filename)     == "example1.jpg"
                ok (upfile2.content_type) == "image/jpeg"
                ok (upfile2.tmp_filepath).is_file()
                with open(data_dir + "/example1.jpg", 'rb') as f:
                    expected_data = f.read()
                with open(upfile2.tmp_filepath, 'rb') as f:
                    actual_data = f.read()
                with open("/tmp/actual2.jpg", 'wb') as f: f.write(actual_data)
                with open("/tmp/expected2.jpg", 'wb') as f: f.write(expected_data)
                ok (len(actual_data)) == len(expected_data)
                ok (actual_data) == expected_data
            #
            finally:
                if files:
                    for x in files.values():
                        x.clean()


    with subject('.randstr_b64()'):

        @test("[!yq0gv] returns random string, encoded with urlsafe base64.")
        def _(self):
            arr = [ k8.util.randstr_b64() for _ in xrange(1000) ]
            ok (len(set(arr))) == 1000
            for s in arr:
                ok (s).matches(r'^[-\w]+$')
                ok (len(s)) == 27   # or 43 if sha256


    with subject('.guess_content_type()'):

        @test("[!xw0js] returns content type guessed from filename.")
        def _(self):
            ok (k8.util.guess_content_type("foo.html")) == "text/html"
            ok (k8.util.guess_content_type("foo.jpg"))  == "image/jpeg"
            ok (k8.util.guess_content_type("foo.json")) == "application/json"
            ok (k8.util.guess_content_type("foo.xls"))  == "application/vnd.ms-excel"

        @test("[!dku5c] returns 'application/octet-stream' when failed to guess content type.")
        def _(self):
            ok (k8.util.guess_content_type("foo.rbc"))  == "application/octet-stream"
            ok (k8.util.guess_content_type("foo"))      == "application/octet-stream"


    with subject('.http_utc_time()'):

        @test("[!5k50b] converts Time object into HTTP date format string.")
        def _(self):
            t = datetime(2015, 2, 3, 4, 5, 6)
            ok (k8.util.http_utc_time(t)) == "Tue, 03 Feb 2015 04:05:06 GMT"

        @test("[!3z5lf] raises error when argument is not UTC.")
        @todo
        def _(self):
            assert False



class UploadedFile_Test(object):


    with subject('#__init__()'):

        @test("[!ityxj] takes filename and content type.")
        def _(self):
            x = k8.UploadedFile("hom.html", "text/html")
            ok (x.filename) == "hom.html"
            ok (x.content_type) == "text/html"

        @test("[!5c8w6] sets temporary filepath with random string.")
        def _(self):
            arr = [ k8.UploadedFile("x", "x").tmp_filepath for _ in xrange(1000) ]
            ok (len(set(arr))) == 1000


    with subject('#__enter__()'):

        @test("[!8ezhr] yields with opened temporary file.")
        def _(self):
            @at_end
            def _():
                if os.path.exists(upfile.tmp_filepath):
                    os.unlink(upfile.tmp_filepath)
            s = b"homhom"
            upfile = k8.UploadedFile("hom.html", "text/html")
            with upfile as f:
                f.write(s)
            ok (upfile.tmp_filepath).is_file()
            with open(upfile.tmp_filepath, 'rb') as f:
                ok (f.read()) == s


    with subject('#clean()'):

        @test("[!ft454] removes temporary file if exists.")
        def _(self):
            @at_end
            def _():
                if os.path.exists(upfile.tmp_filepath):
                    os.unlink(upfile.tmp_filepath)
            upfile = k8.UploadedFile("hom.html", "text/html")
            with upfile as f:
                f.write(b"hom")
            ok (upfile.tmp_filepath).is_file()
            upfile.clean()
            ok (upfile.tmp_filepath).not_exist()


    with subject('.new_filepath()'):

        @test("[!zdkts] use $K8_UPLOAD_DIR environment variable as temporary directory.")
        def _(self):
            dir = "/var/tmp/k8.upload"
            import shutil
            if os.path.exists(dir):
                shutil.rmtree(dir)
            #
            key = "K8_UPLOAD_DIR"
            orig = os.getenv(key)
            try:
                os.environ[key] = dir
                os.mkdir(dir)
                upfile = k8.UploadedFile("hom.txt", "text/plain")
                ok (upfile.new_filepath()).should.startswith(dir + "/up.")
            finally:
                os.environ[key] = orig or ""
                shutil.rmtree(dir)



if __name__ == '__main__':
    oktest.main()
