# -*- coding: utf-8 -*-

###
### $Release: 0.0.0 $
### $Copyright: copyright(c) 2014-2015 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'json'
require 'date'
require 'uri'


module K8

  HTTP_REQUEST_METHODS = {
    "GET"     => :GET,
    "POST"    => :POST,
    "PUT"     => :PUT,
    "DELETE"  => :DELETE,
    "HEAD"    => :HEAD,
    "PATCH"   => :PATCH,
    "OPTIONS" => :OPTIONS,
    "TRACE"   => :TRACE,
  }

  HTTP_RESPONSE_STATUS = {
    100 => "Continue",
    101 => "Switching Protocols",
    102 => "Processing",
    200 => "OK",
    201 => "Created",
    202 => "Accepted",
    203 => "Non-Authoritative Information",
    204 => "No Content",
    205 => "Reset Content",
    206 => "Partial Content",
    207 => "Multi-Status",
    208 => "Already Reported",
    226 => "IM Used",
    300 => "Multiple Choices",
    301 => "Moved Permanently",
    302 => "Found",
    303 => "See Other",
    304 => "Not Modified",
    305 => "Use Proxy",
    307 => "Temporary Redirect",
    400 => "Bad Request",
    401 => "Unauthorized",
    402 => "Payment Required",
    403 => "Forbidden",
    404 => "Not Found",
    405 => "Method Not Allowed",
    406 => "Not Acceptable",
    407 => "Proxy Authentication Required",
    408 => "Request Timeout",
    409 => "Conflict",
    410 => "Gone",
    411 => "Length Required",
    412 => "Precondition Failed",
    413 => "Request Entity Too Large",
    414 => "Request-URI Too Long",
    415 => "Unsupported Media Type",
    416 => "Requested Range Not Satisfiable",
    417 => "Expectation Failed",
    418 => "I'm a teapot",
    422 => "Unprocessable Entity",
    423 => "Locked",
    424 => "Failed Dependency",
    426 => "Upgrade Required",
    500 => "Internal Server Error",
    501 => "Not Implemented",
    502 => "Bad Gateway",
    503 => "Service Unavailable",
    504 => "Gateway Timeout",
    505 => "HTTP Version Not Supported",
    506 => "Variant Also Negotiates",
    507 => "Insufficient Storage",
    508 => "Loop Detected",
    510 => "Not Extended",
  }


  module Util

    module_function

    def parse_query_string(query_str)
      #; [!engr6] returns empty Hash object when query string is empty.
      d = {}
      return d if query_str.empty?
      #; [!fzt3w] parses query string and returns Hahs object.
      equal    = '='
      brackets = '[]'
      query_str.split(/[&;]/).each do |s|
        #kv = s.split('=', 2)
        #if kv.length == 2
        #  k, v = kv
        #else
        #  k = kv[0]; v = ""
        #end
        k, v = s.split(equal, 2)
        v ||= ''
        k = URI.decode_www_form_component(k) unless k =~ /\A[-.\w]+\z/
        v = URI.decode_www_form_component(v) unless v =~ /\A[-.\w]+\z/
        #; [!t0w33] regards as array of string when param name ends with '[]'.
        if k.end_with?(brackets)
          (d[k] ||= []) << v
        else
          d[k] = v
        end
      end
      return d
    end

    def build_query_string(query)
      case query
      when nil    ; return nil
      when String ; return query
      when Hash, Array
        return query.collect {|k, v|
          name  = Util.encode_www_form_component(k.to_s)
          value = Util.encode_www_form_component(v.to_s)
          "#{name}=#{value}"
        }.join('&')
      else
        raise ArgumentError.new("Hash or Array expected but got #{query.inspect}.")
      end
    end

    def mock_env(meth="GET", path="/", query: nil, form: nil, input: nil, headers: nil, env: nil)
      #uri = "http://localhost:80#{path}"n
      #opts["REQUEST_METHOD"] = meth
      #env = Rack::MockRequest.env_for(uri, opts)
      require 'stringio' unless defined?(StringIO)
      https = env && (env['rack.url_scheme'] == 'https' || env['HTTPS'] == 'on')
      input = Util.build_query_string(form) if form
      environ = {
        "rack.version"      => [1, 3],
        "rack.input"        => StringIO.new(input || ""),
        "rack.errors"       => StringIO.new,
        "rack.multithread"  => true,
        "rack.multiprocess" => true,
        "rack.run_once"     => false,
        "rack.url_scheme"   => https ? "https" : "http",
        "REQUEST_METHOD"    => meth,
        "SERVER_NAME"       => "localhost",
        "SERVER_PORT"       => https ? "443" : "80",
        "QUERY_STRING"      => Util.build_query_string(query || ""),
        "PATH_INFO"         => path,
        "HTTPS"             => https ? "on" : "off",
        "SCRIPT_NAME"       => "",
        "CONTENT_LENGTH"    => (input ? input.bytesize.to_s : "0"),
        "CONTENT_TYPE"      => (form ? "application/x-www-form-urlencoded" : nil)
      }
      environ.delete("CONTENT_TYPE") if environ["CONTENT_TYPE"].nil?
      headers.each do |name, value|
        name =~ /\A[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\z/  or
          raise ArgumentError.new("invalid http header name: #{name.inspect}")
        value.is_a?(String)  or
          raise ArgumentError.new("http header value should be a string but got: #{value.inspect}")
        ## ex: 'X-Requested-With' -> 'HTTP_X_REQUESTED_WITH'
        k = "HTTP_#{name.upcase.gsub(/-/, '_')}"
        environ[k] = value
      end if headers
      env.each do |name, value|
        case name
        when /\Arack\./
          # ok
        when /\A[A-Z]+(_[A-Z0-9]+)*\z/
          value.is_a?(String)  or
            raise ArgumentError.new("rack env value should be a string but got: #{value.inspect}")
        else
          raise ArgumentError.new("invalid rack env key: #{name}")
        end
        environ[name] = value
      end if env
      return environ
    end

  end


  class HttpException < Exception

    def initialize(status_code, message=nil, response_headers=nil)
      response_headers, message = message, nil if message.is_a?(Hash)
      @status_code      = status_code
      @message          = message          if message
      @response_headers = response_headers if response_headers
    end

    attr_reader :status_code, :message, :response_headers

    def status_message
      return HTTP_RESPONSE_STATUS[@status_code]
    end

  end


  class BaseError < Exception
  end


  class ContentTypeRequiredError < BaseError
  end


  class UnknownContentError < BaseError
  end


  class Request

    def initialize(env)
      #; [!yb9k9] sets @env.
      @env = env
      #; [!yo22o] sets @method as Symbol value.
      @method = HTTP_REQUEST_METHODS[env['REQUEST_METHOD']]  or
        raise HTTPException.new(400, "#{env['REQUEST_METHOD'].inspect}: unknown request method.")
      #; [!twgmi] sets @path.
      @path = env['PATH_INFO']
    end

    attr_accessor :env, :method, :path

    def header(name)
      return @env["HTTP_#{name.upcase.sub('-', '_')}"]
    end

    def query_params
      return @query_params ||= Util.parse_query_string(@env['QUERY_STRING'] || "")
    end

    def form_params
      d = @form_params
      return d if d
      case @env['CONTENT_TYPE']
      when 'application/x-www-form-urlencoded'
        qstr = @env['rack.input'].read(10*1024*1024)   # TODO
        d = Util.parse_query_string(qstr)
      when /\Amultipart\/form-data;\s*boundary=(.*)/
        d = {}   # TODO
      else
        d = {}
      end
      @form_params = d
      return d
    end

    def json_params
      d = @json_params
      return d if d
      case @env['CONTENT_TYPE']
      when /\Aapplication\/json\b/
        json_str = @env['rack.input'].read(10*1024*1024)   # TODO
        d = JSON.parse(json_str)
      else
        d = {}
      end
      @json_params = d
      return d
    end

    def params
      if @method == :GET || @method == :HEAD
        return self.query_params
      elsif @env['CONTENT_TYPE'] =~ /\Aapplication\/json\b/
        return self.json_params
      else
        return self.form_params
      end
    end

    def cookies
      return {}
    end

  end


  class Response

    def initialize
      @status_code = 200
      @headers = {}
    end

    attr_accessor :status_code
    attr_reader :headers

    def content_type
      return @headers['Content-Type']
    end

    def content_type=(content_type)
      @headers['Content-Type'] = content_type
    end

    def content_length
      s = @headers['Content-Length']
      return s ? s.to_i : nil
    end

    def content_length=(length)
      @headers['Content-Length'] = length.to_s
    end

    def set_cookie(name, value, domain: nil, path: nil, expires: nil, max_age: nil, httponly: nil, secure: nil)
      s = "#{name}=#{value}"
      s << "; Domain=#{domain}"   if domain
      s << "; Path=#{path}"       if path
      s << "; Expires=#{expires}" if expires
      s << "; Max-Age=#{max_age}" if max_age
      s << "; HttpOnly"           if httponly
      s << "; Secure"             if secure
      value = @headers['Set-Cookie']
      @headers['Set-Cookie'] = value ? (value << "\n" << s) : s
      return self
    end

  end


  REQUEST_CLASS  = Request
  RESPONSE_CLASS = Response

  def self.REQUEST_CLASS=(klass)
    #; [!7uqb4] changes default request class.
    remove_const :REQUEST_CLASS
    const_set :REQUEST_CLASS, klass
  end

  def self.RESPONSE_CLASS=(klass)
    #; [!c1bd0] changes default response class.
    remove_const :RESPONSE_CLASS
    const_set :RESPONSE_CLASS, klass
  end


  class BaseAction

    def initialize(req, resp)
      #; [!uotpb] accepts request and response objects.
      @req  = req
      @resp = resp
    end

    attr_reader :req, :resp

    def handle_action(action_method, urlpath_params)
      @current_action = action_method
      ex = nil
      begin
        #; [!5jnx6] calls '#before_action()' before handling request.
        before_action()
        #; [!ddgx3] invokes action method with urlpath params.
        content = self.__send__(action_method, *urlpath_params)
        #; [!aqa4e] returns content.
        return handle_content(content)
      rescue => ex
        raise
      ensure
        #; [!67awf] calls '#after_action()' after handling request.
        #; [!alpka] calls '#after_action()' even when error raised.
        after_action(ex)
      end
    end

    protected

    def before_action
    end

    def after_action(ex)
    end

    def handle_content(content)
      return content
    end

  end


  class Action < BaseAction

    protected

    def before_action
      protect_csrf() if protect_csrf_required?()
    end

    def after_action(ex)
      return if ex
      #; [!qsz2z] raises ContentTypeRequiredError when content type is not set.
      @resp.headers['Content-Type']  or
        raise ContentTypeRequiredError.new("Response header 'Content-Type' expected, but not provided.")
    end

    def handle_content(content)
      case content
      #; [!jhnzu] when content is nil...
      when nil
        #; [!42fxs] sets content length as 0.
        #; [!zcodm] sets content type as octet-stream when not set.
        #; [!sfwfz] returns [''].
        @resp.headers['Content-Length'] = "0"
        @resp.headers['Content-Type'] ||= "application/octet-stream"  # necessary?
        return [""]
      #; [!lkxua] when content is a hash object...
      when Hash
        #; [!9aaxl] converts hash object into JSON string.
        #; [!c7nj7] sets content length.
        #; [!j0c1d] sets content type as 'application/json' when not set.
        #; [!gw05f] returns array of JSON string.
        json_str = JSON.dump(content)
        @resp.headers['Content-Length'] = json_str.bytesize.to_s
        @resp.headers['Content-Type'] ||= "application/json"
        return [json_str]
      #; [!p6p99] when content is a string...
      when String
        #; [!1ejgh] sets content length.
        #; [!uslm5] sets content type according to content when not set.
        #; [!79v6x] returns array of string.
        @resp.headers['Content-Length'] = content.bytesize.to_s
        @resp.headers['Content-Type'] ||= guess_content_type(content)
        return [content]
      #; [!s7eix] when content is an Enumerable object...
      when Enumerable
        #; [!md2go] just returns content.
        #; [!ab3vr] neither content length nor content type are not set.
        return content
      #; [!apwh4] else...
      else
        #; [!wmgnr] raises K8::UnknownContentError.
        raise UnknownContentError.new("Unknown content: class={content.class}, content=#{content.inspect}")
      end
    end

    ## helpers

    ## Returns "text/html; charset=utf-8" or "application/json" or nil.
    def guess_content_type(text)
      case text
      when /\A\s*</ ; return "text/html; charset=utf-8"  # probably HTML
      when /\A\s*{/ ; return "application/json"          # probably JSON
      else          ; return nil
      end
    end

    def protect_csrf_required?
      return false if @req.env['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest'
      req_meth = @req.method
      return req_meth == :POST || req_meth == :PUT || req_meth == :DELETE
    end

    def protect_csrf
      expected = @req.cookies['_csrf']
      actual   = self.params['_csrf']
      expectd == actual  or
        raise HTTP(400, "invalid csrf token")
    end

    def new_csrf_token
      return Digest::MD5.hexdigest("#{rand()}#{rand()}#{rand()}")
    end

    def csrf_token
      token = @_csrf_token
      return token if token
      token = @req.cookies['_csrf']
      unless token
        token = new_csrf_token()
        @resp.set_cookie('_csrf', token)
      end
      @_csrf_token = token
      return token
    end

    def HTTP(status_code, message=nil, response_headers=nil)
      return HttpException.new(status_code, message, response_headers)
    end

    ##
    ## ex:
    ##   mapping '/',     :GET=>:do_index, :POST=>:do_create
    ##   mapping '/{id}', :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
    ##
    def self.mapping(urlpath_pattern, methods={})
      self._action_method_mapping.map(urlpath_pattern, methods)
    end

    def self._action_method_mapping
      return @action_method_mapping ||= ActionMethodMapping.new
    end

  end


  class DefaultPatterns

    def initialize
      @patterns = []
    end

    def register(urlpath_param_name, default_pattern='[^/]*?', &converter)
      #; [!yfsom] registers urlpath param name, default pattern and converter block.
      @patterns << [urlpath_param_name, default_pattern, converter]
      self
    end

    def unregister(urlpath_param_name)
      #; [!3gplv] deletes matched record.
      @patterns.delete_if {|tuple| tuple[0] == urlpath_param_name }
      self
    end

    def lookup(urlpath_param_name)
      #; [!dvbqx] returns default pattern string and converter proc when matched.
      #; [!6hblo] returns '[^/]+?' and nil as default pattern and converter proc when nothing matched.
      for str_or_rexp, default_pat, converter in @patterns
        return default_pat, converter if str_or_rexp === urlpath_param_name
      end
      return '[^/]+?', nil
    end

  end


  class ActionMethodMapping

    def initialize
      @mappings = []
    end

    ##
    ## ex:
    ##   map '/',         :GET=>:do_index, :POST=>:do_create
    ##   map '/{id:\d+}', :GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete
    ##
    def map(urlpath_pattern, action_methods={})
      action_methods = _normalize(action_methods)
      #; [!s7cs9] maps urlpath and methods.
      #; [!o6cxr] returns self.
      @mappings << [urlpath_pattern, action_methods]
      return self
    end

    def _normalize(action_methods)
      d = {}
      action_methods.each do |req_meth, action_method|
        k = HTTP_REQUEST_METHODS[req_meth.to_s]  or
          raise ArgumentError.new("#{req_meth.inspect}: unknown request method.")
        v = action_method
        d[k] = v.is_a?(Symbol) ? v : v.to_s.intern
      end
      return d   # ex: {:GET=>:do_index, :POST=>:do_create}
    end
    private :_normalize

    def each
      #; [!62y5q] yields each urlpath pattern and action methods.
      @mappings.each do |urlpath_pattern, action_methods|
        yield urlpath_pattern, action_methods
      end
      self
    end

  end


  class ActionClassMapping

    def initialize
      @mappings = []
    end

    ##
    ## ex:
    ##   mount '/',              WelcomeAction
    ##   mount '/books',         BooksAction
    ##   mount '/admin', [
    ##           ['/session',    AdminSessionAction],
    ##           ['/books',      AdminBooksAction],
    ##         ]
    ##
    def mount(urlpath_pattern, action_class)
      _mount(@mappings, urlpath_pattern, action_class)
      #; [!w8mee] returns self.
      return self
    end

    def _mount(mappings, urlpath_pattern, action_class)
      #; [!4l8xl] can accept array of pairs of urlpath and action class.
      if action_class.is_a?(Array)
        array = action_class
        child_mappings = []
        array.each {|upath, klass| _mount(child_mappings, upath, klass) }
        action_class = child_mappings
      #; [!lvxyx] raises error when not an action class.
      else
        action_class.is_a?(Class) && action_class < BaseAction  or
          raise ArgumentError.new("mount('#{urlpath_pattern}'): Action class expected but got: #{action_class.inspect}")
      end
      #; [!flb11] mounts action class to urlpath.
      mappings << [urlpath_pattern, action_class]
    end
    private :_mount

    def traverse(&block)
      _traverse(@mappings, "", &block)
      self
    end

    def _traverse(mappings, base_urlpath_pat, &block)
      #; [!ds0fp] yields with event (:enter, :map or :exit).
      mappings.each do |urlpath_pattern, action_class|
        yield :enter, base_urlpath_pat, urlpath_pattern, action_class, nil
        curr_urlpath_pat = "#{base_urlpath_pat}#{urlpath_pattern}"
        if action_class.is_a?(Array)
          child_mappings = action_class
          _traverse(child_mappings, curr_urlpath_pat, &block)
        else
          action_method_mapping = action_class._action_method_mapping
          action_method_mapping.each do |upath_pat, action_methods|
            yield :map, curr_urlpath_pat, upath_pat, action_class, action_methods
          end
        end
        yield :exit, base_urlpath_pat, urlpath_pattern, action_class, nil
      end
    end
    private :_traverse

    def each_mapping
      traverse() do
        |event, base_urlpath_pat, urlpath_pat, action_class, action_methods|
        next unless event == :map
        full_urlpath_pat = "#{base_urlpath_pat}#{urlpath_pat}"
        #; [!driqt] yields full urlpath pattern, action class and action methods.
        yield full_urlpath_pat, action_class, action_methods
      end
      self
    end

  end


  class ActionRouter

    def initialize(action_class_mapping, default_patterns=nil)
      @default_patterns = default_patterns || K8::DefaultPatterns.new
      #; [!dnu4q] calls '#_construct()'.
      _construct(action_class_mapping)
    end

    private

    def _construct(action_class_mapping)
      ##
      ## Example of @rexp:
      ##     \A                                  # ...(0)
      ##     (:?                                 # ...(1)
      ##         /api                            # ...(2)
      ##             (?:                         # ...(3)
      ##                 /books                  # ...(2)
      ##                     (?:                 # ...(3)
      ##                         /\d+(\z)        # ...(4)
      ##                     |                   # ...(5)
      ##                         /\d+/edit(\z)   # ...(4)
      ##                     )                   # ...(6)
      ##             |                           # ...(7)
      ##                 /authors                # ...(2)
      ##                     (:?                 # ...(4)
      ##                         /\d+(\z)        # ...(4)
      ##                     |                   # ...(5)
      ##                         /\d+/edit(\z)   # ...(4)
      ##                     )                   # ...(6)
      ##             )                           # ...(6)
      ##     |                                   # ...(7)
      ##         /admin                          # ...(2)
      ##             (:?                         # ...(3)
      ##                 ....
      ##             )                           # ...(6)
      ##     )                                   # ...(8)
      ##
      ## Example of @dict (fixed urlpaths):
      ##     {
      ##       "/api/books"                      # ...(9)
      ##           => [BooksAction,   {:GET=>:do_index, :POST=>:do_create}],
      ##       "/api/books/new"
      ##           => [BooksAction,   {:GET=>:do_new}],
      ##       "/api/authors"
      ##           => [AuthorsAction, {:GET=>:do_index, :POST=>:do_create}],
      ##       "/api/authors/new"
      ##           => [AuthorsAction, {:GET=>:do_new}],
      ##       "/admin/books"
      ##           => ...
      ##       ...
      ##     }
      ##
      ## Example of @list (variable urlpaths):
      ##     [
      ##       [                                 # ...(10)
      ##         %r'\A/api/books/(\d+)\z',
      ##         ["id"], [proc {|x| x.to_i }],
      ##         BooksAction,
      ##         {:GET=>:do_show, :PUT=>:do_update, :DELETE=>:do_delete},
      ##       ],
      ##       [
      ##         %r'\A/api/books/(\d+)/edit\z',
      ##         ["id"], [proc {|x| x.to_i }],
      ##         BooksAction,
      ##         {:GET=>:do_edit},
      ##       ],
      ##       ...
      ##     ]
      ##
      @dict = {}
      @list = []
      #; [!956fi] builds regexp object for variable urlpaths (= containing urlpath params).
      buf = ['\A']                         # ...(0)
      buf << '(?:'                         # ...(1)
      action_class_mapping.traverse do
        |event, base_urlpath_pat, urlpath_pat, action_class, action_methods|
        first_p = buf[-1] == '(?:'
        case event
        when :map
          full_urlpath_pat = "#{base_urlpath_pat}#{urlpath_pat}"
          if full_urlpath_pat =~ /\{.*?\}/
            buf << '|' unless first_p      # ...(5)
            buf << _compile(urlpath_pat, '', '(\z)').first  # ...(4)
            full_urlpath_rexp_str, param_names, param_converters = \
                _compile(full_urlpath_pat, '\A', '\z', true)
            #; [!sl9em] builds list of variable urlpaths (= containing urlpath params).
            @list << [Regexp.compile(full_urlpath_rexp_str),
                      param_names, param_converters,
                      action_class, action_methods]   # ...(9)
          else
            #; [!6tgj5] builds dict of fixed urlpaths (= no urlpath params).
            @dict[full_urlpath_pat] = [action_class, action_methods] # ...(10)
          end
        when :enter
          buf << '|' unless first_p        # ...(7)
          buf << _compile(urlpath_pat, '', '').first  # ...(2)
          buf << '(?:'                     # ...(3)
        when :exit
          if first_p
            buf.pop()   # '(?:'
            buf.pop()   # urlpath
            buf.pop() if buf[-1] == '|'
          else
            buf << ')'                     # ...(6)
          end
        else
          raise "** internal error: event=#{event.inspect}"
        end
      end
      buf << ')'                           # ...(8)
      @rexp = Regexp.compile(buf.join())
      buf.clear()
    end

    def _compile(urlpath_pattern, start_pat='', end_pat='', grouping=false)
      #; [!izsbp] compiles urlpath pattern into regexp string and param names.
      #; [!olps9] allows '{}' in regular expression.
      #parse_rexp = /(.*?)<(\w*)(?::(.*?))?>/
      #parse_rexp = /(.*?)\{(\w*)(?::(.*?))?\}/
      #parse_rexp  = /(.*?)\{(\w*)(?::(.*?(?:\{.*?\}.*?)*))?\}/
      parse_rexp = /(.*?)\{(\w*)(?::([^{}]*?(?:\{[^{}]*?\}[^{}]*?)*))?\}/
      param_names = []
      converters  = []
      s = ""
      s << start_pat
      urlpath_pattern.scan(parse_rexp) do |text, name, pat|
        proc_ = nil
        pat, proc_ = @default_patterns.lookup(name) if pat.nil? || pat.empty?
        named = !name.empty?
        param_names << name if named
        converters << proc_ if named
        #; [!vey08] uses grouping when 4th argument is true.
        #; [!2zil2] don't use grouping when 4th argument is false.
        #; [!rda92] ex: '/{id:\d+}' -> '/(\d+)'
        #; [!jyz2g] ex: '/{:\d+}'   -> '/\d+'
        #; [!hy3y5] ex: '/{:xx|yy}' -> '/(?:xx|yy)'
        #; [!gunsm] ex: '/{id:xx|yy}' -> '/(xx|yy)'
        if named && grouping
          pat = "(#{pat})"
        elsif pat =~ /\|/
          pat = "(?:#{pat})"
        end
        s << Regexp.escape(text) << pat
      end
      m = Regexp.last_match
      rest = m ? m.post_match : urlpath_pattern
      s << Regexp.escape(rest) << end_pat
      ## ex: ['/api/books/(\d+)', ["id"], [proc {|x| x.to_i }]]
      return s, param_names, converters
    end

    public

    def find(req_path)
      action_class, action_methods = @dict[req_path]
      if action_class
        #; [!p18w0] urlpath params are empty when matched to fixed urlpath pattern.
        param_names  = []
        param_values = []
      else
        #; [!ps5jm] returns nil when not matched to any urlpath patterns.
        m = @rexp.match(req_path)      or return nil
        i = m.captures.find_index('')  or return nil
        #; [!t6yk0] urlpath params are not empty when matched to variable urlpath apttern.
        (full_urlpath_rexp,   # ex: /\A\/api\/books\/(\d+)\z/
         param_names,         # ex: ["id"]
         param_converters,    # ex: [proc {|x| x.to_i }]
         action_class,        # ex: BooksAction
         action_methods,      # ex: {:GET=>:do_show, :PUT=>:do_edit, ...}
        ) = @list[i]
        #; [!0o3fe] converts urlpath param values according to default patterns.
        values = full_urlpath_rexp.match(req_path).captures
        procs = param_converters
        #param_values = procs.zip(values).map {|pr, v| pr ? pr.call(v) : v }
        param_values = \
            case procs.length
            when 1; [procs[0].call(values[0])]
            when 2; [procs[0].call(values[0]), procs[1].call(values[1])]
            else  ; procs.zip(values).map {|pr, v| pr ? pr.call(v) : v }
            end    # ex: ["123"] -> [123]
      end
      #; [!ndktw] returns action class, action methods, urlpath names and values.
      ## ex: [BooksAction, {:GET=>:do_show}, ["id"], [123]]
      return action_class, action_methods, param_names, param_values
    end

  end


  class RackApplication

    def initialize
      @action_class_mapping = ActionClassMapping.new
      @router = nil
      @default_patterns = DefaultPatterns.new
      init_default_param_patterns(@default_patterns)
    end

    def init_default_param_patterns(default_patterns)
      #; [!i51id] registers '\d+' as default pattern of param 'id' or /_id\z/.
      x = default_patterns
      x.register('id',    '\d+') {|val| val.to_i }
      x.register(/_id\z/, '\d+') {|val| val.to_i }
      #; [!8x5mp] registers '\d\d\d\d-\d\d-\d\d' as default pattern of param 'date' or /_date\z/.
      to_date = proc {|val|
        #; [!wg9vl] raises 404 error when invalid date (such as 2012-02-30).
        yr, mo, dy = val.split(/-/).map(&:to_i)
        Date.new(yr, mo, dy)  rescue
          raise HttpException.new(404, "#{val}: invalid date.")
      }
      x.register('date',    '\d\d\d\d-\d\d-\d\d', &to_date)
      x.register(/_date\z/, '\d\d\d\d-\d\d-\d\d', &to_date)
    end
    protected :init_default_param_patterns

    ##
    ## ex:
    ##   mount '/',         WelcomeAction
    ##   mount '/books',    BooksAction
    ##   mount '/admin',    [
    ##           ['/session',    AdminSessionAction],
    ##           ['/books',      AdminBooksAction],
    ##         ]
    ##
    def mount(urlpath_pattern, action_class_or_array)
      @action_class_mapping.mount(urlpath_pattern, action_class_or_array)
      #; [!fm8mh] clears router object.
      @router = nil
      return self
    end

    def find(req_path)
      #; [!vnxoo] creates router object from action class mapping if router is nil.
      @router ||= ActionRouter.new(@action_class_mapping, @default_patterns)
      #; [!o0rnr] returns action class, action methods, urlpath names and values.
      return @router.find(req_path)
    end

    def call(env)
      #; [!uvmxe] takes env object.
      #; [!gpe4g] returns status, headers and content.
      return handle_request(REQUEST_CLASS.new(env), RESPONSE_CLASS.new)
    end

    protected

    def handle_request(req, resp)
      #; [!l6kmc] uses 'GET' method to find action when request method is 'HEAD'.
      req_meth = HTTP_REQUEST_METHODS[req.env['REQUEST_METHOD']]
      req_meth_ = req_meth == :HEAD ? :GET : req_meth
      begin
        #; [!rz13i] returns HTTP 404 when urlpath not found.
        tuple = find(req.path)  or
          raise HttpException.new(404)
        action_class, action_methods, urlpath_param_names, urlpath_param_values = tuple
        #; [!rv3cf] returns HTTP 405 when urlpath found but request method not allowed.
        action_method = action_methods[req_meth_]  or
          raise HttpException.new(405)
        #; [!0fgbd] finds action class and invokes action method with urlpath params.
        action_obj = action_class.new(req, resp)
        content = action_obj.handle_action(action_method, urlpath_param_values)
        tuple = [resp.status_code, resp.headers, content]
      rescue HttpException => ex
        tuple = handle_http(ex, req, resp)
      rescue Exception => ex
        tuple = handle_error(ex, req, resp)
      end
      #; [!9wp9z] returns empty body when request method is HEAD.
      tuple[2] = [""] if req_meth == :HEAD
      return tuple
    end

    def handle_http(ex, req, resp)
      if json_expected?(req)
        content = render_http_exception_as_json(ex, req, resp)
        content_type = "application/json"
      else
        content = render_http_exception_as_html(ex, req, resp)
        content_type = "text/html;charset=utf-8"
      end
      headers = {
        "Content-Type"   => content_type,
        "Content-Length" => content.bytesize.to_s,
      }
      headers.update(ex.response_headers) if ex.response_headers
      return [ex.status_code, headers, [content]]
    end

    def handle_error(ex, req, resp)
      raise ex
    end

    def render_http_exception_as_json(ex, req, resp)
      return JSON.dump({
        "error"  => ex.message,
        "status" => "#{ex.status_code} #{ex.status_message}",
      })
    end

    def render_http_exception_as_html(ex, req, resp)
      return <<"END"
<div>
<h2>#{ex.status_code} #{ex.status_message}</h2>
<p>#{ex.message}</p>
</div>
END
    end

    def json_expected?(req)
      return true if req.path.end_with?('.json')
      return true if req.env['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest'
      return false
    end

    public

    def each_mapping(&block)
      #; [!cgjyv] yields full urlpath pattern, action class and action methods.
      @action_class_mapping.each_mapping(&block)
      self
    end

    def show_mappings()
      #; [!u1g77] returns all mappings as YAML string.
      req_methods = HTTP_REQUEST_METHODS.values() + [:ANY]
      s = ""
      each_mapping do |full_urlpath_pat, action_class, action_methods|
        arr = req_methods.collect {|req_meth|
          action_method = action_methods[req_meth]
          action_method ? "#{req_meth}: #{action_method}" : nil
        }.compact()
        s << "- urlpath: #{full_urlpath_pat}\n"
        s << "  class:   #{action_class}\n"
        s << "  methods: {#{arr.join(', ')}}\n"
        s << "\n"
      end
      return s
    end

  end


end
