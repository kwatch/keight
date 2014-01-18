# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

__doc__ = r"""Keight - very lightweight framework for web application

Example::

    #!/usr/bin/env python -S
    import keight as k8
    k8.cgi_debug()   # for debug mode
    def do_hello(request, response):
        return "<h1>Hello World</h1>"
    app = k8.CGIApplication(do_hello)
    app.run(debug=True)
"""


import sys, os, re, time

__all__ = ()
__globals__ = globals()


###
### configuration
###

class Config(object):

    secret_key         = ''

    session_file_dir   = None
    session_file_depth = 2
    upload_file_dir    = None

    debug              = False
    logging            = True

    editor_schema      = None   # or 'txmt', 'gvim'
    editorkicker_url   = 'http://localhost:10101/'

config = Config()


###
### logger
###

logger = None
def _get_logger():
    global logger
    if logger is None:
        if config.logging:
            import logging
            logging.basicConfig()
            logger = logging.getLogger()
        else:
            logger = False
    return logger

class SimpleLogger(object):

    FATAL = 50
    ERROR = 40
    WARN  = 30
    INFO  = 20
    DEBUG = 10
    TRACE =  0
    _level_list = [ ('fatal', FATAL), ('error', ERROR), ('warn', WARN),
                    ('info', INFO), ('debug', DEBUG), ('trace', TRACE), ]
    _level_dict = dict(_level_list)

    class ListWrapper(object):
        def __init__(self, L=None):
            if L is None: L = []
            self.list = L
        def write(self, arg):
            self.list.append(arg)

    def __init__(self, io=sys.stderr, level=None):
        if isinstance(io, list): io = ListWrapper(io)
        self.io = io
        self.set_level(level or self.INFO)

    def set_level(self, level):
        #: if level is str but not found in level names then raise error
        if isinstance(level, str):
            if level not in self._level_dict:
                raise ValueError('%r: invalid level.' % (level, ))
            n = self._level_dict[level]
        #: if level is int but not in correct range then raise error
        elif isinstance(level, int):
            if self.TRACE <= level <= self.FATAL:
                n = level
            else:
                raise ValueError('%r: level is not in range.' % (level, ))
        #: if level is invalid value then raise error
        else:
            raise TypeError('%r: invalid level value.' % (level, ))
        #:
        self.level = n
        #: set dummy funcs for lower levels
        d = self.__dict__
        dummy = lambda format, *args: None
        for name, x in self._level_list:
            if x >= n:
                d.pop(name, None)
            else:
                d[name] = dummy

    #def f(name, prefix):
    #    def func(self, format, *args):
    #        msg = args and (format % args) or format
    #        self.io.write('%s%s\n' % (prefix, msg))
    #    func.func_name = fund.__name__ = name
    #    return func
    #
    #fatal = f('fatal', '[FATAL] ')
    #error = f('error', '[ERROR] ')
    #warn  = f('warn',  '[warn] ')
    #info  = f('info',  '[info] ')
    #debug = f('debug', '[DEBUG] ')
    #trace = f('trace', '[trace] ')
    #
    #del f

    def fatal(self, fmt, *args):  self.io.write('[FATAL] %s\n' % (args and (fmt % args) or fmt))
    def error(self, fmt, *args):  self.io.write('[ERROR] %s\n' % (args and (fmt % args) or fmt))
    def warn (self, fmt, *args):  self.io.write('[WARN] %s\n'  % (args and (fmt % args) or fmt))
    def info (self, fmt, *args):  self.io.write('[INFO] %s\n'  % (args and (fmt % args) or fmt))
    def debug(self, fmt, *args):  self.io.write('[DEBUG] %s\n' % (args and (fmt % args) or fmt))
    def trace(self, fmt, *args):  self.io.write('[TRACE] %s\n' % (args and (fmt % args) or fmt))


###
### common util
###

random = hexdigest = base64 = struct = binascii = None     # lazy import

python2 = sys.version_info[0] == 2
python3 = sys.version_info[0] == 3

UNDEFINED = object()

def location(depth=0):
    frame = sys._getframe(depth+1)
    return (frame.f_code.co_filename, frame.f_lineno)

def _import(dotted_name):
    """ex. _import('my.handlers.HelloHandler')  #=> my.handlers.HelloHandler"""
    arr = dotted_name.split('.')
    name = arr.pop()
    if arr:
        mod_name = '.'.join(arr)
        mod = __import__(mod_name)
        for x in arr[1:]:
            mod = getattr(mod, x)
        if hasattr(mod, name):
            return getattr(mod, name)
    else:
        if name in globals():
            return globals()[name]
    raise ImportError("%s: object not found." % dotted_name)

_word_rexp   = re.compile(r'^[\/\w]+$')
_escape_rexp = re.compile(r'\\.')
_rexp_rexp   = re.compile(r'[\.\*\+\?\|\^\$\[\]\(\)\{\}]')

def is_rexp(s):
    if not s or _word_rexp.match(s):
        return False
    s = _escape_rexp.sub('', s)
    return _rexp_rexp.search(s) and True or None

def rfc1123_gmt(gmt=None):
    # "Tue, 27 Jul 2010 03:45:11 GMT"
    tupl = isinstance(gmt, (float, int)) and time.gmtime(gmt) or gmt
    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", tupl)

def new_cycle(*args):
    #:* returns cycle object
    def gfunc():
        i = -1
        n = len(args)
        while True:
            i += 1
            if i == n: i = 0
            yield args[i]
    g = gfunc()
    return python2 and g.next or g.__next__
    #return hasattr(g, '__next__') and g.__next__ or g.next

def each_slice(iterable, n, pad=UNDEFINED):
    #:* returns generator object
    #:* yields with n-items
    arr = []
    for item in iterable:
        arr.append(item)
        if len(arr) == n:
            yield arr
            arr = []
    if arr:
        #:* if pad is not specified then length of last items can be less than n
        #:* if pad is specified then padded by it and lenght of last items is equal to n
        if pad is not UNDEFINED:
            for i in xrange(n - len(arr)):
                arr.append(pad)
        yield arr

def _random_seed():
    #return os.urandom(30)
    global random, struct
    if not random: import random
    if not struct: import struct
    r = random.random
    return struct.pack('dddddd', r(), r(), r(), r(), r(), time.time()) + config.secret_key

def random_hexdigest():
    global hashlib
    if not hashlib: import hashlib
    return hashlib.sha1(_random_seed()).hexdigest()   # 40bytes
    #return hashlib.sha256(_random_seed()).hexdigest() # 64bytes

def urandom_hexdigest():
    global binascii
    if not binascii: import binascii
    binascii.b2a_hex(os.urandom(20))

def random_base64():
    global hashlib, base64
    if not hashlib: import hashlib
    if not base64: import base64
    bytes30 = hashlib.sha256(_random_seed()).digest()[0:30] # 30 bytes
    return base64.urlsafe_b64encode(bytes30)    # 40 bytes

def urandom_base64():
    global base64
    if not base64: import base64
    bytes30 = os.urandom(30)                    # 30 bytes
    return base64.urlsafe_b64encode(bytes30)    # 40 bytes

def serial_id(t=None):
    global random
    if not random: import random
    #base = 946684800  # 2000-01-01 00:00:00 GMT
    #return '%011d%05d' % ((t or time.time()) - base, random.randint(0, 99999))
    #return '%011d%05d' % (t or time.time() , random.randint(0, 99999))
    return '%011d%s' % (t or time.time(), ('%.5f' % random.random())[2:])


###
### html
###

def escape_html(val):
    if val is None: return ""
    return str(val).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;') #.replace("'",'&#039;')

h = escape_html

def d2qs(dct):
    return '&'.join(['%s=%s' % (quote_plus(str(k)), quote_plus(str(dct[k]))) for k in dct])

def dict2attr(dct):
    if not dct:
        return ''
    buf = []
    append = buf.append
    for k, v in dct.iteritems():
        if k in _html_attr_dict:
            v and append(_html_attr_dict[k])
        elif v is not None:
            append(' %s="%s"' % (k, escape_html(v)))
    return ''.join(buf)

_html_attr_dict = {
    'checked':  ' checked="checked"',
    'selected': ' selected="selected"',
    'disabled': ' disabled="disabled"',
}


_quote_rexp = None
_quote_plus_rexp = None

def quote(s):   # not tuned
    #:* converts symbols into '%XX'
    #:* if input contains spaces then convert them into '%20'
    global _quote_rexp
    if not _quote_rexp: _quote_rexp = re.compile(r'[^-.\w/]')
    return _quote_rexp.sub(lambda m: '%%%02X' % ord(m.group(0)), s)

def quote_plus(s):   # not tuned
    #:* converts symbols into '%XX'
    #:* if input contains spaces then convert them into '+'
    global _quote_plus_rexp
    if not _quote_plus_rexp: _quote_plus_rexp = re.compile(r'[^- .\w/]')
    return _quote_plus_rexp.sub(lambda m: '%%%02X' % ord(m.group(0)), s).replace(' ', '+')

def unquote_plus(s):
    #:* converts '%XX' into original string
    #:* if '+' is included then converts it as ' '
    arr = s.replace('+', ' ').split('%')
    ## if s doesn't contain '%' then don't call _unquotes()
    n = len(arr)
    if n == 1:
        return arr[0]
    #:* if '%' is appreared at the beginning/end of string then handled correctly
    #:* if upper and lower cases are mixed then ignores case
    #:* if failed to convert then returns as is
    return _unquotes(arr, n)

def _unquotes(arr, n):
    for i in xrange(1, n):
        s = arr[i]
        try:
            arr[i] = _hex2chr[s[:2]] + s[2:]
        except UnicodeDecodeError:
            arr[i] = unichr(int(s[:2], 16)) + s[2:]
        except KeyError:
            try:
                ## if upper and lower cases are mixed then ignores case
                arr[i] = _hex2chr[s[:2].upper()] + s[2:]
            except KeyError:
                ## if failed to convert then returns as is
                arr[i] = '%' + s
    return "".join(arr)

