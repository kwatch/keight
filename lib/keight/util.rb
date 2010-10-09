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


  end


end
