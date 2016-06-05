# -*- coding: utf-8 -*-

###
### keight.py -- fast, compact, and easy to understand framework for Python
###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2013-2016 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

__all__ = (
    'PY2', 'PY3', 'U', 'B', 'S',
    'on', 'mapping',
    'ActionMapping', 'ActionEagerMapping', 'ActionLazyMapping',
    'BaseAction', 'Action', 'Request', 'Response',
    'WSGIApplication',
    'HttpException',
)

import sys, os, re, json, traceback

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
assert PY2 or PY3, "Unexpected python version (%s)" % (sys.version)

if PY3:
    unicode     = str
    xrange      = range
    basestring  = str

ENCODING='utf-8'

def U(v, encoding=None):
    if isinstance(v, bytes):
        return v.decode(encoding or ENCODING)
    return v

def B(v, encoding=None):
    if isinstance(v, unicode):
        return v.encode(encoding or ENCODING)
    return v

if PY2:
    S = B
else:
    S = U


HTTP_STATUS_DICT = {
    100: "100 Continue",
    101: "101 Switching Protocols",
    102: "102 Processing",                # (WebDAV; RFC 2518)
    #
    200: "200 OK",
    201: "201 Created",
    202: "202 Accepted",
    203: "203 Non-Authoritative Information",  # (since HTTP/1.1)
    204: "204 No Content",
    205: "205 Reset Content",
    206: "206 Partial Content",           # (RFC 7233),
    207: "207 Multi-Status",              # (WebDAV; RFC 4918)
    208: "208 Already Reported",          # (WebDAV; RFC 5842)
    226: "226 IM Used",                   # (RFC 3229)
    #
    300: "300 Multiple Choices",
    301: "301 Moved Permanently",
    302: "302 Found",
    303: "303 See Other",                 # (since HTTP/1.1)
    304: "304 Not Modified",              # (RFC 7232)
    305: "305 Use Proxy",                 # (since HTTP/1.1)
    306: "306 Switch Proxy",
    307: "307 Temporary Redirect",        # (since HTTP/1.1)
    308: "308 Permanent Redirect",        # (RFC 7538)
   #308: "308 Resume Incomplete",         # (Google)
    #
    400: "400 Bad Request",
    401: "401 Unauthorized",              # (RFC 7235)
    402: "402 Payment Required",
    403: "403 Forbidden",
    404: "404 Not Found",
    405: "405 Method Not Allowed",
    406: "406 Not Acceptable",
    407: "407 Proxy Authentication Required", # (RFC 7235)
    408: "408 Request Timeout",
    409: "409 Conflict",
    410: "410 Gone",
    411: "411 Length Required",
    412: "412 Precondition Failed",       # (RFC 7232)
    413: "413 Payload Too Large",         # (RFC 7231)
    414: "414 Request-URI Too Long",
    415: "415 Unsupported Media Type",
    416: "416 Requested Range Not Satisfiable",  # (RFC 7233)
    417: "417 Expectation Failed",
    418: "418 I'm a teapot",              # (RFC 2324)
    419: "419 Authentication Timeout",    # (not in RFC 2616)
    420: "420 Method Failure",            # (Spring Framework)
    420: "420 Enhance Your Calm",         # (Twitter)
    421: "421 Misdirected Request",       # (RFC 7540)
    422: "422 Unprocessable Entity",      # (WebDAV; RFC 4918)
    423: "423 Locked",                    # (WebDAV; RFC 4918)
    424: "424 Failed Dependency",         # (WebDAV; RFC 4918)
    426: "426 Upgrade Required",
    428: "428 Precondition Required",     # (RFC 6585)
    429: "429 Too Many Requests",         # (RFC 6585)
    431: "431 Request Header Fields Too Large", # (RFC 6585)
    440: "440 Login Timeout",             # (Microsoft)
    444: "444 No Response",               # (Nginx)
    449: "449 Retry With",                # (Microsoft)
    450: "450 Blocked by Windows Parental Controls", # (Microsoft)
    451: "451 Unavailable For Legal Reasons", # (Internet draft)
    451: "451 Redirect",                  # (Microsoft)
    494: "494 Request Header Too Large",  # (Nginx)
    495: "495 Cert Error",                # (Nginx)
    496: "496 No Cert",                   # (Nginx)
    497: "497 HTTP to HTTPS",             # (Nginx)
    498: "498 Token expired/invalid",     # (Esri)
    499: "499 Client Closed Request",     # (Nginx)
   #499: "499 Token required",            # (Esri)
    #
    500: "500 Internal Server Error",
    501: "501 Not Implemented",
    502: "502 Bad Gateway",
    503: "503 Service Unavailable",
    504: "504 Gateway Timeout",
    505: "505 HTTP Version Not Supported",
    506: "506 Variant Also Negotiates",   # (RFC 2295)
    507: "507 Insufficient Storage",      # (WebDAV; RFC 4918)
    508: "508 Loop Detected",             # (WebDAV; RFC 5842)
    509: "509 Bandwidth Limit Exceeded",  # (Apache bw/limited extension)
    510: "510 Not Extended",              # (RFC 2774)
    511: "511 Network Authentication Required", # (RFC 6585)
    520: "520 Unknown Error",
}

