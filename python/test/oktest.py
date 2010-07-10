# -*- coding: utf-8 -*-

###
### oktest.py -- new style test utility
###
### $Release: 0.4.0 $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

__all__ = ('ok', 'not_ok', 'run', 'dummy_file', 'dummy_dir', 'chdir')

import sys, os, re, types, traceback

python2 = sys.version_info[0] == 2
python3 = sys.version_info[0] == 3
if python2:
    def _is_string(val):
        return isinstance(val, (str, unicode))
    def _is_class(obj):
        return isinstance(obj, (types.TypeType, types.ClassType))
    def _func_firstlineno(func):
        return func.im_func.func_code.co_firstlineno
if python3:
    def _is_string(val):
        return isinstance(val, (str, bytes))
    def _is_class(obj):
        return isinstance(obj, (type, ))
    def _func_firstlineno(func):
        return func.__code__.co_firstlineno


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


#def deprecated(f):
#    return f


class AssertionObject(object):

    def __init__(self, value):
        self.value = value
        self._bool = True

    #def not_(self):
    #    self._bool = not self._bool
    #    return self

    def _failed(self, msg, postfix=' : failed.', depth=2):
        frame = sys._getframe(depth)
        file = frame.f_code.co_filename
        line = frame.f_lineno
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

    def __eq__(self, other):
        if (self.value == other) == self._bool:  return True
        self._failed(_msg(self.value, '==', other))

    def __ne__(self, other):
        if (self.value != other) == self._bool:  return True
        self._failed(_msg(self.value, '!=', other))

    def __gt__(self, other):
        if (self.value > other) == self._bool:  return True
        self._failed(_msg(self.value, '>', other))

    def __ge__(self, other):
        if (self.value >= other) == self._bool:  return True
        self._failed(_msg(self.value, '>=', other))

    def __lt__(self, other):
        if (self.value < other) == self._bool:  return True
        self._failed(_msg(self.value, '<', other))

    def __le__(self, other):
        if (self.value <= other) == self._bool:  return True
        self._failed(_msg(self.value, '<=', other))

    def in_delta(self, other, delta):
        if (self.value <= other - delta) == self._bool:
            self._failed(_msg(self.value, '>', other - delta))
        if (self.value >= other + delta) == self._bool:
            self._failed(_msg(self.value, '<', other + delta))
        return True

#    def __contains__(self, other):
#        if (self.value in other) == self._bool:  return True
#        self._failed(_msg(self.value, 'in', other))
    def in_(self, other):
        if (self.value in other) == self._bool:  return True
        self._failed(_msg(self.value, 'in', other))

    def not_in(self, other):  # DEPRECATED
        if (self.value not in other) == self._bool:  return True
        self._failed(_msg(self.value, 'not in', other))

    def contains(self, other):
        if (other in self.value) == self._bool:  return True
        self._failed(_msg(other, 'in', self.value))

    def not_contain(self, other):  # DEPRECATED
        if (other in self.value) == self._bool:  return True
        self._failed(_msg(other, 'not in', self.value))

    def is_(self, other):
        if (self.value is other) == self._bool:  return True
        self._failed(_msg(self.value, 'is', other))

    def is_not(self, other):
        if (self.value is not other) == self._bool:  return True
        self._failed(_msg(self.value, 'is not', other))

    def is_a(self, other):
        if (isinstance(self.value, other)) == self._bool:  return True
        self._failed("isinstance(%r, %s)" % (self.value, other.__name__))

    def is_not_a(self, other):  # DEPRECATED
        if (not isinstance(self.value, other)) == self._bool:  return True
        self._failed("not isinstance(%r, %s)" % (self.value, other.__name__))

    def matches(self, pattern):
        if isinstance(pattern, type(re.compile('x'))):
            if bool(pattern.search(self.value)) == self._bool:  return True
            self._failed("re.search(%r, %r)" % (pattern.pattern, self.value))
        else:
            if bool(re.search(pattern, self.value)) == self._bool:  return True
            self._failed("re.search(%r, %r)" % (pattern, self.value))

    def not_match(self, pattern):  # DEPRECATED
        if isinstance(pattern, type(re.compile('x'))):
            if (not pattern.search(self.value)) == self._bool:  return True
            self._failed("not re.search(%r, %r)" % (pattern.pattern, self.value))
        else:
            if (not re.search(pattern, self.value)) == self._bool:  return True
            self._failed("not re.search(%r, %r)" % (pattern, self.value))

    def is_file(self):
        if (os.path.isfile(self.value)) == self._bool:  return True
        self._failed('os.path.isfile(%r)' % self.value)

    def is_not_file(self):  # DEPRECATED
        if (not os.path.isfile(self.value)) == self._bool:  return True
        self._failed('not os.path.isfile(%r)' % self.value)

    def is_dir(self):
        if (os.path.isdir(self.value)) == self._bool:  return True
        self._failed('os.path.isdir(%r)' % self.value)

    def is_not_dir(self):  # DEPRECATED
        if (not os.path.isdir(self.value)) == self._bool:  return True
        self._failed('not os.path.isdir(%r)' % self.value)

    def exists(self):
        if (os.path.exists(self.value)) == self._bool:  return True
        self._failed('os.path.exists(%r)' % self.value)

    def not_exist(self):  # DEPRECATED
        if (not os.path.exists(self.value)) == self._bool:  return True
        self._failed('not os.path.exists(%r)' % self.value)

    def raises(self, exception_class, errmsg=None):
        return self._raise_or_not(exception_class, errmsg, self._bool)

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
                if errmsg is None or str(ex) == errmsg:
                    return
                #self._failed("expected %r but got %r" % (errmsg, ex.message))
                self._failed("%r == %r" % (str(ex), errmsg), depth=3)
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
    return ASSERTION_OBJECT(value)

