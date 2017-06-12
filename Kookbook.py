# -*- coding: utf-8 -*-

import sys, os, re
from kook.utils import glob2

kookbook.default = 'help'


@recipe
def task_help(self):
    print(r"""
How to release:

  $ git checkout python-dev
  $ git checkout -b python-1.0
  $ kk edit 1.0.0

  ### create package
  $ kk package
  $ ls dist
  cdnget-1.0.0.tar.gz

  ### confirm package
  $ bash
  $ pyvenv testenv
  $ . testenv/bin/activate
  $ pip install dist/keight-1.0.0.tar.gz
  $ python
  >>> import keight
  >>> keight.__release__
  1.0.0
  >>> exit
  $ deactivate
  $ rm -r testenv

  ### commit and tag
  $ git add -p
  $ git commit -m "python: release preparation for 1.0.0"
  $ git tag py-1.0.0
  $ git push -u origin python-1.0
  $ git push --tags

  ### reset 'python' branch
  $ git checkout python
  $ git reset --hard python-1.0
  $ git push -uf origin python
  $ git checkout python-dev
""")


@recipe
@spices("-s STYLE: '-sv'(verbose), '-ss'(simple), '-sp'(plain)",
        "--all: run on multi version (requires 'versionswitcher')")
def task_test(c, *args, **kwargs):
    target = ' '.join(args or ('tests',))
    target = ' '.join(args or ('tests',))
    os.environ['PYTHONPATH'] = '.'
    if not kwargs.get('all'):
        style = kwargs.get('s') or 'v'
        system(c%"python tests/oktest.py -s$(style) $(target)")
    else:
        style = kwargs.get('s') or 'p'
        try:
            with open("test-all.sh", "w") as f:
                f.write(c%r"""
                    . ~/.vs/bootstrap.sh
                    for pyver in 2.7 3.3 3.4 3.5 3.6; do
                      vs python $pyver > /dev/null
                      version=`python --version 2>&1`
                      echo -n "[$version] "
                      PYTHONPATH=. python tests/oktest.py -sp tests
                    done
                """)
            system_f(c%"bash test-all.sh")
        finally:
            rm_f("test-all.sh")

@recipe
def task_edit(c, release=None):
    """edit files"""
    if release is None:
        print("*** ERROR: edit task requires release number.")
        return 1
    def filenames():
        system("python setup.py sdist --manifest-only > /dev/null 2>&1")
        with open('MANIFEST') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                yield line.strip()
    #
    for fname in filenames():
        print("$ edit %s" % fname)
        with open(fname, 'r+', encoding='utf-8') as f:
            s = f.read()
            s = re.sub(r'\$[R]elease\$', release, s)
            s = re.sub(r'\$[R]elease: .*?\$', '$''Release: %s $' % release, s)
            s = re.sub(r'\$[R]elease: .*?\$', '$''Release: %s $' % release, s)
            #
            f.seek(0)
            f.truncate()
            f.write(s)

@recipe
def task_package(c):
    """create package"""
    system(c%"python setup.py sdist")

@recipe
def task_clean(c):
    """remove files"""
    rm_f("**/*.pyc")
    rm_rf("MANIFEST")
    rm_rf("dist", "build")


@recipe
def task_oktest(c):
    "create hard link of 'oktest.py'"
    fpath = os.path.expanduser('~/src/oktest/python/lib/oktest.py')
    rm_f('tests/oktest.py')
    system(c%'ln $(fpath) tests/oktest.py')


EDITOR_KICKER = os.environ.get('EDITOR_KICKER')