MIME_TYPES = {
    '.html'    : "text/html",
    '.htm'     : "text/html",
    '.shtml'   : "text/html",
    '.css'     : "text/css",
    '.csv'     : "text/comma-separated-values",
    '.tsv'     : "text/tab-separated-values",
    '.xml'     : "text/xml",
    '.mml'     : "text/mathml",
    '.txt'     : "text/plain",
    '.wml'     : "text/vnd.wap.wml",
    '.gif'     : "image/gif",
    '.jpeg'    : "image/jpeg",
    '.jpg'     : "image/jpeg",
    '.png'     : "image/png",
    '.tif'     : "image/tiff",
    '.tiff'    : "image/tiff",
    '.ico'     : "image/x-icon",
    '.bmp'     : "image/x-ms-bmp",
    '.svg'     : "image/svg+xml",
    '.svgz'    : "image/svg+xml",
    '.webp'    : "image/webp",
    '.mid'     : "audio/midi",
    '.midi'    : "audio/midi",
    '.kar'     : "audio/midi",
    '.mp3'     : "audio/mpeg",
    '.ogg'     : "audio/ogg",
    '.m4a'     : "audio/x-m4a",
    '.ra'      : "audio/x-realaudio",
    '.3gpp'    : "video/3gpp",
    '.3gp'     : "video/3gpp",
    '.3g2'     : "video/3gpp2",
    '.ts'      : "video/mp2t",
    '.mp4'     : "video/mp4",
    '.mpeg'    : "video/mpeg",
    '.mpg'     : "video/mpeg",
    '.mov'     : "video/quicktime",
    '.webm'    : "video/webm",
    '.flv'     : "video/x-flv",
    '.m4v'     : "video/x-m4v",
    '.mng'     : "video/x-mng",
    '.asx'     : "video/x-ms-asf",
    '.asf'     : "video/x-ms-asf",
    '.wmv'     : "video/x-ms-wmv",
    '.avi'     : "video/x-msvideo",
    '.json'    : "application/json",
    '.js'      : "application/javascript",
    '.atom'    : "application/atom+xml",
    '.rss'     : "application/rss+xml",
    '.doc'     : "application/msword",
    '.pdf'     : "application/pdf",
    '.ps'      : "application/postscript",
    '.eps'     : "application/postscript",
    '.ai'      : "application/postscript",
    '.rtf'     : "application/rtf",
    '.xls'     : "application/vnd.ms-excel",
    '.eot'     : "application/vnd.ms-fontobject",
    '.ppt'     : "application/vnd.ms-powerpoint",
    '.key'     : "application/vnd.apple.keynote",
    '.pages'   : "application/vnd.apple.pages",
    '.numbers' : "application/vnd.apple.numbers",
    '.zip'     : "application/zip",
    '.lha'     : "application/x-lzh",
    '.lzh'     : "application/x-lzh",
    '.tar'     : "application/x-tar",
    '.tgz'     : "application/x-tar",
    '.gz'      : "application/x-gzip",
    '.bz2'     : "application/x-bzip2",
    '.xz'      : "application/x-xz",
    '.7z'      : "application/x-7z-compressed",
    '.rar'     : "application/x-rar-compressed",
    '.rpm'     : "application/x-redhat-package-manager",
    '.deb'     : "application/vnd.debian.binary-package",
    '.swf'     : "application/x-shockwave-flash",
    '.der'     : "application/x-x509-ca-cert",
    '.pem'     : "application/x-x509-ca-cert",
    '.crt'     : "application/x-x509-ca-cert",
    '.xpi'     : "application/x-xpinstall",
    '.xhtml'   : "application/xhtml+xml",
    '.xspf'    : "application/xspf+xml",
    '.yaml'    : "application/x-yaml",
    '.yml'     : "application/x-yaml",
    '.docx'    : "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    '.xlsx'    : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    '.pptx'    : "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}


def dict2json(jdict):
    return json.dumps(jdict, ensure_ascii=False, indent=None,
                      separators=_dict2json_seps)
_dict2json_seps = (',', ':')


def _re_compile(pattern, flags=0):
    return re._compile(pattern, flags)

def _re_escape(text):
    return re.sub(r'([-.^$*+?{}\\\[\]|()&])', r'\\\1', text)


def _load_module(string):
    mod = __import__(string)
    for x in string.split('.')[1:]:
        mod = getattr(mod, x)
    return mod


def _load_class(string):
    idx = string.rfind('.')
    if idx < 0:
        module_path = None
        class_name  = string
    else:
        module_path = string[:idx]
        class_name  = string[idx+1:]
    mod = _load_module(module_path)
    return getattr(mod, class_name, None)


class KeightError(Exception):
    pass


class ActionMappingError(KeightError):
    pass


class UnknownHttpStatusCodeError(KeightError):
    pass


class HttpException(Exception):

    __slots__ = ('status', 'content', 'headers')

    def __init__(self, status, headers=None, content=None):
        self.status  = status
        self.headers = headers
        self.content = content


class BaseAction(object):

    def __init__(self, req, resp):
        #; [!accud] takes request and response objects.
        self.req  = req
        self.resp = resp

    def before_action(self):
        """will be called before request handling."""
        pass

    def after_action(self, ex):
        """will be called with exception object after request handled."""
        pass

    def run_action(self, action_func, action_args):
        """inokes action function with urlpath parameter values."""
        #; [!5rm14] saves current action func into attribute.
        self.action_func = action_func
        #
        ex = None
        try:
            #; [!23um7] invokes 'before_action()' at first.
            self.before_action()
            #; [!0evnh] calles action function with arguments.
            content = self.invoke_action(action_func, action_args)
            #; [!pzf14] invokes 'handle_content()' and returns result of it.
            return self.handle_content(content)
        except Exception as ex_:
            ex = ex_
            raise
        finally:
            #; [!2cfff] invokes 'after_action()' at end, event if exception raised.
            #; [!khqsv] invokes 'after_action()' even if exception raised.
            #; [!onkcb] if exception raised, it will be passed to after_action().
            self.after_action(ex)

    def invoke_action(self, action_func, action_args):
        if isinstance(action_args, dict):
            return action_func(self, **action_args)
        else:
            return action_func(self, *action_args)

    def handle_content(self, content):
        """ex: converts dict object into JSON string."""
        return content


class Action(BaseAction):

    DEFAULT_CONTENT_TYPE = "text/html;charset=utf-8"
    JSON_CONTENT_TYPE    = "application/json"

    def dict2json(self, jdict):
        return dict2json(jdict)

    def handle_content(self, content):
        binary = None
        #; [!5hs2k] when argument is None...
        if content is None:
            #; [!sq6ov] returns empty binary string when content is None.
            binary = b""
            #; [!piocs] don't set content-type.
            #; [!s380l] sets content-length as 0.
            self.resp.content_length = len(binary)
            return [binary]
        #; [!in858] when argument is a dict object...
        elif isinstance(content, dict):
            #; [!kk6oy] converts it into JSON binary string.
            binary = self.dict2json(content)
            if isinstance(binary, unicode):
                binary = binary.encode('utf-8')   # JSON should be utf-8
            #; [!v5bvs] sets content-type as 'application/json'.
            #; [!15dgy] sets content-length.
            self.resp.content_type = self.JSON_CONTENT_TYPE
            self.resp.content_length = len(binary)
            return [binary]
        #; [!58h7f] when argument is a unicode object...
        elif isinstance(content, unicode):
            #; [!k655a] converts unicode string into binary string.
            binary = content.encode(ENCODING)
            #; [!al4tt] don't touch content-type.
            #; [!ari1a] sets content-length.
            self.resp.content_length = len(binary)
            return [binary]
        #; [!0mejh] when argument is a binary string...
        elif isinstance(content, bytes):
            #; [!9mma6] don't convert binary string.
            binary = content
            #; [!cj7uu] don't touch content-type.
            #; [!mathw] sets content-length.
            self.resp.content_length = len(binary)
            return [binary]
        #; [!lwlxb] else...
        else:
            #; [!zxsbp] returns content as-is, regarding it as iterable object.
            #; [!hsj7v] don't touch content-type.
            #; [!6qall] don't touch content-length.
            iterable = content
            return iterable

    def after_action(self, ex):
        #; [!rc0qi] set content-type automatically when it is blank.
        #; [!r3l7v] guesses content-type from request path if possible.
        if not self.resp.content_type:
            self.resp.content_type = self.guess_content_type() or self.DEFAULT_CONTENT_TYPE

    def guess_content_type(self):
        #; [!ar80y] returns content-type related to suffix of request path.
        #; [!eeimv] returns None when request path has no suffix.
        #; [!qaz00] returns None when suffix of request path is unknown.
        #ext = os.path.splitext(self.req.path)[0]   # slow
        #return MIME_TYPES.get(ext)
        req_path = self.req.path
        pos = req_path.rfind('.')
        if pos < 0:
            return None
        return MIME_TYPES.get(req_path[pos:])


