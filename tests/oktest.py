# -*- coding: utf-8 -*-

###
### oktest.py -- new style test utility
###
### $Release: 0.6.0 $
### $Copyright: copyright(c) 2010-2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

__all__ = ('ok', 'not_ok', 'run', 'spec',)

import sys, os, re, types, traceback

python2 = sys.version_info[0] == 2
python3 = sys.version_info[0] == 3
if python2:
    from cStringIO import StringIO
    def _is_string(val):
        return isinstance(val, (str, unicode))
    def _is_class(obj):
        return isinstance(obj, (types.TypeType, types.ClassType))
    def _is_unbound(method):
        return not method.im_self
    def _func_name(func):
        return func.func_name
    def _func_firstlineno(func):
        func = getattr(func, 'im_func', func)
        return func.func_code.co_firstlineno
    def _read_file(fname):
        f = open(fname)
        s = f.read()
        f.close()
        return s
if python3:
    from io import StringIO
    def _is_string(val):
        return isinstance(val, (str, bytes))
    def _is_class(obj):
        return isinstance(obj, (type, ))
    def _is_unbound(method):
        return not method.__self__
    def _func_name(func):
        return func.__name__
    def _func_firstlineno(func):
        return func.__code__.co_firstlineno
    def _read_file(fname, encoding='utf-8'):
        #with open(fname, encoding=encoding) as f:
        #    s = f.read()
        f = open(fname, encoding=encoding)
        s = f.read()
        f.close()
        return s

def _get_location(depth=0):
    frame = sys._getframe(depth+1)
    return (frame.f_code.co_filename, frame.f_lineno)

def _new_module(name, local_vars, helper=None):
    mod = type(sys)(name)
    sys.modules[name] = mod
    mod.__dict__.update(local_vars)
    if helper and getattr(mod, '__all__', None):
        for k in mod.__all__:
            helper.__dict__[k] = mod.__dict__[k]
        helper.__all__ += mod.__all__
    return mod


__unittest = True    # see unittest.TestResult._is_relevant_tb_level()

## not used for compatibility with unittest
#class TestFailed(AssertionError):
#
#    def __init__(self, mesg, file=None, line=None, diff=None):
#        AssertionError.__init__(self, mesg)
#        self.file = file
#        self.line = line
#        self.diff = diff
#


def ex2msg(ex):
    #return ex.message   # deprecated since Python 2.6
    #return str(ex)      # may be empty
    #return ex.args[0]   # ex.args may be empty (ex. AssertionError)
    #return (ex.args or ['(no error message)'])[0]
    return str(ex) or '(no error message)'


def _msg(target, op, other=None):
    if   op.endswith('()'):   msg = '%r%s'     % (target, op)
    elif op.startswith('.'):  msg = '%r%s(%r)' % (target, op, other)
    else:                     msg = '%r %s %r' % (target, op, other)
    if op == '==' and target != other and _is_string(target) and _is_string(other):
        if DIFF:
            if python2 or isinstance(target, str) and isinstance(other, str):
                diff = _diff(target, other)
                return (msg, diff)
    return msg


DIFF = True

def _diff(target, other):
    from difflib import unified_diff
    if hasattr(DIFF, '__call__'):
        expected = [ DIFF(line) + "\n" for line in other.splitlines(True) ]
        actual   = [ DIFF(line) + "\n" for line in target.splitlines(True) ]
    else:
        if other.find("\n") == -1 and target.find("\n") == -1:
            expected, actual = [other + "\n"], [target + "\n"]
        else:
            expected, actual = other.splitlines(True), target.splitlines(True)
            if not expected: expected.append('')
            if not actual:   actual.append('')
            for lines in (expected, actual):
                if not lines[-1].endswith("\n"):
                    lines[-1] += "\n\\ No newline at end of string\n"
    return ''.join(unified_diff(expected, actual, 'expected', 'actual', n=2))


def assertion_op(func):
    def deco(self, *args):
        self._tested = True
        return func(self, *args)
    if python2:
        deco.func_name = func.func_name
    deco.__name__ = func.__name__
    deco.__doc__ = func.__doc__
    return deco


#def deprecated(f):
#    return f


