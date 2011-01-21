# -*- coding: utf-8 -*-

###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'keight/util'


module K8


  class ConfigObject < Hash

    def initialize(parent=nil)
      @parent = parent
    end

    attr_accessor :parent

    def [](key)
      return super(key)   if has_key?(key)
      return @parent[key] if @parent
      raise NameError.new("#{key.inspect}: key not found.")
    end

    def key?(key)
      return has_key?(key) ? true : @parent ? @parent.key?(key) : false
    end

    def each(&block)
      super(&block)
      @parent.each(&block) if @parent
      return self
    end

    def each_pair(&block)
      super(&block)
      @parent.each_pair(&block) if @parent
      return self
    end

  end


  #Config = {}
  Config = K8::ConfigObject.new()
  Config[:root_url_path] = nil
  Config[:root_dir_path] = nil
  Config[:template_path] = ['_templates', '.']
  Config[:error_template_file] = "_templates/_internal_error.html.tjn"

end