def not_ok(value):
    v = ok(value)
    v._bool = False
    return v


class TestClassRunner(object):

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


TEST_CLASS_RUNNER = TestClassRunner


def run(*classes):
    class_list = []
    pat_type = type(re.compile('x'))
    vars = None
    for arg in classes:
        if _is_string(arg) or isinstance(arg, pat_type):
            pattern = isinstance(arg, pat_type) and arg or re.compile(arg)
            if vars is None: vars = sys._getframe(1).f_locals
            class_list.extend( vars[k] for k in vars if pattern.match(k) )
        elif _is_class(arg):
            klass = arg
            class_list.append(klass)
        else:
            raise Exception("%r: not a class nor pattern string." % arg)
    #
    count = 0
    for klass in class_list:
        runner = TEST_CLASS_RUNNER(klass, REPORTER())
        count += runner.run()
    return count


OUT = sys.stdout


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
            f = open(file)
            s = f.read()
            f.close()
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
        self._write("  %s\n" % (ex.args or ['(no error message)'])[0])
        if not ex.args:
            import traceback
            s = ''.join(traceback.format_exception(*sys.exc_info()))
            sys.stderr.write("\033[0;31m*** debug: s=%s\033[0m\n" % (s))
        file, line, func, text = self._get_location(ex)
        if file:
            #self._write("   %s:%s:  %s\n" % (file, line, text))
            self._write_tb(file, line, func, text)
        if getattr(ex, 'diff', None):
            self._write(ex.diff)

    def print_error(self, obj, ex):
        OUT.write('E'); OUT.flush()
        self._write("ERROR: %s()\n" % self._test_ident(obj))
        self._write("  %s: %s\n" % (ex.__class__.__name__, str(ex)))
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
        OUT.write("[NG] %s\n" % str(ex))
        file, line, func, text = self._get_location(ex)
        if file:
            OUT.write("   %s:%s: %s\n" % (file, line, text))
        if getattr(ex, 'diff', None):
            OUT.write(ex.diff)

    def print_error(self, obj, ex):
        OUT.write("[ERROR] %s: %s\n" % (ex.__class__.__name__, str(ex)))
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
        OUT.write("   #  %s\n" % ex.args[0])
        file, line, func, text = self._get_location(ex)
        if file:
            OUT.write("   #  %s:%s:  %s\n" % (file, line, text))
        if getattr(ex, 'diff', None):
            OUT.write(re.sub(self.BOL_PATTERN, '   #', ex.diff))

    def print_error(self, obj, ex):
        OUT.write("ERROR  # %s\n" % self._test_ident(obj))
        OUT.write("   #  %s: %s\n" % (ex.__class__.__name__, str(ex)))
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
## helpers
##

class _Context(object):

    def __enter__(self, *args):
        return self

    def __exit__(self, *args):
        return self

    def __call__(self, func, *args):
        self.__enter__()
        try:
            func(*args)
        finally:
            self.__exit__()


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


def dummy_file(filename, content):
    return DummyFile(filename, content)

def dummy_dir(dirname):
    return DummyDir(dirname)

def chdir(path):
    return Chdir(path)


if __name__ == '__main__':

    class MyTest(object):
        def before(self):
            self.L = [10, 20, 30]
        def test_ex1(self):
            ok (len(self.L)) == 3
            ok (sum(self.L)) == 60
        def test_ex2(self):
            ok (self.L[-1]) > 31

    run(MyTest)

    import unittest
    class MyTestCase(unittest.TestCase):
        def setUp(self):
            self.L = [10, 20, 30]
        def test_ex1(self):
            ok (len(self.L)) == 3
            ok (sum(self.L)) == 60
        def test_ex2(self):
            ok (self.L[-1]) > 31

    #unittest.main()
    run(MyTestCase)