class AssertionObject(object):

    def __init__(self, value, _bool=True):
        self.value = value
        self._bool = _bool
        self._tested = False
        self._location = None

    def __del__(self):
        if self._tested is False:
            msg = "%s() is called but not tested." % (self._bool and 'ok' or 'not_ok')
            if self._location:
                msg += " (file '%s', line %s)" % self._location
            #import warnings; warnings.warn(msg)
            sys.stderr.write("*** warning: oktest: %s\n" % msg)

    #def not_(self):
    #    self._bool = not self._bool
    #    return self

    def _failed(self, msg, postfix=' : failed.', depth=2):
        file, line = _get_location(depth + 1)
        diff = None
        if isinstance(msg, tuple):
            msg, diff = msg
        if self._bool == False:
            msg = 'not ' + msg
        if postfix:
            msg += postfix
        raise self._assertion_error(msg, file, line, diff)

    def _assertion_error(self, msg, file, line, diff):
        #return TestFailed(msg, file=file, line=line, diff=diff)
        ex = AssertionError(msg)
        ex.file = file;  ex.line = line;  ex.diff = diff
        return ex

    @assertion_op
    def __eq__(self, other):
        if (self.value == other) == self._bool:  return True
        self._failed(_msg(self.value, '==', other))

    @assertion_op
    def __ne__(self, other):
        if (self.value != other) == self._bool:  return True
        self._failed(_msg(self.value, '!=', other))

    @assertion_op
    def __gt__(self, other):
        if (self.value > other) == self._bool:  return True
        self._failed(_msg(self.value, '>', other))

    @assertion_op
    def __ge__(self, other):
        if (self.value >= other) == self._bool:  return True
        self._failed(_msg(self.value, '>=', other))

    @assertion_op
    def __lt__(self, other):
        if (self.value < other) == self._bool:  return True
        self._failed(_msg(self.value, '<', other))

    @assertion_op
    def __le__(self, other):
        if (self.value <= other) == self._bool:  return True
        self._failed(_msg(self.value, '<=', other))

    @assertion_op
    def in_delta(self, other, delta):
        if (self.value <= other - delta) == self._bool:
            self._failed(_msg(self.value, '>', other - delta))
        if (self.value >= other + delta) == self._bool:
            self._failed(_msg(self.value, '<', other + delta))
        return True

#    @assertion_op
#    def __contains__(self, other):
#        if (self.value in other) == self._bool:  return True
#        self._failed(_msg(self.value, 'in', other))
    @assertion_op
    def in_(self, other):
        if (self.value in other) == self._bool:  return True
        self._failed(_msg(self.value, 'in', other))

    @assertion_op
    def not_in(self, other):  # DEPRECATED
        if (self.value not in other) == self._bool:  return True
        self._failed(_msg(self.value, 'not in', other))

    @assertion_op
    def contains(self, other):
        if (other in self.value) == self._bool:  return True
        self._failed(_msg(other, 'in', self.value))

    @assertion_op
    def not_contain(self, other):  # DEPRECATED
        if (other in self.value) == self._bool:  return True
        self._failed(_msg(other, 'not in', self.value))

    @assertion_op
    def is_(self, other):
        if (self.value is other) == self._bool:  return True
        self._failed(_msg(self.value, 'is', other))

    @assertion_op
    def is_not(self, other):
        if (self.value is not other) == self._bool:  return True
        self._failed(_msg(self.value, 'is not', other))

    @assertion_op
    def is_a(self, other):
        if (isinstance(self.value, other)) == self._bool:  return True
        self._failed("isinstance(%r, %s)" % (self.value, other.__name__))

    @assertion_op
    def is_not_a(self, other):  # DEPRECATED
        if (not isinstance(self.value, other)) == self._bool:  return True
        self._failed("not isinstance(%r, %s)" % (self.value, other.__name__))

    @assertion_op
    def hasattr(self, name):
        if hasattr(self.value, name) == self._bool:  return True
        self._failed("hasattr(%r, %r)" % (self.value, name))

    @assertion_op
    def matches(self, pattern):
        if isinstance(pattern, type(re.compile('x'))):
            if bool(pattern.search(self.value)) == self._bool:  return True
            self._failed("re.search(%r, %r)" % (pattern.pattern, self.value))
        else:
            if bool(re.search(pattern, self.value)) == self._bool:  return True
            self._failed("re.search(%r, %r)" % (pattern, self.value))

    @assertion_op
    def not_match(self, pattern):  # DEPRECATED
        if isinstance(pattern, type(re.compile('x'))):
            if (not pattern.search(self.value)) == self._bool:  return True
            self._failed("not re.search(%r, %r)" % (pattern.pattern, self.value))
        else:
            if (not re.search(pattern, self.value)) == self._bool:  return True
            self._failed("not re.search(%r, %r)" % (pattern, self.value))

    @assertion_op
    def is_file(self):
        if (os.path.isfile(self.value)) == self._bool:  return True
        self._failed('os.path.isfile(%r)' % self.value)

    @assertion_op
    def is_not_file(self):  # DEPRECATED
        if (not os.path.isfile(self.value)) == self._bool:  return True
        self._failed('not os.path.isfile(%r)' % self.value)

    @assertion_op
    def is_dir(self):
        if (os.path.isdir(self.value)) == self._bool:  return True
        self._failed('os.path.isdir(%r)' % self.value)

    @assertion_op
    def is_not_dir(self):  # DEPRECATED
        if (not os.path.isdir(self.value)) == self._bool:  return True
        self._failed('not os.path.isdir(%r)' % self.value)

    @assertion_op
    def exists(self):
        if (os.path.exists(self.value)) == self._bool:  return True
        self._failed('os.path.exists(%r)' % self.value)

    @assertion_op
    def not_exist(self):  # DEPRECATED
        if (not os.path.exists(self.value)) == self._bool:  return True
        self._failed('not os.path.exists(%r)' % self.value)

    @assertion_op
    def raises(self, exception_class, errmsg=None):
        return self._raise_or_not(exception_class, errmsg, self._bool)

    @assertion_op
    def not_raise(self, exception_class=Exception):  # DEPRECATED
        return self._raise_or_not(exception_class, None, not self._bool)

    def _raise_or_not(self, exception_class, errmsg, flag_raise):
        if flag_raise:
            try:
                self.value()
            except:
                ex = sys.exc_info()[1]
                self.value.exception = ex
                if not isinstance(ex, exception_class):
                    self._failed('%s%r is kind of %s' % (ex.__class__.__name__, ex.args, exception_class.__name__), depth=3)
                    #raise
                if errmsg is None or str(ex) == errmsg:  # don't use ex2msg(ex)!
                    return
                #self._failed("expected %r but got %r" % (errmsg, str(ex)))
                self._failed("%r == %r" % (str(ex), errmsg), depth=3)   # don't use ex2msg(ex)!
            self._failed('%s should be raised' % exception_class.__name__, depth=3)
        else:
            try:
                self.value()
            except:
                ex = sys.exc_info()[1]
                self.value.exception = ex
                if isinstance(ex, exception_class):
                    self._failed('%s should not be raised' % exception_class.__name__, depth=3)


