# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module K8


  module Debug


    module_function


    def dummy_env(method='GET', path='/', kwargs={})
      require 'stringio' unless defined?(StringIO)
      #: if qs is dict then converts it into query string
      qs   = kwargs[:qs]
      qs   = hash2qs(qs)   if qs.is_a?(Hash)
      #: if body is dict then converts it into query string
      body = kwargs[:body]
      body = hash2qs(body) if body.is_a?(Hash)
      #: sets keys and values automatically
      method = method.to_s
      env = {
        'REQUEST_METHOD'    => method,
        'PATH_INFO'         => path,
        'QUERY_STRING'      => qs,
        'REQUEST_URI'       => (qs ? "#{path}?#{qs}" : path),
        'SCRIPT_NAME'       => '',
        'CONTENT_TYPE'      => '',
        'CONTENT_LENGTH'    => '',
        'SERVER_NAME'       => 'localhost',
        'SERVER_PORT'       => '80',
        'SERVER_PROTOCOL'   => 'HTTP/1.0',
        'rack.input'        => StringIO.new(body || ''),
        'rack.errors'       => StringIO.new(),
        'rack.version'      => [1, 1],
        'rack.run_once'     => true,
        'rack.url_scheme'   => 'http',
        'rack.multithread'  => false,
        'rack.multiprocess' => false,
      }
      #: if request body is specified then set CONTENT_LENGTH as string
      env['CONTENT_LENGTH'] = body.length.to_s if body
      #: if POST and CONTENT_TYPE is not set then set it automatically
      #: if POST and CONTENT_TYPE is already set then don't change it
      env['CONTENT_TYPE'] ||= 'application/x-www-form-urlencoded' if method == 'POST'
      #: if keyword args specified then adds them into env
      kwargs.each_pair do |k, v|
        env[k] = v if k.is_a?(String)
      end
      #: returns dict object
      return env
    end


  end


end