def _get_mapping_dict(urlpath_pattern, depth=2):
    localvars = sys._getframe(depth).f_locals
    tuples = localvars.setdefault('__mapping__', [])
    for t in tuples:
        if t[0] == urlpath_pattern:
            break
    else:
        t = (urlpath_pattern, {})
        tuples.append(t)
    return t[1]


def mapping(urlpath_pattern, **methods):
    """maps urlpath pattern with action methods.
    ex:
        class HelloAction(keight.Action):
            def do_show(self, id):    return "..."
            def do_update(self, id):  return "..."
            def do_delete(self, id):  return "..."
            #
            mapping(r'/{id}', GET=do_show, PUT=do_update, DELETE=do_delete)
    """
    #; [!zfrv6] maps urlpath pattern with action methods.
    d = _get_mapping_dict(urlpath_pattern)
    for meth, func in methods.items():
        ActionMapping._validate_request_method(meth)
        d[meth] = func


def on(request_method, urlpath_pattern, **options):
    """maps request path and urlpath pattern with action method.
    ex:
        class HelloAction(keight.Action):

            @on('GET', r'')
            def do_index(self):
                return "..."

            @on('GET', r'/{id}')
            def do_show(self, id):
                return "..."

            @on('PUT', r'/{id}')
            def do_update(self, id):
                return "..."
    """
    #; [!i47p3] maps request path and urlpath pattern with action method.
    d = _get_mapping_dict(urlpath_pattern)
    def deco(func):
        #; [!a6xv2] sets keyword args to function as options.
        func.options = options
        ActionMapping._validate_request_method(request_method)
        d[request_method] = func
        return func
    return deco


class ActionMapping(object):

    REQUEST_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH',
                       'HEAD', 'OPTIONS', 'TRACE', 'LINK', 'UNLINK', ]

    URLPATH_PARAMETER_REXP = _re_compile(r'\{(\w*)(?::(.*?))?\}')

    @classmethod
    def _validate_request_method(cls, req_meth):
        #; [!548rp] raises ActionMappingError when request method is unknown.
        #; [!trjzz] not raises when request method is known.
        #; [!jsu98] not raises when request method is 'ANY'.
        if req_meth not in cls.REQUEST_METHODS and req_meth != 'ANY':
            raise ActionMappingError("%s: unknown request method." % (req_meth,))

    def lookup(self, req_urlpath):
        """(abstract) returns action class, action methods (dict) and urlpath arguments."""
        #; [!wwvec] raises NotImplementedError.
        raise NotImplementedError("%s.lookup(): not implemented yet." % self.__class__.__name__)

    def dispatch(self, req_meth, req_path, redirect=True):
        """returns action class, action function, and urlpath arguments.

        ex:
            mapping_list = [
                ('/hello', HelloAction)
            ]
            am = ActionMapping(mapping_list)

            ## returns action class, action function and urlpath arguments.
            print(am.dispatch('GET', '/hello'))
                #=> (HelloAction, HelloAction.do_index, ())
            print(am.dispatch('GET', '/hello/World'))
                #=> (HelloAction, HelloAction.do_show, ('World',))

            ## raises 404 Not Found when request path not found.
            am.dispatch('GET', '/foobar')  #=> HttpException(404)

            ## raises 405 Method Not Allowed when request path exists but corresponding method is not found.
            am.dispatch('DELETE', '/hello')  #=> HttpException(405)

            ## raises 301 Found between '/foo/' <=> '/foo' (only on GET or HEAD method).
            am.dispatch('GET', '/hello/123/')  #=> HttpException(301, {'Location': '/hello/123'})
        """
        #; [!oureu] raises 404 Not Found when request path not found.
        #; [!g9k0i] raises 301 Found when '/foo' not found but '/foo/' exists.
        #; [!c9dsj] raises 301 Found when '/foo/' not found but '/foo' exists.
        #; [!u6sqo] redirects between '/foo' <=> '/foo/' only on GET or HEAD method.
        t = self.lookup(req_path)
        if not t:
            if redirect and (req_meth == 'GET' or req_meth == 'HEAD') and req_path != '/':
                location = req_path[:-1] if req_path.endswith('/') else req_path+'/'
                t = self.lookup(location)
                if t:
                    raise HttpException(301, {'Location': location})
            raise HttpException(404)
        action_class, action_methods, urlpath_params = t
        #; [!thk18] falls back to GET method when HEAD method is not provided.
        #; [!rdfcv] falls back to ANY method when corresponding method is not provided.
        get = action_methods.get
        action_func = get(req_meth) or (get('GET') if req_meth == 'HEAD' else None) or get('ANY')
        #; [!j3hfh] raises 405 Method Not Allowed when no action method corresponding to request method.
        if action_func is None:
            raise HttpException(405)
        #; [!akpxj] returns action class, action func, and urlpath param values.
        return action_class, action_func, urlpath_params

    def _upath_pat2rexp(self, pat, begin='', end='', capture=True):
        #; [!r1xu6] ex: _upath_pat2rexp(r'/x.gz', '^', '$') => r'^/x\\.gz$'
        #; [!locca] ex: _upath_pat2rexp(r'/{code}', '^', '$', True) => r'^/(?P<code>[^/]+)$'
        #; [!iibcp] ex: _upath_pat2rexp(r'/{code}', '^', '$', False) => r'^/(?:<code>[^/]+)$'
        #; [!t8u2o] ex: _upath_pat2rexp(r'/{code:\d+}', '^', '$', True) => r'^/(?P<code:\d+>[^/]+)$'
        #; [!9i3gn] ex: _upath_pat2rexp(r'/{code:\d+}', '^', '$', False) => r'^/(?:<code:\d+>[^/]+)$'
        buf = [begin]
        pos = 0
        for m in self.URLPATH_PARAMETER_REXP.finditer(pat):
            text = pat[pos:m.start(0)]
            pname = m.group(1)    # urlpath parameter name
            rexp_str = m.group(2) or '[^/]+'
            pos = m.end(0)
            if capture and pname:
                buf.extend((_re_escape(text), '(?P<%s>' % pname, rexp_str, ')', ))
            else:
                buf.extend((_re_escape(text), '(?:',             rexp_str, ')', ))
        buf.extend((_re_escape(pat[pos:]), end))
        return "".join(buf)

    def _load_action_class(self, class_string):  # ex: 'my.api.HelloAction'
        #; [!gzlsn] converts string (ex: 'my.api.HelloAction') into class object (ex: my.api.HelloAction).
        try:
            action_class = _load_class(class_string)
        except ImportError:
            action_class = None
        #; [!7iso7] raises ValueError when failed to load specified class.
        if not action_class:
            raise ValueError("%s: No such module or class." % class_string)
        #; [!4ci2t] raises TypeError when value is not a class.
        #; [!9861d] raises TypeError when value is not a subclass of BaseAction class.
        #; [!e3qw0] raises ValueError when no action mehtods.
        self._validate_action_class(action_class, class_string)
        #
        return action_class

    def _validate_action_class(self, action_class, class_string):
        #; [!!4ci2t] raises TypeError when value is not a class.
        if not isinstance(action_class, type):
            raise TypeError("%s: Action class expected but got %r." % (class_string, action_class,))
        #; [!!9861d] raises TypeError when value is not a subclass of BaseAction class.
        if not issubclass(action_class, BaseAction):
            raise TypeError("%s: Action class expected." % class_string)
        #; [!!e3qw0] raises ValueError when no action mehtods.
        if not hasattr(action_class, '__mapping__'):
            raise TypeError("%s: No action methods." % class_string)


