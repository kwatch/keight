# -*- coding: utf-8 -*-

###
### oktest.py -- new style test utility
###
### $Release: 0.15.2 $
### $Copyright: copyright(c) 2010-2014 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

__all__ = ('ok', 'NOT', 'NG', 'not_ok', 'run', 'spec', 'test', 'fail',
           'skip', 'todo', 'options_of', 'at_end', 'subject', 'situation', 'main')
__version__ = "$Release: 0.15.2 $".split()[1]

import sys, os, re, types, traceback, time, linecache
from contextlib import contextmanager
import warnings
pformat = None   # on-demand import
json = None      # on-demant import

ENCODING = 'utf-8'
TERMINAL_WIDTH = 80


python2 = sys.version_info[0] == 2
python3 = sys.version_info[0] == 3
if python2:
    _unicode = unicode
    _bytes   = str
    from cStringIO import StringIO
if python3:
    xrange = range
    _unicode = str
    _bytes   = bytes
    from io import StringIO

if python2:
    def _B(val, encoding='utf-8'):
        return val.encode(encoding) if isinstance(val, unicode) else val
    def _U(val, encoding='utf-8'):
        return val.decode(encoding) if isinstance(val, str) else val
    def _S(val, encoding='utf-8'):
        return val.encode(encoding) if isinstance(val, unicode) else val
elif python3:
    def _B(val, encoding='utf-8'):
        return val.encode(encoding) if isinstance(val, str) else val
    def _U(val, encoding='utf-8'):
        return val.decode(encoding) if isinstance(val, bytes) else val
    def _S(val, encoding='utf-8'):
        return val.decode(encoding) if isinstance(val, bytes) else val


def _new_module(name, local_vars, util=None):
    mod = type(sys)(name)
    sys.modules[name] = mod
    mod.__dict__.update(local_vars)
    if util and getattr(mod, '__all__', None):
        for k in mod.__all__:
            util.__dict__[k] = mod.__dict__[k]
        util.__all__ += mod.__all__
    return mod


__unittest = True    # see unittest.TestResult._is_relevant_tb_level()


config = _new_module('oktest.config', {
    "debug": False,
    #"color_enabled": _sys.platform.startswith(('darwin', 'linux', 'freebsd', 'netbsd'))  # not work on Python2.4
    #"color_enabled": any(lambda x: _sys.platform.startswith(x), ('darwin', 'linux', 'freebsd', 'netbsd'))  # not work on Python2.4
    "color_available": bool([ 1 for p in ('darwin', 'linux', 'freebsd', 'netbsd') if sys.platform.startswith(p) ]),
    "color_enabled":  None,    # None means detect automatiallly
    "TARGET_PATTERN": '.*(Test|TestCase|_TC)$',   # class name pattern of test case
})


## not used for compatibility with unittest
#class TestFailed(AssertionError):
#
#    def __init__(self, mesg, file=None, line=None, diff=None):
#        AssertionError.__init__(self, mesg)
#        self.file = file
#        self.line = line
#        self.diff = diff
#

ASSERTION_ERROR = AssertionError


def _diff_p(target, op, other):
    if op != '==':             return False
    if target == other:        return False
    #if not util._is_string(target): return False
    #if not util._is_string(other):  return False
    if not DIFF:               return False
    is_a = isinstance
    if is_a(target, str) and is_a(other, str):
        return True
    if python2 and is_a(target, unicode) and is_a(other, unicode):
        return True
    return False


def _truncated_repr(obj, max=80+15):
    s = repr(obj)
    if len(s) > max:
        return s[:max - 15] + ' [truncated]...'
    return s


def _msg(target, op, other=None):
    if   op.endswith('()'):   msg = '%r%s'     % (target, op)
    elif op.startswith('.'):  msg = '%r%s(%r)' % (target, op, other)
    else:                     msg = '%r %s %r' % (target, op, other)
    msg += " : failed."
    return msg

def _msg2(target, op, other=None):
    diff_str = ''
    if op == '==' and target != other and _pformat_p(target, other):
        global pformat
        if not pformat: from pprint import pformat
        target_s = pformat(target, width=70)
        other_s  = pformat(other,  width=70)
        if _diff_p(target_s, op, other_s):
            diff_str = _diff(target_s, other_s)
    else:
        if _diff_p(target, op, other):
            diff_str = _diff(target, other)
    if diff_str:
        #msg = "actual %s expected : failed.\n" % (op,)
        msg = "%s == %s : failed." % (_truncated_repr(target), _truncated_repr(other))
        return (msg, diff_str)
    else:
        return _msg(target, op, other)

def _pformat_p(target, other):
    return  isinstance(target, (dict, list, tuple)) \
        and isinstance(other,  (dict, list, tuple))


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
    s = ''.join(unified_diff(expected, actual, 'expected', 'actual', n=2))
    return _tweak_diffstr(s)

# workaround to avoid bug of difflib
def _tweak_diffstr(diffstr):
    global _difflib_has_bug
    if _difflib_has_bug is None:
        _difflib_has_bug = diffstr.startswith("--- expected \n")  # extra space at end of line
    if _difflib_has_bug:
        diffstr = diffstr.replace('--- expected ', '--- expected', 1)
        diffstr = diffstr.replace('+++ actual ',   '+++ actual',   1)
    return diffstr

_difflib_has_bug = None


def assertion(func):
    """decorator to declare assertion function.
       ex.
         @oktest.assertion
         def startswith(self, arg):
           boolean = self.target.startswith(arg)
           if boolean == self.boolean:
             return self
           else:
             self.failed("%r.startswith(%r) : failed." % (self.target, arg))
         #
         ok ("Sasaki").startswith("Sas")
    """
    def deco(self, *args, **kwargs):
        self._tested = True
        return func(self, *args, **kwargs)
    deco.__name__ = func.__name__
    deco.__doc__ = func.__doc__
    setattr(AssertionObject, func.__name__, deco)
    return deco


#def deprecated(f):
#    return f


class AssertionObject(object):

    def __init__(self, target, boolean=True):
        self.target = target
        self.boolean = boolean
        self._tested = False
        self._location = None

    def __del__(self):
        if self._tested is False:
            msg = "%s() is called but not tested." % (self.boolean and 'ok' or 'not_ok')
            if self._location:
                msg += " (file '%s', line %s)" % self._location
            #import warnings; warnings.warn(msg)
            sys.stderr.write("*** warning: oktest: %s\n" % msg)

    #def not_(self):
    #    self.boolean = not self.boolean
    #    return self

    def failed(self, msg, depth=2, boolean=None):
        file, line = util.get_location(depth + 1)
        diff = None
        if isinstance(msg, tuple):
            msg, diff = msg
        if boolean is None: boolean = self.boolean
        if boolean is False:
            msg = 'not ' + msg
        raise self._assertion_error(msg, file, line, diff)

    def _assertion_error(self, msg, file, line, diff):
        #return TestFailed(msg, file=file, line=line, diff=diff)
        ex = ASSERTION_ERROR(diff and msg + "\n" + diff or msg)
        ex.file = file;  ex.line = line;  ex.diff = diff;  ex.errmsg = msg
        ex._raised_by_oktest = True
        return ex

    @property
    def should(self):           # UNDOCUMENTED
        """(experimental) allows user to call True/False method as assertion.
           ex.
             ok ("SOS").should.startswith("S")   # same as ok ("SOS".startswith("S")) == True
             ok ("123").should.isdigit()         # same as ok ("123".isdigit()) == True
        """
        return Should(self, self.boolean)

    @property
    def should_not(self):       # UNDOCUMENTED
        """(experimental) allows user to call True/False method as assertion.
           ex.
             ok ("SOS").should_not.startswith("X")   # same as ok ("SOS".startswith("X")) == False
             ok ("123").should_not.isalpha()         # same as ok ("123".isalpha()) == False
        """
        return Should(self, not self.boolean)


def _f():

    @assertion
    def __eq__(self, other):
        boolean = self.target == other
        if boolean == self.boolean:  return self
        #self.failed(_msg(self.target, '==', other))
        self.failed(_msg2(self.target, '==', other))

    @assertion
    def __ne__(self, other):
        boolean = self.target != other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '!=', other))

    @assertion
    def __gt__(self, other):
        boolean = self.target > other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '>', other))

    @assertion
    def __ge__(self, other):
        boolean = self.target >= other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '>=', other))

    @assertion
    def __lt__(self, other):
        boolean = self.target < other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '<', other))

    @assertion
    def __le__(self, other):
        boolean = self.target <= other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, '<=', other))

    @assertion
    def between(self, min, max):
        boolean = (min <= self.target <= max)
        if boolean != self.boolean:
            if self.boolean:
                s = (" (too small)" if self.target < min else
                     " (too large)" if max < self.target else '')
                self.failed("%r <= $actual <= %r: failed%s.\n"
                            "  $actual:  %r" % (min, max, s, self.target), boolean=True)
            else:
                s = ''
                self.failed("not (%r <= $actual <= %r): failed%s.\n"
                            "  $actual:  %r" % (min, max, s, self.target), boolean=True)
        return self

    @assertion
    def in_delta(self, other, delta):
        boolean = self.target > other - delta
        if boolean != self.boolean:
            self.failed(_msg(self.target, '>', other - delta))
        boolean = self.target < other + delta
        if boolean != self.boolean:
            self.failed(_msg(self.target, '<', other + delta))
        return self

#    @assertion
#    def __contains__(self, other):
#        boolean = self.target in other
#        if boolean == self.boolean:  return self
#        self.failed(_msg(self.target, 'in', other))

    @assertion
    def in_(self, other):
        boolean = self.target in other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, 'in', other))

    @assertion
    def not_in(self, other):
        boolean = self.target not in other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, 'not in', other))

    @assertion
    def contains(self, other):
        boolean = other in self.target
        if boolean == self.boolean:  return self
        self.failed(_msg(other, 'in', self.target))

    @assertion
    def not_contain(self, other):
        boolean = other not in self.target
        if boolean == self.boolean:  return self
        self.failed(_msg(other, 'not in', self.target))

    @assertion
    def is_(self, other):
        boolean = self.target is other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, 'is', other))

    @assertion
    def is_not(self, other):
        boolean = self.target is not other
        if boolean == self.boolean:  return self
        self.failed(_msg(self.target, 'is not', other))

    @assertion
    def is_a(self, other):
        boolean = isinstance(self.target, other)
        if boolean == self.boolean:  return self
        self.failed("isinstance(%r, %s) : failed." % (self.target, other.__name__))

    @assertion
    def is_not_a(self, other):
        boolean = not isinstance(self.target, other)
        if boolean == self.boolean:  return self
        self.failed("not isinstance(%r, %s) : failed." % (self.target, other.__name__))

    @assertion
    def has_attr(self, name):
        boolean = hasattr(self.target, name)
        if boolean == self.boolean:  return self
        self.failed("hasattr(%r, %r) : failed." % (self.target, name))

    @assertion
    def has_key(self, key):
        try:
            self.target[key]
        except KeyError:
            boolean = False
        else:
            boolean = True
        if boolean != self.boolean:
            if self.boolean:
                msg = ("$actual[%r]: key not exist.\n"
                       "  $actual:  %r" % (key, self.target))
            else:
                msg = ("$actual[%r]: key exists unexpectedly.\n"
                       "  $actual[%r]:  %r\n"
                       "  $actual:  %r" % (key, key, self.target[key], self.target))
            self.failed(msg, boolean=True)
        return self

    @assertion
    def has_item(self, key, val):
        try:
            actual = self.target[key]
        except KeyError:
            msg = ("$actual[%r]: key not exist.\n"
                   "  $actual:  %r" % (key, self.target))
            self.failed(msg, boolean=True)
        op = None
        if self.boolean:
            if not (actual == val):
                op = '=='
        else:
            if not (actual != val):
                op = '!='
        if op:
            msg = ("$actual[%r] %s $expected: failed.\n"
                   "  $actual[%r]:  %r\n"
                   "  $expected:  %r" % (key, op, key, actual, val))
            self.failed(msg, boolean=True)
        return self

    @assertion
    def attr(self, name, expected):
        if not hasattr(self.target, name):
            self.failed("hasattr(%r, %r) : failed." % (self.target, name), boolean=True)
        boolean = getattr(self.target, name) == expected
        if boolean == self.boolean:  return self
        prefix = 'attr(%r): ' % name
        msg = _msg2(getattr(self.target, name), "==", expected)
        if isinstance(msg, tuple):
            msg = (prefix + msg[0], msg[1])
        else:
            msg = prefix + msg
        self.failed(msg)

    @assertion
    def matches(self, pattern, flags=0):
        if isinstance(pattern, type(re.compile('x'))):
            boolean = bool(pattern.search(self.target))
            if boolean == self.boolean:  return self
            self.failed("re.search(%r, %r) : failed." % (pattern.pattern, self.target))
        else:
            rexp = re.compile(pattern, flags)
            boolean = bool(rexp.search(self.target))
            if boolean == self.boolean:  return self
            self.failed("re.search(%r, %r) : failed." % (pattern, self.target))

    @assertion
    def not_match(self, pattern, flag=0):
        if isinstance(pattern, type(re.compile('x'))):
            boolean = not pattern.search(self.target)
            if boolean == self.boolean:  return self
            self.failed("not re.search(%r, %r) : failed." % (pattern.pattern, self.target))
        else:
            rexp = re.compile(pattern, flag)
            boolean = not rexp.search(self.target)
            if boolean == self.boolean:  return self
            self.failed("not re.search(%r, %r) : failed." % (pattern, self.target))

    @assertion
    def length(self, n):
        if isinstance(n, list):
            min, max = n
            boolean = (min <= len(self.target) <= max)
            if boolean == self.boolean:  return self
            self.failed("%s <= len($actual) <= %s: failed.\n"
                        "  len($actual): %s\n"
                        "  $actual: %r" % (min, max, len(self.target), self.target))
        else:
            boolean = len(self.target) == n
            if boolean == self.boolean:  return self
            self.failed("len(%r) == %r : failed." % (self.target, n))

    @assertion
    def is_file(self):
        boolean = os.path.isfile(self.target)
        if boolean == self.boolean:  return self
        self.failed('os.path.isfile(%r) : failed.' % self.target)

    @assertion
    def not_file(self):
        boolean = not os.path.isfile(self.target)
        if boolean == self.boolean:  return self
        self.failed('not os.path.isfile(%r) : failed.' % self.target)

    @assertion
    def is_dir(self):
        boolean = os.path.isdir(self.target)
        if boolean == self.boolean:  return self
        self.failed('os.path.isdir(%r) : failed.' % self.target)

    @assertion
    def not_dir(self):
        boolean = not os.path.isdir(self.target)
        if boolean == self.boolean:  return self
        self.failed('not os.path.isdir(%r) : failed.' % self.target)

    @assertion
    def exists(self):
        boolean = os.path.exists(self.target)
        if boolean == self.boolean:  return self
        self.failed('os.path.exists(%r) : failed.' % self.target)

    @assertion
    def not_exist(self):
        boolean = not os.path.exists(self.target)
        if boolean == self.boolean:  return self
        self.failed('not os.path.exists(%r) : failed.' % self.target)

    @assertion
    def is_truthy(self):
        boolean = bool(self.target)
        if boolean == self.boolean:  return self
        self.failed('bool(%r) == True : failed.' % self.target)

    @assertion
    def is_falsy(self):
        boolean = not bool(self.target)
        if boolean == self.boolean:  return self
        self.failed('bool(%r) == False : failed.' % self.target)

    @assertion
    def all(self, func):
        if not self.boolean:
            raise TypeError("all() should be called with ok(), not NG() or NOT().")
        for i, x in enumerate(self.target):
            if not func(x):
                self.failed('$actual.all(lambda) : failed at index %s.\n'
                            '  $actual[%s]: %r' % (i, i, x))
        return self

    @assertion
    def any(self, func):
        if not self.boolean:
            raise TypeError("any() should be called with ok(), not NG() or NOT().")
        for x in self.target:
            if func(x):
                break
        else:
            self.failed('$actual.any(lambda) : failed.\n'
                        '  $actual: %r' % self.target)
        return self

    @assertion
    def raises(self, exception_class, errmsg=None):
        return self._raise_or_not(exception_class, errmsg, self.boolean)

    @assertion
    def not_raise(self, exception_class=Exception):
        return self._raise_or_not(exception_class, None, not self.boolean)

    def _raise_or_not(self, exception_class, errmsg, flag_raise):
        ex = None
        try:
            self.target()
        except:
            ex = sys.exc_info()[1]
            ## should not catch AssertionError, except it is specified as exception_class
            if isinstance(ex, AssertionError) and not hasattr(ex, '_raised_by_oktest'):
                if exception_class != AssertionError:
                    raise
            #
            self.target.exception = ex
            if flag_raise:
                if not isinstance(ex, exception_class):
                    self.failed('%s%r is kind of %s : failed.' % (ex.__class__.__name__, ex.args, exception_class.__name__), depth=3)
                    #raise
                if errmsg is None:
                    pass
                elif isinstance(errmsg, _rexp_type):
                    if not errmsg.search(str(ex)):
                        self.failed("error message %r is not matched to pattern." % str(ex), depth=3)   # don't use ex2msg(ex)!
                else:
                    if str(ex) != errmsg:   # don't use ex2msg(ex)!
                        #self.failed("expected %r but got %r" % (errmsg, str(ex)))
                        self.failed("%r == %r : failed." % (str(ex), errmsg), depth=3)   # don't use ex2msg(ex)!
            else:
                if isinstance(ex, exception_class):
                    self.failed('%s should not be raised : failed, got %r.' % (exception_class.__name__, ex), depth=3)
        else:
            if flag_raise and ex is None:
                self.failed('%s should be raised : failed.' % exception_class.__name__, depth=3)
        return self

    AssertionObject._raise_or_not = _raise_or_not
    AssertionObject.hasattr = has_attr      # for backward compatibility
    AssertionObject.is_not_file = not_file  # for backward compatibility
    AssertionObject.is_not_dir  = not_dir   # for backward compatibility