@recipe
@spices('-p port: port number (default 10101)', '-H host: host name', '-q: quiet mode')
def task_editorkicker(c, *args, **kwargs):
    """start editorkicker server"""
    ## command options
    host = kwargs.get('H') or ''
    port = kwargs.get('p')
    port = port and port.isdigit() and int(port) or 10101
    flag_quiet = kwargs.get('q')
    ## report() definition
    if flag_quiet:
        def report(msg): pass
    else:
        def report(msg): sys.stderr.write("*** %s\n" % msg)
    report("host=%s, port=%s" % (repr(host), repr(port)))
    ## wsgi application
    import cgi
    def app(environ, start_response):
        tuples = cgi.parse_qsl(environ.get('QUERY_STRING', ''))
        params = dict(tuples)
        path_info = environ.get('PATH_INFO')
        if path_info == '/ping':
            start_response('200 OK', [('Content-Type', 'text/html')])
            return ["OK"]
        elif path_info == '/hide.js':
            id = params.get('id', 'editorkicker-hide');
            id = re.sub(r'[^-\w]', '', id)
            js = "document.getElementById('%s').style.display='none';" % id
            start_response('200 OK', [('Content-Type', 'text/javascript')])
            return [js]
        elif path_info == '/open':
            file = params.get('file')
            line = params.get('line')
            line = line and line.isdigit() and int(line) or 1
            if not file:
                status = '422 Unprocessable Entity'
                text   = "ERROR: file is not specified."
                environ.get('wsgi.errors').write(text)
            elif not os.path.isfile(file):
                status = '404 Not Found'
                text   = "ERROR: file '%s' not found.\n" % file
                environ.get('wsgi.errors').write(text)
            else:
                command = EDITOR_KICKER % (line, file)
                report(command)
                os.system(command)
                status = '200 OK'
                text   = 'OK'
            start_response(status, [('Content-Type', 'text/plain')])
            return [text]
        elif path_info != '/open':
            start_response('404 Not Found', [('Content-Type', 'text/plain')])
            return ['ERROR: %s: not found.' % path_info]
    ## supress http request log message
    def do_nothing(*args): pass
    import BaseHTTPServer
    BaseHTTPServer.BaseHTTPRequestHandler.log_request = do_nothing
    ## start server
    from wsgiref import simple_server
    server = simple_server.make_server(host, port, app)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        report('stopped')
        pass




###
### form helper
###

import sys, re

@recipe
def task_form(c, *args, **kwargs):
    """generate form classes"""
    import yaml
    for f_yaml in args:
        f_py = f_yaml.replace('.yaml', '.py')
        f = open(f_yaml)
        ydoc = yaml.load(f)
        f.close()
        #
        #form_classes = []
        visitors = [PythonFormVisitor(), PythonFormHelperVisitor()]
        buf = [
            "# -*- coding: utf-8 -*-\n"
            "import keight as k8\n"
            "\n"
        ]
        for d1 in ydoc['models']:
            for d2 in d1.pop('attrs'):
                k = 'control'
                if k in d2:
                    d2[k] = FormControlMetaClass(k, (FormControl, ), d2[k])
                klass = FormParamMetaClass('params_' + d2['name'], (FormParam, ), d2)
                d1[klass.__name__] = klass
            klass = FormMetaClass(d1.get('name'), (Form, ), d1)
            #form_classes.append(klass)
            #print klass._build()
            for visitor in visitors:
                buf.append(klass._accept(visitor))
        #
        f = open(f_py, 'wb')
        f.write(''.join(buf))
        f.close()
        print('# write %r' % f_py)
        system(c%'cat $(f_py)')

def q(s):
    if not isinstance(s, basestring):
        return repr(s)
    s = "'" + s.replace(r"'", r"\\'") + "'"
    if isinstance(s, unicode): s = s.encode('utf-8')
    return s

def qq(s):
    if not isinstance(s, basestring):
        return repr(s)
    s = '"' + s.replace(r'"', r'\\"') + '"'
    if isinstance(s, unicode): s = s.encode('utf-8')
    return s

def _type_init(cls, attrs, _count_arr=[0]):
    frame = sys._getframe(2)
    cls.__filename__ = frame.f_code.co_filename
    cls.__linenum__ = frame.f_lineno
    cls._count = _count_arr[0] = _count_arr[0] + 1
    if not attrs: return
    attrset = set(attrs)
    for k in cls.__dict__:
        if k.startswith('_'): continue
        if not k in attrset:
            raise ValueError("%s:%s: class %s: %r is unknown attribute." %
                              (cls.__filename__, cls.__linenum__, cls.__name__, k))