class ActionRexpMapping(ActionMapping):

    def __init__(self, mappings):
        #; [!qm6q0] accepts urlpath mapping list.
        #; [!cgftn] builds regexp representing routing.
        #; [!ta2hs] builds fixed entries.
        self._fixed_entries    = {}
        self._variable_entries = []
        self._all_entries      = []
        rexp_buf = self._build_entries(mappings, "", ['^'])
        rexp_buf.append('$')
        self._variable_rexp = _re_compile(''.join(rexp_buf))
        #
        #self.lookup = self.lookup
        #self._variable_rexp_match = self._variable_rexp.match
        #self._fixed_entries_get = self._fixed_entries.get

    def _build_entries(self, mappings, base_upath_pat, rexp_buf):
        rexp_buf.append('(?:')            # ... (*A)
        length = len(rexp_buf)
        #
        for upath_pat, item in mappings:
            rexp_str = self._upath_pat2rexp(upath_pat, '', '', False)
            rexp_buf.append(rexp_str)     # ... (*B)
            n = len(rexp_buf)
            #
            full_upath_pat = base_upath_pat + upath_pat
            if isinstance(item, list):
                rexp_buf.append(base_upath_pat)
                self._build_entries(item, full_upath_pat, rexp_buf)
            else:
                if isinstance(item, basestring):
                    action_class = self._load_action_class(item)
                    self._validate_action_class(action_class, item)
                else:
                    action_class = item
                    self._validate_action_class(action_class, repr(item))
                self._register_action_class(action_class, full_upath_pat, rexp_buf)
            #
            if len(rexp_buf) == n:        # if no children,
                rexp_buf.pop()            # then remove (*B)
            else:                         # else
                rexp_buf.append('|')      # concatenate by '|'
        #
        if rexp_buf[-1] == '|':
            rexp_buf.pop()
        if len(rexp_buf) == length:       # if no entries,
            rexp_buf.pop()                # then remove (*A)
        else:                             # else
            rexp_buf.append(')')          # close by ')'
        return rexp_buf

    def _register_action_class(self, action_class, base_upath_pat, rexp_buf):
        action_method_mapping = getattr(action_class, '__mapping__')
        if action_method_mapping is None:
            raise ValueError("%s: There is no action method mapping." % action_class.__name__)
        rexp_strs = []
        for upath_pat, action_methods in action_method_mapping:
            full_upath_pat = base_upath_pat + upath_pat
            if '{' in full_upath_pat:
                #rexp_str = self._upath_pat2rexp(full_upath_pat, '^', '$')
                #upath_rexp = _re_compile(rexp_str)
                #
                arr = self.URLPATH_PARAMETER_REXP.split(full_upath_pat)
                if len(arr) == 2:
                    pname = self.URLPATH_PARAMETER_REXP.search(full_upath_pat).group(1)
                    upath_rexp = (pname, len(arr[0]), -len(arr[1]))  # instead of rexp
                else:
                    rexp_str = self._upath_pat2rexp(full_upath_pat, '^', '$')
                    upath_rexp = _re_compile(rexp_str)
                #
                tupl = (action_class, action_methods, upath_rexp)
                self._variable_entries.append(tupl)
                rexp_strs.append(self._upath_pat2rexp(upath_pat, '', r'($)', False))
            else:
                tupl = (action_class, action_methods, {})
                self._fixed_entries[full_upath_pat] = tupl
            self._all_entries.append((full_upath_pat, action_class, action_methods))
        if rexp_strs:
            if len(rexp_strs) == 1:
                rexp_buf.append(rexp_strs[0])
            else:
                rexp_buf.extend(('(?:', '|'.join(rexp_strs), ')'))

    def lookup(self, req_urlpath):
        tupl = self._fixed_entries.get(req_urlpath)
        #tupl = self._fixed_entries_get(req_urlpath)
        if tupl:
            return tupl   # ex: (BooksAction, {'GET': do_index, 'POST', do_create}, {})
        #for tupl in self._variable_entries:
        #    action_class, action_methods, upath_rexp = tupl
        #    m = upath_rexp.match(req_urlpath)
        #    if m:
        #        pargs = m.groupdict()
        #        return action_class, action_methods, pargs
        #return None
        #; [!wduo6] returns None when not found.
        m = self._variable_rexp.match(req_urlpath)
        #m = self._variable_rexp_match(req_urlpath)
        if m is None:
            return None
        idx = m.groups().index('')
        action_class, action_methods, upath_rexp = self._variable_entries[idx]
        if isinstance(upath_rexp, tuple):
            pname, start, end = upath_rexp
            pval = req_urlpath[start:end] if end else req_urlpath[start:]
            pargs = {pname: pval} if pname else {}
        else:
            m = upath_rexp.match(req_urlpath)
            pargs = m.groupdict()
        #; [!0o1rm] returns action class, action methods and urlpath arguments.
        return action_class, action_methods, pargs

    def __iter__(self):
        #; [!gvtd4] yields each urlpath pattern, action class, and action methods.
        for tupl in self._all_entries:
            urlpath_pat, action_class, action_methods = tupl
            yield urlpath_pat, action_class, action_methods