_f()
del _f

_rexp_type = type(re.compile('x'))

ASSERTION_OBJECT = AssertionObject


##
## (Undocumented) assertions for WebOb/Werkzeug/Requests response object
##
class ResponseAssertionObject(AssertionObject):
    """(experimental) AssertionObject enhancement for Response object.
    ex.
        ok (response).resp.status(200).json({"status": "OK"})
    """

    @staticmethod
    def _resp_code(resp):
        if hasattr(resp, 'status_int'):    # WebOb
            return resp.status_int
        if hasattr(resp, 'status_code'):   # Werkzeug, Requests, oktest.web.WSGIObject
            return resp.status_code
        raise UnsupportedResponseObjectError(resp, 'response status code')

    @staticmethod
    def _resp_status(resp):
        if hasattr(resp, 'status'):        # WebOb, Werkzeug, oktest.web.WSGIObject
            return resp.status
        if hasattr(resp, 'status_code') and hasattr(resp, 'reason'):  # Requests
            return "%s %s" % (resp.status_code, resp.reason)
        raise UnsupportedResponseObjectError(resp, 'response status')

    @staticmethod
    def _resp_header(resp, name):
        if hasattr(resp, 'headers'):       # WebOb, Werkzeug, Requests, oktest.web.WSGIResponse
            return resp.headers.get(name)
        raise UnsupportedResponseObjectError(resp, 'response header')

    @staticmethod
    def _resp_body(resp):
        if hasattr(resp, 'body'):          # WebOb
            return resp.body
        if hasattr(resp, 'data'):          # Werkzeug
            return resp.data
        if hasattr(resp, 'content'):       # Requests
            return resp.content
        if hasattr(resp, 'body_binary'):   # oktest.web.WSGIResponse
            return resp.body_binary
        raise UnsupportedResponseObjectError(resp, 'response binary body')

    @staticmethod
    def _resp_text(resp):
        if hasattr(resp, 'text'):          # WebOb, Requests
            return resp.text
        if hasattr(resp, 'get_data'):      # Werkzeug
            return resp.get_data(as_text=True)
        if hasattr(resp, 'body_unicode'):  # oktest.web.WSGIResponse
            return resp.body_unicode
        raise UnsupportedResponseObjectError(resp, 'response text body')

    @staticmethod
    def _resp_ctype(resp):
        if hasattr(resp, 'content_type'):  # WebOb
            return resp.content_type
        if hasattr(resp, 'mimetype'):      # Werkzeug
            return resp.mimetype
        if hasattr(resp, 'headers'):       # Requests, oktest.web.WSGIResponse
            return resp.headers['Content-Type']
        raise UnsupportedResponseObjectError(resp, 'response content type')

    @assertion
    def status(self, expected_status):
        """(experimental) Asserts status code of WebOb/Werkzeug response object."""
        response = self.target
        errmsg = None
        if isinstance(expected_status, int):         # ex. 200
            actual = self._resp_code(response)
            boolean = (actual == expected_status)
            op = '=='
        elif isinstance(expected_status, tuple):     # ex. (200, 201)
            actual = self._resp_code(response)
            boolean = (actual in expected_status)
            op = 'in'
        else:                                        # ex. '200 OK'
            actual = self._resp_status(response)
            boolean = (actual == expected_status)
            op = '=='
        if self.boolean != boolean:
            self.failed("Response status %r %s %r: failed.\n"
                        "--- response body ---\n"
                        "%s" % (actual, op, expected_status, self._resp_body(response),))
        return self

    @assertion
    def cont_type(self, str_or_regexp):
        """(experimental) Asserts content-type of WebOb/Werkzeug/Requests response object."""
        response = self.target
        cont_type = self._resp_ctype(response)
        ## when regular expression
        if isinstance(str_or_regexp, _rexp_type):
            rexp = str_or_regexp
            m = rexp.search(cont_type)
            if self.boolean != bool(m):
                self.failed("Unexpected content-type value (not matched to pattern).\n"
                            "  expected: re.compile(%r)\n"
                            "  actual:   %r" % (rexp.pattern, cont_type,))
        ## when string
        else:
            text = str_or_regexp
            if self.boolean != (cont_type == text):
                self.failed("Unexpected content-type value.\n"
                            "  expected: %r\n"
                            "  actual:   %r" % (text, cont_type,))
        ##
        return self

    @assertion
    def header(self, name, value):
        """(experimental) Asserts header of WebOb/Werkzeug/Requests response object."""
        response = self.target
        actual = self._resp_header(response, name)
        if value is None:
            if self.boolean != (actual is None):
                self.failed("Response header '%s' should not be set : failed.\n"
                            "  header value: %r" % (name, actual,))
        else:
            if self.boolean != (actual == value):
                self.failed("Response header '%s' is unexpected value.\n"
                            "  expected: %r\n"
                            "  actual:   %r" % (name, value, actual,))
        return self

    @assertion
    def body(self, str_or_regexp):
        """(experimental) Asserts response body of WebOb/Werkzeug/Requests response object."""
        response = self.target
        ## when regular expression
        if isinstance(str_or_regexp, _rexp_type):
            rexp = str_or_regexp
            actual = self._resp_text(response)
            m = rexp.search(actual)
            if self.boolean != bool(m):
                self.failed("Response body failed to match to expected pattern.\n"
                            "  expected pattern: %r\n"
                            "  response body:    %s" % (rexp.pattern, actual,))
        ## when text string
        else:
            expected = str_or_regexp
            if isinstance(expected, _unicode):
                actual = self._resp_text(response)
            else:
                actual = self._resp_body(response)
            if self.boolean != (expected == actual):
                diff_str = _diff(actual, expected)
                self.failed("Response body is different from expected data.\n"+diff_str)
        ##
        return self

    @assertion
    def json(self, expected_jdict):
        """(experimental) Asserts JSON data of WebOb/Werkzeug/Requests response object."""
        ## assert content type
        response = self.target
        content_type = self._resp_ctype(response)
        if not content_type:
            self.failed("Content-Type is not set.")
        if not self.JSON_CONTENT_TYPE_REXP.match(content_type):
            self.failed("Content-Type should be 'application/json' : failed.\n"
                        "--- content-type ---\n"
                        "%r" % (content_type,))
        ## parse response body
        global json
        if json is None: import json
        resp_text = self._resp_text(response)
        try:
            actual_jdict = json.loads(resp_text)
        except ValueError:
            self.failed("Response body should be JSON data : failed.\n"
                        "--- response body ---\n"
                        "%s" % (resp_text,))
        ## assert json jdict
        if self.boolean != (actual_jdict == expected_jdict):
            diff_str = _diff(self._json_dumps(actual_jdict), self._json_dumps(expected_jdict))
            self.failed("Responsed JSON is different from expected data.\n"+diff_str)
        ##
        return self

    def _json_dumps(self, jdict):
        global json
        if json is None: import json
        return json.dumps(jdict, ensure_ascii=False, indent=2, sort_keys=True)

    JSON_CONTENT_TYPE_REXP = re.compile(r'^application/json(; ?charset=(utf|UTF)-?8)?$')

    @assertion
    def cookie(self, name, val, domain=None, path=None, expires=None, max_age=None, secure=None, httponly=None, comment=None, version=None):
        global _SimpleCookie
        if _SimpleCookie is None:
            if python2:
                from Cookie import SimpleCookie
            elif python3:
                from http.cookies import SimpleCookie
            if sys.version >= '3.3.3':
                _SimpleCookie = SimpleCookie
            else:
                ## hack to avoid a bug in standard cookie lib (see http://bugs.python.org/issue16611)
                class _SimpleCookie(SimpleCookie):
                    def load(self, rawdata):
                        for line in re.split(r'\r?\n', rawdata):
                            keys1 = set(self.keys())
                            super(_SimpleCookie, self).load(line)
                            keys2 = set(self.keys())
                            cookie_name = list(keys2 - keys1)[0]
                            morsel = self[cookie_name]
                            for x in line.split(';'):
                                x = x.strip().lower()
                                if x == 'secure' or x == 'httponly':
                                    morsel[x] = True
        #
        response = self.target
        cookie_str = self._resp_header(response, 'Set-Cookie')
        if not cookie_str:
            self.failed("'Set-Cookie' header is empty or not provided in response.")
        cookie_str = _S(cookie_str)        # Werkzeug returns unicode object!!!
        #
        c = _SimpleCookie(cookie_str)
        if not c[name]:
            self.failed("Cookie %r is not set.\n"
                        "  Set-Cookie: %s" % (name, cookie_str))
        #
        actual = c[name].value
        expected = val
        if isinstance(expected, _rexp_type):
            if not expected.search(actual):
                self.failed("Cookie %r: $expected.search($actual): failed.\n"
                            "  $expected: %s\n"
                            "  $actual:   %r" % (name, util.repr_rexp(expected), actual))
        else:
            if actual != expected:
                self.failed("Cookie %r: $actual == $expected: failed.\n"
                            "  $actual:   %r\n"
                            "  $expected: %r" % (name, actual, expected))
        #
        pairs = [
            ('domain',   domain),
            ('path',     path),
            ('expires',  expires),
            ('max-age',  max_age),
            ('secure',   secure),
            ('httponly', httponly),
            ('comment',  comment),
            ('version',  version),
        ]
        for attr, expected in pairs:
            if expected is None: continue
            actual = c[name][attr]
            args = None
            if isinstance(expected, _rexp_type):
                if not expected.search(actual):
                    args = (name, attr, util.repr_rexp(expected), repr(actual))
            else:
                if actual != expected:
                    args = (name, attr, repr(expected), repr(actual))
            if args:
                self.failed("Cookie %r: unexpected %s.\n"
                            "  expected:  %s\n"
                            "  actual:    %s" % args)
        #
        return self

_SimpleCookie = None      # lazy import

del AssertionObject.status
del AssertionObject.cont_type
del AssertionObject.header
del AssertionObject.body
del AssertionObject.json

class UnsupportedResponseObjectError(Exception):
    def __init__(self, response, item):
        msg = "%r: failed to get %s; %r is unsupported response class in oktest." % \
              (response, item, type(response))
        Exception.__init__(self, msg)

def _resp(self):
    """(experimental) Change assertion object class.
    ex:
       ok (value)         #=> AssertionObject
       ok (value)._resp   #=> ResponseAssertionObject
    """
    self.__class__ = ResponseAssertionObject
    return self

AssertionObject._resp = property(_resp)
del _resp

def is_response(self, status=None, content_type=None):
    """(experimental) Assert response status.
    ex:
       ok (response).is_response(200)
       ok (response).is_response((200, 201))
       ok (response).is_response('200 OK')
       ok (response).is_response(200, 'image/jpeg')
       ok (response).is_response(200, re.compile('^image/(jpeg|png|gif)$')
       #
       ok (response).is_response(302).header("Location", "/")
       ok (response).is_response(200).json({"status": "OK"})
       ok (response).is_response(200).body("<h1>Hello</h1>")
       ok (response).is_response(200).body(re.compile("<h1>.*?</h1>"))

    Notice that is_response() changes __class__ attribute.
    ex:
       ok (response).__class__       #=> AssertionObject
       ok (response).is_response()   #=> ResponseAssertionObject
    """
    if self.boolean != True:
        self._tested = True   # supress warning
        raise TypeError("is_response(): not available with NOT() nor NG().")
    self.__class__ = ResponseAssertionObject
    if status is not None:
        self.status(status)
    if content_type is not None:
        self.cont_type(content_type)
    return self

AssertionObject.is_response = is_response
del is_response


##
##
##

def ok(target):
    obj = ASSERTION_OBJECT(target, True)
    obj._location = util.get_location(1)
    return obj

def NG(target):
    obj = ASSERTION_OBJECT(target, False)
    obj._location = util.get_location(1)
    return obj

def not_ok(target):  # for backward compatibility
    obj = ASSERTION_OBJECT(target, False)
    obj._location = util.get_location(1)
    return obj

def NOT(target):     # experimental. prefer to NG()?
    obj = ASSERTION_OBJECT(target, False)
    obj._location = util.get_location(1)
    return obj

def fail(desc):
    raise AssertionError(desc)

def at_end(func, *args, **kwargs):
    frame = sys._getframe(1)
    self_var = frame.f_code.co_varnames[0]  # 'self'
    if self_var != 'self':
        raise RuntimeError("'self' is expected as first argument.")
    self_obj = frame.f_locals.get(self_var)  # self
    attr_name = '_at_end_blocks'  # not '_cleanups'!
    self_obj.__dict__.setdefault(attr_name, []).append((func, args, kwargs))
    return func


class Should(object):

    def __init__(self, assertion_object, boolean=None):
        self.assertion_object = assertion_object
        if boolean is None:
            boolean = assertion_object.boolean
        self.boolean = boolean

    def __getattr__(self, key):
        ass = self.assertion_object
        tested = ass._tested
        ass._tested = True
        val = getattr(ass.target, key)
        if not hasattr(val, '__call__'):
            msg = "%s.%s: not a callable." % (type(ass.target).__name__, key)
            raise ValueError(msg)   # or TypeError?
        ass._tested = tested
        def f(*args, **kwargs):
            ass._tested = True
            ret = val(*args, **kwargs)
            if ret not in (True, False):
                msg = "%r.%s(): expected to return True or False but it returned %r." \
                      % (ass.target, val.__name__, ret)
                raise ValueError(msg)
            if ret != self.boolean:
                buf = [ repr(arg) for arg in args ]
                buf.extend([ "%s=%r" % (k, kwargs[k]) for k in kwargs ])
                msg = "%r.%s(%s) : failed." % (ass.target, val.__name__, ", ".join(buf))
                if self.boolean is False:
                    msg = "not " + msg
                ass.failed(msg)
            return self
        return f


