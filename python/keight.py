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
    def do_hello(request, response):
        return "<h1>Hello World</h1>"
    app = k8.MainApplication()
    app.map("/.*", GET=do_hello)
    #app = k8.ExceptionMiddleware(disp)   # for production
    app = k8.DevelopmentMiddleware(app)   # for development
    from wsgiref.handlers import CGIHandler
    CGIHandler().run(main_app)

"""


import sys, os, re


###
### configuration
###

logger = True
def _config_logger():
    global logger
    if logger is True:
        import logging
        logging.basicConfig()
        logger = logging.getLogger()
    return logger

editor_schema = None   # or 'txmt', 'gvim'



###
### common
###

def location(depth=0):
    frame = sys._getframe(depth+1)
    return (frame.f_code.co_filename, frame.f_lineno)

def _is_func(obj):
    return hasattr(obj, '__call__') and type(obj) is not type

_word_rexp   = re.compile(r'^[\/\w]+$')
_escape_rexp = re.compile(r'\\.')
_rexp_rexp   = re.compile(r'[\.\*\+\?\|\^\$\[\]\(\)\{\}]')

def is_rexp(s):
    if not s or _word_rexp.match(s):
        return False
    s = _escape_rexp.sub('', s)
    return _rexp_rexp.search(s) and True or None


###
### html
###

def escape_html(val):
    if val is None: return ""
    return str(val).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;').replace("'",'&#039;')

h = escape_html

def unquote_plus(s):
    arr = s.replace('+', ' ').split('%')
    n = len(arr)
    if n == 1:
        return arr[0]
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
                arr[i] = _hex2chr[s[:2].upper()] + s[2:]
            except KeyError:
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
        return "<h2>%s</h2>\n<p>%s</p>\n" % (self.status, h(self.message))

    def __str__(self):
        self.to_html()

    def to_response(self):
        return (self.status, self.headers, self.to_html())


class HttpRedirect(HttpException):

    def __init__(self, location):
        HttpException.__init__(self, 'Redirect to %s' % location)
        self.location = location


class Http301MovedPermantly(HttpRedirect):
    status = '301 Moved Permanently'

class Http302Found(HttpRedirect):
    status = '302 Found'

class Http307TemporaryRedirect(HttpRedirect):
    status = '307 Temporary Redirect'


class Http400BadRequest(HttpException):
    status = '400 Bad Request'

class Http401Unauthorized(HttpException):
    status = '401 Unauthorized'

class Http403Forbidden(HttpException):
    status = '403 Forbidden'

class Http404NotFound(HttpException):
    status = '404 Not Found'

class Http405MethodNotAllowed(HttpException):
    status = '405 Method Not Allowed'

class Http406NotAcceptable(HttpException):
    status = '406 Not Acceptable'

class Http409Conflict(HttpException):
    status = '409 Conflict'

class Http422UnprocessableEntity(HttpException):
    status = '422 Unprocessable Entity'

class Http500InternalServerError(HttpException):
    status = '500 Internal Server Error'

class Http501NotImplemented(HttpException):
    status = '501 Not Implemented'

class Http503ServiceUnavailable(HttpException):
    status = '503 Service Unavialable'


def raise_404_not_found(request, response):
    raise Http404NotFound("%s: not found." % request.path)

def raise_405_method_not_allowed(request, response):
    raise Http405MethodNotAllowed("%s: not allowed." % request.method)



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
        self.__iter__     = values
        self.__getitem__  = values.__getitem__
        self.__setitem__  = values.__setitem__
        self.__repr__     = values.__repr__
        self.__str__      = values.__str__
        self.__contains__ = values.__contains__
        #self.clear        = values.clear
        #self.copy         = values.copy
        #self.fromkeys     = values.fromkeys
        self.get          = values.get
        #self.has_key      = values.has_key
        #self.items        = values.items
        #self.iteritems    = values.iteritems
        #self.iterkeys     = values.iterkeys
        #self.itervalues   = values.itervalues
        #self.keys         = values.keys
        #self.pop          = values.pop
        #self.popitem      = values.popitem
        #self.setdefault   = values.setdefault
        #self.update       = values.update
        #self.values       = values.values

    def str(self, name, default=''):
        if name not in self.values:
            return default
        return self.values[name].trim()

    bytes = str

    def unicode(self, name, default=u''):
        if name not in self.values:
            return default
        return self.values[name].trim().decode(self.encoding)

    def raw(self, name, default=''):
        return self.get(name, default)

    def int(self, name, default=False):
        if name not in self.values:
            return None
        try:
            return int(self.values[name].trim())
        except:
            return default

    def float(self, name, default=False):
        if name not in self.values:
            return None
        try:
            return float(self.values[name].trim())
        except:
            return default

    def bool(self, name, default=False):
        if name not in self.value:
            return None
        v = self.values[name].trim()
        if v in self.false_values:
            return False
        return True

PARAMS = Params


class Request(object):

    def __init__(self, env=None):
        if env is None: env = os.environ
        if env:
            self.env = self.headers = env
            self.method = env.get('REQUEST_METHOD')
            self.uri    = env.get('REQUEST_URI') or ''
            #self.path   = self.uri[0:-(len(env.get('QUERY_STRING', '')) + 2)]
            self.path   = self.uri.split('?', 1)[0]
            #self.path   = env.get('PATH_INFO')
            self.input  = env.get('wsgi.input') or sys.stdin
            self.errors = env.get('wsgi.errors') or sys.stdin
            try:
                self.content_length = int(env.get('CONTENT_LENGTH'))
            except Exception:
                self.content_length = None
            self._parse_form_params(env)

    def _parse_form_params(self, env):
        req_method = self.method
        if req_method == 'GET':
            values = self.parse_query_string(env.get('QUERY_STRING'))
            files  = {}
        elif req_method == 'POST' or req_method == 'PUT':
            content_type = env.get('CONTENT_TYPE')
            if content_type == 'application/x-www-form-urlencoded':
                if self.content_length is None:
                    body = self.input.read()
                else:
                    body = self.input.read(self.content_length)
                values = self.parse_query_string(body)
                files = {}
            elif content_type and content_type.startswith('multipart/form-data;'):
                values, files = self.parse_multipart(self.input, self.content_length, content_type)
            else:
                values = {};  files = {}
        else:
            values = {};  files = {}
        self.params = PARAMS(values)
        self.files = PARAMS(files)

    @staticmethod
    def parse_query_string(query_string,
                           _sep=re.compile(r'[&;]')):
        _unq = _unquotes
        values = {}
        if query_string:
            for s in _sep.split(query_string):
                pair = s.split('=', 1)
                if len(pair) == 2:
                    k, v = pair
                else:
                    k = pair[0]
                    v = ''
                ## unquote param name
                #if k.endswith('%5B%5D'):
                #    k = k[:-6] + '[]'
                arr = k.replace('+', ' ').split('%')
                n = len(arr)
                if n == 1:
                    k = arr[0]
                else:
                    k = _unq(arr, n)
                ## unquote param value
                arr = v.replace('+', ' ').split('%')
                n = len(arr)
                if n == 1:
                    v = arr[0]
                else:
                    v = _unq(arr, n)
                ## set name and value
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
        return values

    @staticmethod
    def parse_request_body(stdin, content_length, content_type):
        assert isinstance(content_length, int)
        if content_type == 'application/x-www-form-urlencoded':
            body = stdin.read(content_length)
            values = self.parse_query_string(body)
            files = {}
        elif content_type.startswith('multipart/form-data;'):
            values, files = self.parse_multipart(stdin, content_length, content_type)
        else:
            values = {}
            files  = {}
        return (values, files)

    @staticmethod
    def parse_multipart(stdin, content_length, content):
        values = {}
        files = {}
        return (values, files)

    def build(self, params=None):
        pass

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

    def __init__(self, env=None):
        self.status = 200   # OK
        self.headers = [('Content-Type', 'text/html; charset=utf-8')]
        self.cookies = []

    def set_status(self, status_code):
        if status_code not in STATUS_CODES:
            raise ValueError('%s: unknown status code.' % status_code)
        self.status = status_code

    def get_status_str(self):
        return STATUS_CODES.get(self.status)

    def set_content_type(self, content_type):
        self.headers[0] = ('Content-Type', content_type)

    def get_content_type(self):
        return self.headers[0][1]

    def set_encoding(self, encoding):
        self.encoding = encoding
        self.headers[0] = ('Content-Type', 'text/html; charset=' + encoding)

    def add_header(self, name, value):
        self.headers.append((name, value))

    def add_cookie(self, cookie):
        self.cookies.append(cookie)

    def set_redirect(self, location, permanently=False):
        if permanently:
            self.status = 301  # Moved Permanently
        else:
            self.status = 302  # Found
        self.add_header('Location', location)

    def build(self):
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
    pass


COOKIE = Cookie



###
### session
###

class Session(object):
    def __init__(self, request, response):
        self.request  = request
        self.response = response
        self.values = {}
        self.__getitem__ = self.values.__getitem__
        self.__setitem__ = self.values.__setitem__
        self.get = self.values.get


class CookieSession(Session):
    pass


SESSION = CookieSession



###
### router
###

class Router(object):

    def __init__(self):
        self.mappings = []
        self._mapping_dict = {}  # key: str, val: (dict, klass)
        self._mapping_list = []  # list of (paht, rexp, dict, klass)
        self.base_path = None
        self._base_path_rexp = None

    def set_base_path(self, base_path):
        self.base_path = base_path
        self._base_path_rexp = is_rexp(base_path) and re.compile(base_path) or None
        has_lazy = False
        for path, kwargs, handler_class in self.mappings:
            if kwargs:
                for req_method, func in kwargs.iteritems():
                    func.path = self._build_path_func(base_path + path)
                    func.method = req_method
            if handler_class:
                if getattr(handler_class, 'router', None):
                    handler_class.router.set_base_path(base_path + path)
                elif isinstance(handler_class, str):
                    has_lazy = True
        if not has_lazy:
            return
        i = -1
        for path, rexp, kwargs, handler_class in self._mapping_list:
            i += 1
            if handler_class and isinstance(handler_class, str):
                class_name = handler_class
                def callback(klass, _mappings=self._mapping_list, _i=i, _path=base_path+path):
                    if type(klass) is not type:
                        raise ValueError("%s: class object expected but got %r." % (class_name, klass))
                    t = _mappings[_i]
                    _mappings[_i] = (t[0], t[1], t[2], klass)
                    if getattr(klass, 'router', None):
                        klass.router.set_base_path(_path)
                    return klass
                t = self._mapping_list[i]
                self._mapping_list[i] = (t[0], t[1], t[2], OnDemandLoader(class_name, callback))

    def _build_path_func(self, map_path):
        return _build_path_func(map_path)

    def map(self, path, **kwargs):
        self.mappings.append((path, kwargs, None))
        rexp = is_rexp(path) and re.compile(path) or None
        if rexp:
            self._mapping_list.append((path, rexp, kwargs, None))
        else:
            self._mapping_dict[path] = (kwargs, None)
        return self

    def mount(self, path, handler_class):
        self.mappings.append((path, None, handler_class))
        rexp = is_rexp(path) and re.compile(path) or None
        self._mapping_list.append((path, rexp, None, handler_class))
        return self

    def route(self, req_path, req_method):
        rest_path, args = self._match_to_base_path(req_path)
        if rest_path in self._mapping_dict:
            kwargs, handler_class = self._mapping_dict[rest_path]
        else:
            rest_path_len = len(rest_path)
            for path, rexp, kwargs, handler_class in self._mapping_list:
                if rexp:
                    m = rexp.match(rest_path)
                    if m and (kwargs and m.end() == rest_path_len or handler_class):
                        if args:  args += m.groups()
                        else:     args = m.groups()
                        break
                else:
                    if rest_path.startswith(path):
                        break
            else:
                kwargs = handler_class = None
        if kwargs:
            func = kwargs.get(req_method)
            if not func:
                return (False, rest_path)    # method not allowd
            return (func, args)
        elif handler_class:
            if type(handler_class) is OnDemandLoader:
                handler_class = handler_class.load()
            return (handler_class, args)
        else:
            return (None, rest_path)         # not found

    def _match_to_base_path(self, req_path):
        rexp = self._base_path_rexp
        if rexp:
            m = rexp.match(req_path)
            assert m
            args = m.groups()
            rest_path = req_path[m.end():]
        else:
            base_path = self.base_path
            if not base_path:
                raise ValueError("base path is not set to router object (do you forget to mount handler class?)")
            assert req_path.startswith(base_path)
            rest_path = req_path[len(base_path):]
            args = ()
        return rest_path, args

ROUTER = Router


class OnDemandLoader(object):

    def __init__(self, name, callback=None):
        self.name = name
        self.callback = callback

    def _import(self, dotted_name):
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

    def load(self):
        obj = self._import(self.name)
        if self.callback:
            return self.callback(obj)
        return obj


_path_func_rexp = re.compile(r'\(.*?\)')

def _build_path_func(path):
    format = _path_func_rexp.sub('%s', path)
    n = format.count('%s')
    if n == 0:  return lambda: format
    if n == 1:  return lambda a: format % (a, )
    if n == 2:  return lambda a, b: format % (a, b)
    if n == 3:  return lambda a, b, c: format % (a, b, c)
    return lambda *args: format % args



###
### handler
###

class Handler(object):

    router = None
    _current = None

    def __init__(self, request, response):
        self.request  = request
        self.response = response

    def before(self):
        pass

    def after(sef):
        pass

    @classmethod
    def handle(cls, request, response):
        mapped, args = cls.router.route(request.path, request.method)
        if mapped is None:
            raise Http404NotFound("%s: not found." % request.path)
        if mapped is False:
            raise Http405MethodNotAllowed("%s: method not allowed." % request.method)
        if type(mapped) is type:
            handler_class = mapped
            return handler_class.handle(request, response)
        else:
            unbound_func = mapped
            obj = cls(request, response)
            obj.action = unbound_func
            cls._current = obj
            try:
                obj.before()
                return unbound_func(obj, *args)
            finally:
                obj.after()



###
### wsgi app
###

class MainApplication(object):

    def __init__(self):
        self.router = _root_router()

    def map(self, path, **kwargs):
        for req_method, func in kwargs.iteritems():
            func.path   = _build_path_func(path)
            func.method = req_method
        return self.router.map(path, **kwargs)

    def mount(self, path, handler_class):
        if hasattr(handler_class, 'router'):
            handler_class.router.set_base_path(path)
        return self.router.mount(path, handler_class)

    def __call__(self, env, start_response):
        #try:
            ## create request and response objects
            req = REQUEST(env)
            res = RESPONSE(env)
            status, headers, content = self.run(req, res)
            if isinstance(content, str):
                ret = [content]
            elif isinstance(content, unicode):
                ret = [content.encode(res.encoding or 'utf-8')]
            else:
                ret = content or ['']
            start_response(status, headers)
            return ret
        #except Exception, ex:
        #    _config_logger()
        #    if logger:
        #        import backtrace
        #        arr = backtrace.format_exc(*sys.exc_info())
        #        logger.error(''.join(arr))
        #    status  = '500 Internal Server Error'
        #    headers = [('Content-Type', 'text/html; charset=utf-8')]
        #    ret     = ["<h1>500 Internal Server Error</h1>"]
        ##
        #start_response(status, headers)
        #return ret

    def run(self, req, res):
        try:
            handler = self.find_handler(req)
            if not handler:
                raise Http404NotFound("%s: not found." % req_path)
            content = handler(req, res)
            status  = res.get_status_str()
            headers = res.get_headers()
        except HttpException, ex:
            status, headers, content = self.handle_http_exception(ex)
        ##
        return status, headers, content

    def find_handler(self, req):
        req_path = req.path
        mapped, args = self.router.route(req_path, req.method)
        if mapped is None:
            raise Http404NotFound("%s: not found." % req.path)
        if mapped is False:
            raise Http405MethodNotAllowed("%s: method not found." % req.method)
        req.args = args
        if hasattr(mapped, 'handle'):
            return mapped.handle
        return mapped
        #req_path = req.path
        #for base_path, rexp, handler, klass in self.mappings:
        #    if rexp:
        #        if rexp.match(req_path):
        #            return handler
        #    else:
        #        if req_path.startswith(base_path):
        #            return handler
        #return None

    def handle_http_exception(self, ex):
        return ex.to_response()


def _root_router():
    router = ROUTER()
    def _match_to_base_path(req_path):
        return (req_path, ())
    router._match_to_base_path = _match_to_base_path
    return router



###
### middleware
###

class Middleware(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, env, start_response):
        return self.app(env, start_resonse)


class ExceptionMiddleware(Middleware):

    def __call__(self, env, start_response):
        try:
            return self.app(env, start_response)
        except Exception, ex:
            return self.handle_exception(ex, env, start_response)

    def handle_exception(self, ex, env, start_response):
        _config_logger()
        if logger:
            import traceback
            arr = traceback.format_exception(*sys.exc_info())
            logger.error(''.join(arr))
        start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
        return ["<h2>500 Internal Server Error</h2>"]


class DevelopmentMiddleware(ExceptionMiddleware):

    def __call__(self, env, start_response):
        #'REQUEST_METHOD' not in env or 'QUERY_STRING' not in env
        if 'SERVER_SOFTWARE' not in env:
            env2 = dummy_env()
            env2.update(env)
            env = env2
        return ExceptionMiddleware.__call__(self, env, start_response)

    def handle_exception(self, ex, env, start_response):
        ret = ExceptionMiddleware.handle_exception(self, ex, env, start_response)
        ## TODO: support editor kicker
        ## get traceback
        import traceback
        arr = traceback.format_exception(*sys.exc_info())
        ## log traceback
        _config_logger()
        if logger:
            logger.error("".join(arr))
        ## print exception
        buf = []
        buf.append("<h2>%s: %s</h2>\n" % (ex.__class__.__name__, h(str(ex))))
        ## function to create editorkicker url
        from urllib import quote_plus
        if editor_schema:
            url_format = editor_schema + '://open?url=file://%s&line=%s'
            js = 'editorkicker(ths);return false'
        else:
            url_format = 'http://localhost:10101/open?file=%s&line=%s'
            js = ''
        url = lambda file, line: url_format % (quote_plus(file), line)
        ##
        rexp = re.compile(r'^  File "(.*?)", line (\d+)')
        format = '  <a href="%s" onclick="%s">File "%s", line %s</a>%s'
        buf.append('<pre>')
        for s in arr:
            m = rexp.match(s)
            if m:
                file, line = m.groups()
                rest = s[m.end():]
                href = url(file, line)
                buf.append(format % (h(href), h(js), h(file), line, h(rest)))
            else:
                buf.append(h(s))
        buf.append('</pre>')
        buf.append("""