ASSERTION_OBJECT = AssertionObject


def ok(value):
    obj = ASSERTION_OBJECT(value, True)
    obj._location = _get_location(1)
    return obj

def not_ok(value):
    obj = ASSERTION_OBJECT(value, False)
    obj._location = _get_location(1)
    return obj


class TestRunner(object):

    def __init__(self, klass, reporter=None):
        self.klass = klass
        if reporter is None:  reporter = REPORTER()
        self.reporter = reporter

    def run(self):
        klass = self.klass
        reporter = self.reporter
        ## gather test methods
        tuples = []   # pairs of method name and function
        for k in dir(klass):
            v = getattr(klass, k)
            if k.startswith('test') and hasattr(v, '__call__'):
                tuples.append((k, v))
        ## filer by $TEST environment variable
        pattern = os.environ.get('TEST')
        def _test_name(name):
            return re.sub(r'^test_?', '', name)
        if pattern:
            regexp = re.compile(pattern)
            tuples = [ t for t in tuples if regexp.search(_test_name(t[0])) ]
        ## sort by linenumber
        tuples.sort(key=lambda t: _func_firstlineno(t[1]))
        ## invoke before_all()
        reporter.before_all(klass)
        if hasattr(klass, 'before_all'):
            klass.before_all()
        ## invoke test methods
        count = 0
        for method_name, func in tuples:
            ## create instance object for each test
            try:
                obj = klass()
            except ValueError:     # unittest.TestCase raises ValueError
                obj = klass(method_name)
            obj.__name__ = _test_name(method_name)
            obj._testMethodName = method_name    # unittest.TestCase compatible
            obj._testMethodDoc = func.__doc__    # unittest.TestCase compatible
            ## invoke before() or setUp()
            reporter.before(obj)
            if   hasattr(obj, 'before'):       obj.before()
            elif hasattr(obj, 'before_each'):  obj.before_each()  # for backward compatibility
            elif hasattr(obj, 'setUp'):        obj.setUp()
            try:
                try:
                    func(obj)
                    reporter.print_ok(obj)
                #except TestFailed, ex:
                except AssertionError:
                    ex = sys.exc_info()[1]
                    count += 1
                    reporter.print_failed(obj, ex)
                except Exception:
                    ex = sys.exc_info()[1]
                    count += 1
                    reporter.print_error(obj, ex)
            finally:
                ## invoke after() or tearDown()
                if   hasattr(obj, 'after'):       obj.after()
                elif hasattr(obj, 'after_each'):  obj.after_each()  # for backward compatibility
                elif hasattr(obj, 'tearDown'):    obj.tearDown()
                reporter.after(obj)
        ## invoke after_all()
        if hasattr(klass, 'after_all'):
            klass.after_all()
        reporter.after_all(klass)
        return count