#_hex2chr = dict(('%02x' % i, chr(i)) for i in xrange(256))
#_hex2chr.update(('%02X' % i, chr(i)) for i in xrange(256))
#import pprint
#pprint.pprint(_hex2chr)
_hex2chr = {
        '00': '\x00', '01': '\x01', '02': '\x02', '03': '\x03', '04': '\x04', '05': '\x05', '06': '\x06', '07': '\x07', '08': '\x08', '09': '\t', '0A': '\n', '0B': '\x0b', '0C': '\x0c', '0D': '\r', '0E': '\x0e', '0F': '\x0f', '0a': '\n', '0b': '\x0b', '0c': '\x0c', '0d': '\r', '0e': '\x0e', '0f': '\x0f',
        '10': '\x10', '11': '\x11', '12': '\x12', '13': '\x13', '14': '\x14', '15': '\x15', '16': '\x16', '17': '\x17', '18': '\x18', '19': '\x19', '1A': '\x1a', '1B': '\x1b', '1C': '\x1c', '1D': '\x1d', '1E': '\x1e', '1F': '\x1f', '1a': '\x1a', '1b': '\x1b', '1c': '\x1c', '1d': '\x1d', '1e': '\x1e', '1f': '\x1f',
        '20': ' ', '21': '!', '22': '"', '23': '#', '24': '$', '25': '%', '26': '&', '27': "'", '28': '(', '29': ')', '2A': '*', '2B': '+', '2C': ',', '2D': '-', '2E': '.', '2F': '/', '2a': '*', '2b': '+', '2c': ',', '2d': '-', '2e': '.', '2f': '/',
        '30': '0', '31': '1', '32': '2', '33': '3', '34': '4', '35': '5', '36': '6', '37': '7', '38': '8', '39': '9', '3A': ':', '3B': ';', '3C': '<', '3D': '=', '3E': '>', '3F': '?', '3a': ':', '3b': ';', '3c': '<', '3d': '=', '3e': '>', '3f': '?',
        '40': '@', '41': 'A', '42': 'B', '43': 'C', '44': 'D', '45': 'E', '46': 'F', '47': 'G', '48': 'H', '49': 'I', '4A': 'J', '4B': 'K', '4C': 'L', '4D': 'M', '4E': 'N', '4F': 'O', '4a': 'J', '4b': 'K', '4c': 'L', '4d': 'M', '4e': 'N', '4f': 'O',
        '50': 'P', '51': 'Q', '52': 'R', '53': 'S', '54': 'T', '55': 'U', '56': 'V', '57': 'W', '58': 'X', '59': 'Y', '5A': 'Z', '5B': '[', '5C': '\\', '5D': ']', '5E': '^', '5F': '_', '5a': 'Z', '5b': '[', '5c': '\\', '5d': ']', '5e': '^', '5f': '_',
        '60': '`', '61': 'a', '62': 'b', '63': 'c', '64': 'd', '65': 'e', '66': 'f', '67': 'g', '68': 'h', '69': 'i', '6A': 'j', '6B': 'k', '6C': 'l', '6D': 'm', '6E': 'n', '6F': 'o', '6a': 'j', '6b': 'k', '6c': 'l', '6d': 'm', '6e': 'n', '6f': 'o',
        '70': 'p', '71': 'q', '72': 'r', '73': 's', '74': 't', '75': 'u', '76': 'v', '77': 'w', '78': 'x', '79': 'y', '7A': 'z', '7B': '{', '7C': '|', '7D': '}', '7E': '~', '7F': '\x7f', '7a': 'z', '7b': '{', '7c': '|', '7d': '}', '7e': '~', '7f': '\x7f',
        '80': '\x80', '81': '\x81', '82': '\x82', '83': '\x83', '84': '\x84', '85': '\x85', '86': '\x86', '87': '\x87', '88': '\x88', '89': '\x89', '8A': '\x8a', '8B': '\x8b', '8C': '\x8c', '8D': '\x8d', '8E': '\x8e', '8F': '\x8f', '8a': '\x8a', '8b': '\x8b', '8c': '\x8c', '8d': '\x8d', '8e': '\x8e', '8f': '\x8f',
        '90': '\x90', '91': '\x91', '92': '\x92', '93': '\x93', '94': '\x94', '95': '\x95', '96': '\x96', '97': '\x97', '98': '\x98', '99': '\x99', '9A': '\x9a', '9B': '\x9b', '9C': '\x9c', '9D': '\x9d', '9E': '\x9e', '9F': '\x9f', '9a': '\x9a', '9b': '\x9b', '9c': '\x9c', '9d': '\x9d', '9e': '\x9e', '9f': '\x9f',
        'A0': '\xa0', 'A1': '\xa1', 'A2': '\xa2', 'A3': '\xa3', 'A4': '\xa4', 'A5': '\xa5', 'A6': '\xa6', 'A7': '\xa7', 'A8': '\xa8', 'A9': '\xa9', 'AA': '\xaa', 'AB': '\xab', 'AC': '\xac', 'AD': '\xad', 'AE': '\xae', 'AF': '\xaf',
        'B0': '\xb0', 'B1': '\xb1', 'B2': '\xb2', 'B3': '\xb3', 'B4': '\xb4', 'B5': '\xb5', 'B6': '\xb6', 'B7': '\xb7', 'B8': '\xb8', 'B9': '\xb9', 'BA': '\xba', 'BB': '\xbb', 'BC': '\xbc', 'BD': '\xbd', 'BE': '\xbe', 'BF': '\xbf',
        'C0': '\xc0', 'C1': '\xc1', 'C2': '\xc2', 'C3': '\xc3', 'C4': '\xc4', 'C5': '\xc5', 'C6': '\xc6', 'C7': '\xc7', 'C8': '\xc8', 'C9': '\xc9', 'CA': '\xca', 'CB': '\xcb', 'CC': '\xcc', 'CD': '\xcd', 'CE': '\xce', 'CF': '\xcf',
        'D0': '\xd0', 'D1': '\xd1', 'D2': '\xd2', 'D3': '\xd3', 'D4': '\xd4', 'D5': '\xd5', 'D6': '\xd6', 'D7': '\xd7', 'D8': '\xd8', 'D9': '\xd9', 'DA': '\xda', 'DB': '\xdb', 'DC': '\xdc', 'DD': '\xdd', 'DE': '\xde', 'DF': '\xdf',
        'E0': '\xe0', 'E1': '\xe1', 'E2': '\xe2', 'E3': '\xe3', 'E4': '\xe4', 'E5': '\xe5', 'E6': '\xe6', 'E7': '\xe7', 'E8': '\xe8', 'E9': '\xe9', 'EA': '\xea', 'EB': '\xeb', 'EC': '\xec', 'ED': '\xed', 'EE': '\xee', 'EF': '\xef',
        'F0': '\xf0', 'F1': '\xf1', 'F2': '\xf2', 'F3': '\xf3', 'F4': '\xf4', 'F5': '\xf5', 'F6': '\xf6', 'F7': '\xf7', 'F8': '\xf8', 'F9': '\xf9', 'FA': '\xfa', 'FB': '\xfb', 'FC': '\xfc', 'FD': '\xfd', 'FE': '\xfe', 'FF': '\xff',
        'a0': '\xa0', 'a1': '\xa1', 'a2': '\xa2', 'a3': '\xa3', 'a4': '\xa4', 'a5': '\xa5', 'a6': '\xa6', 'a7': '\xa7', 'a8': '\xa8', 'a9': '\xa9', 'aa': '\xaa', 'ab': '\xab', 'ac': '\xac', 'ad': '\xad', 'ae': '\xae', 'af': '\xaf',
        'b0': '\xb0', 'b1': '\xb1', 'b2': '\xb2', 'b3': '\xb3', 'b4': '\xb4', 'b5': '\xb5', 'b6': '\xb6', 'b7': '\xb7', 'b8': '\xb8', 'b9': '\xb9', 'ba': '\xba', 'bb': '\xbb', 'bc': '\xbc', 'bd': '\xbd', 'be': '\xbe', 'bf': '\xbf',
        'c0': '\xc0', 'c1': '\xc1', 'c2': '\xc2', 'c3': '\xc3', 'c4': '\xc4', 'c5': '\xc5', 'c6': '\xc6', 'c7': '\xc7', 'c8': '\xc8', 'c9': '\xc9', 'ca': '\xca', 'cb': '\xcb', 'cc': '\xcc', 'cd': '\xcd', 'ce': '\xce', 'cf': '\xcf',
        'd0': '\xd0', 'd1': '\xd1', 'd2': '\xd2', 'd3': '\xd3', 'd4': '\xd4', 'd5': '\xd5', 'd6': '\xd6', 'd7': '\xd7', 'd8': '\xd8', 'd9': '\xd9', 'da': '\xda', 'db': '\xdb', 'dc': '\xdc', 'dd': '\xdd', 'de': '\xde', 'df': '\xdf',
        'e0': '\xe0', 'e1': '\xe1', 'e2': '\xe2', 'e3': '\xe3', 'e4': '\xe4', 'e5': '\xe5', 'e6': '\xe6', 'e7': '\xe7', 'e8': '\xe8', 'e9': '\xe9', 'ea': '\xea', 'eb': '\xeb', 'ec': '\xec', 'ed': '\xed', 'ee': '\xee', 'ef': '\xef',
        'f0': '\xf0', 'f1': '\xf1', 'f2': '\xf2', 'f3': '\xf3', 'f4': '\xf4', 'f5': '\xf5', 'f6': '\xf6', 'f7': '\xf7', 'f8': '\xf8', 'f9': '\xf9', 'fa': '\xfa', 'fb': '\xfb', 'fc': '\xfc', 'fd': '\xfd', 'fe': '\xfe', 'ff': '\xff',
    }



###
### exception
###

class HttpException(Exception):

    status = None
    headers = [('Content-Type', 'text/html; charset=utf-8'), ]

    def to_html(self):
        return "<h2>%s</h2>\n<p>%s</p>\n" % (STATUS_CODES.get(self.status), h(str(self)))

    def handle(self, request, response):
        response.set_status(self.status)
        response.set_content_type('text/html; charset=utf-8')
        return self.to_html()


class HttpRedirect(HttpException):

    def __init__(self, location):
        HttpException.__init__(self, 'Redirect to %s' % location)
        self.location = location

    def handle(self, request, response):
        content = HttpException.handle(self, request, response)
        response.add_header('Location', self.location)
        return content


class Http301MovedPermanently(HttpRedirect):
    status = 301  #'301 Moved Permanently'

class Http302Found(HttpRedirect):
    status = 302  #'302 Found'

class Http307TemporaryRedirect(HttpRedirect):
    status = 307  #'307 Temporary Redirect'


class Http400BadRequest(HttpException):
    status = 400  #'400 Bad Request'

class Http401Unauthorized(HttpException):
    status = 401  #'401 Unauthorized'

class Http403Forbidden(HttpException):
    status = 403  #'403 Forbidden'

class Http404NotFound(HttpException):
    status = 404  #'404 Not Found'
    def __init__(self, path):
        HttpException.__init__(self, "%s: not found." % path)
        self.path = path

class Http405MethodNotAllowed(HttpException):
    status = 405  #'405 Method Not Allowed'
    def __init__(self, method):
        HttpException.__init__(self, "%s: method not allowed." % method)
        self.method = method

class Http406NotAcceptable(HttpException):
    status = 406  #'406 Not Acceptable'

class Http409Conflict(HttpException):
    status = 409  #'409 Conflict'

class Http413RequestEntityTooLarge(HttpException):
    status = 413  #'413 Request Entity Too Large'

class Http422UnprocessableEntity(HttpException):
    status = 422  #'422 Unprocessable Entity'

class Http500InternalServerError(HttpException):
    status = 500  #'500 Internal Server Error'

class Http501NotImplemented(HttpException):
    status = 501  #'501 Not Implemented'

class Http503ServiceUnavailable(HttpException):
    status = 503  #'503 Service Unavialable'



###
### core
###

class Params(object):

    encoding = 'utf-8'
    false_values = { '': '', '0': '0', 'False': 'False', 'false': 'false' }

    def __init__(self, values=None, encoding=None):
        if values is None: values = {}
        if encoding is not None:
            self.encoding = encoding
        self.values = values
        #self.get = values.get

    def get(self, key, default=None):  return self.values.get(key, default)
    def __setitem__(self, key, val):   self.values[key] = val
    def __contains__(self, key):       return key in self.values
    def __iter__(self):                return self.values.__iter__()

    def __getitem__(self, key):
        if key.endswith('[]'):
            return self.values.get(key, [])
        else:
            return self.values.get(key, '')

    def str(self, name, default=''):
        if name in self.values:
            self.values[name] = val = self.values[name].strip()
        else:
            self.values[name] = val = default
        return val

    bytes = str

    def unicode(self, name, default=u''):
        if name in self.values:
            self.values[name] = val = self.values[name].strip().decode(self.encoding)
        else:
            self.values[name] = val = default
        return val

    def raw(self, name, default=''):
        return self.setdefault(name, default)

    def _get_list(self, name, func):
        if not name.endswith('[]'):
            raise ValueError("name is not ended with '[]'.")
        if name in self.values:
            arr = self.values[name]
            arr[:] = [ func(s) for s in arr if s.strip() ]
        else:
            self.values[name] = []
        return self.values[name]

    def str_list(self, name):
        return self._get_list(name, lambda s: s.strip())

    def str_list(self, name):
        return self._get_list(name, lambda s, _enc=self.encoding: s.strip().decode(_enc))

    def raw_list(self, name):
        return self._get_list(name, lambda s: s)

    def int(self, name, default=False):  # TODO:
        if name not in self.values:
            if type(default) is int:
                self.values[name] = str(default)
            else:
                self.values[name] = ''
            return default
        else:
            val = self.values[name].strip()
            self.values[name] = val
            try:
                return int(val)
            except ValueError:
                return default

    def float(self, name, default=False):   # TODO:
        if name not in self.values:
            if isinstance(default, (float, str)):
                self.values[name] = str(default)
                return float(default)
            else:
                self.values[nam] = ''
                return default
        else:
            val = self.values[name].strip()
            self.values[name] = val
            try:
                return float(val)
            except:
                return default

    def bool(self, name, default=False):   # TODO:
        if name not in self.value:
            self.values[name] = default and '1' or '0'
            return default
        else:
            val = self.values[name].strip()
            if val in self.false_values:
                self.values[name] = '0'
                return False
            else:
                self.values[name] = '1'
                return True