class ActionRexpLazyMapping(ActionMapping):

    def __init__(self, mappings):
        #; [!ie7w7] accepts urlpath mapping list.
        #; [!hdb1y] builds regexp representing routing.
        #; [!np9zn] no fixed entries at first.
        self._all_urlpaths    = []
        self._fixed_urlpaths  = {}
        self._variable_urlpaths = []
        rexp_buf = self._nested_mappings = self._build(mappings, '', ['^'])
        rexp_buf.append('(?=[./]|$)')
        self._urlpath_rexp = _re_compile("".join(rexp_buf))

    def _reorder_mappings(self, mappings):
        if not any( '{' in x[0] for x in mappings ):
            return mappings
        fn = lambda t, rx=self.URLPATH_PARAMETER_REXP: rx.sub('*', t[0])
        return sorted(mappings, key=fn, reverse=True)

    def _build(self, mappings, base_upath_pat, rexp_buf):
        rexp_buf.append('(?:')
        length = len(rexp_buf)
        for upath_pat, item in self._reorder_mappings(mappings):
            rexp_str = self._upath_pat2rexp(upath_pat, '', '', False)
            rexp_buf.append(rexp_str)
            n = len(rexp_buf)
            #
            full_upath_pat = base_upath_pat + upath_pat
            if isinstance(item, list):
                self._build(item, full_upath_pat, rexp_buf)
            else:
                action_class = item
                if '{' in full_upath_pat:
                    rexp_str = self._upath_pat2rexp(full_upath_pat, '^', '(?=[/.]|$)')
                    full_upath_rexp = _re_compile(rexp_str)
                else:
                    full_upath_rexp = None
                t = [full_upath_pat, full_upath_rexp, action_class, None]
                self._variable_urlpaths.append(t)
                #
                rexp_buf.append('((?=[/.]|$))')
                #
                self._all_urlpaths.append((full_upath_pat, action_class))
            #
            if len(rexp_buf) == n:
                rexp_buf.pop()
            else:
                rexp_buf.append('|')
        #
        if rexp_buf[-1] == '|':
            rexp_buf.pop()
        if len(rexp_buf) == length:
            rexp_buf.pop()
        else:
            rexp_buf.append(')')
        return rexp_buf

    def lookup(self, req_urlpath):
        pair = self._fixed_urlpaths.get(req_urlpath)
        if pair:
            action_class, action_methods = pair
            return action_class, action_methods, {}
        #
        m = self._urlpath_rexp.match(req_urlpath)
        if not m:
            return None
        idx = m.groups().index('')
        tupl = self._variable_urlpaths[idx]
        base_upath_pat, base_upath_rexp, action_class, arr = tupl
        #; [!8ktv8] loads action class from file when class is a string.
        if isinstance(action_class, basestring):
            action_class = self._load_action_class(action_class)
            tupl[2] = action_class
        #
        if base_upath_rexp:
            m = base_upath_rexp.match(req_urlpath)
            pargs = m.groupdict()
            remaining = req_urlpath[m.end(0):]
        else:
            pargs = None
            remaining = req_urlpath[len(base_upath_pat):]
        #
        if arr is None:
            arr = []
            found = None
            for upath_pat, action_methods in action_class.__mapping__:
                full_upath_pat = base_upath_pat + upath_pat
                if '{' not in full_upath_pat:
                    self._fixed_urlpaths[full_upath_pat] = (action_class, action_methods)
                    if upath_pat == remaining:
                        found = action_methods
                else:
                    rexp_str = self._upath_pat2rexp(upath_pat, '^', '$')
                    upath_rexp = _re_compile(rexp_str)
                    arr.append([upath_rexp, action_methods])
            tupl[3] = arr
            if found:
                action_methods = found
                return action_class, action_methods, pargs or {}
        #; [!sb5h9] returns action class, action methods and urlpath arguments.
        for upath_rexp, action_methods in arr:
            m = upath_rexp.match(remaining)
            if m:
                if pargs is None:
                    pargs = m.groupdict()
                else:
                    pargs.update(m.groupdict())
                return action_class, action_methods, pargs
        #; [!vtgiz] returns None when not found.
        return None

    def __iter__(self):
        #; [!u58yc] yields each urlpath pattern, action class, and action methods.
        for base_upath_pat, action_class in self._all_urlpaths:
            if isinstance(action_class, basestring):
                action_class = self._load_action_class(action_class)
            for upath_pat, action_methods in action_class.__mapping__:
                yield base_upath_pat + upath_pat, action_class, action_methods