TEST_RUNNER = TestRunner


TARGET_PATTERN = '.*Test(Case)?$'

def run(*targets):
    if len(targets) == 0:
        targets = (TARGET_PATTERN, )
    target_list = []
    rexp_type = type(re.compile('x'))
    vars = None
    for arg in targets:
        if _is_class(arg):
            klass = arg
            target_list.append(klass)
        elif _is_string(arg) or isinstance(arg, rexp_type):
            rexp = _is_string(arg) and re.compile(arg) or arg
            if vars is None: vars = sys._getframe(1).f_locals
            klasses = [ vars[k] for k in vars if rexp.search(k) and _is_class(vars[k]) ]
            if TESTCLASS_SORT_KEY:
                klasses.sort(key=TESTCLASS_SORT_KEY)
            target_list.extend(klasses)
        else:
            raise Exception("%r: not a class nor pattern string." % arg)
    #
    count = 0
    for klass in target_list:
        runner = TEST_RUNNER(klass, REPORTER())
        count += runner.run()
    return count


OUT = sys.stdout


def _min_firstlineno_of_methods(klass):
    func_types = (types.FunctionType, types.MethodType)
    d = klass.__dict__
    linenos = [ _func_firstlineno(d[k]) for k in d
                if k.startswith('test') and type(d[k]) in func_types ]
    return linenos and min(linenos) or -1

TESTCLASS_SORT_KEY = _min_firstlineno_of_methods



##
## Reporter
##

class Reporter(object):

    def before_all(self, klass):
        pass

    def after_all(self, klass):
        pass

    def before(self, obj):
        pass

    def after(self, obj):
        pass

    def print_ok(self, obj):
        pass

    def print_failed(self, obj, ex):
        pass

    def print_error(self, obj, ex):
        pass


class BaseReporter(Reporter):

    def before_all(self, klass):
        self.klass = klass

    def _test_ident(self, obj):
        return '%s#%s' % (self.klass.__name__, obj._testMethodName)

    def _get_line_text(self, file, line):
        if not hasattr(self, '_lines'):
            self._lines = {}
        if file not in self._lines:
            if not os.path.isfile(file): return None
            s = _read_file(file)
            self._lines[file] = s.splitlines(True)
        return self._lines[file][line-1]

    def _get_location(self, ex):
        if hasattr(ex, 'file') and hasattr(ex, 'line'):
            text = self._get_line_text(ex.file, ex.line)
            if text: text = text.strip()
            return (ex.file, ex.line, None, text)
        else:
            tb = traceback.extract_tb(sys.exc_info()[2])
            for file, line, func, text in tb:
                if os.path.basename(file) not in ('oktest.py', 'oktest.pyc'):
                    return (file, line, func, text)
            return (None, None, None, None)

    def _write(self, str):
        OUT.write(str)

    def _write_tb(self, filename, linenum, funcname, linetext):
        if funcname:
            self._write('  File "%s", line %s, in %s\n' % (filename, linenum, funcname))
        else:
            self._write('  File "%s", line %s\n' % (filename, linenum))
        if linetext:
            self._write('    %s\n' % linetext)


## NOTICE! reporter spec will be changed frequently
class SimpleReporter(BaseReporter):

    def before_all(self, klass):
        self.klass = klass
        OUT.write("### %s\n" % klass.__name__)
        self.buf = []

    def after_all(self, klass):
        OUT.write("\n")
        OUT.write("".join(self.buf))

    def print_ok(self, obj):
        OUT.write("."); OUT.flush()

    def _write(self, str):
        self.buf.append(str)

    def print_failed(self, obj, ex):
        OUT.write("f"); OUT.flush()
        self._write("Failed: %s()\n" % self._test_ident(obj))
        self._write("  %s\n" % ex2msg(ex))
        file, line, func, text = self._get_location(ex)
        if file:
            #self._write("   %s:%s:  %s\n" % (file, line, text))
            self._write_tb(file, line, func, text)
        if getattr(ex, 'diff', None):
            self._write(ex.diff)

    def print_error(self, obj, ex):
        OUT.write('E'); OUT.flush()
        self._write("ERROR: %s()\n" % self._test_ident(obj))
        self._write("  %s: %s\n" % (ex.__class__.__name__, ex2msg(ex)))
        #traceback.print_exc(file=sys.stdout)
        tb = traceback.extract_tb(sys.exc_info()[2])
        iter = tb.__iter__()
        for filename, linenum, funcname, linetext in iter:
            if os.path.basename(filename) not in ('oktest.py', 'oktest.pyc'):
                break
        self._write_tb(filename, linenum, funcname, linetext)
        for filename, linenum, funcname, linetext in iter:
            self._write_tb(filename, linenum, funcname, linetext)
        tb = iter = None