class FormMetaClass(type):

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)
        _type_init(cls, False)


class Form(object):
    __metaclass__  = FormMetaClass

    name = None
    prefix = ''

    @classmethod
    def _get_all_param_defs(cls):
        param_defs = []
        for k in dir(cls):
            if k.startswith('_'): continue
            v = getattr(cls, k)
            if isinstance(v, type) and issubclass(v, FormParam):
                param_defs.append(v)
        #param_defs.sort(key=lambda x: x.__linenum__)
        param_defs.sort(key=lambda x: x._count)
        return param_defs

    @classmethod
    def _accept(cls, visitor):
        return visitor.visit_form(cls)


class FormParamMetaClass(type):

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)
        _type_init(cls, 'name type ref label required length range pattern enum default control'.split(' '))


class FormParam(object):
    __metaclass__  = FormParamMetaClass

    name     = None
    type     = 'str'
    ref      = None
    label    = None
    required = False
    length   = None
    range    = None
    pattern  = None
    enum     = None
    default  = None
    control  = None

    @classmethod
    def _accept(cls, visitor):
        return visitor.visit_form_param(cls)


class FormControlMetaClass(type):

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)
        _type_init(cls, ['type', 'desc', 'attrs', 'blank'])


class FormControl(object):
    __metaclass__  = FormControlMetaClass

    type = None
    desc = None
    blank = None
    pass

    @classmethod
    def _accept(cls, visitor):
        return visitor.visit_form_control(cls)


class Visitor(object):

    def visit_form(self, cls):
        pass

    def visit_form_param(self, cls):
        pass

    def visit_form_control(self, cls):
        pass


class PythonFormVisitor(Visitor):

    def visit_form(self, cls):
        prefix = cls.prefix or ''
        param_defs = cls._get_all_param_defs()
        buf = []
        a = buf.append
        if getattr(cls, 'form'):
            prefix = cls.form.get('prefix')
        else:
            prefix = ''
        #
        #a(    "import keight as k8\n")
        #a(    "\n")
        #
        a(    "class %sForm(k8.Form):\n" % cls.__name__)
        a(    "\n")
        a(    "    def validate(self):\n")
        a(    "        self.values = {}\n")
        a(    "        self.validate_params()\n")
        a(    "        return self.errors\n")
        a(    "\n")
        #
        a(    "    def validate_params(self)\n")
        for pdef in param_defs:
            name = re.sub(r'[^\w]', '_', pdef.name)
            a("        self.valdiate__%s(%s)\n" % (name, repr(prefix + pdef.name)))
        a(    "\n")
        #
        for pdef in param_defs:
            #a(pdef._build())
            a(pdef._accept(self))
            a("\n")
        #
        return "".join(buf)

    def visit_form_param(self, cls):
        pdef = cls
        buf = []
        a = buf.append
        #
        a(    "    def validate__%s(self, k):\n" % pdef.name)
        #
        not_strip = pdef.type in ('text')
        if pdef.type in ('file'):
            a("        v = self.params.files.get(k)\n")
        elif not_strip:
            a("        v = self.params.get(k, '')\n")
        else:
            a("        v = self.params.get(k, '').strip()\n")
            a("        self.params[k] = v\n")
        #
        s = not_strip and 'v.strip()' or 'v'
        if pdef.required and pdef.type in ('file'):
            a("        if not self.chk_file_required(k, v): return False\n")
        elif pdef.required and not_strip:
            a("        if not self.chk_required(k, %s): return False\n" % s)
        elif pdef.required and not not_strip:
            a("        if not self.chk_required(k, %s): return False\n" % s)
        else:
            a("        if not v: return True\n")
        #
        if pdef.enum:
            t = tuple([ str(d['value']) for d in pdef.enum ])
            a("        if not self.chk_enum(k, v, %r): return False\n" % (t, ))
        #
        if pdef.type in ('int', 'float'):
            s = pdef.type
            a("        if not self.chk_%s_type(k, v): return False\n" % s)
            a("        v = %s(v)\n" % s)
        #
        if pdef.length and pdef.length.get('max') is not None:
            max = pdef.length.get('max')
            a("        if not self.chk_max_length(k, v, %s): return False\n" % max)
        if pdef.length and pdef.length.get('min') is not None:
            min = pdef.length.get('min')
            a("        if not self.chk_min_length(k, v, %s): return False\n" % min)
        #
        if pdef.range and pdef.range.get('max') is not None:
            max = pdef.range.get('max')
            a("        if not self.chk_max_value(k, v, %s): return False\n" % max)
        if pdef.range and pdef.range.get('min') is not None:
            min = pdef.range.get('min')
            a("        if not self.chk_min_value(k, v, %s): return False\n" % min)
        #
        if pdef.pattern:
            s = pdef.pattern
            a("        if not self.chk_pattern(k, v, %r): return False\n" % pdef.pattern)
        #
        a(    "        self.values[k] = v\n")
        a(    "        return True\n")
        #
        return ''.join(buf)