class SkipTest(Exception):
    pass

try:
    from unittest import SkipTest
except ImportError:
    if python2:
        sys.exc_clear()


class SkipObject(object):

    def __call__(self, reason):
        raise SkipTest(reason)

    def when(self, condition, reason):
        if condition:
            def deco(func):
                def fn(self):
                    raise SkipTest(reason)
                fn.__name__ = func.__name__
                fn.__doc__  = func.__doc__
                fn._firstlineno = util._func_firstlineno(func)
                return fn
        else:
            def deco(func):
                return func
        return deco

    #def unless(self, condition, reason):
    #    if not condition:
    #        raise SkipException(reason)

skip = SkipObject()


def todo(func):
    def deco(*args, **kwargs):
        exc_info = None
        try:
            func(*args, **kwargs)
            raise _UnexpectedSuccess("test should be failed (because not implemented yet), but passed unexpectedly.")
        except AssertionError:
            raise _ExpectedFailure(sys.exc_info())
    deco.__name__ = func.__name__
    deco.__doc__  = func.__doc__
    deco._original_function = func
    return deco

class _ExpectedFailure(Exception):

    def __init__(self, exc_info=None):
        Exception.__init__(self, "expected failure")
        if exc_info:
            self.exc_info = exc_info

class _UnexpectedSuccess(Exception):
    pass

try:
    from unittest.case import _ExpectedFailure, _UnexpectedSuccess
except ImportError:
    if python2:
        sys.exc_clear()


def options_of(self):
    """returns user-defined options of current test case.
    ex.
        class FooTestCase(unittest.TestCase):
            def setUp(self):
                print(repr(options_of(self)))   #=> {'tag': 'exp', 'num': 123}

            @test("example", tag='exp', num=123)
            def _(self):
                print(repr(options_of(self)))   #=> {'tag': 'exp', 'num': 123}
    """
    if not hasattr(self, '_testMethodName'):
        raise TypeError("options_of(): argument should be a test case, but got:%r" % (self,))
    fn = self.__class__.__dict__[self._testMethodName]
    return getattr(fn, '_options')



ST_PASSED  = "pass"
ST_FAILED  = "fail"
ST_ERROR   = "error"
ST_SKIPPED = "skip"
ST_TODO    = "todo"
#ST_UNEXPECTED = "unexpected"


class TestRunner(object):

    _filter_test = _filter_key = _filter_val = None

    def __init__(self, reporter=None, filter=None):
        self._reporter = reporter
        self.filter = filter
        filter = filter and filter.copy() or {}
        if filter:
            self._filter_test = filter.pop('test', None)
        if filter:
            self._filter_key  = list(filter.keys())[0]
            self._filter_val  = filter.pop(self._filter_key)

    def __get_reporter(self):
        if self._reporter is None:
            self._reporter = REPORTER()
        return self._reporter

    def __set_reporter(self, reporter):
        self._reporter = reporter

    reporter = property(__get_reporter, __set_reporter)

    def _test_name(self, name):
        return re.sub(r'^test_?', '', name)

    def get_testnames(self, klass):
        #names = [ name for name in dir(klass) if name.startswith('test') ]
        #names.sort()
        #return names
        testnames = [ k for k in dir(klass) if k.startswith('test') and hasattr(getattr(klass, k), '__class__') ]
        ## filter by test name or user-defined options
        pattern, key, val = self._filter_test, self._filter_key, self._filter_val
        if pattern or key:
            testnames = [ s for s in testnames
                              if _filtered(klass, getattr(klass, s), s, pattern, key, val) ]
        ## filter by $TEST environment variable
        pattern = os.environ.get('TEST')
        if pattern:
            rexp  = re.compile(pattern)
            testnames = [ s for s in testnames
                              if rexp.search(self._test_name(s)) ]
        ## sort by linenumber
        def fn(testname, klass=klass):
            func = getattr(klass, testname)
            lineno = getattr(func, '_firstlineno', None) or util._func_firstlineno(func)
            return (lineno, testname)
        testnames.sort(key=fn)
        return testnames

    def _invoke(self, obj, method1, method2):
        meth = getattr(obj, method1, None) or getattr(obj, method2, None)
        if not meth: return None, None
        try:
            meth()
            return meth, None
        except KeyboardInterrupt:
            raise
        except Exception:
            return meth.__name__, sys.exc_info()

    def run_class(self, klass, testnames=None):
        self._enter_testclass(klass)
        try:
            method_name, exc_info = self._invoke(klass, 'before_all', 'setUpClass')
            if not exc_info:
                try:
                    self.run_testcases(klass, testnames)
                finally:
                    method_name, exc_info = self._invoke(klass, 'after_all', 'tearDownClass')
        finally:
            if not exc_info: method_name = None
            self._exit_testclass(klass, method_name, exc_info)

    def run_testcases(self, klass, testnames=None):
        if testnames is None:
            testnames = self.get_testnames(klass)
        context_list = getattr(klass, '_context_list', None)
        if context_list:
            items = []
            for tname in testnames:
                meth = getattr(klass, tname)
                if not hasattr(meth, '_test_context'):
                    items.append((tname, meth))
            items.extend(context_list)
            TestContext._sort_items(items)
            allowed = dict.fromkeys(testnames)
            self._run_items(klass, items, allowed)
        else:
            for testname in testnames:
                testcase = self._new_testcase(klass, testname)
                self.run_testcase(testcase, testname)

    def _run_items(self, klass, items, allowed):
        for item in items:
            if isinstance(item, tuple):
                testname = item[0]
                if testname in allowed:
                    testcase = self._new_testcase(klass, testname)
                    self.run_testcase(testcase, testname)
            else:
                assert isinstance(item, TestContext)
                context = item
                self._enter_testcontext(context)
                try:
                    self._run_items(klass, context.items, allowed)
                finally:
                    self._exit_testcontext(context)

    def _new_testcase(self, klass, method_name):
        try:
            obj = klass()
        except ValueError:     # unittest.TestCase raises ValueError
            obj = klass(method_name)
        meth = getattr(obj, method_name)
        obj.__name__ = self._test_name(method_name)
        obj._testMethodName = method_name    # unittest.TestCase compatible
        obj._testMethodDoc  = meth.__doc__   # unittest.TestCase compatible
        obj._run_by_oktest  = True
        obj._oktest_specs   = []
        return obj

    def run_testcase(self, testcase, testname):
        self._enter_testcase(testcase, testname)
        status = exc_info = None
        exc_info_list = []
        try:
            _, exc_info_ = self._invoke(testcase, 'before', 'setUp')
            if exc_info_:
                exc_info_list.append(exc_info_)
            else:
                try:
                    status, exc_info = self._run_testcase(testcase, testname)
                finally:
                    if hasattr(testcase, '_at_end_blocks'):
                        errs = self._run_blocks(testcase._at_end_blocks[::-1])
                        if errs:
                            exc_info_list.extend(errs)
                    _, exc_info_ = self._invoke(testcase, 'after', 'tearDown')
                    if exc_info_:
                        exc_info_list.append(exc_info_)
                    #else:
                        #assert status is not None
                    if hasattr(testcase, '_cleanups'):
                        errs = self._run_blocks(testcase._cleanups[::-1])
                        if errs:
                            exc_info_list.extend(errs)
        finally:
            if exc_info_list:    # errors in setUp or tearDown
                if status == ST_FAILED or status == ST_ERROR:
                    exc_info_list.insert(0, exc_info)
                else:
                    status = ST_ERROR
                self._exit_testcase(testcase, testname, status, exc_info_list)
            else:
                self._exit_testcase(testcase, testname, status, exc_info)

    def _run_testcase(self, testcase, testname):
        try:
            meth = getattr(testcase, testname)
            meth()
        except KeyboardInterrupt:
            raise
        except AssertionError:
            return ST_FAILED, sys.exc_info()
        except SkipTest:
            return ST_SKIPPED, sys.exc_info()
        except _ExpectedFailure:   # when failed expectedly
            return ST_TODO, ()
        except _UnexpectedSuccess: # when passed unexpectedly
            #return ST_UNEXPECTED, ()
            ex = sys.exc_info()[1]
            if not ex.args:
                ex.args = ("test should be failed (because not implemented yet), but passed unexpectedly.",)
            return ST_FAILED, sys.exc_info()
        except Exception:
            return ST_ERROR, sys.exc_info()
        else:
            specs = getattr(testcase, '_oktest_specs', None)
            arr = specs and [ spec for spec in specs if spec._exception ]
            if arr: return ST_FAILED, arr
            return ST_PASSED, ()

    def _run_blocks(self, blocks):
        errors = []
        for func, args, kwargs in blocks:
            try:
                func(*args, **kwargs)
            except:
                errors.append(sys.exc_info())
        return errors

    def _enter_testclass(self, testclass):
        self.reporter.enter_testclass(testclass)

    def _exit_testclass(self, testclass, method_name, exc_info):
        self.reporter.exit_testclass(testclass, method_name, exc_info)

    def _enter_testcase(self, testcase, testname):
        self.reporter.enter_testcase(testcase, testname)

    def _exit_testcase(self, testcase, testname, status, exc_info):
        self.reporter.exit_testcase(testcase, testname, status, exc_info)

    def _enter_testcontext(self, context):
        self.reporter.enter_testcontext(context)

    def _exit_testcontext(self, context):
        self.reporter.exit_testcontext(context)

    def __enter__(self):
        self.reporter.enter_all()
        return self

    def __exit__(self, *args):
        self.reporter.exit_all()


def _filtered(klass, meth, tname, pattern, key, val, _rexp=re.compile(r'^test(_|_\d\d\d(_|: ))?')):
    from fnmatch import fnmatch
    if pattern:
        if not fnmatch(_rexp.sub('', tname), pattern):
            return False   # skip testcase
    if key:
        if not meth: meth = getattr(klass, tname)
        d = getattr(meth, '_options', None)
        if not (d and isinstance(d, dict) and fnmatch(str(d.get(key)), val)):
            return False   # skip testcase
    return True   # invoke testcase


TEST_RUNNER = TestRunner


def run(*targets, **kwargs):
    out    = kwargs.pop('out', None)
    color  = kwargs.pop('color', None)
    filter = kwargs.pop('filter', {})
    style  = kwargs.pop('style', None)
    klass  = kwargs.pop('reporter_class', None)
    #
    if not klass:
        if style:
            klass = BaseReporter.get_registered_class(style)
            if not klass:
                raise ValueError("%r: unknown report style." % style)
        else:
            klass = REPORTER
    #
    reporter = klass(out=out, color=color)
    runner = TEST_RUNNER(reporter=reporter, filter=filter)
    #
    if len(targets) == 0:
        targets = (config.TARGET_PATTERN, )
    #
    runner.__enter__()
    try:
        for klass in _target_classes(targets):
            runner.run_class(klass)
    finally:
        runner.__exit__(sys.exc_info())
    counts = runner.reporter.counts
    get = counts.get
    #return get(ST_FAILED, 0) + get(ST_ERROR, 0) + get(ST_UNEXPECTED, 0)
    return get(ST_FAILED, 0) + get(ST_ERROR, 0)


def _target_classes(targets):
    target_classes = []
    rexp_type = type(re.compile('x'))
    vars = None
    for arg in targets:
        if util._is_class(arg):
            klass = arg
            target_classes.append(klass)
        elif util._is_string(arg) or isinstance(arg, rexp_type):
            rexp = util._is_string(arg) and re.compile(arg) or arg
            if vars is None: vars = sys._getframe(2).f_locals
            klasses = [ vars[k] for k in vars if rexp.search(k) and util._is_class(vars[k]) ]
            if TESTCLASS_SORT_KEY:
                klasses.sort(key=TESTCLASS_SORT_KEY)
            target_classes.extend(klasses)
        else:
            raise ValueError("%r: not a class nor pattern string." % (arg, ))
    return target_classes


def _min_firstlineno_of_methods(klass):
    func_types = (types.FunctionType, types.MethodType)
    d = klass.__dict__
    linenos = [ util._func_firstlineno(d[k]) for k in d
                if k.startswith('test') and type(d[k]) in func_types ]
    return linenos and min(linenos) or -1

TESTCLASS_SORT_KEY = _min_firstlineno_of_methods


##
## Reporter
##

class Reporter(object):

    def enter_all(self): pass
    def exit_all(self):  pass
    def enter_testclass(self, testclass): pass
    def exit_testclass (self, testclass, method_name, exc_info): pass
    def enter_testcase (self, testcase, testname): pass
    def exit_testcase  (self, testcase, testname, status, exc_info): pass
    def enter_testcontext (self, context): pass
    def exit_testcontext  (self, context): pass


