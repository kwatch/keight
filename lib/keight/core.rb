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
      @path         = (@uri || '').sub(/\?.*/, '')
      #
      parse_request()
    end

    attr_accessor :env, :method, :query_string, :uri, :path
    attr_accessor :params, :files

    private

    def parse_request
      case @method
      when :GET, :HEAD
        @params, @files = parse_query_string()
      else
        if @env['CONTENT_TYPE'] =~ /\Amultipart\/formdata\b/
          @params, @files = parse_multipart()
        else
          @params, @files = parse_query_string()
        end
      end
    end

    def parse_query_string
      return K8::Util::parse_query_string(@query_string || ''), {}
    end

    def parse_multipart
      return K8::MultPart::parse(@input)
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