## NOTICE! reporter spec will be changed frequently
class OldStyleReporter(BaseReporter):

    def before_all(self, klass):
        self.klass = klass

    def after_all(self, klass):
        pass

    def _test_ident(self, obj):
        return '%s.%s' % (self.klass.__name__, obj._testMethodName)

    def before(self, obj):
        OUT.write("* %s ... " % self._test_ident(obj))

    def print_ok(self, obj):
        OUT.write("[ok]\n")

    def print_failed(self, obj, ex):
        OUT.write("[NG] %s\n" % ex2msg(ex))
        file, line, func, text = self._get_location(ex)
        if file:
            OUT.write("   %s:%s: %s\n" % (file, line, text))
        if getattr(ex, 'diff', None):
            OUT.write(ex.diff)

    def print_error(self, obj, ex):
        OUT.write("[ERROR] %s: %s\n" % (ex.__class__.__name__, ex2msg(ex)))
        #traceback.print_exc(file=sys.stdout)
        tb = traceback.extract_tb(sys.exc_info()[2])
        iter = tb.__iter__()
        for filename, linenum, funcname, linetext in iter:
            if os.path.basename(filename) not in ('oktest.py', 'oktest.pyc'):
                break
        OUT.write(    "  - %s:%s:  %s\n" % (filename, linenum, linetext))
        for filename, linenum, funcname, linetext in iter:
            OUT.write("  - %s:%s:  %s\n" % (filename, linenum, linetext))
        tb = iter = None


## NOTICE! reporter spec will be changed frequently
class TapStyleReporter(BaseReporter):

    BOL_PATTERN = re.compile(r'^', re.M)

    def before_all(self, klass):
        self.klass = klass
        OUT.write("### %s\n" % klass.__name__)

    def after_all(self, klass):
        OUT.write("\n")

    def print_ok(self, obj):
        OUT.write("ok     # %s\n" % self._test_ident(obj))

    def print_failed(self, obj, ex):
        OUT.write("not ok # %s\n" % self._test_ident(obj))
        OUT.write("   #  %s\n" % ex2msg(ex))
        file, line, func, text = self._get_location(ex)
        if file:
            OUT.write("   #  %s:%s:  %s\n" % (file, line, text))
        if getattr(ex, 'diff', None):
            OUT.write(re.sub(self.BOL_PATTERN, '   #', ex.diff))

    def print_error(self, obj, ex):
        OUT.write("ERROR  # %s\n" % self._test_ident(obj))
        OUT.write("   #  %s: %s\n" % (ex.__class__.__name__, ex2msg(ex)))
        #traceback.print_exc(file=sys.stdout)
        tb = traceback.extract_tb(sys.exc_info()[2])
        iter = tb.__iter__()
        for file, line, func, text in iter:
            if os.path.basename(file) not in ('oktest.py', 'oktest.pyc'):
                break
        OUT.write(    "   #  %s:%s:  %s" % (file, line, text))
        for filename, linenum, funcname, linetext in iter:
            OUT.write("   #  %s:%s:  %s" % (file, line, text))
        tb = iter = None


REPORTER = SimpleReporter
#REPORTER = OldStyleReporter
#REPORTER = TapStyleReporter
if os.environ.get('OKTEST_REPORTER'):
    REPORTER = globals().get(os.environ.get('OKTEST_REPORTER'))
    if not REPORTER:
        raise ValueError("%s: reporter class not found." % os.environ.get('OKTEST_REPORTER'))



##
## _Context
##
class _Context(object):

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        return None

    def __call__(self, func, *args):
        self.__enter__()
        try:
            func(*args)
        finally:
            self.__exit__(sys.exc_info())



##
## spec()
##
class Spec(_Context):

    def __init__(self, desc):
        self.desc = desc

    def __iter__(self):
        self.__enter__()
        #try:
        #    yield self  # (Python2.4) SyntaxError: 'yield' not allowed in a 'try' block with a 'finally' clause
        #finally:
        #    self.__exit__(sys.exc_info())
        ex = None
        try:
            yield self
        except:
            ex = None
        self.__exit__(sys.exc_info())
        if ex:
            raise ex


def spec(desc):
    return Spec(desc)



