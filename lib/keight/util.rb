# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


require 'keight/params'


module K8


  module Util


    module_function

    def escape_html(val)
      val.to_s.gsub(/&/, '&amp;').gsub(/</, '&lt;').gsub(/>/, '&gt;').gsub(/"/, '&quot;').gsub(/'/, '&#039;')
    end

    ESCAPE_HTML = {'&'=>'&amp;', '<'=>'&lt;', '>'=>'&gt;', '"'=>'&quot;', "'"=>'&#039;'}

    def h(val)
      val.to_s.gsub(/[&<>"]/) { ESCAPE_HTML[$&] }
    end

    UNESCAPE_HTML = {'&amp;'=>'&amp', '&lt;'=>'<', '&gt;'=>'>', '&quot;'=>'"', '&#039;'=>"'"}

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

    def parse_query_string(query_string, parse_dotted=false)
      params = Params.new
      (query_string || '').split(/[&;]/n).each do |s|
        k, v = s.split(/\=/, 2)
        #k = unquote_uri(k) unless k =~ /\A[-\.\w]+\z/
        #v = unquote_uri(v) unless k =~ /\A[-\.\w]+\z/
        k = unquote_uri(k) if k =~ /%|\+/
        v = unquote_uri(v) if v =~ /%|\+/
        if parse_dotted
          normalize_dotted_params(params, k, v)
        else
          if k =~ /\[\]\z/
            (params[k] ||= []) << v
          else
            params[k] = v
          end
        end
      end
      params
    end

    def normalize_dotted_params(params, k, v)
      items = k.split(/\./)
      d = params  # dictionary
      items[0...-1].each do |item|
        if d[item].is_a?(Hash)
          d = d[item]
        else
          d = d[item] = {}
        end
      end
      item = items[-1]
      #if item.end_with?('[]')
      if item =~ /\[\]\z/
        #item = item[0...-2]
        if d[item].is_a?(Array)
          d[item] << v
        else
          d[item] = [v]
        end
      else
        d[item] = v
      end
    end

    ## ex. hash2qs(:a=>1, :b=>2)  #=> "a=1&b=2")
    def hash2qs(hash, sep='&')
      hash.collect {|k, v| "#{quote_uri(k.to_s)}=#{quote_uri(v.to_s)}" }.join(sep)
    end

    ## ex. options2hash(:required, :type=>'str')  #=> {:required=>true, :type=>"str"}
    def options2hash(options)
      case options
      when Array
        hash = options[-1].is_a?(Hash) ? options.pop : {}
        options.each {|k| hash[k] = true }
        return hash
      when Hash
        return options
      when nil
        return {}
      else
        raise ArgumentError.new("#{options.inspect}: hash or array expected.")
      end
    end


  end


  class PrototypeObject

    def initialize(prototype=nil)
      @__proto__ = prototype
    end

    attr_accessor :__proto__

    def method_missing(method_name, *args)
      method_name.to_s =~ /([=!?])?\z/
      name = $`
      ch = $1
      case ch
      when nil, '?'
        if instance_variable_defined?("@#{name}")
          return instance_variable_get("@#{name}")
        elsif @__proto__
          return @__proto__.__send__(method_name, *args)
        else
          return super(method_name, *args)
        end
      when '='
        instance_variable_set("@#{name}", args[0])
        eval "class << self
                def #{name}; @#{name}; end
              end"
      when '!'
        if instance_variable_defined?("@#{name}")
          return instance_variable_get("@#{name}")
        else
          begin
            return @__proto__.__send__(method_name, *args)
          rescue NameError
            return nil
          end
        end
      else
        raise "assertion failed: ch=#{ch.inspect}"
      end
    end

  end


end