class BaseReporter(Reporter):

    INDICATOR = {
        ST_PASSED:  "pass",          # or "ok" ?
        ST_FAILED:  "Fail",
        ST_ERROR:   "ERROR",
        ST_SKIPPED: "skip",
        ST_TODO:    "TODO",
        #ST_UNEXPECTED: "Unexpected",
    }

    separator =  "-" * 70

    def __init__(self, out=None, color=None):
        self._color = color
        self.out = out
        self.counts = {}
        self._context_stack = []

    def _set_color(self, color=None):
        if color is not None:
            self._color = color
        elif config.color_enabled is not None:
            self._color = config.color_enabled
        elif not config.color_available:
            self._color = False
        else:
            self._color = is_tty(self._out)

    def __get_out(self):
        if not self._out:
            self.out = sys.stdout
        return self._out

    def __set_out(self, out):
        self._out = out
        if out is not None and self._color is None:
            self._set_color(None)

    def write(self, string):
        try:
            self.out.write(string)
        except UnicodeDecodeError:
            if isinstance(string, _bytes):
                self.out.write(string.decode('utf-8'))
            else:
                raise
        except UnicodeEncodeError:
            if isinstance(string, _unicode):
                self.out.write(string.encode('utf-8'))
            else:
                raise

    out = property(__get_out, __set_out)

    def clear_counts(self):
        self.counts = {
            ST_PASSED:     0,
            ST_FAILED:     0,
            ST_ERROR:      0,
            ST_SKIPPED:    0,
            ST_TODO:       0,
            #ST_UNEXPECTED: 0,
        }

    _counts2str_table = [
        (ST_PASSED,     "pass",       True),
        (ST_FAILED,     "fail",       True),
        (ST_ERROR,      "error",      True),
        (ST_SKIPPED,    "skip",       True),
        (ST_TODO,       "todo",       True),
        #(ST_UNEXPECTED, "unexpected", False),
    ]

    def counts2str(self):
        buf = [None]; add = buf.append
        total = 0
        for status, word, required in self._counts2str_table:
            n = self.counts.get(status, 0)
            s = "%s:%s" % (word, n)
            if n: s = self.colorize(s, status)
            if required or n:
                add(s)
            total += n
        buf[0] = "total:%s" % total
        return ", ".join(buf)

    def enter_all(self):
        self.clear_counts()
        self._start_time = time.time()

    def exit_all(self):
        dt = time.time() - self._start_time
        min = int(int(dt) / 60)     # int / int is float on Python3
        sec = dt - (min * 60)
        elapsed = min and "%s:%06.3f" % (min, sec) or "%.3f" % sec
        self.write("## %s  (%s sec)\n" % (self.counts2str(), elapsed))
        self.out.flush()

    def enter_testclass(self, testclass):
        self._exceptions = []

    def exit_testclass(self, testclass, method_name, exc_info):
        for tupl in self._exceptions:
            self.report_exceptions(*tupl)
        if exc_info:
            self.report_exception(testclass, method_name, ST_ERROR, exc_info, None)
        if self._exceptions or exc_info:
            self.write_separator()
        self.out.flush()

    def enter_testcase(self, testcase, testname):
        pass

    def exit_testcase(self, testcase, testname, status, exc_info):
        self.counts[status] = self.counts.setdefault(status, 0) + 1
        #if exc_info and status != ST_SKIPPED:
        #    context = self._context_stack and self._context_stack[-1] or None
        #    self._exceptions.append((testcase, testname, status, exc_info, context))
        if exc_info:
            def ignore_p(t):
                return isinstance(t, tuple) and t[0] == SkipTest
            context = self._context_stack and self._context_stack[-1] or None
            if isinstance(exc_info, list):
                exc_info_list = [ t for t in exc_info if not ignore_p(t) ]
                self._exceptions.append((testcase, testname, status, exc_info_list, context))
            elif not ignore_p(exc_info):
                self._exceptions.append((testcase, testname, status, exc_info, context))

    def enter_testcontext(self, context):
        self._context_stack.append(context)

    def exit_testcontext(self, context):
        popped = self._context_stack.pop()
        assert popped is context

    def indicator(self, status):
        indicator = self.INDICATOR.get(status) or '???'
        if self._color:
            indicator = self.colorize(indicator, status)
        return indicator

    def get_testclass_name(self, testclass):
        subject = testclass.__dict__.get('SUBJECT') or testclass
        return getattr(subject, '__name__', None) or str(subject)

    def get_testcase_desc(self, testcase, testname):
        meth = getattr(testcase, testname)
        return meth and meth.__doc__ and meth.__doc__ or testname

    def report_exceptions(self, testcase, testname, status, exc_info_list, context):
        if not isinstance(exc_info_list, list):
            exc_info = exc_info_list
            self.report_exception(testcase, testname, status, exc_info, context)
        elif isinstance(exc_info_list[0], Spec):
            specs = exc_info_list
            for spec in specs:
                self.report_spec_esception(testcase, testname, status, spec, context)
        else:
            for exc_info in exc_info_list:
                self.report_exception(testcase, testname, status, exc_info, context)

    def report_exception(self, testcase, testname, status, exc_info, context):
        self.report_exception_header(testcase, testname, status, exc_info, context)
        self.report_exception_body  (testcase, testname, status, exc_info, context)
        self.report_exception_footer(testcase, testname, status, exc_info, context)

    def report_exception_header(self, testcase, testname, status, exc_info, context):
        if isinstance(testcase, type):
            klass, method = testcase, testname
            title = "%s > %s()" % (self.get_testclass_name(klass), method)
            desc   = None
        else:
            parent, child, desc = self._get_testcase_header_items(testcase, testname)
            items = [child]
            c = context
            while c:
                items.append(c.desc)
                c = c.parent
            items.append(parent)
            items.reverse()
            title = " > ".join(items)
        indicator = self.indicator(status)
        self.write_separator()
        self.write("[%s] %s\n" % (indicator, title))
        if desc: self.write(desc + "\n")

    def _get_testcase_header_items(self, testcase, testname):
        parent = self.get_testclass_name(testcase.__class__)
        if re.match(r'^test_\d\d\d: ', testname):
            child = testname[5:]
            desc  = None
        else:
            child = testname + '()'
            desc  = getattr(testcase, testname).__doc__
        return parent, child, desc

    def _filter(self, tb, filename, linenum, funcname):
        #return not filename.startswith(_oktest_filepath)
        return "__unittest" not in tb.tb_frame.f_globals

    def report_exception_body(self, testcase, testname, status, exc_info, context):
        assert exc_info
        ex_class, ex, ex_traceback = exc_info
        filter = not config.debug and self._filter or None
        arr = format_traceback(ex, ex_traceback, filter=filter)
        for x in arr:
            self.write(x)
        try:
            errmsg = "%s: %s" % (ex_class.__name__, ex)
        except UnicodeEncodeError:
            errmsg = unicode("%s: %s") % (ex_class.__name__, ex)
        tupl = errmsg.split("\n", 1)
        if len(tupl) == 1:
            first_line, rest = tupl[0], None
        else:
            first_line, rest = tupl
        self.write(self.colorize(first_line, status) + "\n")
        if rest:
            self.write(rest)
            if not rest.endswith("\n"): self.write("\n")
        self.out.flush()

    def report_exception_footer(self, testcase, testname, status, exc_info, context):
        pass

    def _print_temporary_str(self, string):
        if is_tty(self.out):
            #self.__string = string
            if not util._is_unicode(string):
                string = string.decode(ENCODING)
            if util.zenkaku_width(string) >= TERMINAL_WIDTH:
                shorten = util.zenkaku_shorten(string, TERMINAL_WIDTH - 4)
                #self.write(string)
                self.write(shorten + '...')
            else:
                self.write(string)
            self.out.flush()

    def _erase_temporary_str(self):
        if is_tty(self.out):
            #n = len(self.__string) + 1    # why '+1' ?
            #self.write("\b" * n)          # not work with wide-chars
            #self.out.flush()
            #del self.__string
            self.write("\r")     # or "\r\033[K"
            self.out.flush()

    def report_spec_esception(self, testcase, testname, status, spec, context):
        ex = spec._exception
        exc_info = (ex.__class__, ex, spec._traceback)
        #self.report_exception_header(testcase, testname, status, exc_info, context)
        parent, child, desc = self._get_testcase_header_items(testcase, testname)
        indicator = self.indicator(status)
        self.write_separator()
        self.write("[%s] %s > %s > %s\n" % (indicator, parent, child, spec.desc))
        if desc: self.write(desc + "\n")
        #
        stacktrace = self._filter_stacktrace(spec._stacktrace, spec._traceback)
        self._print_stacktrace(stacktrace)
        #
        self.report_exception_body(testcase, testname, status, exc_info, context)
        self.report_exception_footer(testcase, testname, status, exc_info, context)

    def _filter_stacktrace(self, stacktrace, traceback_):
        entries = traceback.extract_tb(traceback_)
        file, line, func, text = entries[0]
        i = len(stacktrace) - 1
        while i >= 0 and not (stacktrace[i][0] == file and stacktrace[i][2] == func):
            i -= 1
        bottom = i
        while i >= 0 and not _is_oktest_py(stacktrace[i][0]):
            i -= 1
        top = i + 1
        return stacktrace[top:bottom]

    def _print_stacktrace(self, stacktrace):
        for file, line, func, text in stacktrace:
            self.write('  File "%s", line %s, in %s\n' % (file, line, func))
            self.write('    %s\n' % text)

    def colorize(self, string, kind):
        if self._color is None:
            self._set_color(None)
        if not self._color:
            return string
        if kind == ST_PASSED:  return util.Color.green(string, bold=True)
        if kind == ST_FAILED:  return util.Color.red(string, bold=True)
        if kind == ST_ERROR:   return util.Color.red(string, bold=True)
        if kind == ST_SKIPPED: return util.Color.yellow(string, bold=True)
        if kind == ST_TODO:    return util.Color.yellow(string, bold=True)
        #if kind == ST_UNEXPECTED: return util.Color.red(string, bold=True)
        if kind == "topic":    return util.Color.bold(string)
        if kind == "sep":      return util.Color.red(string)
        if kind == "context":  return util.Color.bold(string)
        return util.Color.yellow(string)

    def write_separator(self):
        self.write(self.colorize(self.separator, "sep") + "\n")

    def status_char(self, status):
        if not hasattr(self, '_status_chars'):
            self._status_chars = {
                ST_PASSED : ".",
                ST_FAILED : self.colorize("f", ST_FAILED ),
                ST_ERROR  : self.colorize("E", ST_ERROR  ),
                ST_SKIPPED: self.colorize("s", ST_SKIPPED),
                ST_TODO   : self.colorize("t", ST_TODO),
                #ST_UNEXPECTED: self.colorize("u", ST_UNEXPECTED),
                None      : self.colorize("?", None),
            }
        return self._status_chars.get(status) or self._status_chars.get(None)

    _registered = {}

    @classmethod
    def register_class(cls, name, klass):
        cls._registered[name] = klass

    @classmethod
    def get_registered_class(cls, name):
        return cls._registered.get(name)


def _is_oktest_py(filepath, _dirpath=os.path.dirname(__file__)):
    #return re.search(r'oktest.py[co]?$', filepath)
    return filepath.startswith(_dirpath)


def is_tty(out):
    return hasattr(out, 'isatty') and out.isatty()


def traceback_formatter(file, line, func, linestr):
    text = linestr.strip()
    return func and '  File "%s", line %s, in %s\n    %s\n' % (file, line, func, text) \
                or  '  File "%s", line %s\n    %s\n'        % (file, line,       text)


def format_traceback(exception, traceback, filter=None, formatter=traceback_formatter):
    limit = getattr(sys, 'tracebacklimit', 200)
    if not formatter:
        formatter = lambda *args: args
    pos = -1
    if hasattr(exception, '_raised_by_oktest'):
        _file, _line = exception.file, exception.line
    else:
        _file, _line = False, -1
    tb = traceback
    arr = []; add = arr.append
    i = 0
    while tb and i < limit:
        linenum  = tb.tb_lineno
        filename = tb.tb_frame.f_code.co_filename
        funcname = tb.tb_frame.f_code.co_name
        if not filter or filter(tb, linenum, filename, funcname):
            linecache.checkcache(filename)
            linestr = linecache.getline(filename, linenum)
            add(formatter(filename, linenum, funcname, linestr))
            if linenum == _line and filename == _file:
                pos = i
            i += 1
        tb = tb.tb_next
    if pos >= 0:
        arr[pos+1:] = []
    return arr


class VerboseReporter(BaseReporter):

    _super = BaseReporter

    def __init__(self, *args, **kwargs):
        self._super.__init__(self, *args, **kwargs)
        self.depth = 1

    def enter_testclass(self, testclass):
        self._super.enter_testclass(self, testclass)
        self.write("* %s\n" % self.colorize(self.get_testclass_name(testclass), "topic"))
        self.out.flush()

    def enter_testcase(self, testcase, testname):
        desc = self.get_testcase_desc(testcase, testname)
        self._print_temporary_str("  " * self.depth + "- [    ] " + desc)

    def exit_testcase(self, testcase, testname, status, exc_info):
        s = ""
        if status == ST_SKIPPED:
            ex = exc_info[1]
            #reason = getattr(ex, 'reason', '')
            reason = ex.args[0]
            s = " (reason: %s)" % (reason, )
            exc_info = ()
        self._super.exit_testcase(self, testcase, testname, status, exc_info)
        self._erase_temporary_str()
        indicator = self.indicator(status)
        desc = self.get_testcase_desc(testcase, testname)
        self.write("  " * self.depth + "- [%s] %s%s\n" % (indicator, desc, s))
        self.out.flush()

    def enter_testcontext(self, context):
        self._super.enter_testcontext(self, context)
        s = context.desc
        if not (s.startswith("when ") or s == "else:"):
            s = self.colorize(s, "context")
        self.write("  " * self.depth + "+ %s\n" % s)
        self.depth += 1

    def exit_testcontext(self, context):
        self._super.exit_testcontext(self, context)
        self.depth -= 1

BaseReporter.register_class("verbose", VerboseReporter)


class SimpleReporter(BaseReporter):

    _super = BaseReporter

    def __init__(self, *args, **kwargs):
        self._super.__init__(self, *args, **kwargs)

    def enter_testclass(self, testclass):
        self._super.enter_testclass(self, testclass)
        self.write("* %s: " % self.colorize(self.get_testclass_name(testclass), "topic"))
        self.out.flush()

    def exit_testclass(self, *args):
        self.write("\n")
        self._super.exit_testclass(self, *args)

    def exit_testcase(self, testcase, testname, status, exc_info):
        self._super.exit_testcase(self, testcase, testname, status, exc_info)
        self.write(self.status_char(status))
        self.out.flush()

BaseReporter.register_class("simple", SimpleReporter)


class PlainReporter(BaseReporter):

    _super = BaseReporter

    def __init__(self, *args, **kwargs):
        self._super.__init__(self, *args, **kwargs)

    def exit_testclass(self, testclass, method_name, exc_info):
        if self._exceptions or exc_info:
            self.write("\n")
        self._super.exit_testclass(self, testclass, method_name, exc_info)

    def exit_testcase(self, testcase, testname, status, exc_info):
        self._super.exit_testcase(self, testcase, testname, status, exc_info)
        self.write(self.status_char(status))
        self.out.flush()

    def exit_all(self):
        self.write("\n")
        self._super.exit_all(self)

BaseReporter.register_class("plain", PlainReporter)


class UnittestStyleReporter(BaseReporter):

    _super = BaseReporter

    def __init__(self, *args, **kwargs):
        self._super.__init__(self, *args, **kwargs)
        self._color = False
        self.separator = "-" * 70

    def enter_testclass(self, testclass):
        if getattr(self, '_exceptions', None) is None:
            self._exceptions = []

    def exit_testclass(self, testclass, method_name, exc_info):
        if exc_info:
            self._exceptions.append((testclass, method_name, ST_ERROR, exc_info))

    def enter_testcase(self, *args):
        self._super.enter_testcase(self, *args)

    def exit_testcase(self, testcase, testname, status, exc_info):
        self._super.exit_testcase(self, testcase, testname, status, exc_info)
        self.write(self.status_char(status))
        self.out.flush()

    def exit_all(self):
        self.write("\n")
        for tupl in self._exceptions:
            self.report_exceptions(*tupl)
        self._super.exit_all(self)

    def report_exception_header(self, testcase, testname, status, exc_info, context):
        if isinstance(testcase, type):
            klass, method = testcase, testname
            parent = self.get_testclass_name(klass)
            child  = method
        else:
            parent = testcase.__class__.__name__
            child  = testname
        indicator = self.INDICATOR.get(status) or '???'
        self.write("=" * 70 + "\n")
        self.write("%s: %s#%s()\n" % (indicator, parent, child))
        self.write("-" * 70 + "\n")

BaseReporter.register_class("unittest", SimpleReporter)


class OldStyleReporter(BaseReporter):

    _super = BaseReporter

    def enter_all(self):
        pass

    def exit_all(self):
        pass

    def enter_class(self, testcase, testname):
        pass

    def exit_class(self, testcase, testname):
        pass

    def enter_testcase(self, testcase, testname):
        self.write("* %s.%s ... " % (testcase.__class__.__name__, testname))

    def exit_testcase(self, testcase, testname, status, exc_info):
        if status == ST_PASSED:
            self.write("[ok]\n")
        elif status == ST_FAILED:
            ex_class, ex, ex_traceback = exc_info
            flag = hasattr(ex, '_raised_by_oktest')
            self.write("[NG] %s\n" % (flag and ex.errmsg or util.ex2msg(ex)))
            def formatter(filepath, lineno, funcname, linestr):
                return "   %s:%s: %s\n" % (filepath, lineno, linestr.strip())
            arr = format_traceback(ex, ex_traceback, filter=self._filter, formatter=formatter)
            for x in arr:
                self.write(x)
            if flag and getattr(ex, 'diff', None):
                self.write(ex.diff)
        elif status == ST_ERROR:
            ex_class, ex, ex_traceback = exc_info
            self.write("[ERROR] %s: %s\n" % (ex_class.__name__, util.ex2msg(ex)))
            def formatter(filepath, lineno, funcname, linestr):
                return "  - %s:%s:  %s\n" % (filepath, lineno, linestr.strip())
            arr = format_traceback(ex, ex_traceback, filter=self._filter, formatter=formatter)
            for x in arr:
                self.write(x)
        elif status == ST_SKIPPED:
            self.write("[skip]\n")
        elif status == ST_TODO:
            self.write("[TODO]\n")
        #elif status == ST_UNEXPECTED:
        #    self.write("[Unexpected]\n")
        else:
            assert False, "UNREACHABLE: status=%r" % (status,)