##
## helpers
##
def _dummy():

    __all__ = ('chdir', 'using')


    class Chdir(_Context):

        def __init__(self, dirname):
            self.dirname = dirname
            self.path    = os.path.abspath(dirname)
            self.back_to = os.getcwd()

        def __enter__(self, *args):
            os.chdir(self.path)
            return self

        def __exit__(self, *args):
            os.chdir(self.back_to)


    class Using(_Context):
        """ex.
             class MyTest(object):
                pass
             with oktest.Using(MyTest):
                def test_1(self):
                  ok (1+1) == 2
             if __name__ == '__main__':
                oktest.run(MyTest)
        """
        def __init__(self, klass):
            self.klass = klass

        def __enter__(self):
            self.locals = sys._getframe(1).f_locals
            self.start_names = self.locals.keys()
            if python3: self.start_names = list(self.start_names)
            return self

        def __exit__(self, *args):
            curr_names = self.locals.keys()
            diff_names = list(set(curr_names) - set(self.start_names))
            for name in diff_names:
                setattr(self.klass, name, self.locals[name])


    def chdir(path):
        return Chdir(path)

    def using(klass):
        return Using(klass)


    def flatten(arr, type=(list, tuple)):   ## undocumented
        L = []
        for x in arr:
            if isinstance(x, type):
                L.extend(flatten(x))
            else:
                L.append(x)
        return L

    def rm_rf(*fnames):                     ## undocumented
        for fname in flatten(fnames):
            if os.path.isfile(fname):
                os.unlink(fname)
            elif os.path.isdir(fname):
                from shutil import rmtree
                rmtree(fname)


    return locals()


helper = _new_module('oktest.helper', _dummy())
del _dummy



##
## dummy
##
def _dummy():

    __all__ = ('dummy_file', 'dummy_dir', 'dummy_values', 'dummy_attrs', 'dummy_environ_vars', 'dummy_io')


    class DummyFile(_Context):

        def __init__(self, filename, content):
            self.filename = filename
            self.path     = os.path.abspath(filename)
            self.content  = content

        def __enter__(self, *args):
            f = open(self.path, 'w')
            try:
                f.write(self.content)
            finally:
                f.close()
            return self

        def __exit__(self, *args):
            os.unlink(self.path)


    class DummyDir(_Context):

        def __init__(self, dirname):
            self.dirname = dirname
            self.path    = os.path.abspath(dirname)

        def __enter__(self, *args):
            os.mkdir(self.path)
            return self

        def __exit__(self, *args):
            import shutil
            shutil.rmtree(self.path)


    class DummyValues(_Context):

        def __init__(self, dictionary, items_=None, **kwargs):
            self.dict = dictionary
            self.items = {}
            if isinstance(items_, dict):
                self.items.update(items_)
            if kwargs:
                self.items.update(kwargs)

        def __enter__(self):
            self.original = d = {}
            for k in self.items:
                if k in self.dict:
                    d[k] = self.dict[k]
            self.dict.update(self.items)
            return self

        def __exit__(self, *args):
            for k in self.items:
                if k in self.original:
                    self.dict[k] = self.original[k]
                else:
                    del self.dict[k]
            self.__dict__.clear()


    class DummyIO(_Context):

        def __init__(self, stdin_content=None):
            self.stdin_content = stdin_content

        def __enter__(self):
            self.stdout, sys.stdout = sys.stdout, StringIO()
            self.stderr, sys.stderr = sys.stderr, StringIO()
            if self.stdin_content is not None:
                self.stdin, sys.stdin  = sys.stdin, StringIO(self.stdin_content)
            return self

        def __exit__(self, *args):
            sout, serr = sys.stdout.getvalue(), sys.stderr.getvalue()
            sys.stdout, self.stdout = self.stdout, sys.stdout.getvalue()
            sys.stderr, self.stderr = self.stderr, sys.stderr.getvalue()
            if self.stdin_content is not None:
                sys.stdin = self.stdin


    def dummy_file(filename, content):
        return DummyFile(filename, content)

    def dummy_dir(dirname):
        return DummyDir(dirname)

    def dummy_values(dictionary, items_=None, **kwargs):
        return DummyValues(dictionary, items_, **kwargs)

    def dummy_attrs(object, items_=None, **kwargs):
        return DummyValues(object.__dict__, items_, **kwargs)

    def dummy_environ_vars(**kwargs):
        return DummyValues(os.environ, **kwargs)

    def dummy_io(stdin_content=None, func=None, *args, **kwargs):
        obj = dummy.DummyIO(stdin_content)
        if func is None:
            return obj    # for with-statement
        obj.__enter__()
        try:
            func(*args, **kwargs)
        finally:
            obj.__exit__()
        #return obj.stdout, obj.stderr
        return obj


    return locals()


dummy = _new_module('oktest.dummy', _dummy(), helper)
del _dummy



