from __future__ import with_statement

import sys, os
if '..' not in sys.path: sys.path.append('..')

import oktest
from oktest import ok, not_ok, run, spec
import keight as k8
try:
    from cStringIO import StringIO
except LoadError:
    from io import StringIO


BOUNDARY = "foobar1234"
MULTIPART_CONTENT = (
     "--foobar1234\r\n"
     "Content-Disposition: form-data; name=\"name1\"\r\n"
     "\r\n"
     "value1\r\n"
     "--foobar1234\r\n"
     "Content-Disposition: form-data; name=\"file1\"; filename=\"file1.html\"\r\n"
     "Content-Type: text/html\r\n"
     "\r\n"
     "<html>\n"
     "<body><p>Hello</p></body>\n"
     "</html>\n"
     "\r\n"
     "--foobar1234--\r\n"
)


class MultiPartTest(object):

    @classmethod
    def before_all(cls):
        cls._orig = orig = k8.config.upload_file_dir
        k8.config.upload_file_dir = '_test.upload'
        os.mkdir(k8.config.upload_file_dir)

    @classmethod
    def after_all(cls):
        import shutil
        shutil.rmtree(k8.config.upload_file_dir)
        k8.config.upload_file_dir = cls._orig

    def before(self):
        self.mpart = k8.MultiPart(BOUNDARY)

    def test_add(self):
        mpart = self.mpart
        with spec("saves name, value, filename, and content_type"):
            mpart.add('A', 'foo')
            ok (mpart._added) == [('A', 'foo', None, None)]
        with spec("if filename is specified but content_type is not then guess it from filename"):
            mpart.add('B', 'bar', 'B.png', None)
            ok (mpart._added[-1]) == ('B', 'bar', 'B.png', 'image/png')
            mpart.add('C', 'baz', 'C.png', 'image/gif')
            ok (mpart._added[-1]) == ('C', 'baz', 'C.png', 'image/gif')
        with spec("returns self"):
            ret = mpart.add('X', 'xxx')
            ok (ret).is_(mpart)

    def test_build(self):
        with spec("builds multipart data and returns it"):
            mpart = self.mpart
            mpart.add('name1', 'value1')
            mpart.add('file1', "<html>\n<body><p>Hello</p></body>\n</html>\n", 'file1.html', 'text/html')
            ok (mpart.build()) == MULTIPART_CONTENT
        with spec("clears internal buffer"):
            ok (mpart._added) == []

    def test_parse(self):
        with spec("returns params and files"):
            stdin = StringIO(MULTIPART_CONTENT)
            #ok (stdin.read()) == MULTIPART_CONTENT
            content_length = len(MULTIPART_CONTENT)
            mpart = k8.MultiPart(BOUNDARY)
            params, files = mpart.parse(stdin, content_length)
            ok (params.get('name1')) == 'value1'
            ok (params.get('file1')) == 'file1.html'
            upfile = files.get('file1')
            ok (upfile).is_a(k8.UploadedFile)
            ok (upfile.filename) == 'file1.html'
            ok (upfile.content_type) == 'text/html'
            ok (upfile.filepath).is_file()
            ok (os.path.dirname(upfile.filepath)) == k8.config.upload_file_dir
            ok (os.path.basename(upfile.filepath)).matches(r'^[0-9a-f]{40}$')
            ok (open(upfile.filepath).read()) == "<html>\n<body><p>Hello</p></body>\n</html>\n"


if __name__ == '__main__':
    oktest.run()
