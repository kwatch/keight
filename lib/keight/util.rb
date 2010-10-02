# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module K8


  module Util


    module_function


    def escape_html(val)
      val.to_s.gsub(/&/, '&amp;').gsub(/</, '&lt;').gsub(/>/, '&gt;').gsub(/"/, '&quot;')#.gsub(/'/, '&039;')
    end

    ESCAPE_HTML = {'&'=>'&amp;', '<'=>'&lt;', '>'=>'&gt;', '"'=>'&quot;', "'"=>'&039;'}

    def h(val)
      val.to_s.gsub(/&<>"/) { ESCAPE_HTML[$&] }
    end

    def quote_url
    end

    def hash2qs(hash)
      hash.collect {|k, v| "#{quote_url(k.to_s)}=#{quote_url(v.to_s)}" }.join('&')
    end

    def options2hash(options)
      case options
      when Array
        hash = {}
        options.each {|v| v.is_a?(Hash) ? hash.update(v) : (hash[v] = true) }
        return hash
      when Hash
        return hash
      when nil
        return {}
      else
        raise ArgumentError.new("#{options.inspect}: hash or array expected.")
      end
    end

    def dummy_env(method='GET', path='/', kwargs={})
      require 'stringio' unless defined?(StringIO)
      #: if qs is dict then converts it into query string
      qs   = kwargs[:qs]
      qs   = hash2qs(qs)   if qs.is_a?(Hash)
      #: if body is dict then converts it into query string
      body = kwargs[:body]
      body = hash2qs(body) if body.is_a?(Hash)
      #: sets keys and values automatically
      require 'stringio'
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
        'rack.version'      => [1, 0],
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
      env.update(kwargs)
      #: returns dict object
      return env
    end


  end


end