##
## Tracer
##
def _dummy():

    __all__ = ('Tracer', 'FakeObject')


    class Call(object):

        def __init__(self, name=None, args=None, kwargs=None, ret=None):
            self.name   = name     # method name
            self.args   = args
            self.kwargs = kwargs
            self.ret    = ret

        def __repr__(self):
            return '%s(args=%r, kwargs=%r, ret=%r)' % (self.name, self.args, self.kwargs, self.ret)

        def __iter__(self):
            yield self.name
            yield self.args
            yield self.kwargs
            yield self.ret

        def __eq__(self, other):
            if isinstance(other, list):
                return list(self) == other
            elif isinstance(other, tuple):
                return tuple(self) == other
            elif isinstance(other, self.__class__):
                return self.name == other.name and self.args == other.args \
                    and self.kwargs == other.kwargs and self.ret == other.ret
            else:
                return False


    class FakeObject(object):
        """dummy object class which can be stub or mock object.
           ex.
              from oktest.helper import FakeObject
              obj = FakeObject(hi="Hi", hello=lambda self, x: "Hello %s!" % x)
              obj.hi()           #=> 'Hi'
              obj.hello("SOS")   #=> 'Hello SOS!'
              obj._calls[0].name    #=> 'hi'
              obj._calls[0].args    #=> ()
              obj._calls[0].kwargs  #=> {}
              obj._calls[0].ret     #=> 'Hi'
              obj._calls[1].name    #=> 'hello'
              obj._calls[1].args    #=> ('SOS', )
              obj._calls[1].kwargs  #=> {}
              obj._calls[1].ret     #=> 'Hello SOS!'
        """

        def __init__(self, **kwargs):
            self._calls = self.__calls = []
            for name in kwargs:
                setattr(self, name, self.__new_method(name, kwargs[name]))

        def __new_method(self, name, val):
            fake_obj = self
            if isinstance(val, types.FunctionType):
                func = val
                def f(self, *args, **kwargs):
                    r = Call(name, args, kwargs, None)
                    fake_obj.__calls.append(r)
                    r.ret = func(self, *args, **kwargs)
                    return r.ret
            else:
                def f(self, *args, **kwargs):
                    r = Call(name, args, kwargs, val)
                    fake_obj.__calls.append(r)
                    return val
            f.func_name = f.__name__ = name
            if python2: return types.MethodType(f, self, self.__class__)
            if python3: return types.MethodType(f, self)


    class Tracer(object):
        """trace function or method call to record arguments and return value.

           ex. trace functions
               def f(x):
                   return x+1
               def g(y):
                   return f(y+1) + 1
               ## trace functions
               from oktest.helper import Tracer
               tr = Tracer()
               f = tr.trace_func(f)
               g = tr.trace_func(g)
               ## call functions
               ok (g(0))         == 3
               ## check results
               ok (tr[0].name)   == 'g'
               ok (tr[0].args)   == (0,)
               ok (tr[0].kwargs) == {}
               ok (tr[0].ret)    == 3
               ok (list(tr[0]))  == ['g', (0,), {}, 3]
               #
               ok (tr[1].name)   == 'f'
               ok (tr[1].args)   == (1,)
               ok (tr[1].kwargs) == {}
               ok (tr[1].ret)    == 2
               ok (list(tr[1]))  == ['f', (1,), {}, 2]

           ex. trace methods
               class Foo(object):
                   def m1(self, x):
                       return x + 1
                   def m2(self, y):
                       return y + 1
               obj = Foo()
               ## trace methods
               from oktest.helper import Tracer
               tr = Tracer()
               def dummy(original_func, *args, **kwargs):
                   #return original_func(*args, **kwargs)
                   return 100
               tr.fake_method(obj, m1=dummy, m2=200)
               ## call methods
               ok (obj.m1(1))    == 100
               ok (obj.m2(2))    == 200
               ## check results
               ok (tr[0].name)   == 'm1'
               ok (tr[0].args)   == (1,)
               ok (tr[0].kwargs) == {}
               ok (tr[0].ret)    == 100
               ok (list(tr[0]))  == ['m1', (1,), {}, 100]
               #
               ok (tr[1].name)   == 'm2'
               ok (tr[1].args)   == (2,)
               ok (tr[1].kwargs) == {}
               ok (tr[1].ret)    == 200
               ok (list(tr[1]))  == ['m2', (2,), {}, 200]

           ex. dummy function
               def f(x):
                   return x*2
               ## fake a function
               def dummy(original_func, x):
                   #return original_func(x)
                   return 'x=%s' % repr(x)
               from oktest.helper import Tracer
               tr = Tracer()
               f = tr.fake_func(f, dummy)
               ## call function
               f(3)             #=> 'x=3'
               ## check result
               ok (list(tr[0])) == ['f', (3,), {}, 'x=3']

           ex. dummy method
               class Foo(object):
                   def m1(self, x):
                       return x + 1
                   def m2(self, y):
                       return y + 1
               obj = Foo()
               ## fake methods
               from oktest.helper import Tracer
               tr = Tracer()
               def dummy(original_func, *args, **kwargs):
                   #return original_func(*args, **kwargs)
                   return 100
               tr.fake_method(obj, m1=dummy, m2=200)
               ## call method
               ok (obj.m1(1))    == 100
               ok (obj.m2(2))    == 200
               ## check result
               ok (list(tr[0]))  == ['m1', (1,), {}, 100]
               ok (list(tr[1]))  == ['m2', (2,), {}, 200]

           ex. dummy object
               ## create fake objects
               from oktest.helper import Tracer
               tr = Tracer()
               foo = tr.fake_obj(m1=100, m2=200)
               bar = tr.fake_obj(m3=lambda self, x: x+1)
               ## call fake method
               ok (bar.m3(0))  == 1
               ok (foo.m2())   == 200
               ok (foo.m1())   == 100
               ## check results
               ok (list(tr[0])) == ['m3', (0,), {}, 1]
               ok (list(tr[1])) == ['m2', (), {}, 200]
               ok (list(tr[2])) == ['m1', (), {}, 100]
        """

        def __init__(self):
            self.calls = []

        def __getitem__(self, index):
            return self.calls[index]

        def called(self):
            return len(self.calls) > 0

        def _attr(name):
            def f(self):
                if len(self.calls) == 0: return None
                return getattr(self.calls[0], name, None)
            return f

        name   = property(_attr('name'))
        args   = property(_attr('args'))
        kwargs = property(_attr('kwargs'))
        ret    = property(_attr('ret'))

        def __len__(self):
            return len(self.calls)

        def __iter__(self):
            return self.calls.__iter__()

        def _copy_attrs(self, func, newfunc):
            for k in ('func_name', '__name__', '__doc__'):
                if hasattr(func, k):
                    setattr(newfunc, k, getattr(func, k))

        def _wrap_func(self, func, block):
            intr = self
            def newfunc(*args, **kwargs):                # no 'self'
                call = Call(_func_name(func), args, kwargs, None)
                intr.calls.append(call)
                if block:
                    ret = block(func, *args, **kwargs)
                else:
                    ret = func(*args, **kwargs)
                #newfunc._return = ret
                call.ret = ret
                return ret
            self._copy_attrs(func, newfunc)
            return newfunc

        def _wrap_method(self, method_obj, block):
            func = method_obj
            intr = self
            def newfunc(self, *args, **kwargs):          # has 'self'
                call = Call(_func_name(func), args, kwargs, None)
                intr.calls.append(call)
                if _is_unbound(func): args = (self, ) + args   # call with 'self' if unbound method
                if block:
                    ret = block(func, *args, **kwargs)
                else:
                    ret = func(*args, **kwargs)
                call.ret = ret
                return ret
            self._copy_attrs(func, newfunc)
            if python2:  return types.MethodType(newfunc, func.im_self, func.im_class)
            if python3:  return types.MethodType(newfunc, func.__self__)

        def trace_func(self, func):
            newfunc = self._wrap_func(func, None)
            return newfunc

        def fake_func(self, func, block):
            newfunc = self._wrap_func(func, block)
            return newfunc

        def trace_method(self, obj, *method_names):
            for method_name in method_names:
                if not hasattr(obj, method_name):
                    raise ValueError("%s: no method found on %r." % (method_name, obj))
                method_obj = getattr(obj, method_name)
                setattr(obj, method_name, self._wrap_method(method_obj, None))
            return None

        def fake_method(self, obj, **kwargs):
            def _new_block(ret_val):
                def _block(*args, **kwargs):
                    return ret_val
                return _block
            for method_name in kwargs:
                #if not hasattr(obj, method_name):
                #    raise ValueError("%s: no method found on %r." % (method_name, obj))
                method_obj = getattr(obj, method_name, None)
                block = kwargs[method_name]
                if not isinstance(block, types.FunctionType):
                    block = _new_block(block)
                setattr(obj, method_name, self._wrap_method(method_obj, block))
            return None

        def trace(self, target, *args):
            if type(target) is types.FunctionType:       # function
                func = target
                return self.trace_func(func)
            else:
                obj = target
                return self.trace_method(obj, *args)

        def fake(self, target, *args, **kwargs):
            if type(target) is types.FunctionType:       # function
                func = target
                block = args and args[0] or None
                return self.fake_func(func, block)
            else:
                obj = target
                return self.fake_method(obj, **kwargs)

        def fake_obj(self, **kwargs):
            obj = FakeObject(**kwargs)
            obj._calls = obj._FakeObject__calls = self.calls
            return obj


    return locals()


tracer = _new_module('oktest.tracer', _dummy(), helper)
del _dummy