BaseReporter.register_class("oldstyle", SimpleReporter)


REPORTER = VerboseReporter
#REPORTER = SimpleReporter
#REPORTER = PlainReporter
#REPORTER = OldStyleReporter
if os.environ.get('OKTEST_REPORTER'):
    REPORTER = globals().get(os.environ.get('OKTEST_REPORTER'))
    if not REPORTER:
        raise ValueError("%s: reporter class not found." % os.environ.get('OKTEST_REPORTER'))


##
## util
##
def _dummy():

    __all__ = ('chdir', 'rm_rf')

    if python2:
        _unicode = unicode
        def _is_string(val):
            return isinstance(val, (str, unicode))
        def _is_unicode(val):
            return isinstance(val, unicode)
        def _is_class(obj):
            return isinstance(obj, (types.TypeType, types.ClassType))
        def _is_unbound(method):
            return not method.im_self
        def _func_name(func):
            return func.func_name
        def _func_firstlineno(func):
            func = getattr(func, 'im_func', func)
            return func.func_code.co_firstlineno
    if python3:
        _unicode = str
        def _is_string(val):
            return isinstance(val, (str, bytes))
        def _is_unicode(val):
            return isinstance(val, str)
        def _is_class(obj):
            return isinstance(obj, (type, ))
        def _is_unbound(method):
            return not method.__self__
        def _func_name(func):
            return func.__name__
        def _func_firstlineno(func):
            return func.__code__.co_firstlineno

    ##
    ## _Context
    ##
    class Context(object):

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None


    class RunnableContext(Context):

        def run(self, func, *args, **kwargs):
            self.__enter__()
            try:
                return func(*args, **kwargs)
            finally:
                self.__exit__(*sys.exc_info())

        def deco(self, func):
            def f(*args, **kwargs):
                return self.run(func, *args, **kwargs)
            return f

        __call__ = run    # for backward compatibility


    class Chdir(RunnableContext):

        def __init__(self, dirname):
            self.dirname = dirname
            self.path    = os.path.abspath(dirname)
            self.back_to = os.getcwd()

        def __enter__(self, *args):
            os.chdir(self.path)
            return self

        def __exit__(self, *args):
            os.chdir(self.back_to)


    class Using(Context):
        """ex.
             class MyTest(object):
                pass
             with oktest.util.Using(MyTest):
                def test_1(self):
                  ok (1+1) == 2
             if __name__ == '__main__':
                oktest.run(MyTest)
        """
        def __init__(self, klass):
            self.klass = klass

        def __enter__(self):
            localvars = sys._getframe(1).f_locals
            self._start_names = localvars.keys()
            if python3: self._start_names = list(self._start_names)
            return self

        def __exit__(self, *args):
            localvars  = sys._getframe(1).f_locals
            curr_names = localvars.keys()
            diff_names = list(set(curr_names) - set(self._start_names))
            for name in diff_names:
                setattr(self.klass, name, localvars[name])


    def chdir(path, func=None):
        cd = Chdir(path)
        return func is not None and cd.run(func) or cd

    def using(klass):                       ## undocumented
        return Using(klass)


    def ex2msg(ex):
        #return ex.message   # deprecated since Python 2.6
        #return str(ex)      # may be empty
        #return ex.args[0]   # ex.args may be empty (ex. AssertionError)
        #return (ex.args or ['(no error message)'])[0]
        return str(ex) or '(no error message)'

    def flatten(arr, type=(list, tuple)):   ## undocumented
        L = []
        for x in arr:
            if isinstance(x, type):
                L.extend(flatten(x))
            else:
                L.append(x)
        return L

    def rm_rf(*fnames):
        for fname in flatten(fnames):
            if os.path.isfile(fname):
                os.unlink(fname)
            elif os.path.isdir(fname):
                from shutil import rmtree
                rmtree(fname)

    def repr_rexp(rexp):
        pattern = ("r%r" % rexp.pattern).replace(r'\\', '\\')
        flags = rexp.flags
        if python3:
            flags = flags ^ re.U
        if flags:
            arr = []
            if re.T & flags: arr.append('re.T')
            if re.I & flags: arr.append('re.I')
            if re.L & flags: arr.append('re.L')
            if re.M & flags: arr.append('re.M')
            if re.S & flags: arr.append('re.S')
            if re.U & flags: arr.append('re.U')
            if re.X & flags: arr.append('re.X')
            if python3:
                if re.A & flags: arr.append('re.A')
            return "re.compile(%s, %s)" % (pattern, '|'.join(arr))
        else:
            return "re.compile(%s)" % (pattern,)

    @contextmanager
    def from_here(dirpath=None):
        """
        Set current directory as the first element of sys.path temporarily.

        usage:
          from oktest.util import from_here
          with from_here():
            import mymodule
        """
        from os.path import dirname, abspath, isabs, realpath, join
        depth = 2   # not 1, because using @contextlib
        filepath = sys._getframe(depth).f_globals.get('__file__')
        currpath = dirname(abspath(filepath))
        if dirpath:
            if isabs(dirpath):
                currpath = dirpath
            else:
                currpath = realpath(join(currpath, dirpath))
        sys.path.insert(0, currpath)
        yield
        if sys.path and sys.path[0] == currpath:
            sys.path.pop(0)

    def randstr(n=8):
        """Returns n-width number string."""
        from random import randint
        format = '%0'+str(n)+'d'
        return format % randint(0, 10**n-1)

    def get_location(depth=0):
        frame = sys._getframe(depth+1)
        return (frame.f_code.co_filename, frame.f_lineno)

    def read_binary_file(fname):
        f = open(fname, 'rb')
        try:
            b = f.read()
        finally:
            f.close()
        return b

    if python2:
        _rexp = re.compile(r'(?:^#!.*?\r?\n)?#.*?coding:[ \t]*([-\w]+)')
        def read_text_file(fname,  _rexp=_rexp, _read_binary_file=read_binary_file):
            b = _read_binary_file(fname)
            m = _rexp.match(b)
            encoding = m and m.group(1) or 'utf-8'
            u = b.decode(encoding)
            assert isinstance(u, unicode)
            return u
    if python3:
        _rexp = re.compile(r'(?:^#!.*?\r?\n)?#.*?coding:[ \t]*([-\w]+)'.encode('us-ascii'))
        def read_text_file(fname,  _rexp=_rexp, _read_binary_file=read_binary_file):
            b = _read_binary_file(fname)
            m = _rexp.match(b)
            encoding = m and m.group(1).decode('us-ascii') or 'utf-8'
            u = b.decode(encoding)
            assert isinstance(u, str)
            return u

    import unicodedata as _unicodedata
    _CHAR_WIDTH = {'W': 2, 'F': 2, 'A': 2}

    def zenkaku_width(unicode_string,
                      _unicode=_unicode, _eaw=_unicodedata.east_asian_width, _widths=_CHAR_WIDTH):
        if not isinstance(unicode_string, _unicode):
            raise TypeError('unicode expected but got %s.' % type(unicode_string))
        return sum( _widths.get(_eaw(ch), 1) for ch in unicode_string )

    def zenkaku_shorten(unicode_string, max_width,
                      _unicode=_unicode, _eaw=_unicodedata.east_asian_width, _widths=_CHAR_WIDTH):
        if not isinstance(unicode_string, _unicode):
            raise TypeError('unicode expected but got %s.' % type(unicode_string))
        w = i = 0
        for ch in unicode_string:
            w += _widths.get(_eaw(ch), 1)   # 2 when zenkaku, 1 when hankaku
            if w > max_width:
                break
            i += 1
        else:
            return unicode_string
        return unicode_string[:i]

    from types import MethodType as _MethodType

    if python2:
        def func_argnames(func):
            if isinstance(func, _MethodType):
                codeobj = func.im_func.func_code
                index = 1
            else:
                codeobj = func.func_code
                index = 0
            return codeobj.co_varnames[index:codeobj.co_argcount]
        def func_defaults(func):
            if isinstance(func, _MethodType):
                return func.im_func.func_defaults
            else:
                return func.func_defaults
    if python3:
        def func_argnames(func):
            if isinstance(func, _MethodType):
                codeobj = func.__func__.__code__
                index = 1
            else:
                codeobj = func.__code__
                index = 0
            return codeobj.co_varnames[index:codeobj.co_argcount]
        def func_defaults(func):
            if isinstance(func, _MethodType):
                return func.__func__.__defaults__
            else:
                return func.__defaults__

    ##
    ## color
    ##
    class Color(object):

        @staticmethod
        def bold(s):
            return "\033[0;1m" + s + "\033[22m"

        @staticmethod
        def black(s, bold=False):
            return "\033[%s;30m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def red(s, bold=False):
            return "\033[%s;31m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def green(s, bold=False):
            return "\033[%s;32m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def yellow(s, bold=False):
            return "\033[%s;33m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def blue(s, bold=False):
            return "\033[%s;34m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def magenta(s, bold=False):
            return "\033[%s;35m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def cyan(s, bold=False):
            return "\033[%s;36m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def white(s, bold=False):
            return "\033[%s;37m%s\033[0m" % (bold and 1 or 0, s)

        @staticmethod
        def _colorize(s):
            s = re.sub(r'<b>(.*?)</b>', lambda m: Color.bold(m.group(1)), s)
            s = re.sub(r'<R>(.*?)</R>', lambda m: Color.red(m.group(1), bold=True), s)
            s = re.sub(r'<r>(.*?)</r>', lambda m: Color.red(m.group(1), bold=False), s)
            s = re.sub(r'<G>(.*?)</G>', lambda m: Color.green(m.group(1), bold=True), s)
            s = re.sub(r'<Y>(.*?)</Y>', lambda m: Color.yellow(m.group(1), bold=True), s)
            return s


    return locals()

util = _new_module('oktest.util', _dummy())
del _dummy

helper = util  ## 'help' is an alias of 'util' (for backward compatibility)
sys.modules['oktest.helper'] = sys.modules['oktest.util']


##
## spec()   # deprecated
##
class Spec(util.Context):   # deprecated

    _exception  = None
    _traceback  = None
    _stacktrace = None

    def __init__(self, desc):
        self.desc = desc
        self._testcase = None

    def __enter__(self):
        self._testcase = tc = self._find_testcase_object()
        if getattr(tc, '_run_by_oktest', None):
            tc._oktest_specs.append(self)
        return self

    def _find_testcase_object(self):
        max_depth = 10
        for i in xrange(2, max_depth):
            try:
                frame = sys._getframe(i)   # raises ValueError when too deep
            except ValueError:
                break
            method = frame.f_code.co_name
            if method.startswith("test"):
                arg_name = frame.f_code.co_varnames[0]
                testcase = frame.f_locals.get(arg_name, None)
                if hasattr(testcase, "_testMethodName") or hasattr(testcase, "_TestCase__testMethodName"):
                    return testcase
        return None

    def __exit__(self, *args):
        ex = args[1]
        tc = self._testcase
        if ex and hasattr(ex, '_raised_by_oktest') and hasattr(tc, '_run_by_oktest'):
            self._exception  = ex
            self._traceback  = args[2]
            self._stacktrace = traceback.extract_stack()
            return True

    def __iter__(self):
        self.__enter__()
        #try:
        #    yield self  # (Python2.4) SyntaxError: 'yield' not allowed in a 'try' block with a 'finally' clause
        #finally:
        #    self.__exit__(*sys.exc_info())
        ex = None
        try:
            yield self
        except:
            ex = None
        self.__exit__(*sys.exc_info())
        if ex:
            raise ex

    def __call__(self, func):
        self.__enter__()
        try:
            func()
        finally:
            self.__exit__(*sys.exc_info())

    def __bool__(self):       # for Pyton3
        filter = os.environ.get('SPEC')
        return not filter or (filter in self.desc)

    __nonzero__ = __bool__    # for Python2


def spec(desc):   # deprecated
    #if not os.getenv('OKTEST_WARNING_DISABLED'):
    #    import warnings
    #    warnings.warn("oktest.spec() is deprecated.", DeprecationWarning, 2)
    return Spec(desc)


##
## @test() decorator
##

def test(description_text=None, **options):
    frame = sys._getframe(1)
    localvars  = frame.f_locals
    globalvars = frame.f_globals
    n = localvars.get('__n', 0) + 1
    localvars['__n'] = n
    m = SPEC_ID_REXP.match(description_text or '')
    if m:
        options['sid'] = m.group(1)
    def deco(orig_func):
        if hasattr(orig_func, '_original_function'):
            orig_func_ = orig_func._original_function or orig_func
        else:
            orig_func_ = orig_func
        argnames = util.func_argnames(orig_func_)
        fixture_names = argnames[1:]   # except 'self'
        if fixture_names:
            def newfunc(self):
                self._options = options
                self._description = description_text
                return fixture_injector.invoke(self, orig_func, globalvars)
        else:
            def newfunc(self):
                self._options = options
                self._description = description_text
                return orig_func(self)
        orig_name = orig_func.__name__
        newfunc.__doc__  = orig_func.__doc__ or description_text
        newfunc._options = options
        newfunc._firstlineno = getattr(orig_func, '_firstlineno', None) or util._func_firstlineno(orig_func)
        if orig_name.startswith('test'):
            newfunc.__name__ = orig_name
            return newfunc
        else:
            s = "test_%03d: %s" % (n, description_text)
            if python2 and isinstance(s, unicode):
                s = s.encode('utf-8')
            newfunc.__name__ = s
            localvars[newfunc.__name__] = newfunc
            #return None  # for 'nosetests' command
            return newfunc
    return deco

test.__test__ = False    # for 'nosetests' command

SPEC_ID_REXP = re.compile(r'^\[\!([-\w]+)\]')


##
## fixture manager and injector
##

class FixtureManager(object):

    def provide(self, name):
        raise NameError("Fixture provider for '%s' not found." % (name,))

    def release(self, name, value):
        pass

fixture_manager = FixtureManager()