<script>
  function _ajax(url, callback) {
    var xhr;
    if (window.XMLHttpRequest) {
      xhr = new XMLHttpRequest();
    } else if (window.ActiveXObject) {
      try        { xhr = new ActiveXObject("Msxml2.XMLHTTP"); }
      catch (ex) { xhr = new ActiveXObject("Microsoft.XMLHTTP"); }
    } else {
      return false;
    }
    xhr.onreadystatechange = function() {
      var completed = 4;
      if (xhr.readyState == completed) {
        if (callback) callback(xhr);
      }
    }
    xhr.open('GET', url, true);
    xhr.send(null);
    return true;
  }
  function editorkicker(elem) {
    _ajax(elem.href, function(text) { null; });
  }
</script>""")
        return ''.join(buf)



###
### debug
###
_StringIO = None

def dummy_env(method='GET', path='/', qs='', body='', **kwargs):
    global _StringIO
    if not _StringIO:
        try:
            from cStringIO import StringIO as _StringIO    # Python 2.x
        except ImportError:
            from io import StringIO as _StringIO           # Python 3.x
    #
    env = {
        'REQUEST_METHOD': method,
        'PATH_INFO':      path,
        'QUERY_STRING':   qs,
        'REQUEST_URI':    path + (qs and '?' + qs or ''),
        'wsgi.input':     _StringIO(body),
        'wsgi.errors':    _StringIO(),
    }
    if body:
        env['CONTENT_LENGTH'] = len(body)
    if method == 'POST' and 'CONTENT_TYPE' not in env:
        env['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
    env.update(kwargs)
    return env