class ActionTrieMapping(ActionMapping):
    """Action mappging class using State Machine."""

    def __init__(self, mapping_list, lazy=False):
        self._lazy = lazy
        #; [!1gp9m] accepts urlpath mapping list.
        self._build(mapping_list)

    def _build(self, mapping_list):
        # ex:
        #   {
        #       "/api/books"         : (BooksAction, {"GET": BooksAction.do_index, ...}, ()),
        #       "/api/books/new.html": (BooksAction, {"GET": BooksAction.do_new, ...}, ()),
        #   }
        self._fixed_entries = {}
        # ex:
        #   {
        #       "api": {
        #           "books": {
        #               1: {    # '1' means int value of urlpath parameter
        #                   None:     (BooksAPI, {"GET": BooksAPI.do_show, ...}, ""),
        #                   "edit": {
        #                       None: (BooksAPI, {"GET": BooksAPI.do_edit, ...}, ".html"),
        #                   }
        #               }
        #           }
        #       }
        #   }
        self._variable_entries = {}
        #
        self._traverse(mapping_list, "")

    def _traverse(self, mapping_list, base_urlpath):
        lazy = self._lazy
        for urlpath, target in mapping_list:
            #; [!uno07] loads action classes if layz=False.
            #; [!ifj4v] don't load classes if lazy=True.
            if not lazy and isinstance(target, basestring):
                target = self._load_action_class(target)
            #
            full_urlpath = base_urlpath + urlpath
            if isinstance(target, list):
                self._traverse(target, full_urlpath)
            elif isinstance(target, type) and issubclass(target, BaseAction):
                self._register_permanently(full_urlpath, target)
            elif isinstance(target, basestring):
                self._register_temporarily(full_urlpath, target)
            else:
                raise NotActionClassError("%r: Action class expected." % (target,))

    _URLPATH_PARAM_TYPES = {'int': 1, 'str': 2, 'path': 3}
    _URLPATH_PARAM_REXP  = re.compile(r'^\{(\w*)(?::(.*?))?\}$')

    def _find_entries(self, path_elems, root_entries=None):
        if root_entries is None:
            root_entries = self._variable_entries
        param_types = self._URLPATH_PARAM_TYPES
        d = root_entries
        for s in path_elems:
            if '{' in s:
                pname, ptype = self._parse_urlpath_param(s)
                if ptype not in param_types:
                    raise UnknownUrlpathParameterTypeError(
                            "%r: Unknown paramter type name." % (s,))
                key = param_types[ptype]  # 1, 2 or 3
            else:
                key = s
            if key in d:
                d = d[key]
            else:
                d[key] = {}
                d = d[key]
        entries = d
        return entries

    def _register_temporarily(self, base_urlpath, action_class, entries=None):
        if entries is None:
            path_elems, _ = self._split_path(base_urlpath)  # ex: '/a/b/c.x' -> (['a','b','c'], '.x')
            entries = self._find_entries(path_elems)
        key = 0     # key for temporary registration
        entries[key] = (action_class, base_urlpath)

    def _register_permanently(self, base_urlpath, action_class, entries=None):
        if entries is None:
            path_elems, _ = self._split_path(base_urlpath)  # ex: '/a/b/c.x' -> (['a','b','c'], '.x')
            entries = self._find_entries(path_elems)
        if isinstance(action_class, basestring):
            class_str = action_class
            action_class = self._load_action_class(class_str)
            self._validate_action_class(action_class, class_str)
        for urlpath, action_methods in action_class.__mapping__:
            full_urlpath = base_urlpath + urlpath
            if '{' not in full_urlpath:
                self._fixed_entries[full_urlpath] = (action_class, action_methods, ())
            else:
                path_elems, extension = self._split_path(urlpath)
                leaf_entries = self._find_entries(path_elems, entries)
                leaf_entries[None] = (action_class, action_methods, extension)

    def _change_temporary_registration_to_permanently(self, entries):
        try:
            action_class, base_urlpath = entries.pop(0)
        except IndexError:
            pass
        else:
            self._register_permanently(base_urlpath, action_class, entries)

    def _parse_urlpath_param(self, string):
        param_rexp  = self._URLPATH_PARAM_REXP
        m = param_rexp.match(string)
        if not m:
            raise InvalidUrlpathParameterPatternError(
                    "%r: Invalid urlpath parameter patter." % (string,))
        pname, ptype = m.groups()
        if not ptype:
            ptype = self._guess_param_type_of(pname)
        return pname, ptype

    def _guess_param_type_of(self, pname):
        if pname == "id" or pname.endswith("_id"):
            return "int"
        return "str"

    def lookup(self, req_path):
        t = self._fixed_entries.get(req_path)
        if t:
            return t   # (action_class, action_methos, ())
        #
        lazy = self._lazy
        param_types = self._URLPATH_PARAM_TYPES
        key_int  = param_types['int']   # == 1
        key_str  = param_types['str']   # == 2
        key_path = param_types['path']  # == 3
        args = []; add = args.append
        d = self._variable_entries
        path_elems, extension = self._split_path(req_path)  # ex: '/a/b.x' => (['a','b'], '.x')
        for s in path_elems:
            #; [!05a7a] loads action classes dinamically if lazy=True.
            if lazy and 0 in d:         # if temporary key exists
                self._change_temporary_registration_to_permanently(d)
                t = self._fixed_entries.get(req_path)
                if t:
                    return t
            #
            if s in d:
                d = d[s]
            elif key_int in d and s.isdigit():
                d = d[key_int]
                add(int(s))
            elif key_str in d:
                d = d[key_str]
                add(s)
            elif key_path in d:
                for i, x in enumerate(path_elems):
                    if x is s:
                        break
                add("/".join(path_elems[i+1:]))
                break
            else:
                return None    # not found
            if d is None:
                return None    # not found
        if lazy and 0 in d:
            self._change_temporary_registration_to_permanently(d)
            t = self._fixed_entries.get(req_path)
            if t:
                return t
        #; [!ltatd] returns None when not found.
        t = d.get(None)
        if not t:
            return None        # not found
        action_class, action_methods, expected_ext = t
        if expected_ext != extension and expected_ext != '.*':
            return None        # not found
        #; [!u95qz] returns action class, action methods and urlpath arguments.
        return (action_class,      # ex: HelloAction
                action_methods,    # ex: {'GET': do_show, 'PUT': do_update}
                args)              # ex: [123]

    @staticmethod
    def _split_path(req_path):
        assert req_path.startswith('/')
        pos = req_path.rfind('.')
        if pos < 0 or pos < req_path.rfind('/'):
            path_elems = req_path[1:].split('/')
            extension  = ""
        else:
            path_elems = req_path[1:pos].split('/')
            extension  = req_path[pos:]
        return path_elems, extension


class ActionTrieLazyMapping(ActionTrieMapping):

    def __init__(self, mapping_list):
        ActionTrieMapping.__init__(self, mapping_list, lazy=True)


class WSGIRequestHeaders(object):

    def __init__(self, env):
        self.env = env

    def __getitem__(self, key):
        k = key.lower()
        if k == 'content-type':
            return self.env.get('CONTENT_TYPE')
        if k == 'content-length':
            return self.env.get('CONTENT_LENGTH')
        k = 'HTTP_' + k.upper().replace('-', '_')
        return self.env.get(k)

    def __iter__(self):
        env = self.env
        if 'CONTENT_TYPE' in env:
            yield 'Content-Type'
        if 'CONTENT_LENGTH' in env:
            yield 'Content-Length'
        for k in env:
            if k.startswith('HTTP_'):
                yield k[5:].title().replace('_', '-')

    def items(self):
        env = self.env
        if 'CONTENT_TYPE' in env:
            yield 'Content-Type', env['CONTENT_TYPE']
        if 'CONTENT_LENGTH' in env:
            yield 'Content-Length', env['CONTENT_LENGTH']
        for k in env:
            if k.startswith('HTTP_'):
                yield k[5:].title().replace('_', '-'), env[k]