class PythonFormHelperVisitor(Visitor):

    prefix = None

    def visit_form(self, cls):
        prefix = cls.prefix or ''
        param_defs = cls._get_all_param_defs()
        buf = []
        a = buf.append
        if getattr(cls, 'form'):
            self.prefix = cls.form.get('prefix')
        else:
            self.prefix = ''
        #
        #a(    "import keight as k8\n")
        #a(    "\n")
        #
        a(    "class %sFormHelper(k8.FormHelper):\n" % cls.__name__)
        a(    "\n")
        #
        for pdef in param_defs:
            a(pdef._accept(self))
        #
        return ''.join(buf)

    def visit_form_param(self, cls):
        if cls.control is None:
            return ''
        type = getattr(cls.control, 'type', 'text')
        attrs = getattr(cls.control, 'attrs', {})
        #s = attrs and repr(k8.dict2attr(attrs)) + ', ' or ''
        s = attrs and ','.join('%s=%r' % (k, attrs[k]) for k in attrs) + ', ' or ''
        type = type == 'radio' and 'radios' or type
        name = cls.name
        label = cls.label or cls.name.title()
        desc = cls.control.desc
        buf = []
        a = buf.append
        if type in ('text', 'password'):
            a("    def %s__%s(self, label=%s, desc=%s, **kwargs):\n" % (type, name, q(label), q(desc), ))
            a("        return self.%s(%r, label, desc, %s**kwargs)\n" % (type, (self.prefix + name), s, ))
        elif type == 'textarea':
            a("    def %s__%s(self, label=%s, desc=%s, **kwargs):\n" % (type, name, q(label), q(desc), ))
            a("        return self.%s(%r, label, desc, %s**kwargs)\n" % (type, (self.prefix + name), s, ))
        elif type == 'select':
            a("    def %s__%s(self, label=%s, desc=%s, items=None, blank='-', **kwargs):\n" % (type, name, q(label), q(desc), ))
            if cls.enum:
                t = tuple([ (d['value'], d['label']) for d in cls.enum ])
            else:
                t = ()
            a("        if items is None: items = %r\n" % (t, ))
            a("        return self.%s(%r, label, desc, items=items, blank=blank, %s**kwargs)\n" % (type, (self.prefix + name), s, ))
        elif type == 'radios':
            a("    def %s__%s(self, label=%s, desc=%s, items=None, sep='', **kwargs):\n" % (type, name, label, desc, ))
            if cls.enum:
                t = tuple([ (d['value'], d['label']) for d in cls.enum ])
            else:
                t = ()
            a("        if items is None: items = %r\n" % (t, ))
            a("        return self.%s(%r, label=label, desc=desc, items=items, sep=sep, %s**kwargs)\n" % (type, (self.prefix + name), s, ))
        a("\n")
        #
        return ''.join(buf)