class FixtureInjector(object):

    def invoke(self, object, func, *opts):
        """invoke function with fixtures."""
        releasers = {"self": None}     # {"arg_name": releaser_func()}
        resolved  = {"self": object}   # {"arg_name": arg_value}
        in_progress = []
        ##
        if hasattr(func, '_original_function'):
            func_ = func._original_function or func
        else:
            func_ = func
        arg_names = util.func_argnames(func_)
        ## default arg values of test method are stored into 'resolved' dict
        ## in order for providers to access to them
        defaults = util.func_defaults(func_)
        if defaults:
            idx = - len(defaults)
            for aname, default in zip(arg_names[idx:], defaults):
                resolved[aname] = default
            arg_names = arg_names[:idx]
        ##
        def _resolve(arg_name):
            aname = arg_name
            if aname not in resolved:
                pair = self.find(aname, object, *opts)
                if pair:
                    provider, releaser = pair
                    resolved[aname] = _call(provider, aname)
                    releasers[aname] = releaser
                else:
                    resolved[aname] = fixture_manager.provide(aname)
            return resolved[aname]
        def _call(provider, resolving_arg_name):
            arg_names = util.func_argnames(provider)
            if not arg_names:
                return provider()
            in_progress.append(resolving_arg_name)
            defaults = util.func_defaults(provider)
            if not defaults:
                arg_values = [ _get_value(aname) for aname in arg_names ]
            else:
                idx  = - len(defaults)
                arg_values = [ _get_value(aname) for aname in arg_names[:idx] ]
                for aname, default in zip(arg_names[idx:], defaults):
                    arg_values.append(resolved.get(aname, default))
            in_progress.remove(resolving_arg_name)
            return provider(*arg_values)
        def _get_value(arg_name):
            if arg_name in resolved:        return resolved[arg_name]
            if arg_name not in in_progress: return _resolve(arg_name)
            raise self._looped_dependency_error(arg_name, in_progress, object)
        ##
        arguments = [ _resolve(aname) for aname in arg_names ]
        assert not in_progress
        try:
            #return func(object, *arguments)
            return func(*arguments)
        finally:
            self._release_fixtures(resolved, releasers)

    def _release_fixtures(self, resolved, releasers):
        for name in resolved:
            if name in releasers:
                releaser = releasers[name]
                if releaser:
                    names = util.func_argnames(releaser)
                    if names and names[0] == "self":
                        releaser(resolved["self"], resolved[name])
                    else:
                        releaser(resolved[name])
            else:
                fixture_manager.release(name, resolved[name])

    def find(self, name, object, *opts):
        """return provide_xxx() and release_xxx() functions."""
        globalvars = opts[0]
        provider_name = 'provide_' + name
        releaser_name = 'release_' + name
        meth = getattr(object, provider_name, None)
        if meth:
            provider = meth
            if python2:
                if hasattr(meth, 'im_func'):  provider = meth.im_func
            elif python3:
                if hasattr(meth, '__func__'): provider = meth.__func__
            releaser = getattr(object, releaser_name, None)
            return (provider, releaser)
        elif provider_name in globalvars:
            provider = globalvars[provider_name]
            if not isinstance(provider, types.FunctionType):
                raise TypeError("%s: expected function but got %s." % (provider_name, type(provider)))
            releaser = globalvars.get(releaser_name)
            return (provider, releaser)
        #else:
        #    raise NameError("%s: no such fixture provider for '%s'." % (provider_name, name))
            return None

    def _looped_dependency_error(self, aname, in_progress, object):
        names = in_progress + [aname]
        pos   = names.index(aname)
        loop  = '=>'.join(names[pos:])
        if pos > 0:
            loop = '->'.join(names[0:pos]) + '->' + loop
        classname = object.__class__.__name__
        testdesc  = object._description
        return LoopedDependencyError("fixture dependency is looped: %s (class: %s, test: '%s')" % (loop, classname, testdesc))


fixture_injector = FixtureInjector()


class LoopedDependencyError(ValueError):
    pass


##
## test context
##
def context():

    __all__ = ('subject', 'situation', )
    global TestContext

    class TestContext(object):
        """grouping test methods.

        normally created with subject() or situation() helpers.

        ex::
            class HelloClassTest(unittest.TestCase):
                SUBJECT = Hello
                with subject('#method1()'):
                    @test("spec1")
                    def _(self):
                        ...
                    @test("spec2")
                    def _(self):
                        ...
                with subject('#method2()'):
                    with situation('when condition:'):
                        @test("spec3")
                        def _(self):
                    with situation('else:')
                        @test("spec3")
                        def _(self):
                        ...
        """

        def __init__(self, desc, options=None, _lineno=None):
            self.desc = desc
            self.options = options
            self.items = []
            self.parent = None
            self._lineno = _lineno

        def __repr__(self):
            return "<TestContext desc=%r items=[%s]>" % \
                       (self.desc, ','.join(repr(x) for x in self.items))

        def __enter__(self):
            f_locals = sys._getframe(1).f_locals
            self._f_locals = f_locals
            self._varnames = set(f_locals.keys())
            stack = f_locals.setdefault('_context_stack', [])
            if not stack:
                f_locals.setdefault('_context_list', []).append(self)
            else:
                self.parent = stack[-1]
                self.parent.items.append(self)
            stack.append(self)
            return self

        def __exit__(self, *args):
            f_locals = self._f_locals
            popped = f_locals['_context_stack'].pop()
            assert popped is self
            newvars = set(f_locals.keys()) - self._varnames
            for name in newvars:
                if name.startswith('test'):
                    func = f_locals[name]
                    if not hasattr(func, '_test_context'):
                        func._test_context = self.desc
                        self.items.append((name, func))
                    if self.options:
                        if not hasattr(func, '_options'):
                            func._options = self.options.copy()
                        else:
                            for k, v in self.options.items():
                                if k not in func._options:
                                    func._options[k] = v
            self._sort_items(self.items)
            del self._f_locals
            del self._varnames

        @staticmethod
        def _sort_items(items):
            def fn(item):
                if isinstance(item, tuple):
                    return getattr(item[1], '_firstlineno', None) or \
                           util._func_firstlineno(item[1])
                elif isinstance(item, TestContext):
                    return item._lineno or 0
                else:
                    assert False, "** item=%r" % (item, )
            items.sort(key=fn)

        @staticmethod
        def _inspect_items(items):
            def _inspect(items, depth, add):
                for item in items:
                    if isinstance(item, tuple):
                        add("  " * depth + "- %s()\n" % item[0])
                    else:
                        add("  " * depth + "- Context: %r\n" % item.desc)
                        _inspect(item.items, depth+1, add)
            buf = []
            _inspect(items, 0, buf.append)
            return "".join(buf)


    def subject(desc, **options):
        """helper to group test methods by subject"""
        lineno = sys._getframe(1).f_lineno
        return TestContext(desc, options, _lineno=lineno)

    def situation(desc, **options):
        """helper to group test methods by situation or condition"""
        lineno = sys._getframe(1).f_lineno
        return TestContext(desc, options, _lineno=lineno)


    return locals()

context = _new_module("oktest.context", context())
context.TestContext = TestContext
subject   = context.subject
situation = context.situation


##
## dummy
##
def _dummy():

    __all__ = ('dummy_file', 'dummy_dir', 'dummy_values', 'dummy_attrs', 'dummy_environ_vars', 'dummy_io')


    class DummyFile(util.RunnableContext):

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


    class DummyDir(util.RunnableContext):

        def __init__(self, dirname):
            self.dirname = dirname
            self.path    = os.path.abspath(dirname)

        def __enter__(self, *args):
            os.mkdir(self.path)
            return self

        def __exit__(self, *args):
            import shutil
            shutil.rmtree(self.path)


    class DummyValues(util.RunnableContext):

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


    class DummyIO(util.RunnableContext):

        def __init__(self, stdin_content=None):
            self.stdin_content = stdin_content

        def __enter__(self):
            self.stdout, sys.stdout = sys.stdout, StringIO()
            self.stderr, sys.stderr = sys.stderr, StringIO()
            self.stdin,  sys.stdin  = sys.stdin,  StringIO(self.stdin_content or "")
            return self

        def __exit__(self, *args):
            sout, serr = sys.stdout.getvalue(), sys.stderr.getvalue()
            sys.stdout, self.stdout = self.stdout, sys.stdout.getvalue()
            sys.stderr, self.stderr = self.stderr, sys.stderr.getvalue()
            sys.stdin,  self.stdin  = self.stdin,  self.stdin_content

        def __call__(self, func, *args, **kwargs):
            self.returned = self.run(func, *args, **kwargs)
            return self

        def __iter__(self):
            yield self.stdout
            yield self.stderr


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

    def dummy_io(stdin_content="", func=None, *args, **kwargs):
        obj = dummy.DummyIO(stdin_content)
        if func is None:
            return obj    # for with-statement
        obj.__enter__()
        try:
            func(*args, **kwargs)
        finally:
            obj.__exit__(*sys.exc_info())
        #return obj.stdout, obj.stderr
        return obj


    return locals()


dummy = _new_module('oktest.dummy', _dummy(), util)
del _dummy



##
## Tracer
##
def _dummy():

    __all__ = ('Tracer', )


    class Call(object):

        __repr_style = None

        def __init__(self, receiver=None, name=None, args=None, kwargs=None, ret=None):
            self.receiver = receiver
            self.name   = name     # method name
            self.args   = args
            self.kwargs = kwargs
            self.ret    = ret

        def __repr__(self):
            #return '%s(args=%r, kwargs=%r, ret=%r)' % (self.name, self.args, self.kwargs, self.ret)
            if self.__repr_style == 'list':
                return repr(self.list())
            if self.__repr_style == 'tuple':
                return repr(self.tuple())
            buf = []; a = buf.append
            a("%s(" % self.name)
            for arg in self.args:
                a(repr(arg))
                a(", ")
            for k in self.kwargs:
                a("%s=%s" % (k, repr(self.kwargs[k])))
                a(", ")
            if buf[-1] == ", ":  buf.pop()
            a(") #=> %s" % repr(self.ret))
            return "".join(buf)

        def __iter__(self):
            yield self.receiver
            yield self.name
            yield self.args
            yield self.kwargs
            yield self.ret

        def list(self):
            return list(self)

        def tuple(self):
            return tuple(self)

        def __eq__(self, other):
            if isinstance(other, list):
                self.__repr_style = 'list'
                return list(self) == other
            elif isinstance(other, tuple):
                self.__repr_style = 'tuple'
                return tuple(self) == other
            elif isinstance(other, self.__class__):
                return self.name == other.name and self.args == other.args \
                    and self.kwargs == other.kwargs and self.ret == other.ret
            else:
                return False

        def __ne__(self, other):
            return not self.__eq__(other)


    class FakeObject(object):

        def __init__(self, **kwargs):
            self._calls = self.__calls = []
            for name in kwargs:
                setattr(self, name, self.__new_method(name, kwargs[name]))

        def __new_method(self, name, val):
            fake_obj = self
            if isinstance(val, types.FunctionType):
                func = val
                def f(self, *args, **kwargs):
                    r = Call(fake_obj, name, args, kwargs, None)
                    fake_obj.__calls.append(r)
                    r.ret = func(self, *args, **kwargs)
                    return r.ret
            else:
                def f(self, *args, **kwargs):
                    r = Call(fake_obj, name, args, kwargs, val)
                    fake_obj.__calls.append(r)
                    return val
            f.func_name = f.__name__ = name
            if python2: return types.MethodType(f, self, self.__class__)
            if python3: return types.MethodType(f, self)


    class Tracer(object):
        """trace function or method call to record arguments and return value.
           see README.txt for details.
        """

        def __init__(self):
            self.calls = []

        def __getitem__(self, index):
            return self.calls[index]

        def __len__(self):
            return len(self.calls)

        def __iter__(self):
            return self.calls.__iter__()

        def _copy_attrs(self, func, newfunc):
            for k in ('func_name', '__name__', '__doc__'):
                if hasattr(func, k):
                    setattr(newfunc, k, getattr(func, k))

        def _wrap_func(self, func, block):
            tr = self
            def newfunc(*args, **kwargs):                # no 'self'
                call = Call(None, util._func_name(func), args, kwargs, None)
                tr.calls.append(call)
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
            tr = self
            def newfunc(self, *args, **kwargs):          # has 'self'
                call = Call(self, util._func_name(func), args, kwargs, None)
                tr.calls.append(call)
                if util._is_unbound(func): args = (self, ) + args   # call with 'self' if unbound method
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
                method_obj = getattr(obj, method_name, None)
                if method_obj is None:
                    raise NameError("%s: method not found on %r." % (method_name, obj))
                setattr(obj, method_name, self._wrap_method(method_obj, None))
            return None

        def fake_method(self, obj, **kwargs):
            def _new_block(ret_val):
                def _block(*args, **kwargs):
                    return ret_val
                return _block
            def _dummy_method(obj, name):
                fn = lambda *args, **kwargs: None
                fn.__name__ = name
                if python2: fn.func_name = name
                if python2: return types.MethodType(fn, obj, type(obj))
                if python3: return types.MethodType(fn, obj)
            for method_name in kwargs:
                method_obj = getattr(obj, method_name, None)
                if method_obj is None:
                    method_obj = _dummy_method(obj, method_name)
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


tracer = _new_module('oktest.tracer', _dummy(), util)
del _dummy



##
## wsgi
##
web = type(sys)('oktest.web')
sys.modules[web.__name__] = web
web.__file__ = __file__

_BytesIO    = None          # on-demand import
_quote_plus = None          # on-demand import
_json       = None          # on-demand import
_types      = None          # on-demand import

_wsgiref_util      = None   # on-demand import
_wsgiref_validate  = None   # on-demand import
_wsgiref_headers   = None   # on-demand import

_cookie_quote      = None   # on-demand import

def _monkey_patch_for_wsgiref_validate():
    global _wsgiref_validate
    assert _wsgiref_validate is not None
    ## patch to wsgiref.validate.InputWrapper class
    def read(self, *args):
        _wsgiref_validate.assert_(len(args) <= 1)
        v = self.input.read(*args)
        _wsgiref_validate.assert_(type(v) is _bytes)
        return v
    def readline(self, *args):
        _wsgiref_validate.assert_(len(args) <= 1)
        v = self.input.readline(*args)
        _wsgiref_validate.assert_(type(v) is _bytes)
        return v
    InputWrapper = _wsgiref_validate.InputWrapper
    if '3.0' <= sys.version < '3.2':
        InputWrapper.read = read
    InputWrapper.readline = readline
    ## patch to wsgiref.validate.IteratorWrapper class
    def __next__(self):
        self._started = True
        return self._original__next__()
    def __del__(self):
        if getattr(self, '_started', None) and hasattr(self.iterator, 'close'):
            self._original__del__()
    IteratorWrapper = _wsgiref_validate.IteratorWrapper
    if python2:
        IteratorWrapper._original__next__ = IteratorWrapper.next
        IteratorWrapper.next = __next__
        __next__.__name__ = 'next'
    elif python3:
        IteratorWrapper._original__next__ = IteratorWrapper.__next__
        IteratorWrapper.__next__ = __next__
    IteratorWrapper._original__del__  = IteratorWrapper.__del__
    IteratorWrapper.__del__ = __del__


