
if RUBY_VERSION < '1.8.7'


  class Object

    def tap(*args)
      yield(*args)
      self
    end

    def instance_variable_defined?(name)
      instance_variables().include?(name.to_s)
    end unless Object.new.respond_to?('instance_variable_defined?')

  end


  class String

    def start_with?(s)
      self[0, s.length] == s
    end

    def end_with?(s)
      self[-s.length..-1] == s
    end

  end


  class Integer

    def odd?
      self % 2 == 1
    end

    def even?
      self % 2 == 0
    end

  end


  module Enumerable

    def group_by
      hash = {}
      each {|x| (hash[yield(x)] ||= []) << x }
      hash
    end

    #--
    #def index_by
    #  hash = {}
    #  each {|x| hash[yield(x)] = x }
    #  hash
    #end
    #++

  end


  class Symbol

    def to_proc
      proc {|x| x.__send__(self) }
    end

  end


end
