# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module K8


  class Request

    def initialize(env)
      return unless env
      @env = env
      @method       = (s = env['REQUEST_METHOD']) ? s.intern : s
      @query_string = env['QUERY_STRING']
      @uri          = env['REQUEST_URI']
      @path         = (@uri || '').sub(/\?.*/, '')
    end
    attr_accessor :env, :method, :query_string, :uri, :path

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