PARAMS = Params


class Request(object):

    max_content_length = 20 * 1024 * 1024

    def __init__(self, env=None):
        if env is None: env = os.environ
        if env:
            #:* sets attributes
            self.env = self.headers = env
            self.method = env.get('REQUEST_METHOD')
            self.uri    = env.get('REQUEST_URI') or ''
            if self.uri:
                #self.path   = self.uri[0:-(len(env.get('QUERY_STRING', '')) + 2)]
                self.path = self.uri.split('?', 1)[0]
            else:
                self.path = env.get('PATH_INFO')
            self.input  = env.get('wsgi.input') or sys.stdin
            self.errors = env.get('wsgi.errors') or sys.stdin
            #:* if request body is empty then content length is None
            try:
                self.content_length = int(env.get('CONTENT_LENGTH'))
            except Exception:
                self.content_length = None
            #:* if GET method then only query string is parsed
            #:* if POST or PUT method then only request body is parsed
            self._parse_form_params(env)
            #:* parses cookie
            self.cookies = self._parse_cookies(env)

    def destroy(self):
        if hasattr(self, 'env'):
            self.params.files.clear()      # to invoke UploadedFile.__del__()
            self.params.values.clear()
            self.cookies.clear()
        self.__dict__.clear()

    def _parse_form_params(self, env):
        if self.content_length and self.content_length > self.max_content_length:
            raise Http413RequestEntityTooLarge("Content length is too large.")
        req_method = self.method
        if req_method == 'GET':
            values = self.parse_query_string(env.get('QUERY_STRING'))
            files  = {}
        elif req_method == 'POST' or req_method == 'PUT':
            content_type = env.get('CONTENT_TYPE')
            values, files = self.parse_request_body(self.input, self.content_length or 0, content_type)
        else:
            values = {};  files = {}
        self.params = PARAMS(values)
        #self.files  = files   # or PARAMS(files) ?
        self.params.files = files

    def parse_query_string(self, query_string,
                           _sep_rexp=re.compile(r'[&;]')):
        _unq = _unquotes
        values = {}
        if query_string:
            #:* if separater is ';' then parsed as well as '&'
            for s in _sep_rexp.split(query_string):
                pair = s.split('=', 1)
                if len(pair) == 2:
                    #:* if value is omitted then empty string is assumed
                    k, v = pair
                else:
                    #:* if '=' is missing then value is empty string
                    k = pair[0]
                    v = ''
                #:* if url-escaped then unescape it
                ## unquote param name
                if k.endswith('%5B%5D'):
                    k = k[:-6] + '[]'
                #k.replace('+', ' ').split('%')
                arr = k.split('%')
                if len(arr) == 1:
                    k = arr[0]
                else:
                    k = _unq(arr, len(arr))
                ## unquote param value
                arr = v.replace('+', ' ').split('%')
                n = len(arr)
                if n == 1:
                    v = arr[0]
                else:
                    v = _unq(arr, n)
                #:* if param name ends with '[]' then value is list
                if k.endswith('[]'):
                #if k.endswith('%5B%5D') or k.endswith('%05b%5d'):
                #    k = k[0:-6] + '[]'
                    #values.setdefault(k, []).append(v)
                    if k in values:
                        values[k].append(v)
                    else:
                        values[k] = [v]
                else:
                    values[k] = v
        #:* returns a dict
        return values

    def parse_request_body(self, stdin, content_length, content_type,
                           _boundary_rexp=re.compile(r'\bboundary=(?:"([^\";,]+)"|([^;,]+))')):
        assert isinstance(content_length, int)
        if content_type == 'application/x-www-form-urlencoded':
            if content_length is None:
                body = stdin.read()
            else:
                body = stdin.read(content_length)
            values = self.parse_query_string(body)
            files = {}
        elif content_type and content_type.startswith('multipart/form-data;'):
            m = _boundary_rexp.search(content_type)
            if not m:
              raise Http400BadRequest("%r: can't find boundary of multipart data." % content_type)
            boundary = m.group(1) or m.group(2)
            values, files = self.parse_multipart(stdin, content_length, boundary)
        else:
            values = {}
            files  = {}
        return (values, files)

    def parse_multipart(self, stdin, content_length, boundary):
        return MultiPart(boundary).parse(stdin, content_length)

    @staticmethod
    def _parse_cookies(env):
        cookie = env.get('HTTP_COOKIE')
        cookies = {}
        if cookie:
            for item in cookie.split(';'):
                try:
                    k, v = item.strip().split('=', 1)
                except ValueError:  # if item doesn't contain '='
                    pass            # then ignore it
                else:
                    cookies[unquote_plus(k)] = unquote_plus(v)
        return cookies

    def _delete_uploaded_files(self):
        if self.files:
            for k, uploaded_file in self.files.iteritems():
                uploaded_file.unlink()

    def is_xhr(self):
        return env.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

REQUEST = Request


STATUS_CODES = {
    100: "100 Continue",
    101: "101 Switching Protocols",
    102: "102 Processing",
    200: "200 OK",
    201: "201 Created",
    202: "202 Accepted",
    203: "203 Non-Authoritative Information",
    204: "204 No Content",
    205: "205 Reset Content",
    206: "206 Partial Content",
    207: "207 Multi-Status",
    226: "226 IM Used",
    300: "300 Multiple Choices",
    301: "301 Moved Permanently",
    302: "302 Found",
    303: "303 See Other",
    304: "304 Not Modified",
    305: "305 Use Proxy",
    307: "307 Temporary Redirect",
    400: "400 Bad Request",
    401: "401 Unauthorized",
    402: "402 Payment Required",
    403: "403 Forbidden",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
    406: "406 Not Acceptable",
    407: "407 Proxy Authentication Required",
    408: "408 Request Timeout",
    409: "409 Conflict",
    410: "410 Gone",
    411: "411 Length Required",
    412: "412 Precondition Failed",
    413: "413 Request Entity Too Large",
    414: "414 Request-URI Too Long",
    415: "415 Unsupported Media Type",
    416: "416 Requested Range Not Satisfiable",
    417: "417 Expectation Failed",
    418: "418 I'm a teapot",
    422: "422 Unprocessable Entity",
    423: "423 Locked",
    424: "424 Failed Dependency",
    426: "426 Upgrade Required",
    500: "500 Internal Server Error",
    501: "501 Not Implemented",
    502: "502 Bad Gateway",
    503: "503 Service Unavailable",
    504: "504 Gateway Timeout",
    505: "505 HTTP Version Not Supported",
    506: "506 Variant Also Negotiates",
    507: "507 Insufficient Storage",
    510: "510 Not Extended",
}


class Response(object):

    encoding = 'utf-8'

    def __init__(self):
        #:* set status code to 200
        self.status  = 200   # OK
        #:* content type is set to 'text/html; charset=utf-8'
        self.headers = [('Content-Type', 'text/html; charset=utf-8')]
        self.cookies = []

    def destroy(self):
        self.headers[:] = ()
        self.cookies[:] = ()
        self.__dict__.clear()

    def set_status(self, status_code):
        #:* if status_code is unknown then raises ValueError
        if status_code not in STATUS_CODES:
            raise ValueError('%s: unknown status code.' % status_code)
        #:* if status_code is valid then set it to attr
        self.status = status_code

    def get_status_str(self):
        #:* returns status code and message
        return STATUS_CODES.get(self.status)

    def set_content_type(self, content_type):
        #:* sets content type
        self.headers[0] = ('Content-Type', content_type)

    def get_content_type(self):
        #:* returns content type
        return self.headers[0][1]

    def set_encoding(self, encoding):
        #:* sets encoding and changes content type
        self.encoding = encoding
        self.headers[0] = ('Content-Type', 'text/html; charset=' + encoding)

    def add_header(self, name, value):
        #:* adds header
        self.headers.append((name, value))

    def add_cookie(self, name, value='', path=None, domain=None, expires=None, secure=None):
        if isinstance(name, basestring):
            cookie = COOKIE(name, value, path, domain, expires, secure)
        else:
            cookie = name
        self.cookies.append(cookie)

    def expire_cookie(self, name, value='', path=None, domain=None, expires=None, secure=None):
        self.add_cookie(name, value, path, domain, expires, secure)
        self.cookies[-1].expires = time.gmtime(0)

    def set_redirect(self, location, permanently=False):
        #:* if permantently is True then sets status code to 301
        if permanently:
            self.status = 301  # Moved Permanently
        #:* if permantently is False then sets status code to 302
        else:
            self.status = 302  # Found
        #:* set Location header
        self.add_header('Location', location)

    def build(self):
        #:* returns http response string
        buf = ['Status: ', self.get_status_str(), "\r\n"]
        for k, v in self.headers:
            #if isinstance(v, list):
            #    for item in v:
            #        buf.extend((k, ': ', str(item), "\r\n"))
            #else:
                buf.extend((k, ': ', str(v), "\r\n"))
        for c in self.cookies:
            buf.extend(('Set-Cookie: ', str(c), "\r\n"))
        buf.append("\r\n")
        return ''.join(buf)

    def gen_headers(self):
        for k, v in self.headers:
            #if isinstance(v, list):
            #    for item in v:
            #        yield k, str(item)
            #else:
                yield k, str(v)
        for c in self.cookies:
            yield 'Set-Cookie', str(c)

    def get_headers(self):
        return list(self.gen_headers())

RESPONSE = Response


class Cookie(object):

    path    = None
    domain  = None
    expires = None
    secure  = None

    def __init__(self, name, value, path=None, domain=None, expires=None, secure=None):
        #:* takes name, value, path, domain, expires, and secore args
        self.name = name
        self.value = value
        if path    is not None:  self.path    = path
        if domain  is not None:  self.domain  = domain
        if expires is not None:  self.expires = expires
        if secure  is not None:  self.secure  = secure

    def destrory(self):
        self.__dict__.clear()

    def __str__(self):
        #:* handles unicode object
        #:* quotes name and value
        buf = [quote(self.name), '=', quote(self.value)]
        _extend = buf.extend
        if self.path:     _extend(('; path=',    self.path))
        if self.domain:   _extend(('; domain=',  self.domain))
        #:* if 'expires' is integer then regard it as seconds
        if self.expires:  _extend(('; expires=', rfc1123_gmt(self._calc_expires())))
        if self.secure:   _extend(('; secure',))
        #:* converts into str
        return ''.join(buf)

    def __repr__(self):
        s = object.__repr__(self)
        return '%s: %s%s' % (s[:-1], self.__str__(), s[-1])
        #d = self.__dict__
        #b.extend([ ' %s=%r' % (k, d[k]) for k in d ])
        #b.append(s[-1])
        #return ''.join(b)

    def _calc_expires(self):
        #:* if 'expires' is int then returns time.gmtime(time.time()+expires)
        if isinstance(self.expires, int):
            return time.gmtime(time.time() + self.expires)
        #:* if 'expires' is not an int then returns it
        return self.expires