class WSGIRequest(object):
    _REQUEST_HEADERS = WSGIRequestHeaders

    def __init__(self, env):
        #; [!ualzp] accepts environ object.
        #; [!841wq] sets method and path attributes.
        self.env    = env
        self.method = env['REQUEST_METHOD']
        self.path   = env['PATH_INFO'] or '/'

    @property
    def content_type(self):
        #; [!l88e2] returns CONTENT_TYPE value in environ object.
        return self.env.get('CONTENT_TYPE')

    @property
    def content_length(self):
        #; [!uwj7o] returns CONTENT_LENGTH value in environ object.
        #; [!j39md] returns int value instead of string.
        v = self.env.get('CONTENT_LENGTH')
        if v is None:
            return None
        return int(v)

    @property
    def wsgi_input(self):
        return self.env.get('wsgi.input')

    @property
    def wsgi_errors(self):
        return self.env.get('wsgi.errors')

    @property
    def headers(self):
        #; [!n45wo] returns header object which wraps environ object.
        headers = getattr(self, '_headers', None)
        if headers is None:
            self._headers = headers = self._REQUEST_HEADERS(self.env)
        return headers

    def header(self, name):
        #; [!3ymtd] returns header value in environ object.
        k = name.lower()
        if k == 'content-type':
            return self.env.get('CONTENT_TYPE')
        if k == 'content-length':
            return self.env.get('CONTENT_LENGTH')
        k = 'HTTP_' + k.upper().replace('-', '_')
        return self.env.get(k)


class WSGIResponse(object):

    __slots__ = ('status', 'content_type', 'content_length', '_header_list')

    def __init__(self):
        #; [!3d06t] default status code is 200.
        self.status         = 200
        self.content_type   = None
        self.content_length = None
        self._header_list   = [None, None]  # ex: [('Content-Type','text/html'), ('Content-Lenght','99')]

    def header(self, name):
        #; [!u5pqv] returns header value.
        name = name.lower()
        if name == 'content-type':
            return self.content_type
        if name == 'content-length':
            v = self.content_length
            return str(v) if v is not None else None
        for kv in self._header_list[2:]:
            k, v = kv
            if k.lower() == name:
                return v
        return None

    def set_header(self, name, value):
        key = name.lower()
        if key == 'content-type':
            self.content_type = value
            return self
        if key == 'content-length':
            self.content_length = str(value) if value is not None else None
            return self
        for i, (k, _) in enumerate(self._header_list[2:]):
            if k == key:
                self._header_list[i] = (name, value)
                return self
        self._header_list.append((name, value))
        return self

    def add_header(self, name, value):
        #; [!xeqt9] adds response header.
        self._header_list.append((name, value))

    def get_header_list(self):
        """Returns list of header name and value.
        Don't call this directly because this method is destructive;
        this method is intended to be called only by application object.
        """
        arr = self._header_list
        #; [!zvggv] header list contains Content-Length header if it is set.
        clen = self.content_length
        if clen is not None:  # ex: [None, None] -> [None, ('Content-Length', "9")]
            arr[1] = ('Content-Length', str(clen))
        else:                 # ex: [None, None] -> [None]
            arr.pop(1)
        #; [!oij5a] header list contains Content-Type header if it is set.
        ctype = self.content_type
        if ctype:             # ex: [None, (...)] -> [('Content-Type', "text/html"), (...)]
            arr[0] = ('Content-Type', ctype)
        else:                 # ex: [None, (...)] -> [(...)]
            arr.pop(0)
        #; [!pducc] returns list of pair header name and value.
        return arr

    def add_cookie(self, name, value, _=None,
                   domain=None, path=None, max_age=None, expires=None,
                   httponly=None, secure=None):
        if _ is not None:
            raise TypeError("add_cookie(): use keyword arguments for cookie attributes.")
        #; [!eng8x] builds cookie string.
        buf = []; add = buf.append
        add("%s=%s" % (name, value))
        if domain:   add("; Domain=%s"  % domain)
        if path:     add("; Path=%s"    % path)
        if max_age:  add("; Max-Age=%s" % max_age)
        if expires:  add("; Expires=%s" % expires)
        if httponly: add("; HttpOnly")
        if secure:   add("; Secure")
        cookie_str = S(''.join(buf))
        #; [!a17wa] adds Set-Cookie header.
        self._header_list.append(('Set-Cookie', cookie_str))
        #; [!fw2f5] returns cookie string.
        return cookie_str