class WSGITest(object):
    __slots__ = ('_app', '_environ')
    __test__  = None    # for 'nosetests' command

    def __init__(self, app, environ={}):
        self._app = app
        self._environ = environ

    def __call__(self, method='GET', urlpath='/', _=None,
                 params=None, form=None, query=None, json=None, multipart=None,
                 headers=None, environ=None, cookies=None):
        global _wsgiref_validate
        if not _wsgiref_validate:
            import wsgiref.validate as _wsgiref_validate
            _monkey_patch_for_wsgiref_validate()
        env = self._new_env(method, urlpath, params=params,
                            form=form, query=query, json=json, multipart=multipart,
                            headers=headers, environ=environ, cookies=cookies)
        start_resp = web.WSGIStartResponse()
        iterable = _wsgiref_validate.validator(self._app)(env, start_resp)
        resp = web.WSGIResponse(start_resp.status, start_resp.headers, iterable)
        resp._environ = env
        return resp

    def _base_env(self, method, urlpath):
        if python3:
            urlpath = urlpath.encode('utf-8').decode('latin-1')
        env = {
            'REQUEST_METHOD': method,
            'PATH_INFO':      urlpath,
            'SCRIPT_NAME':    '',
            'QUERY_STRING':   '',
        }
        env.update(self._environ)
        return env

    def _new_env(self, method='GET', urlpath='/', _=None,
                 params=None, form=None, query=None, json=None, multipart=None,
                 headers=None, environ=None, cookies=None):
        global _BytesIO
        if _BytesIO is None:
            if python2:
                from cStringIO import StringIO as _BytesIO
            if python3:
                #from io import StringIO as _BytesIO
                from io import BytesIO as _BytesIO
        global _wsgiref_util
        if not _wsgiref_util:
            import wsgiref.util as _wsgiref_util
        #
        if params is not None:
            if method in ('GET', 'HEAD'):
                if query is not None:
                    raise TypeError("Both `params' and `query' are specified for %s method." % method)
                query = params
            elif method in ('POST', 'PUT', 'DELETE', 'PATCH'):
                if form is not None:
                    raise TypeError("Both `params' and `form' are specified for %s method." % method)
                if multipart is not None:
                    raise TypeError("Both `params' and `multipart' are specified for %s method." % method)
                if isinstance(params, web.MultiPart):
                    multipart = params
                else:
                    form = params
            else:
                raise TypeError("%s: unexpected method (expected GET, POST, PUT, DELETE, PATCH, or HEAD)." % method)
        #
        env = self._base_env(method, urlpath)
        if environ:
            env.update(environ)
        if query is not None:
            s = self._build_paramstr(query) if isinstance(query, dict) else str(query)
            env['QUERY_STRING'] = s
        if form is not None:
            s = self._build_paramstr(form) if isinstance(form, dict) else str(form)
            b = _B(s)
            env['wsgi.input']     = _BytesIO(b)
            env['CONTENT_TYPE']   = 'application/x-www-form-urlencoded'
            env['CONTENT_LENGTH'] = str(len(b))
        if json is not None:
            s = self._build_jsonstr(json) if isinstance(json, dict) else str(json)
            b = _B(s)
            env['wsgi.input']     = _BytesIO(b)
            env['CONTENT_TYPE']   = 'application/json'
            env['CONTENT_LENGTH'] = str(len(b))
        if multipart is not None:
            if _BytesIO is None:
                if python2:
                    from cStringIO import StringIO as _BytesIO
                if python3:
                    from io import BytesIO as _BytesIO
            if not isinstance(multipart, web.MultiPart):
                raise TypeError("'mutipart' should be oktest.web.MultiPart object, but got:%s" % (type(multipart), ))
            b = multipart.build()
            assert isinstance(b, _bytes)
            env['wsgi.input']     = _BytesIO(b)
            env['CONTENT_TYPE']   = multipart.content_type
            env['CONTENT_LENGTH'] = str(len(b))
        if headers:
            self._update_http_headers(env, headers)
        if cookies:
            if isinstance(cookies, dict):
                env['HTTP_COOKIE'] = self._build_cookie_str(cookies)
            else:
                env['HTTP_COOKIE'] = str(cookies)
        #
        _wsgiref_util.setup_testing_defaults(env)
        return env

    def _build_paramstr(self, param_dict):
        global _quote_plus
        if _quote_plus is None:
            if python2:
                from urllib import quote_plus as _quote_plus
            if python3:
                from urllib.parse import quote_plus as _quote_plus
        #
        q = _quote_plus
        arr = []; add = arr.append
        for k in param_dict:
            v = param_dict[k]
            if isinstance(v, (list, tuple)):
                vs = v
                for v in vs:
                    s = '' if v is None else str(v)
                    add("%s=%s" % (q(k), q(s)))
            else:
                s = '' if v is None else str(v)
                add("%s=%s" % (q(k), q(s)))
        return '&'.join(arr)

    def _build_jsonstr(self, jdict):
        global _json
        if _json is None:
            import json as _json
        #
        return _json.dumps(jdict, ensure_ascii=False, separators=(',', ':'))

    def _build_cookie_str(self, dct):
        global _cookie_quote
        if not _cookie_quote:
            if python2:
                from Cookie import _quote as _cookie_quote
            elif python3:
                from http.cookies import _quote as _cookie_quote
        return "; ".join( "%s=%s" % (k, _cookie_quote(str(v))) for k, v in dct.items() )

    def _update_http_headers(self, env, headers):
        if headers:
            for k in headers:
                if re.match(r'^HTTP_[A-Z_]+$', k):
                    name = k
                else:
                    name = 'HTTP_'+(k.upper().replace('-', '_'))
                env[name] = headers[k]


    ###

    def GET    (self, urlpath='/', **kw): return self.__call__('GET',     urlpath, **kw)
    def POST   (self, urlpath='/', **kw): return self.__call__('POST',    urlpath, **kw)
    def PUT    (self, urlpath='/', **kw): return self.__call__('PUT',     urlpath, **kw)
    def DELETE (self, urlpath='/', **kw): return self.__call__('DELETE',  urlpath, **kw)
    def PATCH  (self, urlpath='/', **kw): return self.__call__('PATCH',   urlpath, **kw)
    def HEAD   (self, urlpath='/', **kw): return self.__call__('HEAD',    urlpath, **kw)
    def OPTIONS(self, urlpath='/', **kw): return self.__call__('OPTIONS', urlpath, **kw)
    def TRACE  (self, urlpath='/', **kw): return self.__call__('TRACE',   urlpath, **kw)

    def _define(method):
        def fn(self, urlpath='/', _=None, _method=method,
               params=None, form=None, query=None, json=None, multipart=None,
               headers=None, environ=None, cookies=None):
            if _ is not None:
                raise TypeError("%s(): keyword argument expected but got:%r" % (method, _))
            return self.__call__(_method, urlpath, params=params,
                                 form=form, query=query, json=json, multipart=multipart,
                                 headers=headers, environ=environ, cookies=cookies)
        fn.__name__ = method
        return fn
    _localvars = locals()
    for _meth in "GET POST PUT DELETE PATCH HEAD OPTIONS TRACE".split():
        _localvars[_meth] = _define(_meth)
    del _define, _localvars, _meth


class WSGIStartResponse(object):
    __slots__ = ('status', 'headers')

    def __call__(self, status, headers):
        self.status  = status
        self.headers = headers


class WSGIResponse(object):
    __slots__ = ('status', 'status_code', 'headers_list', 'headers',
                 'body_iterable', '_body_binary', '_body_unicode', '_body_json',
                 '_environ',
                 )

    encoding = 'utf-8'

    def __init__(self, status='200 OK', headers=[], iterable=[]):
        global _wsgiref_headers
        if _wsgiref_headers is None:
            import wsgiref.headers as _wsgiref_headers
        self.status = status
        if status and re.match(r'^\d+ ', status):
            self.status_code = int(status.split()[0])
        else:
            self.status_code = None
        self.headers_list = headers
        self.headers = _wsgiref_headers.Headers(headers)
        self.body_iterable = iterable
        self._body_binary  = None
        self._body_unicode = None
        self._body_json    = None

    @property
    def body_binary(self):
        if self._body_binary == None:
            self._set_body_and_text(self.body_iterable)
        return self._body_binary

    @property
    def body_unicode(self):
        if self._body_unicode == None:
            self._set_body_and_text(self.body_iterable)
        return self._body_unicode

    @property
    def body_json(self):
        global json
        if json is None: import json
        self._validate_json_content_type()
        if self._body_json == None:
            self._body_json = json.loads(self.body_unicode)
        return self._body_json

    #body = body_binary
    #text = body_unicode

    def _set_body_and_text(self, iterable):
        buf = []; add = buf.append
        try:
            for x in iterable:
                if not isinstance(x, _bytes):
                    if isinstance(x, _unicode):
                        msg = "response body should be binary, but got unicode data: %r\n" % \
                            (x if len(x) < 30 else x[:30]+"...")
                        warnings.warn(msg, web.OktestWSGIWarning)
                        x = x.encode(self.encoding)
                    else:
                        raise ValueError("Unexpected response body data type: %r (%r)" % (type(x), x))
                add(x)
            self._body_binary  = _B("").join(buf)
            self._body_unicode = self._body_binary.decode(self.encoding)
        finally:
            if hasattr(iterable, 'close'):
                iterable.close()

    def _validate_json_content_type(self):
        cont_type = self.headers.get('Content-Type')
        if not cont_type:
            raise AssertionError("Content-Type is expected 'applicaiton/json' but empty.")
        if not re.match(r'^application/json(?:; *charset=(?:utf|UTF)-?8)?$', cont_type):
            raise AssertionError("Content-Type is expected 'application/json' but got %r" % (cont_type,))

    def __iter__(self):
        status = self.status
        headers = self.headers_list
        iterable = self.body_iterable
        if hasattr(iterable, 'original_iterator'):
            iterable = iterable.original_iterator
        return iter((status, headers, iterable))


class OktestWSGIWarning(Warning):
    pass


class MultiPart(object):
    """
    Builds multipart form data.

    ex:
        from oktest.web import MultiPart
        mp = MultiPart()              # generate boundary automatically
        #mp = MultiPart("abcdefg")    # specify boundary explicitly
        mp.add("name1", "value1")     # add string value
        with open("photo.jpg", 'rb') as f:
            mp.add("file1", f.read(), "photo.jpg", "image/jpeg")  # add file
        #
        print(mp.boundary)
        print(mp.content_type)
        print(mp.build())
        #
        import wsgiref.util
        import webob.request
        try:
            from cStringIO import StringIO as BytesIO
        except LoadError:
            from io import BytesIO
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE':   mp.content_type,
            'wsgi.input':     BytesIO(mp.build()),
        }
        wsgiref.util.setup_testing_defaults(environ)
        request = webob.request.Request(environ)
        print("request.POST=%r" % request.POST)
    """

    def __init__(self, boundary=None):
        self.boundary = boundary or self.new_boundary()
        self._data = []

    @staticmethod
    def new_boundary():
        from random import random
        from time import time
        import hashlib, base64
        s = "%s%s" % (random(), time())
        b = hashlib.sha256(_B(s)).digest()
        b = base64.urlsafe_b64encode(b)
        return _S(b).rstrip('=')

    def add(self, name, value, filename=None, content_type=None):
        if '"' in name:
            raise ValueError("'\"' is not available as parameter name.")
        if filename and '"' in filename:
            raise ValueError("'\"' is not available as filename.")
        self._data.append((_B(name), _B(value), _B(filename), _B(content_type), ))
        return self

    @property
    def content_type(self):
        return "multipart/form-data; boundary="+self.boundary

    def build(self):
        buf = []; extend = buf.extend
        boundary = _B('--') + _B(self.boundary)
        #
        for name, value, filename, content_type in self._data:
            assert isinstance(name, _bytes)
            assert isinstance(value, _bytes)
            assert filename is None or isinstance(filename, _bytes)
            assert content_type is None or isinstance(content_type, _bytes)
            #
            extend((boundary, _B('\r\n'), ))
            if filename:
                extend((_B('Content-Disposition: form-data; name="'), name, _B('"; filename="'), filename, _B('"\r\n'), ))
            else:
                extend((_B('Content-Disposition: form-data; name="'), name, _B('"\r\n'), ))
            if content_type:
                extend((_B('Content-Type: '), content_type, _B('\r\n'), ))
            extend((_B('\r\n'), value, _B('\r\n'), ))
        #
        extend((boundary, _B('--\r\n'), ))
        return _B('').join(buf)


web.WSGITest          = WSGITest
web.WSGIStartResponse = WSGIStartResponse
web.WSGIResponse      = WSGIResponse
web.OktestWSGIWarning = OktestWSGIWarning
web.MultiPart         = MultiPart
del WSGITest, WSGIStartResponse, WSGIResponse, OktestWSGIWarning, MultiPart



##
## validator
##

validator = type(sys)('oktest.validator')
sys.modules[validator.__name__] = validator
validator.__file__ = __file__


class Validator(object):
    """
    (Experimental) Utility class for validation.
    Example::

      from oktest.validator import Validator as V
      ok (json_data) == {
          "status": "OK",
          "member": {
              "id":       1,
              "name":     "Haruhi",
              "gender":   V('gender', enum=('M', 'F')),
              "age":      V('age', type=int),
              "birthday": V('birthday', pattern=r'^\d\d\d\d-\d\d-\d\d$'),
          }
      }

    Constructor::

      Validator(name, type=None, enum=None, between=None, length=None,
                pattern=None, func=None, **validations):

    Parameters:

    * name: arbitrary name to distinguish others on assertion error.
    * type: type such as int, float, str, and so on.
          Validator(name, type=int)
          Validator(name, type=(int, long, float))
    * enum: expected values of that actual value should be member
          Validator(name, enum=('jpg', 'png', 'gif'))
    * between: tuple of min and max value
          Validator(name, between(0, 100))
    * length: int of length, or tuple of min and max length.
          Validator(name, 255)
          Validator(name, (1, 255))
    * pattern: regular expression string or pattern object or tuple of pattern and option
          Validator(name, r'^[a-f0-9]+$')
          Validator(name, (r'^[a-f0-9]+$', re.I))
          Validator(name, re.pattern(r'^[a-f0-9]+$', re.I))
    * func: callback function which returns error message when validation failed
          Validator(name, func=lambda actual: \
                               "Even number expected" if actual % 2 != 0 else None)

    You can extend Validator class by yourself.
    See source code of Validator class.
    """

    @classmethod
    def register(self, name, validator_op):
        self._validator_ops[name] = validator_op

    _validator_ops = {}

    def __init__(self, name, **validations):
        self.name = name
        self._validations = validations
        validator_ops = self._validator_ops
        for k in validations:
            if k not in validator_ops:
                raise TypeError("%s: unknown validator name." % (k,))
            validator_ops[k].init(self, validations[k])

    def __eq__(self, actual):
        validator_ops = self._validator_ops
        for k in self._validations:
            validator_op = validator_ops.get(k)
            if not validator_op:
                raise TypeError("%s: unknown validator name." % (k,))
            validator_op.validate(self, actual)   # may raise AssertionError
        return True    # passed all assertions

    def __req__(self, actual):
        return self.__eq__(actual)

    def __str__(self):
        buf = []; add = buf.append
        add("<Validator(%s):" % self.name)
        for k in self._validations:
            add(" %s=%r" % (k, self._validations[k]))
        add(">")
        return "".join(buf)

    def __repr__(self):
        return self.__str__()


class ValidatorOp(object):

    def init(self, vali, arg):
        raise NotImplementedError("%s.init(): not implemented yet." % self.__class__.__name__)

    def validate(self, vali, actual):
        raise NotImplementedError("%s.validate(): not implemented yet." % self.__class__.__name__)


class TypeValidatorOp(ValidatorOp):

    def init(self, vali, arg):
        vali._type = arg

    def validate(self, vali, actual):
        if not isinstance(actual, vali._type):
            raise AssertionError(
                "Validator(%r):  isinstance($actual, %s): failed.\n"
                "  $actual: %r" % (vali.name, vali._type, actual)
            )


class EnumValidatorOp(ValidatorOp):

    def init(self, vali, arg):
        vali._enum = arg

    def validate(self, vali, actual):
        if actual not in vali._enum:
            raise AssertionError(
                "Validator(%r):  $actual in %r: failed.\n"
                "  $actual: %r" % (vali.name, vali._enum, actual)
            )


class BetweenValidatorOp(ValidatorOp):

    def init(self, vali, arg):
        if not isinstance(arg, tuple) or len(arg) != 2:
            raise TypeError("'between' should be a tuple of two values, but got:%r" % (arg,))
        vali._between = arg

    def validate(self, vali, actual):
        min, max = vali._between
        if min is not None and not (min <= actual):
            raise AssertionError(
                "Validator(%r):  $actual >= %r: failed.\n"
                "  $actual: %r" % (vali.name, min, actual)
            )
        if max is not None and not (actual <= max):
            raise AssertionError(
                "Validator(%r):  $actual <= %r: failed.\n"
                "  $actual: %r" % (vali.name, max, actual)
            )