COOKIE = Cookie



###
### multipart
###
random = mimetypes = None    # lazy import

_mpart_rexp1 = None
_mpart_rexp2 = None

class MultiPart(object):

    BUF_SIZE = 10 * 1024 * 1024    # 10MB

    def __init__(self, boundary=None):
        self.boundary = boundary or self.create_boundary()
        self._added = []

    def destroy(self):
        self.__dict__.clear()

    def add(self, name, value, filename=None, content_type=None):
        #:* if filename is specified but content_type is not then guess it from filename
        if filename and not content_type:
            content_type = self.detect_content_type(filename)
        #:* saves name, value, filename, and content_type
        self._added.append((name, value, filename, content_type))
        #:* returns self
        return self

    def build(self):
        #:* builds multipart data and returns it
        q = quote
        buf = []
        extend = buf.extend
        for name, value, filename, content_type in self._added:
            extend(('--', self.boundary, "\r\n", ))
            if filename:
                extend(('Content-Disposition: form-data; name="', q(name), '"; filename="', q(filename), "\"\r\n", ))
            else:
                extend(('Content-Disposition: form-data; name="', q(name),                               "\"\r\n", ))
            if content_type:
                extend(('Content-Type: ', content_type, "\r\n", ))
            extend(("\r\n",
                    value, "\r\n", ))
        extend(('--', self.boundary, "--\r\n"))
        #:* clears internal buffer
        self._added = []
        return ''.join(buf)

    @staticmethod
    def create_boundary():
        global random, hashlib
        if not random: import random
        if not hashlib: import hashlib
        #return ('-boundary%.20f' % random.random())[2:]
        return '--boundary' + hashlib.sha1(str(random.random())).hexdigest()

    @staticmethod
    def detect_content_type(filename):
        global mimetypes
        if not mimetypes:
            import mimetypes
            mimetypes.init()
        ctype, encoding = mimetypes.guess_type(filename)
        if encoding == 'gzip':
            return 'application/gzip'
        return ctype or 'application/octet-stream'

    def parse(self, stdin, content_length):
        #:* returns params and files
        global _mpart_rexp1, _mpart_rexp2
        if not _mpart_rexp1:
            _mpart_rexp1 = re.compile('form-data; name=(?:"([^"\r\n]*)"|([^;\r\n]+))')
            _mpart_rexp2 = re.compile('; filename=(?:"([^"\r\n]*)"|([^;\r\n]+))')
        uq = unquote_plus
        params = {}
        files = {}
        def _split(s, sep, default):
            t = s.split(sep, 1)
            if len(t) == 2: return t
            return t[0], default
        for s in self._read(stdin, content_length):
            header, value = _split(s, "\r\n\r\n", '')
            #t = s.split("\r\n\r\n", 1)
            #header, value = len(t) == 2 and t or (t[0], '')
            headers = dict([ _split(x, ': ', '') for x in header.split("\r\n") ])
            disp = headers.get('Content-Disposition') or ''
            if not disp:
                raise Http400BadRequest("Content-Disposition is required.")
            m = _mpart_rexp1.search(disp)
            if not m:
                raise Http400BadRequest("Content-Disposition is invalid.")
            name = uq(m.group(1) or m.group(2))
            m = _mpart_rexp2.search(disp)
            if m:
                filename = m.group(1) or m.group(2) or ''
                cont_type = headers.get('Content-Type')
                upfile = filename and self._uploaded_file(uq(filename), value, cont_type) or None
                if name.endswith('[]'):
                    params.setdefault(name, []).append(filename)
                    arr = files.setdefault(name, [])
                    if upfile: arr.append(upfile)
                else:
                    params[name] = filename
                    if upfile: files[name] = upfile
            else:
                if name.endswith('[]'):
                    params.setdefault(name, []).append(value)
                else:
                    params[name] = value
        return params, files

    def _uploaded_file(self, filename, content, content_type):
        #return (content, filename, content_type)
        assert filename
        upfile = UploadedFile(filename, content_type)
        f = upfile.open()
        try:     f.write(content)
        finally: f.close()
        return upfile

    def _read(self, stdin, content_length):
        ## read first line
        first_line = "--" + self.boundary + "\r\n"
        buf = stdin.read(len(first_line))
        if buf != first_line:
            raise Http400BadRequest("invalid first boundary.")
        rest_len = content_length
        rest_len -= len(first_line)
        ## read separated contents
        separator = "\r\n--%s\r\n" % self.boundary
        last = None
        buf_size = self.BUF_SIZE
        while rest_len > 0:
            buf = stdin.read(rest_len > buf_size and buf_size or rest_len)
            if not buf:
                break
            rest_len -= len(buf)
            if last:
                buf = last + buf
            arr = buf.split(separator)
            last = arr.pop()
            for item in arr:
                yield item
        #arr = buf = header = headers = value = None
        ## check content length
        if rest_len != 0:
            raise Http400BadRequest("wrong content length.")
        ## handle last item
        last_line = "\r\n--%s--\r\n" % self.boundary
        if not last.endswith(last_line):
            raise Http400BadRequest("invalid last boundary.")
        yield last[:-len(last_line)]


class UploadedFile(object):

    def __init__(self, filename, content_type):
        #if filepath is None:
        #    pass
        self.filename = filename
        self.content_type = content_type
        self.filepath = None

    def open(self, filepath=None):
        self.filepath = filepath or self.new_filepath()
        return open(self.filepath, 'wb')

    def new_filepath(self):
        dir = config.upload_file_dir
        if not dir:
            raise ValueError("'config.upload_file_dir' should be configured.")
        return os.path.join(dir, random_hexdigest())

    def read(self):
        f = open(self.filepath, 'rb')
        try:     s = f.read()
        finally: f.close()
        return s

    def rename(self, new_filepath):
        os.rename(self.filepath, new_filepath)
        #self.filepath = new_filepath

    def unlink(self):
        if self.filepath:
            try:
                os.unlink(self.filepath)
            except OSError:
                pass

    def __del__(self):
        self.unlink()

    def __repr__(self):
        names = ('filename', 'content_type', 'filepath')
        s = object.__repr__(self)
        b = [s[:-1], ':']
        d = self.__dict__
        b.extend([ ' %s=%r' % (k, d[k]) for k in names if k in d ])
        b.append(s[-1])
        return ''.join(b)



###
### session
###
random = hashlib = base64 = pickle = None    # lazy import

class Session(object):

    def __init__(self, request, response):
        #:* takes request and response objects
        self.request  = request
        self.response = response
        self.values = {}
        #self.__getitem__ = self.values.__getitem__
        #self.__setitem__ = self.values.__setitem__
        #self.get = self.values.get
        #self.__contains__ = self.values.__contains__

    def destroy(self):
        self.values.clear()
        self.__dict__.clear()

    def get(self, key, default=None):
        #:* returns corresponding value in self.values
        #:* if key not found then returns default value
        return self.values.get(key, default)

    def __getitem__(self, key):
        #:* returns corresponding value in self.values
        #:* if key is not found then raises KeyError
        return self.values[key]

    def __setitem__(self, key, val):
        #:* sets corresponding value into self.values
        self.values[key] = val

    def __contains__(self, key):
        #:* returns True if key is in self.values
        #:* returns False if key is not in self.values
        return key in self.values

    def pop(self, key, default=UNDEFINED):
        if default is UNDEFINED:
            return self.values.pop(key)
        else:
            return self.values.pop(key, default)

    def set_id(self, id):
        #:* sets session id
        self.id = id
        self.values['_id'] = id

    def save(self):
        raise NotImplementedError("%s.save(): not implemented yet." % self.__class__.__name__)

    def clear(self):
        self.values.clear()
        self.values['_id'] = self.id

    def expire(self):
        raise NotImplementedError("%s.expire(): not implemented yet." % self.__class__.__name__)

    @staticmethod
    def new_id():
        #:* returns new session id
        #return urandom_hexdigest()   # 40 bytes
        return random_hexdigest()     # 40 bytes
        ## don't use base64 because some filesystems are case-insensitive!
        #return urandom_base64()      # 40 bytes

    @staticmethod
    def is_valid_id(sid):
        global _session_id_rexp
        if not _session_id_rexp: _session_id_rexp = re.compile(r'^[0-9a-f]+$')   # for hexdigest
        #if not _session_id_rexp: _session_id_rexp = re.compile(r'^[-\w]+$')     # for base64
        return isinstance(sid, str) and _session_id_rexp.match(sid) and len(sid) == 40

_session_id_rexp = None    # lazy compilation


class CookieSession(Session):

    cookie_name    = '_sess'
    cookie_path    = None
    cookie_domain  = None
    cookie_expires = None
    cookie_secure  = None

    #def __init__(self, request, response, cookie_name=None):
    #    Session.__init__(self, request, response)
    #    if cookie_name    is not None: self.cookie_name    = cookie_name
    #    #if cookie_path    is not None: self.cookie_path    = cookie_path
    #    #if cookie_domain  is not None: self.cookie_domain  = cookie_domain
    #    #if cookie_expires is not None: self.cookie_expires = cookie_expires
    #    #if cookie_secure  is not None: self.cookie_secure  = cookie_secure
    def __init__(self, request, response):
        Session.__init__(self, request, response)
        #:* creates a cookie object
        cookie_val = request.cookies.get(self.cookie_name) or ''
        self.cookie = COOKIE(self.cookie_name, cookie_val, self.cookie_path, self.cookie_domain, self.cookie_expires, self.cookie_secure)

    def expire(self):
        #:* sets 'expires' attr of cookie object to old timestamp
        #self.cookie_expires = time.gmtime(0)
        self.cookie.expires = time.gmtime(0)
        #self.save()


