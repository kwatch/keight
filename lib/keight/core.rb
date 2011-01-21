# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module K8


  class Request

    def initialize(env)
      init(env) if env
    end

    def init(env)
      @env = env
      @method       = (s = env['REQUEST_METHOD']) ? s.intern : s
      @query_string = env['QUERY_STRING']
      @uri          = env['REQUEST_URI']
      @path         = (@uri || '').split(/\?/, 2)[0]
      @content_length = (env['CONTENT_LENGTH'] || 0).to_i
      #
      parse_request()
    end

    attr_accessor :env, :method, :query_string, :uri, :path, :content_length
    attr_accessor :params, :files

    private

    def parse_request
      case @method
      when :GET, :HEAD
        @params = parse_query_string(@query_string)
        @files = {}
      else
        stdin = @env['rack.input'] || $stdin
        if @env['CONTENT_TYPE'] =~ /\Amultipart\/formdata\b/
          @params, @files = parse_multipart(stdin, @content_length)
        else
          content = @content_length > 0 ? stdin.read(@content_length) : stdin.read()
          @params = parse_query_string(content)
          @files = {}
        end
      end
    end

    def parse_query_string(qs)
      ret = K8::Util::parse_query_string(qs)
      return ret
    end

    def parse_multipart
      @env['CONTENT_TYPE'] =~ /boundary=(?:"([^";,]+?)"|([^;,\s]+))/  or
        raise "Boundary not found for multipart data."
      boundary = $1 || $2
      content_length = Integer(@env['CONTENT_LENGTH'])
      return K8::MultPart::parse(@input, boundary, content_length)
    end

  end


  class Response

    def initialize
      @status_code = 200
      @headers = [ ['Content-Type', 'text/html'] ]
    end

    attr_accessor :status_code, :headers

    def content_type=(cont_type)
      @headers[0][1] = cont_type
    end

    def add_header(name, value)
      @headers << [name, value]
    end

  end


  class Cookie

  end



  REQUEST  = Request
  RESPONSE = Response
  COOKIE   = Cookie


end
