# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


module K8


  class Params < Hash

    def str(key, strip=true)
      s = self[key] || ''
      s = s.strip if strip
      return s.empty? ? nil : s
    end

    def text(key, nl=true)
      s = self[key] || ''
      s = s.gsub(/\r\n/, "\n") if nl
      return s.empty? ? nil : s
    end

    def int(key, default=nil)
      begin
        return Integer(self[key] || '')
      rescue ArgumentError
        return default
      end
    end

    def float(key, default=nil)
      begin
        return Float(self[key] || '')
      rescue ArgumentError
        return default
      end
    end

    def bool(key, default=nil)
      s = self.str(key)
      return true  if s == "1"
      return false if s == "0"
      return default
    end

    def view(prefix)
      prefix = "#{prefix}." unless prefix[-1] == ?.
      return ParamsView.new(self, prefix)
    end

    def with_prefix(prefix)
      bkup = @prefix
      @prefix = prefix
      yield
    ensure
      @prefix = bkup
    end

  end


  class ParamsView

    def initialize(params, prefix)
      @params = params
      @prefix = prefix
    end

    attr_reader :params

    def original
      return @params
    end

    def str(key, strip=true)
      return @params.str("#{@prefix}#{key}", strip)
    end

    def text(key, nl=true)
      return @params.text("#{@prefix}#{key}", nl)
    end

    def int(key, default=nil)
      return @params.int("#{@prefix}#{key}", default)
    end

    def float(key, default=nil)
      return @params.float("#{@prefix}#{key}", default)
    end

    def bool(key, default=nil)
      return @params.bool("#{@prefix}#{key}", default)
    end

  end


  class Errors < Hash

    def initialize
      @keys = []
      @prefix = nil
    end

    attr_accessor :prefix

    def prefix=(prefix)
      prefix << "." if prefix && prefix[-1] != ?.
      @prefix = prefix
    end

    def with_prefix(prefix)
      bkup = @prefix
      @prefix = prefix
      yield
    ensure
      @prefix = bkup
    end

    alias _orig_has_key? has_key?

    def [](key)
      key = "#{prefix}#{key}" if @prefix
      super(key)
    end

    def []=(key, val)
      key = "#{prefix}#{key}" if @prefix
      @keys << key unless _orig_has_key?(key)
      super(key, val)
    end

    def key?(key)
      key = "#{@prefix}#{key}" if @prefix
      super(key)
    end

    def has_key?(key)
      key = "#{@prefix}#{key}" if @prefix
      super(key)
    end

    def each
      @keys.each do |key|
        yield [key, self[key]]
      end
    end

    def each_pair
      @keys.each do |k|
        yield k, self[k]
      end
    end

    def classattr(key)
      self[key] ? " class=\"err-exist\"" : nil
    end

  end


end