class FileStoreSession(CookieSession):

    depth = 2
    _expired = False

    @classmethod
    def init_session_dir(cls, dir=None):
        if dir is None: dir = config.session_file_dir
        if not dir:
            raise ValueError("%s.dir is not configured." % cls.__name__)
        _join, _isdir, _mkdir = os.path.join, os.path.isdir, os.mkdir
        _isdir(dir) or _mkdir(dir)
        #chars = 'abcdefghijklmnopqrstuvwxyz0123456789-_'  # for base64
        #assert len(chars) == 26 + 10 + 2
        chars = '0123456789abcdef'        # for hexdigest
        names = [ c1 + c2 for c1 in chars for c2 in chars ]
        def mkdirs(dir, depth):
            for name in names:
                child = _join(dir, name)
                _mkdir(child)
                if depth > 1:
                    mkdirs(child, depth - 1)
        mkdirs(dir, config.session_file_depth)

    def __init__(self, request, response):
        CookieSession.__init__(self, request, response)
        sid = self.cookie.value
        if not sid:
            fpath = None
        elif not self.is_valid_id(sid):
            fpath = None
            if config.logging:
                _get_logger().warn('invalid session id: %r' % sid)
        else:
            fpath = self._get_fpath(sid)
            if not os.path.isfile(fpath):
                if config.logging:
                    _get_logger().warn('session file not found: %r' % fpath)
                fpath = None
        #:* if session file exists then restore session id from cookie and session values from session file
        if fpath:
            self._fpath = fpath
            self.values = self._load_values(fpath)
            self.id     = sid
        #:* if session file doesn't exist then session id is not restored from cookie and values is empty
        else:
            self._fpath = None
            self.values = {}
            self.id     = self.cookie.value = self.new_id()

    def save(self):
        #:* if session is expired then do nothing
        if not self._expired:
            if not self._fpath:
                #:* [b] if k8.config.session_file_dir is not specified then raise ValueError
                #:* [b] if directory doesn't exist then create it recursively
                self._fpath = self._get_fpath(self.id, True)
            #:* creates session file
            self._dump_values(self._fpath, self.values)
        self.response.add_cookie(self.cookie)
        pass

    def expire(self):
        CookieSession.expire(self)
        #self.id = None
        self._expired = True
        #:* remove session file
        if self._fpath:
            os.unlink(self._fpath)

    def _get_fpath(self, sid, forced=False,
                        _join = os.path.join, _isdir=os.path.isdir):
        #:* [p] if k8.config.session_file_dir is not specified then raise ValueError
        dir = config.session_file_dir
        if not dir:
            raise ValueError("'config.session_file_dir' should be set.")
        #:* [p] if directory doesn't exist then create it recursively
        depth = config.session_file_depth
        #for ch in sid[:depth]
        #    s = ch
        for i in xrange(0, 2 * depth, 2):
            s = sid[i:i+2].lower()
            dir = _join(dir, s)
            if forced and not _isdir(dir):
                os.mkdir(dir)
        fpath = _join(dir, sid)
        return fpath

    def _load_values(self, fpath):
        global pickle
        if not pickle: import cPickle as pickle
        #:* load dumped file and returns undumped values
        f = open(fpath, 'rb')
        try:
            values = pickle.load(f)
        except Exception, ex:
            if config.logging:
                _get_logger().error('%s: %s' % (fpath, ex))
            values = {}
        finally:
            f.close()
        return values

    def _dump_values(self, fpath, values):
        global random, pickle
        if not random: import random
        if not pickle: import cPickle as pickle
        #:* saves dumped data into file.
        #:* dumped file is loadable by _load_values().
        tmppath = fpath + str(random.random())
        f = open(tmppath, 'wb')
        ok = False
        try:
            pickle.dump(values, f, protocol=2)
            ok = True
        except Exception, ex:
            if config.logging:
                _get_logger().error('%s: %s' % (fpath, ex))
            raise
        finally:
            f.close()
            if ok:
                os.rename(tmppath, fpath)
            elif os.path.isfile(tmppat):
                os.unlink(tmppath)


class CookieStoreSession(CookieSession):

    def __init__(self, request, response):
        CookieSession.__init__(self, request, response)
        #:* if secret_key is not specified then raises exception
        if not config.secret_key:
            raise ValueError("'config.secret_key' should be set.")
        #:* restore session id and values from cookie value
        #:* create empty values if session cookie is not found
        self.values = self._build_values(self.cookie.value)
        self.id = self.values.get('_id')

    def save(self):
        #:* sets cookie value
        self.cookie.value = self._dump_values(self.values)
        self.response.add_cookie(self.cookie)

    def _build_values(self, cookie_val):
        values = cookie_val and self._load_values(cookie_val) or None
        if values:
            errmsg = self._check_values(values)
            if errmsg:
                #logger.info(errmsg)
                values = None
        if not values:
            values = self._new_values()
        self._update_values(values)
        return values

    def _check_values(self, values):
        if not values.get('_id'):
            return "'_id' is not found in session cookie."
        return None

    def _new_values(self):
        return {
            '_id': self.new_id(),
        }

    def _update_values(self, values):
        return values

    def _load_values(self, cookie_val):
        global base64, pickle
        if not base64: import base64
        if not pickle: import cPickle as pickle
        #:* if cookie value is invalid then return None
        chksum, encoded = cookie_val.split(':', 1)
        if chksum != self._chksum(encoded):
            return None
        #:* load values from str
        serialized = base64.urlsafe_b64decode(encoded)
        values = pickle.loads(serialized)
        return values

    def _dump_values(self, values):
        global base64, pickle
        if not base64: import base64
        if not pickle: import cPickle as pickle
        #:* dumps values into str
        serialized = pickle.dumps(values, protocol=2)
        encoded = base64.urlsafe_b64encode(serialized)
        chksum = self._chksum(encoded)
        return '%s:%s' % (chksum, encoded)

    def _chksum(self, s):
        global hashlib
        if not hashlib: import hashlib
        return hashlib.sha1(s + config.secret_key).hexdigest()

SESSION = CookieStoreSession



###
### router
###

class Router(object):

    def __init__(self):
        self.mappings = []
        self._mapping_dict = {}  # key: str, val: (dict, klass)
        self._mapping_list = []  # list of (path, rexp, dict, klass)
        self.base_path = None
        self._base_path_rexp = None

    def set_base_path(self, base_path):
        #:* set base_path into self.base_path
        self.base_path = base_path
        #:* if base_path is a pattern then compile and save it
        self._base_path_rexp = is_rexp(base_path) and re.compile(base_path) or None
        #
        has_lazy = False
        for path, kwargs, handler_class in self.mappings:
            #:* sets path function and request method to each action method
            if kwargs:
                for req_method, func in kwargs.iteritems():
                    self._config_action_func(func, base_path + path, req_method)
            #:* if handler class is string then create OnDemandLoader object with callback
            if handler_class:
                if isinstance(handler_class, str):
                    has_lazy = True
                elif getattr(handler_class, 'router', None):
                    handler_class.router.set_base_path(base_path + path)
        if has_lazy:
            self._set_ondemand_loader(base_path)

    def _set_ondemand_loader(self, base_path):
        for items in self._mapping_list:
            path, rexp, kwargs, handler_class = items
            if handler_class and isinstance(handler_class, str):
                class_name = handler_class
                def callback(klass, _items=items, _path=base_path+path):
                    if type(klass) is not type:
                        raise ValueError("%s: class object expected but got %r." % (class_name, klass))
                    _items[-1] = klass
                    if getattr(klass, 'router', None):
                        klass.router.set_base_path(_path)
                items[-1] = OnDemandLoader(class_name, callback)

    def map(self, path, **kwargs):
        #:* store path and kwargs
        self.mappings.append((path, kwargs, None))
        #:* if path arg is a pattern then appends into self._mapping_list
        rexp = is_rexp(path) and re.compile(path) or None
        if rexp:
            self._mapping_list.append([path, rexp, kwargs, None])
        #:* if path arg is not a pattern then appends into self._mapping_dict
        else:
            self._mapping_dict[path] = [kwargs, None]
        #:* if path is '/' then prepares to redirect when empty path
        if path == '/':
            d = {'GET': 301}
            #self.mappings.append(('', d, None))
            self._mapping_dict.setdefault('', [d, None])
        #:* returns self
        return self

    def mount(self, path, handler_class):
        #:* store path and handler_class
        self.mappings.append((path, None, handler_class))
        #:* if path arg is not a pattern then compile and appends to self._mapping_list
        #:* if path arg is not a pattern then appends None to self._mapping_list
        rexp = is_rexp(path) and re.compile(path) or None
        self._mapping_list.append([path, rexp, None, handler_class])
        #:* returns self
        return self

    def route(self, req_path, req_method):
        #:* if base path is not set then raises error
        rest_path, args = self._match_to_base_path(req_path)
        #if not rest_path.startswith('/'):
        #    rest_path = '/' + rest_path
        ## find kwargs and handler_class
        kwargs, handler_class, args2 = self._find_kwargs_or_handler_class(rest_path)
        if args2:
            if args: args += args2
            else:    args = args2
        #:* if matched path is found then returns function and arguments
        if kwargs:
            func = kwargs.get(req_method) or kwargs.get('ALL')
            if func:
                return (func, args)
            #:* if ALL is specified then returns matched function in any method
            func = kwargs.get('ALL')
            if func:
                return (func, args)
            #:* if method is not allowed then raises Http405MethodNotAllowed
            #return (False, args)    # method not allowd
            raise Http405MethodNotAllowed(req_method)
        #:* if matched handler class is found then returns it and args
        elif handler_class:
            #:* if mapped object is OnDemandLoader then call load()
            if type(handler_class) is OnDemandLoader:
                handler_class = handler_class.load()
            return (handler_class, args)
        #:* if not matched to function nor class then raises Http404NotFound
        else:
            #return (None, args)         # not found
            raise Http404NotFound(req_path)

    def _match_to_base_path(self, req_path):
        #:* returns rest_path and args in case base_path is a pattern
        rexp = self._base_path_rexp
        if rexp:
            m = rexp.match(req_path)
            assert m
            args = m.groups()
            rest_path = req_path[m.end():]
        #:* returns rest_path and args in case base_path is not a pattern
        else:
            base_path = self.base_path
            #:* if base_path is not set then raises error
            if not base_path:
                raise ValueError("base path is not set to router object (do you forget to mount handler class?)")
            assert req_path.startswith(base_path)
            rest_path = req_path[len(base_path):]
            args = ()
        return rest_path, args

    def _find_kwargs_or_handler_class(self, rest_path):
        args = None
        #:* if rest_path is in self._mapping_dict then returns corresponding values
        if rest_path in self._mapping_dict:
            kwargs, handler_class = self._mapping_dict[rest_path]
        #:* if rest_path is not in self._mapping_dict then search self._mapping_list
        else:
            rest_path_len = len(rest_path)
            for path, rexp, kwargs, handler_class in self._mapping_list:
                if rexp:
                    m = rexp.match(rest_path)
                    if m and (kwargs and m.end() == rest_path_len or handler_class):
                        args = m.groups()
                        #if args:  args += m.groups()
                        #else:     args = m.groups()
                        break
                else:
                    if rest_path.startswith(path):
                        break
            #:* if not matched then returns Nones
            else:
                kwargs = handler_class = None
        return (kwargs, handler_class, args)

    @staticmethod
    def _config_action_func(func, path, req_method,
                            _path_func_rexp=re.compile(r'\(.*?\)')):
        #:* sets request method
        func.method = req_method
        #:* if path is specified then sets path() function
        if path:
            format = _path_func_rexp.sub('%s', path)
            n = format.count('%s')
            if   n == 0:  func.path = lambda: format
            elif n == 1:  func.path = lambda a: format % (a, )
            elif n == 2:  func.path = lambda a, b: format % (a, b)
            elif n == 3:  func.path = lambda a, b, c: format % (a, b, c)
            else:         func.path = lambda *args: format % args
        #:* if path is not specified then path() function is empty
        else:
            func.path = lambda: path
        #:* sets hidden_tag() function which returns hidden tag only if request method is not GET nor POST
        if req_method in ('GET', 'POST'):
            func.hidden_tag = lambda: ''
        else:
            func.hidden_tag = lambda: '<input type="hidden" name="_method" value="%s" />' % req_method


ROUTER = Router


class RootRouter(Router):     ## TODO: necessary?

    __super = Router

    def map(self, path, **kwargs):
        #:* configure each action functions
        for req_method, func in kwargs.iteritems():
            self._config_action_func(func, path, req_method)
        return self.__super.map(self, path, **kwargs)

    def mount(self, path, handler_class):
        #:* if handler_class has router then set path as base_path of it
        if hasattr(handler_class, 'router'):
            handler_class.router.set_base_path(path)
        return self.__super.mount(self, path, handler_class)

    def _match_to_base_path(self, path):
        #:* returns passed path and an empty tuple
        return (path, ())


class OnDemandLoader(object):

    def __init__(self, name, callback=None):
        self.name = name
        self.callback = callback

    def load(self):
        #:* loads object with importing module
        obj = _import(self.name)
        #:* if callback is specified then call it with loaded object
        if self.callback:
            self.callback(obj)
        #:* returns loaded object (typically class object)
        return obj



###
### handler
###

