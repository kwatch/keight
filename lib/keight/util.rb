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
      val.to_s.gsub(/[&<>"]/) { ESCAPE_HTML[$&] }
    end

    UNESCAPE_HTML = {'&amp;'=>'&amp', '&lt;'=>'<', '&gt;'=>'>', '&quot;'=>'"', '&039;'=>"'"}

    def unescape_html(str)
      str.to_s.gsub(/&(amp|lt|gt|quot|039);/) { UNESCAPE_HTML[$1] }
    end

    def quote_uri(str)
      #str.gsub(/([^ a-zA-Z0-9_.-]+)/n) {
      #  '%' + $1.unpack('H2' * $1.size).join('%').upcase
      #}.tr(' ', '+')
      str.gsub(/[^ a-zA-Z0-9_.-]+/n) {
        '%' + $&.unpack('H2' * $&.size).join('%').upcase
      }.tr(' ', '+')
    end

    def unquote_uri(str)
      #str.tr('+', ' ').gsub(/((?:%[0-9a-fA-F]{2})+)/n) {
      #  [$1.delete('%')].pack('H*')
      #}
      #str.tr('+', ' ').gsub(/((?:%[0-9a-fA-F][0-9a-fA-F])+)/n) {
      #  [$1.delete('%')].pack('H*')
      #}
      str.tr('+', ' ').gsub(/(?:%[0-9a-fA-F][0-9a-fA-F])+/n) {
        [$&.delete('%')].pack('H*')
      }
    end

    def parse_query_string(query_string)
      params = {}
      (query_string || '').split(/[&;]/n).each do |s|
        k, v = s.split(/=/, 2)
        k = unquote_uri(k) unless k =~ /\A[-\.\w]+\z/
        v = unquote_uri(v) unless k =~ /\A[-\.\w]+\z/
        if k =~ /\[\]\z/
          (params[k] ||= []) << v
        else
          params[k] = v
        end
      end
      params
    end

    def hash2qs(hash)
      hash.collect {|k, v| "#{quote_uri(k.to_s)}=#{quote_uri(v.to_s)}" }.join('&')
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