class LengthValidatorOp(ValidatorOp):

    def init(self, vali, arg):
        if not isinstance(arg, (int, tuple)):
            raise TypeError("'length' should be an integer or tuple of min/max length, but got:%r" % (arg,))
        vali._length = arg

    def validate(self, vali, actual):
        length = vali._length
        if isinstance(length, int):
            if len(actual) != length:
                raise AssertionError(
                    "Validator(%r):  len($actual) == %r: failed.\n"
                    "  len($actual): %r\n"
                    "  $actual     : %r" % (vali.name, length, len(actual), actual)
                )
        elif isinstance(length, tuple):
            minlen, maxlen = length
            if minlen is not None and not (minlen <= len(actual)):
                raise AssertionError(
                    "Validator(%r):  len($actual) >= %r: failed.\n"
                    "  len($actual): %r\n"
                    "  $actual     : %r" % (vali.name, minlen, len(actual), actual)
                )
            if maxlen is not None and not (len(actual) <= maxlen):
                raise AssertionError(
                    "Validator(%r):  len($actual) <= %r: failed.\n"
                    "  len($actual): %r\n"
                    "  $actual     : %r" % (vali.name, maxlen, len(actual), actual)
                )


class PatternValidatorOp(ValidatorOp):

    def init(self, vali, arg):
        vali._pattern = pattern = arg
        if pattern is None:
            vali._rexp = None
        elif isinstance(pattern, str):
            vali._rexp = re.compile(pattern)
        elif isinstance(pattern, _rexp_type):
            vali._rexp = pattern
        elif isinstance(pattern, tuple):
            vali._rexp = re.compile(*pattern)
        else:
            raise TypeError("'pattern' should be a string or %r object, but got:%r" % (_rexp_type, pattern))

    def validate(self, vali, actual):
        rexp = vali._rexp
        if not rexp.search(actual):
            raise AssertionError(
                "Validator(%r):  re.search($actual, %r): failed.\n"
                "  $actual: %r" % (vali.name, rexp.pattern, actual)
            )


class FuncValidatorOp(ValidatorOp):

    def init(self, vali, arg):
        vali._func = arg

    def validate(self, vali, actual):
        errmsg = vali._func(actual)
        if errmsg:
            raise AssertionError("Validator(%r):  %s" % (vali.name, errmsg))


Validator.register('type',     TypeValidatorOp())
Validator.register('enum',     EnumValidatorOp())
Validator.register('between',  BetweenValidatorOp())
Validator.register('length',   LengthValidatorOp())
Validator.register('pattern',  PatternValidatorOp())
Validator.register('func',     FuncValidatorOp())


validator.Validator = Validator
validator.TypeValidatorOp      = TypeValidatorOp
validator.EnumValidatorOp      = EnumValidatorOp
validator.BetweenValidatorOp   = BetweenValidatorOp
validator.LengthValidatorOp    = LengthValidatorOp
validator.PatternValidatorOp   = PatternValidatorOp
validator.FuncValidatorOp  = FuncValidatorOp
del Validator
del TypeValidatorOp, EnumValidatorOp, BetweenValidatorOp, LengthValidatorOp
del PatternValidatorOp, FuncValidatorOp



##
## mainapp
##
import unittest

def load_module(mod_name, filepath, content=None):
    mod = type(os)(mod_name)
    mod.__dict__["__name__"] = mod_name
    mod.__dict__["__file__"] = filepath
    #mod.__dict__["__file__"] = os.path.abspath(filepath)
    if content is None:
        if python2:
            content = util.read_binary_file(filepath)
        if python3:
            content = util.read_text_file(filepath)
    if filepath:
        code = compile(content, filepath, "exec")
        exec(code, mod.__dict__, mod.__dict__)
    else:
        exec(content, mod.__dict__, mod.__dict__)
    return mod

def rglob(dirpath, pattern, _entries=None):
    import fnmatch
    if _entries is None: _entries = []
    isdir, join = os.path.isdir, os.path.join
    add = _entries.append
    if isdir(dirpath):
        items = os.listdir(dirpath)
        for item in fnmatch.filter(items, pattern):
            path = join(dirpath, item)
            add(path)
        for item in items:
            path = join(dirpath, item)
            if isdir(path) and not item.startswith('.'):
                rglob(path, pattern, _entries)
    return _entries


def _dummy():

    global optparse
    import optparse

    class MainApp(object):

        debug = False

        def __init__(self, command=None):
            self.command = command

        def _new_cmdopt_parser(self):
            #import cmdopt
            #parser = cmdopt.Parser()
            #parser.opt("-h").name("help")                         .desc("show help")
            #parser.opt("-v").name("version")                      .desc("version of oktest.py")
            ##parser.opt("-s").name("testdir").arg("DIR[,DIR2,..]") .desc("test directory (default 'test' or 'tests')")
            #parser.opt("-p").name("pattern").arg("PAT[,PAT2,..]") .desc("test script pattern (default '*_test.py,test_*.py')")
            #parser.opt("-x").name("exclude").arg("PAT[,PAT2,..]") .desc("exclue file pattern")
            #parser.opt("-D").name("debug")                        .desc("debug mode")
            #return parser
            parser = optparse.OptionParser(conflict_handler="resolve")
            parser.add_option("-h", "--help",       action="store_true",     help="show help")
            parser.add_option("-v", "--version",    action="store_true",     help="verion of oktest.py")
            parser.add_option("-s", dest="style",   metavar="STYLE",         help="reporting style (plain/simple/verbose, or p/s/v)")
            parser.add_option(      "--color",      metavar="true|false",    help="enable/disable output color")
            parser.add_option("-K", dest="encoding", metavar="ENCODING",     help="output encoding (utf-8 when system default is US-ASCII)")
            parser.add_option("-p", dest="pattern", metavar="PAT[,PAT2,..]", help="test script pattern (default '*_test.py,test_*.py')")
            #parser.add_option("-x", dest="exclude", metavar="PAT[,PAT2,..]", help="exclue file pattern")
            parser.add_option("-U", dest="unittest", action="store_true",    help="run testcases with unittest.main instead of oktest.run")
            parser.add_option("-D", dest="debug",   action="store_true",     help="debug mode")
            parser.add_option("-f", dest="filter",  metavar="FILTER",        help="filter (class=xxx/test=xxx/sid=xxx/useroption=xxx)")
            return parser

        def _load_modules(self, filepaths, pattern=None):
            from fnmatch import fnmatch
            modules = []
            for fpath in filepaths:
                mod_name = os.path.basename(fpath).replace('.py', '')
                if pattern and not fnmatch(mod_name, pattern):
                    continue
                mod = load_module(mod_name, fpath)
                modules.append(mod)
            self._trace("modules: ", modules)
            return modules

        def _load_classes(self, modules, pattern=None):
            from fnmatch import fnmatch
            testclasses = []
            unittest_testclasses = []
            oktest_testclasses   = []
            for mod in modules:
                for k in dir(mod):
                    #if k.startswith('_'): continue
                    v = getattr(mod, k)
                    if not isinstance(v, type): continue
                    klass = v
                    if pattern and not fnmatch(klass.__name__, pattern):
                        continue
                    if issubclass(klass, unittest.TestCase):
                        testclasses.append(klass)
                        unittest_testclasses.append(klass)
                    elif re.search(config.TARGET_PATTERN, klass.__name__):
                        testclasses.append(klass)
                        oktest_testclasses.append(klass)
            return testclasses, unittest_testclasses, oktest_testclasses

        def _run_unittest(self, klasses, pattern=None, filters=None):
            self._trace("test_pattern: %r" % (pattern,))
            self._trace("unittest_testclasses: ", klasses)
            loader = unittest.TestLoader()
            the_suite = unittest.TestSuite()
            rexp = re.compile(r'^test(_|_\d\d\d(_|: ))?')
            if filters:
                key = list(filters.keys())[0]
                val = filters[key]
            else:
                key = val = None
            for klass in klasses:
                if pattern or filters:
                    testnames = loader.getTestCaseNames(klass)
                    testcases = [ klass(tname) for tname in testnames
                                      if _filtered(klass, None, tname, pattern, key, val) ]
                    suite = loader.suiteClass(testcases)
                else:
                    suite = loader.loadTestsFromTestCase(klass)
                the_suite.addTest(suite)
            #runner = unittest.TextTestRunner()
            runner = unittest.TextTestRunner(stream=sys.stderr)
            result = runner.run(the_suite)
            n_errors = len(result.errors) + len(result.failures)
            return n_errors

        def _run_oktest(self, klasses, pattern, kwargs):
            self._trace("test_pattern: %r" % (pattern,))
            self._trace("oktest_testclasses: ", klasses)
            if pattern:
                kwargs.setdefault('filter', {})['test'] = pattern
            import oktest; run = oktest.run    # don't remove!
            n_errors = run(*klasses, **kwargs)
            return n_errors

        def _trace(self, msg, items=None):
            write = sys.stderr.write
            if items is None:
                write("** DEBUG: %s\n" % msg)
            else:
                write("** DEBUG: %s[\n" % msg)
                for item in items:
                    write("**   %r,\n" % (item,))
                write("** ]\n")

        def _help_message(self, parser):
            buf = []; add = buf.append
            add("Usage: python -m oktest [options] file_or_directory...\n")
            #add(parser.help_message(20))
            add(re.sub(r'^.*\n.*\n[oO]ptions:\n', '', parser.format_help()))
            add("Example:\n")
            add("   ## run test scripts in plain format\n")
            add("   $ python -m oktest -sp tests/*_test.py\n")
            add("   ## run test scripts in 'tests' dir with pattern '*_test.py'\n")
            add("   $ python -m oktest -p '*_test.py' tests\n")
            add("   ## filter by class name\n")
            add("   $ python -m oktest -f class='ClassName*' tests\n")
            add("   ## filter by test method name\n")
            add("   $ python -m oktest -f '*method*' tests   # or -f test='*method*'\n")
            add("   ## filter by user-defined option added by @test decorator\n")
            add("   $ python -m oktest -f tag='*value*' tests\n")
            return "".join(buf)

        def _version_info(self):
            buf = []; add = buf.append
            add("oktest: " + __version__)
            add("python: " + sys.version.split("\n")[0])
            add("")
            return "\n".join(buf)

        def _get_files(self, args, pattern):
            filepaths = []
            for arg in args:
                if os.path.isfile(arg):
                    filepaths.append(arg)
                elif os.path.isdir(arg):
                    files = self._find_files_recursively(arg, pattern)
                    filepaths.extend(files)
                else:
                    raise ValueError("%s: file or directory expected." % (arg,))
            return filepaths

        def _find_files_recursively(self, testdir, pattern):
            isdir = os.path.isdir
            assert isdir(testdir)
            filepaths = []
            for pat in pattern.split(","):
                files = rglob(testdir, pat)
                if files:
                    filepaths.extend(files)
                    self._trace("testdir: %r, pattern: %r, files: " % (testdir, pat), files)
            return filepaths

        #def _exclude_files(self, filepaths, pattern):
        #    from fnmatch import fnmatch
        #    _trace = self._trace
        #    basename = os.path.basename
        #    original = filepaths[:]
        #    for pat in pattern.split(","):
        #        filepaths = [ fpath for fpath in filepaths
        #                          if not fnmatch(basename(fpath), pat) ]
        #    _trace("excluded: %r" % (list(set(original) - set(filepaths)), ))
        #    return filepaths

        def _get_filters(self, opts_filter):
            filters = {}
            if opts_filter:
                pair = opts_filter.split('=', 2)
                if len(pair) != 2:
                    pair = ('test', pair[0])
                filters[pair[0]] = pair[1]
            return filters

        def _handle_opt_report(self, opt_report, parser):
            key = None
            d = {"p": "plain", "s": "simple", "v": "verbose"}
            key = d.get(opt_report, opt_report)
            self._trace("reporter: %s" % key)
            if not BaseReporter.get_registered_class(key):
                #raise optparse.OptionError("%r: unknown report sytle (plain/simple/verbose, or p/s/v)" % opt_report)
                parser.error("%r: unknown report sytle (plain/simple/verbose, or p/s/v)" % opt_report)
            return key

        def _handle_opt_color(self, opt_color, parser):
            import oktest.config
            if   opt_color in ('true', 'yes', 'on'):
                oktest.config.color_enabled = True
            elif opt_color in ('false', 'no', 'off'):
                oktest.config.color_enabled = False
            else:
                #raise optparse.OptionError("--color=%r: 'true' or 'false' expected" % opt_color)
                parser.error("--color=%r: 'true' or 'false' expected" % opt_color)
            return oktest.config.color_enabled

        def _get_output_writer(self, encoding):
            self._trace('output encoding: ' + encoding)
            if python2:
                import codecs
                return codecs.getwriter(encoding)(sys.stdout)
            if python3:
                import io
                return io.TextIOWrapper(sys.stdout.buffer, encoding=encoding)

        def run(self, args=None, **kwargs):
            if args is None: args = sys.argv[1:]
            parser = self._new_cmdopt_parser()
            #opts = parser.parse(args)
            opts, args = parser.parse_args(args)
            if opts.debug:
                self.debug = True
                _trace = self._trace
                import oktest.config
                oktest.config.debug = True
            else:
                _trace = self._trace = lambda msg, items=None: None
            _trace("python: " + sys.version.split()[0])
            _trace("oktest: " + __version__)
            _trace("opts: %r" % (opts,))
            _trace("args: %r" % (args,))
            if opts.help:
                print(self._help_message(parser))
                return
            if opts.version:
                print(self._version_info())
                return
            #
            if opts.style:
                kwargs['style'] = self._handle_opt_report(opts.style, parser)
            if opts.color:
                kwargs['color'] = self._handle_opt_color(opts.color, parser)
            if 'out' not in kwargs:
                if opts.encoding:
                    kwargs['out'] = self._get_output_writer(opts.encoding)
                elif not hasattr(sys.stdout, 'encoding') or \
                        sys.stdout.encoding in ('US-ASCII', 'ISO-8859-1', 'ANSI_X3.4-1968'):
                    kwargs['out'] = self._get_output_writer('utf-8')
            #
            pattern = opts.pattern or '*_test.py,test_*.py'
            filepaths = self._get_files(args, pattern)
            #if opts.exclude:
            #    filepaths = self._exclude_files(filepaths, opts.exclude)
            filters = self._get_filters(opts.filter)
            fval = lambda key, filters=filters: filters.pop(key, None)
            modules = self._load_modules(filepaths, fval('module'))
            tupl = self._load_classes(modules, fval('class'))
            testclasses, unittest_testclasses, oktest_testclasses = tupl
            kwargs['filter'] = filters
            if opts.unittest:
                n_errors = 0
                if unittest_testclasses:
                    n_errors += self._run_unittest(unittest_testclasses, fval('test'), filters)
                if oktest_testclasses:
                    n_errors += self._run_oktest(oktest_testclasses, fval('test'), kwargs)
            else:
                n_errors = self._run_oktest(testclasses, fval('test'), kwargs)
            return n_errors

        @classmethod
        def main(cls, sys_argv=None):
            #import cmdopt
            if sys_argv is None: sys_argv = sys.argv
            #app = cls(sys_argv[0])
            #try:
            #    app.run(sys_argv[1:])
            #    sys.exit(0)
            #except cmdopt.ParseError:
            #    ex = sys.exc_info()[1]
            #    sys.stderr.write("%s" % (ex, ))
            #    sys.exit(1)
            app = cls(sys_argv[0])
            n_errors = app.run(sys_argv[1:])
            sys.exit(n_errors)

    return locals()


mainapp = _new_module('oktest.mainapp', _dummy(), util)
del _dummy


def main(*args):
    sys_argv = [__file__] + sys.argv + list(args)
    mainapp.MainApp.main(sys_argv)


if __name__ == '__main__':
    mainapp.MainApp.main()