class Handler(object):

    router = None
    _current = None

    def __init__(self, request, response):
        #:* takes request and response
        self.request  = request
        self.response = response

    def before(self):
        pass

    def after(sef):
        pass

    def destroy(self):
        """called by Handler.handle() to release circular reference()."""
        pass

    def invoke(self, unbound_func, args=()):
        #self.__class__._current = self
        self.action = unbound_func
        try:
            #:* calls before() before invoking action method
            self.before()
            #:* args are passed to action method
            #:* returns result of action method
            return unbound_func(self, *args)
        finally:
            #:* calls after() after action method is invoked, even when error raised
            self.after()
            #:* calls destroy() method to release circular reference
            self.destroy()
            #self.__class__._current = None

    @classmethod
    def handle(cls, request, response):
        #:* if request method is POST and _method param is specified then use it as request method value
        method = request.method
        if method == 'POST':
            request.method = method = request.params.get('_method') or method
        #:* if request path is not matched then raises Http404NotFound
        #:* if request path is matched but method is not matched then raises Http405MethodNotAllowed
        mapped, args = cls.router.route(request.path, method)
        #:* if request is matched to other handler class then delegates request and response to it
        if hasattr(mapped, 'handle'):    # tipically handler class
            return mapped.handle(request, response)
        #:* if 301 is mapped then raises Http301MovedPermanently with current request path and query string
        elif mapped == 301:
            qs = request.env.get('QUERY_STRING')
            location = request.path + (qs and '/?' + qs or '/')
            raise Http301MovedPermanently(location)
        #:* if request is matched to unbond function then mapped then invokes it with new instance object
        else:
            unbound_func = mapped
            obj = cls(request, response)
            return obj.invoke(unbound_func, args)



###
### controller
###

class Controller(Handler):

    #_engine = tenjin.Engine(path=['views'], postfix='.pyhtml', layout=':_layout')
    _engine = None    # SHOULD BE CONFIGURED BY DEVELOPER
    _last_console = None   # required for ExceptionRenderer

    router = None

    def __init__(self, *args):
        #:* calls parent __init__() method
        Handler.__init__(self, *args)
        #:* creates context object and adds self to it
        self.context = {'self': self}

    def __getitem__(self, key):
        #:* returns context data
        return self.context[key]

    def __setitem__(self, key, value):
        #:* sets context data
        self.context[key] = value

    def destroy(self):
        self.context.clear()
        #self.request.destroy()    # called from MainApplication#__call__()
        #self.response.destroy()   # called from MainApplication#__call__()
        d = self.__dict__
        if 'session' in d:  d.get('session').destroy()
        if 'csrf'    in d:  d.get('csrf').destroy()
        #if 'console' in d:  d.get('console').destroy()
        Controller._last_console = d.get('console')  # required for ExceptionRenderer
        d.clear()

    def render(self, template_name, **kwargs):
        return self._engine.render(template_name, self.context, globals=sys._getframe(1).f_globals, **kwargs)  # for Tenjin

    CSRF_SKIP_METHODS = set(['GET', 'HEAD', 'OPTIONS'])

    def before(self):
        Handler.before(self)
        #:* if request method is not GET, HEAD nor HEAD then checks CSRF token forcedly
        if self.request.method not in self.CSRF_SKIP_METHODS:
            self.csrf.protect()

    def after(self):
        Handler.after(self)
        #:* if session object exists then save it
        session = self.__dict__.get('session')
        if session:
            session.save()

#    def _get_session(self):
#        session = self.__dict__.get('session')
#        if not session:
#            session = SESSION(self.request, self.response)
#            #setattr(self, 'session', session)
#            self.__dict__['session'] = session
#        return session
#
#    session = property(_get_session)
#
#    def _get_csrf(self):
#        csrf = self.__dict__.get('csrf')
#        if not csrf:
#            csrf = CSRF(self.request, self.response)
#            #setattr(self, 'csrf', csrf)
#            self.__dict__['csrf'] = csrf
#        return csrf
#
#    csrf = property(_get_csrf)
#
#    def _get_console(self):
#        console = self.__dict__.get('console')
#        if not console:
#            console = CONSOLE()
#            #setattr(self, 'console', console)
#            self.__dict__['console'] = console
#        return console
#
#    console = property(_get_console)

    def _def_getter(key, builder):
        #:* helps to define properties
        def _getter(self, _key=key, _builder=builder):
            obj = self.__dict__.get(_key)
            if not obj:
                self.__dict__[_key] = obj = _builder(self)
            return obj
        return _getter

    session = property(_def_getter('session', lambda self: SESSION(self.request, self.response)))
    csrf    = property(_def_getter('csrf',    lambda self: CSRF(self.request, self.response)))
    console = property(_def_getter('console', lambda self: CONSOLE()))

    def redirect_to(self, location):
        #:* raises Http302Found with location
        raise Http302Found(location)

    def redirect_permanently_to(self, location):
        #:* raises Http301MovedPermanently with location
        raise Http301MovedPermanently(location)

    def not_found(self, request_uri=None):
        #:* if request_uri is not specified then reports current request uri
        if request_uri is None: request_uri = self.request.uri
        #:* raises Http404NotFound
        raise Http404NotFound(request_uri)

    def url_path(self, arg, **kwargs):
        #:* if current class doesn't have router object then raises error
        if not self.router:
            raise ValueError("%s.router is not configured." % (self.__class__.__name__, ))
        #:* builds url path from arg
        path = self.router.base_path
        if arg:
            path += arg
        #elif '/' in self.router._mapping_dict:
        #    path += '/'
        #:* kwargs are regarded as query string
        if kwargs:
            path = '%s?%s' % (path, d2qs(kwargs))
        return path

CONTROLLER = Controller


class Csrf(object):

    _renewed = False

    def __init__(self, request, response):
        #self.handler = handler
        self.request = request
        self.response = response
        self.token = self.load_token()
        if not self.token:
            self.renew(True)

    def destroy(self):
        self.__dict__.clear()

    def load_token(self):
        #return self.handler.session.get('_csrf')  # slow
        return self.request.cookies.get('_csrf')   # fast

    def store_token(self, token):
        #self.handler.session['_csrf'] = token     # slow
        self.response.add_cookie('_csrf', token)   # fast
        return self

    def renew(self, forcedly=False):
        if forcedly or not self._renewed:
            self.token = self.new_token()
            self.store_token(self.token)
            self._renewed = True
        return self

    @staticmethod
    def new_token():
        return random_hexdigest()

    def hidden_tag(self):
        return '<input type="hidden" name="_csrf" value="%s" />' % self.token

    def check(self):
        assert self.token
        return self.token == self.request.params.get('_csrf')

    def protect(self):
        if not self.check():
            raise Http403Forbidden("Csrf token check failed.")

CSRF = Csrf


pprint = None   # lazy import

class Console(object):

    def __init__(self):
        self.buf = []

    def destroy(self):
        self.__dict__.clear()

    def log(self, message):
        if message and not message.endswith("\n"):
            message += "\n"
        self.buf.append(message)

    def pp(self, expr):
        global pprint
        if not pprint: import pprint
        if not isinstance(expr, basestring):
            raise ValueError('console.pp(): string expression expected but got %s.' % type(expr))
        frame = sys._getframe(1)
        val = eval(expr, frame.f_globals, frame.f_locals)
        file, line = os.path.basename(frame.f_code.co_filename), frame.f_lineno
        self.log('(%s:%s) %s=%s\n' % (file, line, expr, pprint.pformat(val)))

    def __str__(self):
        return ''.join(self.buf)

CONSOLE = Console



###
### wsgi app
###

_CGIHandler = None   # lazy import

class Application(object):

    def __call__(self, env, start_response):
        #:* creates request and response objects
        req = REQUEST(env)
        res = RESPONSE()
        #:* handles request and get content
        content = self.handle(req, res)   # may raise Exception except HttpException
        #:* converts content into iterable object
        if isinstance(content, str):
            ret = [content]
        elif isinstance(content, unicode):
            ret = [content.encode(res.encoding or 'utf-8')]
        else:
            ret = content or ['']
        #:* calls start_response
        status  = res.get_status_str()
        headers = res.get_headers()
        start_response(status, headers)
        #:* releases request and response objects
        #req.destroy()
        #res.destroy()
        if hasattr(req, 'destroy'): req.destroy()
        if hasattr(res, 'destroy'): res.destroy()
        #:* returns iterable object
        return ret

    def handle(self, req, res):
        try:
            handler = self.find_handler(req)
            content = handler(req, res)
        except HttpException, ex:
            content = ex.handle(req, res)
        return content

    def find_handler(self, req):
        raise NotImplementedError("%s#find_handler(): not implemented yet." % self.__class__.__name__)

    def run(self, debug=False):
        #:* if debug is False then wraps by ProductionMiddleware
        #:* if debug is True then wraps by DevelopmentMiddleware
        app = self
        app = debug and DevelopmentMiddleware(app) \
                    or  ProductionMiddleware(app)
        #:* invokes wsgiref.handlers.CGIHandler().run(app)
        global _CGIHandler
        if not _CGIHandler: from wsgiref.handlers import CGIHandler as _CGIHandler
        _CGIHandler().run(app)
        return app


class MainApplication(Application):

    def __init__(self):
        self.router = RootRouter()

    def map(self, path, **kwargs):
        #:* if path is None then detect it from $SCRIPT_NAME.
        if path is None: path = self.default_root_path()
        self.router.map(path, **kwargs)
        #:* returns self
        return self

    def mount(self, path, handler_class):
        #:* if path is None then detect it from $SCRIPT_NAME.
        if path is None: path = self.default_root_path()
        #:* sets base_path of handler_class automatically
        self.router.mount(path, handler_class)
        #:* returns self
        return self

    @staticmethod
    def default_root_path():
        #:* if $SCRIPT_NAME is set then returns it's dirname.
        script_name = os.environ.get('SCRIPT_NAME')
        if script_name:
            return os.path.dirname(script_name)
        #:* if $SCRIPT_NAME is not set then returns None.
        return None

    def find_handler(self, req):
        #:* if request path is not found then raises 404 not found
        #:* if request method is not matched (to mapped function) then raises 405 method not allowed
        mapped, args = self.router.route(req.path, req.method)  # may raise Http404NotFound or Http405MethodNotAllowed
        #:* sets args to request object
        req.args = args
        #:* if request is matched to mounted handler class then returns it's handle() method
        if hasattr(mapped, 'handle'):
            return mapped.handle
        #:* if request is matched to mapped action function then returns it
        return mapped


class CGIApplication(Application):

    def __init__(self, handler, **kwargs):
        self.mapping = {}
        if type(handler) is type:
            #:* if handler is class object but not subclass of Handler then raises error
            klass = handler
            if not issubclass(klass, Handler):
                raise TypeError("%s: Handler subclass is expected." % klass.__name__)
            #
            for req_method, func_name in kwargs.iteritems():
                #:* if function is not found in handler class then raises error
                unbound_func = klass.__dict__.get(func_name)
                if not unbound_func:
                    raise ValueError('%s=%r: function not found in %s class.' % (req_method, func_name, klass.__name__))
                #
                unbound_func.path = lambda *args: ''
                unbound_func.method = req_method
                unbound_func.hidden_tag = lambda: ''
                #:* if handler is Handler subclass then create new handler function
                def handler(request, response, _klass=klass, _func=unbound_func):
                    obj = _klass(request, response)
                    return obj.invoke(_func)
                handler.func_name = func_name
                self.mapping[req_method] = handler
        elif type(handler) is type(lambda: 0):
            #:* if handler is function then it will be invoked in any request method
            self.mapping['ALL'] = handler
        else:
            #:* if handler is not a function nor a class object then raises error
            raise TypeError("%r: handler should be function or Handler subclass." % (handler, ))

    def find_handler(self, req):
        #:* finds handler by request method
        handler = self.mapping.get(req.method) or self.mapping.get('ALL')
        #:* if handler is not found then raises Http405MethodNotAllowed
        if not handler:
            raise Http405MethodNotAllowed(req.method)
        req.args = ()
        #:* if handler is found then returns it
        return handler



###
### middleware
###

class Middleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, env, start_response):
        return self.app(env, start_resonse)


class ProductionMiddleware(Middleware):

    def __call__(self, env, start_response):
        try:
            return self.app(env, start_response)
        except Exception, ex:
            return self.handle_exception(ex, env, start_response)

    def handle_exception(self, ex, env, start_response):
        exc_info = sys.exc_info()
        if config.logging:
            import traceback
            arr = traceback.format_exception(*exc_info)
            _get_logger().error(''.join(arr))
        start_response('500 Internal Server Error', [('Content-Type', 'text/html')], exc_info)
        return ["<h2>500 Internal Server Error</h2>"]


class DevelopmentMiddleware(ProductionMiddleware):

    __super = ProductionMiddleware

    def _is_terminal(self):
        #return sys.stderr.isatty() and 'REMOTE_PORT' not in os.environ
        return 'REMOTE_PORT' not in os.environ

    def __call__(self, env, start_response):
        ## set dummy environment if invoked from console
        if self._is_terminal():
            if not sys.stdin.isatty():   # stdin is redirected
                s = sys.stdin.read()
                headers, body = _parse_http_request(s)
                env.update(dict(headers))
            else:
                env2 = dummy_env()
                env2.update(env)
                env = env2
        return self.__super.__call__(self, env, start_response)

    def handle_exception(self, ex, env, start_response):
        ret = self.__super.handle_exception(self, ex, env, start_response)
        return ExceptionRenderer().render(sys.exc_info())


class ExceptionRenderer(object):

    def render(self, exc_info):
        ## function to create editorkicker url
        if config.editor_schema:
            url_format = config.editor_schema + '://open?url=file://%s&line=%s'
            js = ''
        else:
            url_format = config.editorkicker_url + 'open?file=%s&line=%s'
            #js = 'editorkicker(this);return false'
            js = ''
        url = lambda file, line: url_format % (quote_plus(file), line)
        ## get traceback
        import traceback
        arr = traceback.format_exception(*exc_info)
        ## convert it into html
        rexp = re.compile(r'^  File "(.*?)", line (\d+)')
        format = '  <a href="%s" onclick="%s">File "%s", line %s</a>%s'
        buf = []
        for s in arr:
            m = rexp.match(s)
            if m:
                file, line = m.groups()
                rest = s[m.end():]
                href = url(os.path.abspath(file), line)
                buf.append(format % (h(href), h(js), h(file), line, h(rest)))
            else:
                buf.append(h(s))
        ##
        #tb = exc_info[2]
        #controller = None
        #arr = []
        #while tb:
        #    selfobj =  tb.tb_frame.f_locals.get('self')
        #    if selfobj and isinstance(selfobj, Controller):
        #        controller = selfobj
        #        #break
        #        arr.append(controller)
        #    tb = tb.tb_next
        #sys.stderr.write("\033[0;31m*** debug: controller.console.buf=%r\033[0m\n" % (controller.console.buf, ))
        #sys.stderr.write("\033[0;31m*** debug: arr=%r\033[0m\n" % (arr, ))
        #for c in arr:
        #    sys.stderr.write("\033[0;31m*** debug: c.console.buf=%r\033[0m\n" % (c.console.buf, ))
        ## context
        context = { 'ex':        exc_info[1],
                    'title':     '%s: %s' % (exc_info[0].__name__, exc_info[1].message),
                    'traceback': ''.join(buf) }
        ## return error page
        return self._render_html(context)

    def _render_html(self, context):
        buf = []; append = buf.append
        append(self.ERROR_PAGE_HEADER)
        append("<h2>%s</h2>\n" % h(context['title']))
        append("<pre>")
        append(context['traceback'])
        append("</pre>\n")
        append("<br />\n")
        append('<div class="console">\n')
        append('<strong class="console">Console:</strong>\n')
        append('''&nbsp; (try <code>self.console.pp('varname')</code> in Controller to inspect value.)\n''')
        console = Controller._last_console
        if console and str(console):
            append('<pre>%s</pre>\n' % h(str(console)))
        else:
            append('<div style="margin-top:10px"><em>(nothing)</em></div>\n')
        append('</div>\n')
        append(self.ERROR_PAGE_FOOTER)
        return ''.join(buf)

    ERROR_PAGE_HEADER = r"""<!DOCTYPE>
<html>
<head>
  <title>ERROR</title>
  <style>
    div.console {
      border: solid 1px #999;
      padding: 0px 5px;
      background: #EEE;
    }
  </style>
</head>
<body>
"""

    ERROR_PAGE_FOOTER = r"""
<p id="warning" style="color:#F00; border:solid 2px red; background:#FEE; padding: 5px 10px;">
  Warning: Editor kicker process is not started.
</p>
<script>
//  function new_xhr() {
//    if (window.XMLHttpRequest) { return new XMLHttpRequest(); }
//    else {
//      try        { return new ActiveXObject("Msxml2.XMLHTTP"); }
//      catch (ex) { return new ActiveXObject("Microsoft.XMLHTTP"); }
//    }
//  }
//  function ajax_get(url, callback) {
//    var xhr = new_xhr();
//    if (callback) {
//      var completed = 4;
//      xhr.onreadystatechange = function() {
//        if (xhr.readyState == completed) { callback(xhr); }
//      };
//    }
//    xhr.open('GET', url, true);
//    xhr.send();
//    return xhr;
//  }
//  function editorkicker(elem) {
//    var url = elem.href;
//    ajax_get(url);
//  }
</script>
<script type="text/javascript" src="%shide.js?id=warning"></script>
</body>
</html>
""" % config.editorkicker_url



###
### debug
###
_StringIO = None