class WSGIApplication(object):

    REQUEST  = WSGIRequest
    RESPONSE = WSGIResponse

    def __init__(self, mapping_list, _=None, lazy=False, engine='rexp'):
        #; [!us151] accepts mapping list and creates ActionMapping object.
        if _ is not None:
            raise TypeError("%r: Unexpected 2nd argument for %s()." % (_, self.__class__.__name__))
        if isinstance(mapping_list, ActionMapping):
            self._mapping = mapping_list
        index = 0
        if lazy: index += 1
        if engine == 'statemachine': index += 2
        klass = (ActionRexpMapping, ActionRexpLazyMapping, ActionTrieMapping, ActionTrieLazyMapping)[index]
        self._mapping = klass(mapping_list)

    def lookup(self, req_urlpath):
        """Delegates to ActionMapping#lookup()."""
        #; [!1rmcr] returns action class, action methods, and urlpath arguments.
        return self._mapping.lookup(req_urlpath)

    def dispatch(self, req_meth, req_path, redirect=True):
        """Delegates to ActionMapping#dispatch()."""
        #; [!wtp8c] returns action class, action func, and urlpath arguments.
        return self._mapping.dispatch(req_meth, req_path, redirect)

    def each_mapping(self):
        """Returns iteration of urlpath pattern, action class and action methods."""
        #; [!rfx5n] iterates urlpath pattern, action class and action methods.
        return iter(self._mapping)

    def show_mapping(self):
        req_methods = ActionMapping.REQUEST_METHODS + ['ANY']
        buf = []; add = buf.append
        for urlpath_pat, action_class, action_methods in self.each_mapping():
            lst = [ "%s: %s()" % (k, action_methods[k].__name__)
                      for k in req_methods if k in action_methods ]
            add("- urlpath:  %s\n" % urlpath_pat)
            add("  class:    %s\n" % action_class.__name__)
            add("  methods:  {%s}\n" % ", ".join(lst))
            add("\n")
        return "".join(buf)

    def __call__(self, env, start_response):
        #; [!8lx2o] invokes action corresponding to request path and method.
        status, headers, body = self.handle_request(env)
        #; [!2z6xr] raises UnknownHttpStatusCodeError when status code is unknown.
        status_str = HTTP_STATUS_DICT.get(status)
        if not status_str:
            raise UnknownHttpStatusCodeError("%s: unknown http status code." % status)
        #; [!huptr] calls start_response and returns response body.
        start_response(status_str, headers)
        return body

    def handle_request(self, env):
        #; [!0cd7m] handles request.
        req  = self.REQUEST(env)
        resp = self.RESPONSE()
        try:
            t = self.dispatch(req.method, req.path)
            action_class, action_func, urlpath_params = t
            action_obj = action_class(req, resp)
            body = action_obj.run_action(action_func, urlpath_params)
            return resp.status, resp.get_header_list(), body
        #; [!f66z9] handles http exception.
        except HttpException as ex:
            return self.handle_http_exception(ex, req, resp)
        #; [!ewqep] don't catch KeyboardInterrupt error.
        except KeyboardInterrupt:
            raise
        #; [!tn8yy] returns 500 Internal Server Error when exception raised.
        except Exception as ex:
            return self.handle_exception(ex, req, resp)

    def error_4xx(self, status_code, env):
        status = HTTP_STATUS_DICT[status_code]
        html = """<h2>%s</h2>""" % status
        binary = B(htm)
        headers = [
            ('Content-Type',   "text/html;charset=utf-8"),
            ('Content-Length', str(len(binary))),
        ]
        return status, headers, [binary]

    def handle_http_exception(self, ex, req, resp):
        status  = ex.status       # int
        content = ex.content
        #if content is None:
        #    content = resp.body
        if content is None:
            binary = B(HTTP_STATUS_DICT[status])
            ctype  = "text/plain;charset=utf-8"
        elif isinstance(content, dict):
            binary = B(dict2json(content))
            ctype  = "application/json;charset=utf-8"
        elif isinstance(content, binary):
            binary = content
            ctype  = "application/octet-stream"
        elif isinstance(content, unicode):
            binary = B(content)
            ctype  = "text/plain;charset=" + ENCODING
        else:
            raise TypeError("%r: unexpected data type of content." % (content,))
        resp.content_type   = ctype
        resp.content_length = len(binary)
        return status, resp.get_header_list(), [binary]

    def handle_exception(self, ex, req, resp):
        #; [!7qgls] writes traceback to stderr.
        #stderr = sys.stderr
        stderr = req.env['wsgi.errors']
        errtext = traceback.format_exc()
        stderr.write(S(errtext))
        #
        status  = 500
        binary  = b"<h2>500 Internal Server Error</h2>"
        headers = [
            ('Content-Type',   "text/html;charset=utf-8"),
            ('Content-Length', str(len(binary))),
        ]
        return status, headers, [binary]


def _create_module(module_name, **kwargs):
    """ex. mod = create_module('keight.wsgi')"""
    try:
        mod = type(sys)(module_name)
    except:    # on Jython 2.5.2
        import imp
        mod = imp.new_module(module_name)
    mod.__file__ = __file__
    mod.__dict__.update(kwargs)
    sys.modules[module_name] = mod
    return mod


wsgi = _create_module("keight.wsgi")
wsgi.RequestHeaders = WSGIRequestHeaders
wsgi.Request        = WSGIRequest
wsgi.Response       = WSGIResponse
wsgi.Application    = WSGIApplication
del WSGIRequestHeaders, WSGIRequest, WSGIResponse, WSGIApplication


_setup_testing_defaults = None  # import from wsgi.util
_BytesIO = None   # io.BytesIO or cStringIO.StringIO

def mock_env(req_meth, req_urlpath, _=None, query=None, form=None, json=None,
             headers=None, cookies=None, env=None):
    global _BytesIO
    try:
        from io import BytesIO as _BytesIO
    except ImportError:
        from cStringIO import StringIO as _BytesIO
    if _ is not None:
        raise TypeError("mock_env(): 'query' argument should be specfied as keyword argument.")
    if env is None:
        env = {}
    if req_meth:
        env['REQUEST_METHOD'] = S(req_meth)
    if req_urlpath:
        env['PATH_INFO'] = S(req_urlpath)
    if query:
        env['QUERY_STRING'] = S(_build_query_string(query))
    if form:
        env['wsgi.input'] = _BytesIO(B(_build_query_string(query)))
    if json:
        import json as json_
        json_str = json_.dumps(json)
        env['wsgi.input'] = _BytesIO(B(json_str))
    if headers:
        for k in headers:
            v = headers[k]
            if k.lower() == 'content-type':
                env['CONTENT_TYPE'] = S(v)
            elif k.lower() == 'content-length':
                env['CONTENT_LENGTH'] = S(str(v))
            else:
                env['HTTP_' + k.upper().replace('-', '_')] = S(v)
    if cookies:
        env['HTTP_COOKIE'] = S(_build_cookie_string(cookie))
    #
    global _setup_testing_defaults
    if _setup_testing_defaults is None:
        from wsgiref.util import setup_testing_defaults as _setup_testing_defaults
    _setup_testing_defaults(env)
    return env

def _build_query_string(query):
    if isinstance(query, (unicode, binary)):
        return query
    if isinstance(query, dict):  # TODO: percent encode
        return '&'.join("%s=%s" % (k, query[k]) for k in query)
    raise TypeError("%r: failed to build query string." % (query,))

def _build_cookie_string(cookie):
    if isinstance(cookie, (unicode, binary)):
        return cookie
    if isinstance(cookie, dict):  # TODO: percent encode
        return '; '.join("%s=%s" % (k, cookie[k]) for k in cookie)
    raise TypeError("%r: failed to build cookie string." % (cookie,))


class StartResponse(object):
    __slots__ = ('status', 'headers')

    def __init__(self):
        self.status  = None
        self.headers = None

    def __call__(self, status, headers):
        self.status  = status
        self.headers = headers

wsgi.mock_env      = mock_env
wsgi.StartResponse = StartResponse
del mock_env
del StartResponse