def dummy_env(method='GET', path='/', qs='', body='', **kwargs):
    global _StringIO
    if not _StringIO:
        if python2: from cStringIO import StringIO as _StringIO
        if python3: from io        import StringIO as _StringIO
    #:* if qs is dict then converts it into query string
    if isinstance(qs,   dict):  qs   = d2qs(qs)
    #:* if body is dict then converts it into query string
    if isinstance(body, dict):  body = d2qs(body)
    #:* sets keys and values automatically
    env = {
        'REQUEST_METHOD'    : method,
        'PATH_INFO'         : path,
        'QUERY_STRING'      : qs,
        'REQUEST_URI'       : path + (qs and '?' + qs or ''),
        'SCRIPT_NAME'       : '',
        'CONTENT_TYPE'      : '',
        'CONTENT_LENGTH'    : '',
        'SERVER_NAME'       : 'localhost',
        'SERVER_PORT'       : '80',
        'SERVER_PROTOCOL'   : 'HTTP/1.0',
        'wsgi.input'        : _StringIO(body),
        'wsgi.errors'       : _StringIO(),
        'wsgi.version'      : (1, 0),
        'wsgi.run_once'     : True,
        'wsgi.url_scheme'   : 'http',
        'wsgi.multithread'  : False,
        'wsgi.multiprocess' : False,
    }
    #:* if request body is specified then set CONTENT_LENGTH as string
    if body:
        env['CONTENT_LENGTH'] = str(len(body))
    #:* if body is not empty and CONTENT_TYPE is not set then set it automatically
    #:* if body is not empty and CONTENT_TYPE is already set then don't change it
    if body:
        env['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
    #:* if keyword args specified then adds them into env
    env.update(kwargs)
    #:* returns dict object
    return env

def _read_http_request(input):
    i = 0
    pos = 0
    for m in re.finditer(r'.*?\r?\n', input):
        line = m.group(0).strip()
        if i == 0:
            m = re.match(r'^([A-Z]+)\s+(\S+)\s+(HTTP/1\.\d)', line)
            if not m:
                raise ValueError('%r: invalid request line.' % line)
            yield m.group(1), m.group(2), m.group(3)
        elif not line:
            pos = m.end()
            yield None
            break
        else:
            #print repr(line)
            pair = line.split(':', 1)
            if len(pair) != 2:
                raise ValueError('%r: invalid request header.' % line)
            k, v = pair
            yield k.strip(), v.strip()
        i += 1
    body = input[pos:]
    yield body

def _parse_http_request(request_str):
    header_names = {
        'Content-Type':    'CONTENT_TYPE',
        'Content-Length':  'CONTENT_LENGHT',
        'Accept':          'HTTP_ACCEPT',
        'Accept-Encoding': 'HTTP_ACCEPT_ENCODING',
        'Accpet-Language': 'HTTP_ACCPET_LANGUAGE',
        'Cookie':          'HTTP_COOKIE',
        'Host':            'HTTP_HOST',
        'Referer':         'HTTP_REFERER',
        'User-Agent':      'HTTP_USER_AGENT',
    }
    headers = []
    gen = _read_http_request(request_str)
    for req_method, req_uri, http_ver in gen:
        break
    headers.append(('REQUEST_METHOD',  req_method))
    headers.append(('REQUEST_URI',     req_uri))
    headers.append(('SERVER_PROTOCOL', http_ver))
    pos = req_uri.find('?')
    query_str = pos >= 0 and req_uri[pos+1:] or ''
    headers.append(('QUERY_STRING', query_str))
    for pair in gen:
        if pair is None:
            break
        k, v = pair
        if k in header_names:
            k = header_names[k]
        headers.append((k, v))
    for body in gen:
        break
    return headers, body


class StartResponse(object):

    def __init__(self):
        global _StringIO
        if not _StringIO:
            if python2: from cStringIO import StringIO as _StringIO
            if python3: from io        import StringIO as _StringIO
        self.status = self.headers = self.exc_info = None
        self.out = _StringIO()

    def __call__(self, status, headers, exc_info=None):
        self.status, self.headers, self.exc_info = status, headers, exc_info
        return self.out.write

    def __str__(self):
        buf = ["HTTP/1.0 %s\r\n" % self.status]
        for k, v in self.headers:
            buf.append("%s: %s\r\n" % (k, v))
        return "".join(buf)

    def __repr__(self):
        return "<StartResponse:\n  status: %r\n  headers: %r\n  exc_info: %r>\n" % \
               (self.status, self.headers, self.exc_info)

def new_start_response():
    return StartRespones()


def cgi_debug():
    def show_exception():
        ex = getattr(sys, 'last_value', None)    # not sys.exc_info()[1]
        if ex:
            write = sys.stdout.write
            write("Status: 500 Internal Server Error\r\n")
            write("Content-Type: text/html\r\n")
            write("\r\n")
            #write("500 Internal Server Error\n")
            #write("\n")
            #import traceback
            #traceback.print_exception(sys.last_type, ex, sys.last_traceback, None, sys.stdout)
            exc_info = (sys.last_type, sys.last_value, sys.last_traceback)
            html = ExceptionRenderer().render(exc_info)
            write(html)
            write("<!-- by cgi_debug() -->")
    import atexit
    atexit.register(show_exception)



###
### form
###

class FormHelper(object):

    __globals__ = globals()
    buf = None

    def __init__(self, params, errors, buf=None):
        self.params = params    # k8.Params object
        self.errors = errors    # k8.FormErrors object
        self.buf    = buf       # '_buf' object of tenjin
        self._setup()

    def _setup(self):
        ##//:* hacks to get escape() and to_str() functions into globals
        #__globals__ = self.__globals__
        #if not ('escape' in __globals__ and 'to_str' in __globals__):
        #    frame = sys._getframe(2)
        #    f_globals = frame.f_globals
        #    func = f_globals.get('escape')
        #    if func: __globals__['escape'] = func
        #    func = f_globals.get('to_str')
        #    if func: __globals__['to_str'] = func
        pass

    def get_value(self, key):
        return self.params.get(key)

    #def _def_input_control(type_attr):
    #    def _input_control(self, key, label, desc=None, _type_attr=type_attr, **kwargs):
    #        def _control():
    #            v = self.params.get(key) or ''
    #            return '<input type="%s" name="%s" value="%s"%s />' % \
    #                       (_type_attr, key, escape_html(v), dict2attr(kwargs))
    #        return self._form_control(_control, key, label, desc, kwargs)
    #    return _input_control
    #
    #text     = _def_input_control('text')
    #password = _def_input_control('password')

    def text(self, key, label, desc=None, **kwargs):
        #:* returns (or prints) text field tag.
        #:* if error exists then prints error message.
        def _control():
            v = self.params.get(key) or ''
            return '<input type="text" name="%s" value="%s"%s />' % (key, escape_html(v), dict2attr(kwargs))
        return self._form_control(_control, key, label, desc, kwargs)

    def password(self, key, label, desc=None, **kwargs):
        #:* returns (or prints) password field tag.
        #:* if error exists then prints error message.
        def _control():
            v = self.params.get(key) or ''
            return '<input type="password" name="%s" value="%s"%s />' % (key, escape_html(v), dict2attr(kwargs))
        return self._form_control(_control, key, label, desc, kwargs)

    def file(self, key, label, desc=None, **kwargs):
        #:* returns (or prints) file field tag.
        #:* if error exists then prints error message.
        def _control():
            return '<input type="file" name="%s"%s />' % (key, dict2attr(kwargs))
        return self._form_control(_control, key, label, desc, kwargs)

    def textarea(self, key, label, desc=None, **kwargs):
        #:* returns (or prints) textarea tag.
        #:* if error exists then prints error message.
        def _control():
            v = self.get_value(key) or ''
            return '<textarea name="%s"%s>%s</textarea>' % (key, dict2attr(kwargs), escape_html(v))
        return self._form_control(_control, key, label, desc, kwargs)

    def select(self, key, label, desc=None, items=None, blank='-', **kwargs):
        #:* returns (or prints) select tag and option tags.
        #:* if error exists then prints error message.
        def _control():
            current = self.get_value(key)
            sb = []
            append = sb.append
            append('<select name="%s"%s>\n' % (key, dict2attr(kwargs)))
            if blank is not None:
                append('  <option value="">%s</option>\n' % escape_html(blank or ''))
            if items:
                for value, label in items:
                    s = str(value) == current and ' selected="selected"' or ''
                    append('  <option value="%s"%s>%s</option>\n' % (value, s, escape_html(label), ))
            append('</select>')
            return ''.join(sb)
        return self._form_control(_control, key, label, desc, kwargs)

    def radios(self, key, label, desc=None, items=None, sep='', **kwargs):
        #:* returns (or prints) radio button tags.
        #:* if error exists then prints error message.
        def _control():
            current = self.get_value(key)
            sb = []
            append = sb.append
            for value, label in items:
                s = str(value) == current and ' checked="checked"' or ''
                append('<label><input type="radio" name="%s" value="%s"%s>%s</label>%s\n' % \
                           (key, escape_html(value), s, escape_html(label), sep, ))
            return ''.join(sb)
        return self._form_control(_control, key, label, desc, kwargs)

    def _start_form_control(self, label, classattr):
        cl = classattr
        #return '<dt%s>%s</dt>\n<dd%s>\n' % (cl, label, cl)
        return '<tr>\n <th%s>%s</th>\n <td%s>\n' % (cl, label, cl)

    def _end_form_control(self):
        #return '</dd>\n'
        return ' </td>\n</tr>\n'

    def _form_class_attr(self, errmsg, kwargs):
        #:* if errmsg exists then returns class attr string
        #:* if errmsg doesn't exist then returns empty string
        return errmsg and ' class="has-error"' or ''

    def _form_control(self, _control, key, label, desc, kwargs):
        errmsg = self.errors and self.errors.get(key) or ''
        cl = self._form_class_attr(errmsg, kwargs)
        #:* if self.buf is specified then appends output to it
        buf = self.buf
        if buf is None: buf = []
        a = buf.append
        a(self._start_form_control(label, cl))
        a(    '  <span%s>%s</span>\n' % (cl, _control()))
        if errmsg:
            a('  <div class="error-msg">%s</div>\n' % escape_html(errmsg))
        if desc:
            a('  <div class="desc"><em>(%s)</em></div>\n' % desc)
        a(self._end_form_control())
        #:* if self.buf is specified then returns empty string
        #:* if self.buf is not specified then returns output string
        return self.buf is None and ''.join(buf) or ''

    def to_hidden_tags(self):
        #:* converts params into hidden tags.
        format = '<input type="hidden" name="%s" value="%s" />'
        params = self.params
        buf = []; a = buf.append
        for k in params:
            if k.startswith('_'):
                continue
            v = params[k]
            if v.endswith('[]'):
                assert isinstance(v, list)
                arr = v
                for v in arr:
                    a(format % (k, escape_html(v), ))
            else:
                a(format % (k, escape_html(v), ))
        return "\n".join(buf)


class FormErrors(object):

    def __init__(self):
        self.list = []
        self.dict = {}

    def get(self, key):
        return self.dict.get(key)

    def __getitem__(self, key):
        return self.dict[key]

    def __setitem__(self, key, val):
        self.list.append((key, val))
        self.dict[key] = val

    def __iter__(self):
        return self.list.__iter__()

    def __contains__(self, key):
        return key in self.dict

    def __len__(self):
        return len(self.list)

    def __nonzero__(self):
        return bool(self.list)

    def clear(self):
        self.list[:] = ()
        self.dict.clear()

    def __del__(self):
        self.clear()


class FormValidator(object):

    def __init__(self, params, errors=None):
        self.params = params
        self.errors = errors or FormErrors()

    def ok(self):
        errors = self.validate()
        return len(self.errors) == 0

    def validate(self):
        #self.errors = FormErrors()
        self.values = {}
        self.validate_params()
        #if len(self.errors) == 0:
        #    return None
        return self.errors

    def validate_params(self):
        self.validate__name()
        self.validate__age()

    def validate__name(self):
        k = 'name'
        self.params[k] = v
        v = self.params.get(k, '').strip()
        if not self.chk_required(k, v): return False
        if not self.chk_max_length(k, v, 32): return False
        self.values[k] = v
        return True

    def validate__age(self):
        k = 'age'
        v = self.params.get(k, '').strip()
        self.params[k] = v
        if not v: return True
        if self.chk_int_type(k, v): return False
        v = int(v)
        if self.chk_range(k, v, 0, 100): return False
        self.values[k] = v
        return True

    def chk_required(self, k, v, message='Required.'):
        if not v:
            self.errors[k] = message
            return False
        return True

    def chk_max_length(self, k, v, max, message='Too long (>%s).'):
        if len(v) > max:
            self.errors[k] = (message, max)
            return False
        return True

    def chk_min_length(self, k, v, min, message='Too short (<%s).'):
        if len(v) < min:
            self.errors[k] = (message, min)
            return False
        return True

    def chk_int_type(self, k, v, message='Integer required.'):
        try:
            int(v)
        except ValueError:
            self.errors[k] = message
            return False
        return True

    def chk_float_type(self, k, v, message='Float required.'):
        try:
            float(v)
        except ValueError:
            self.errors[k] = message
            return False
        return True

    def chk_max_value(self, k, v, max, message='Too large (>%s).'):
        if v > max:
            self.errors[k] = (message, max)
            return False
        return True

    def chk_min_value(self, k, v, min, message='Too small (<%s).'):
        if v < min:
            self.errors[k] = (message, min)
            return False
        return True

    def chk_range(self, k, v, min, max, message='Not in range (%s to %s).'):
        if v < min or max < v:
            self.errors[k] = (message, min, max)
            return False
        return True

    def chk_pattern(self, k, v, pattern, message='Invalid pattern (%s).', _dict={}):
        if isinstance(pattern, basestring):
            rexp = _dict.get(rexp) or re.compile(pattern)
        else:
            rexp = pattern
        if not rexp.search(v):
            self.errors[k] = (message, pattern)
            return False
        return True

    def chk_file_required(self, k, v, message="File required."):
        if not v:
            self.errors[k] = message
            return False
        return True

    def chk_filename_required(self, k, v, message="Filename required."):
        if not v.filename:
            self.errors[k] = message
            return False
        return True

    def chk_filename_suffix(self, k, v, suffix=(), message="Unsupported suffix."):
        if not v.filename.endswith(suffix):
            self.errors[k] = message
            return False
        return True

    def chk_content_type(self, k, v, cont_types=(), message="Unsupported content type."):
        if v.content_type not in cont_types:
            self.errors[k] = message
            return False
        return True


class Form(FormValidator):

    prefix = ''

    def __init__(self, params, errors=None):
        #if not isinstance(params, PARAMS):
        #    d = params.__dict__
        #    params = {}
        #    for k in d:
        #        params[prefix + k] = d[k]
        if errors is None: errors = FormErrors()
        FormValidator.__init__(self, params, errors)
        #FormHelper.__init__(self, params, errors)
        self.values = {}

    def get_values(self, prefix=None):
        if not prefix:
            return self.values
        values = {}
        pos = len(prefix)
        for k in self.values:
            if k.startswith(prefix):
                values[k[pos:]] = self.values[k]
        return values


###
### component
###

class Paginator(object):

    size  = 20
    label_prev  = '&lt;'
    label_next  = '&gt;'
    label_first = '&lt;&lt;'
    label_last  = '&gt;&gt;'

    def __init__(self, count, current, size=None):
        self.count = count
        self.current = int(current)
        if size is None:
            size = self.size
        else:
            self.size = size = int(size)
        self.page_count = count / size + (count % size and 1 or 0)
        #self.page_count = math.ceil(float(count) / size)

    def is_first(self):
        return self.current == 1

    def is_last(self):
        return self.current == self.page_count

    def has_prev(self):
        return self.current > 1

    def has_next(self):
        return self.current < self.page_count

    def index_range(self):
        return ((self.current - 1) * self.size, self.current * self.size - 1)

    def offset(self):
        return (self.current - 1) * self.size

    def limit(self):
        return self.offset(), self.size

    def render(self, url_path):
        current = self.current
        buf = []
        add = buf.append
        self._render_begin(url_path, add)
        self._render_backward(url_path, add)
        self._render_pagination(url_path, add)
        self._render_forward(url_path, add)
        self._render_end(url_path, add)
        return "\n".join(buf)

    def _render_begin(self, url_path, add):
        add(    '<div class="paginator">')

    def _render_backward(self, url_path, add):
        add(    '  <span class="backward">')
        if not self.is_first():
            add('    <a href="%s?page=1">%s</a>\n' % (url_path, self.label_first))
            add('    <a href="%s?page=%s">%s</a>\n' % (url_path, self.current - 1, self.label_prev))
        else:
            add('    <span>%s</span>' % self.label_first)
            add('    <span>%s</span>' % self.label_prev)
        add(    '  </span>\n')

    def _render_pagination(self, url_path, add):
        add(    '  <span class="pagination">')
        current = self.current
        for i in xrange(1, self.page_count + 1):
            attr = i == current and ' class="current"' or ''
            add('    <a href="%s?page=%s"%s>%s</a>' % (url_path, i, attr, i))
        add(    '  </span>')

    def _render_forward(self, url_path, add):
        add(    '  <span class="forward">')
        if not self.is_last():
            add('    <a href="%s?page=%s">%s</a>' % (url_path, self.current + 1, self.label_next))
            add('    <a href="%s?page=%s">%s</a>' % (url_path, self.page_count, self.label_last))
        else:
            add('    <span>%s</span>' % self.label_next)
            add('    <span>%s</span>' % self.label_last)
        add(    '  </span>')

    def _render_end(self, url_path, add):
        #add(    '  <em>%s/%s</em>' % (current, self.page_count))
        add(    '</div>')



##
if __name__ == '__main__':
    print(Session.new_id())
