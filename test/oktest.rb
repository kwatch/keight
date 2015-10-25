###
### $Release: $
### $Copyright: copyright(c) 2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

require 'test/unit'
if defined?(Test::Unit::Runner)
  Test::Unit::Runner.class_variable_set(:@@stop_auto_run, true)
end

#require 'section/tmp'
#require 'section/recorder'


module Oktest


  VERSION = '$Release: 0.0.0 $'.split(/ /)[1]


  class SkipException < Exception
  end

  class TodoException < Exception
  end

  FAIL_EXCEPTION = defined?(MiniTest) ? MiniTest::Assertion : Test::Unit::AssertionFailedError  # :nodoc:
  SKIP_EXCEPTION = SkipException
  TODO_EXCEPTION = TodoException


  class AssertionObject
    include Test::Unit::Assertions

    self.instance_methods.grep(/\?\z/).each do |k|
      undef_method k unless k.to_s == 'equal?' || k.to_s =~ /^assert/
    end

    NOT_YET = {}

    def initialize(actual, bool, location)
      @actual   = actual
      @bool     = bool
      @location = location
    end

    attr_reader :actual, :bool, :location

    def _done
      AssertionObject::NOT_YET.delete(self.__id__)
    end
    private :_done

    def self.report_not_yet
      return if NOT_YET.empty?
      NOT_YET.each_value do |ass|
        $stderr.write "** warning: ok() is called but not tested yet (at #{ass.location})\n"
      end
    end

    def _not
      return @bool ? '' : 'not '
    end
    private :_not

    if defined?(MiniTest)
      def __assert result
        if result
          assert true
        else
          #assert_block(yield) { false }
          #flunk yield
          assert false, yield
        end
      end
    else
      def __assert result
        if result
          assert true
        else
          assert_block(yield) { false }
        end
      end
    end

    def NOT
      @bool = ! @bool
      self
    end

    def ==(expected)
      _done()
      __assert(@bool == (@actual == expected)) {
        if @bool && ! (@actual == expected) \
          && @actual.is_a?(String) && expected.is_a?(String) \
          && (@actual =~ /\n/ || expected =~ /\n/)
          diff = Util.unified_diff(expected, @actual, "--- $expected\n+++ $actual\n")
          "$actual == $expected: failed.\n#{diff}"
        else
          op = @bool ? '==' : '!='
          "$actual #{op} $expected: failed.\n"\
          "    $actual:   #{@actual.inspect}\n"\
          "    $expected: #{expected.inspect}"
        end
      }
      self
    end

    if RUBY_VERSION >= '1.9'
      op = @bool ? '==' : '!='
      eval <<-END, binding, __FILE__, __LINE__+1
      def !=(expected)
        _done()
        __assert(@bool == (@actual != expected)) {
          "$actual #{op} $expected: failed.\n"\
          "    $actual:   \#{@actual.inspect}\n"\
          "    $expected: \#{expected.inspect}"
        }
        self
      end
      END
    end

    #--
    #def >  expected; _done(); assert_operator(@actual, @bool ? :> : :<=, expected); self end
    def >= expected; _done(); assert_operator(@actual, @bool ? :>= : :<, expected); self end
    def <  expected; _done(); assert_operator(@actual, @bool ? :< : :>=, expected); self end
    def <= expected; _done(); assert_operator(@actual, @bool ? :<= : :>, expected); self end
    #++

    def >(expected)
      _done()
      __assert(@bool == (@actual > expected)) {
        "#{@actual.inspect} #{@bool ? '>' : '<='} #{expected}: failed."
      }
      self
    end

    def >=(expected)
      _done()
      __assert(@bool == (@actual >= expected)) {
        "#{@actual.inspect} #{@bool ? '>=' : '<'} #{expected}: failed."
      }
      self
    end

    def <(expected)
      _done()
      __assert(@bool == (@actual < expected)) {
        "#{@actual.inspect} #{@bool ? '<' : '>='} #{expected}: failed."
      }
      self
    end

    def <=(expected)
      _done()
      __assert(@bool == (@actual <= expected)) {
        "#{@actual.inspect} #{@bool ? '<=' : '>'} #{expected}: failed."
      }
      self
    end

    def =~(expected)
      _done()
      #@bool ? assert_match(expected, @actual) : assert_no_match(expected, @actual)
      __assert(@bool == !!(@actual =~ expected)) {
        op = @bool ? '=~' : '!~'
        msg = "$actual #{op} $expected: failed.\n"\
              "    $expected: #{expected.inspect}\n"
        if @actual =~ /\n\z/
          msg << "    $actual:   <<'END'\n#{@actual}END\n"
        else
          msg << "    $actual:   #{@actual.inspect}\n"
        end
      }
      self
    end

    if RUBY_VERSION >= "1.9"
      eval <<-'END', binding, __FILE__, __LINE__+1
      def !~(expected)
        _done()
        #@bool ? assert_no_match(expected, @actual) : assert_match(expected, @actual)
        __assert(@bool == !!(@actual !~ expected)) {
          op = @bool ? '!~' : '=~'
          msg = "$actual #{op} $expected: failed.\n"\
                "    $expected: #{expected.inspect}\n"
          if @actual =~ /\n\z/
            msg << "    $actual:   <<'END'\n#{@actual}END\n"
          else
            msg << "    $actual:   #{@actual.inspect}\n"
          end
        }
        self
      end
      END
    end

    def in_delta?(expected, delta)
      _done()
      __assert(@bool == !!((@actual - expected).abs < delta)) {
        eq = @bool ? '' : ' == false'
        "($actual - $expected).abs < #{delta}#{eq}: failed.\n"\
                "    $actual:   #{@actual.inspect}\n"\
                "    $expected: #{expected.inspect}\n"\
                "    ($actual - $expected).abs: #{(@actual - expected).abs.inspect}"
      }
      self
    end

    def same?(expected)
      _done()
      #@bool ? assert_same(expected, @actual) \
      #      : assert_not_same(expected, @actual)
      __assert(@bool == !! @actual.equal?(expected)) {
        eq = @bool ? '' : ' == false'
        "$actual.equal?($expected)#{eq}: failed.\n"\
        "    $actual:   #{@actual.inspect}\n"\
        "    $expected: #{expected.inspect}\n"
      }
      self
    end

    def method_missing(method_name, *args)
      _done()
      method_name.to_s =~ /\?\z/  or
        super
      begin
        ret = @actual.__send__(method_name, *args)
      rescue NoMethodError, TypeError => ex
        ex.set_backtrace(caller(1))
        raise ex
      end
      if ret == true || ret == false
        __assert(@bool == ret) {
          args = args.empty? ? '' : "(#{args.collect {|x| x.inspect }.join(', ')})"
          eq = @bool ? '' : ' == false'
          "$actual.#{method_name}#{args}#{eq}: failed.\n"\
          "    $actual:   #{@actual.inspect}"
        }
      else
        raise TypeError.new("ok(): #{@actual.class}##{method_name}() expected to return true or false, but got #{ret.inspect}.")
      end
      self
    end

    #--
    #def same?         expected ; _done(); assert_same        expected, @actual; self; end
    #def not_same?     expected ; _done(); assert_not_same    expected, @actual; self; end
    #def is_a?         expected ; _done(); assert_kind_of     expected, @actual; self; end
    #def instance_of?  expected ; _done(); assert_instance_of expected, @actual; self; end
    #def respond_to?   expected ; _done(); assert_respond_to  expected, @actual; self; end
    #def nil?     ; _done(); assert_nil     @actual; self; end
    #def not_nil? ; _done(); assert_not_nil @actual; self; end
    #++

    def raise?(expected=Exception, errmsg=nil)
      _done()
      proc_obj = @actual
      if @bool
        ex = nil
        begin
          proc_obj.call
        rescue Exception => ex
          ex.is_a?(expected)  or
            __assert(false) { "Expected #{expected.inspect} to be raised but got #{ex.class}." }
        end
        (class << proc_obj; self; end).class_eval { attr_accessor :exception }
        proc_obj.exception = ex
        __assert(! ex.nil?) { "Expected #{expected.inspect} to be raised but nothing raised." }
        case errmsg
        when nil;     # do nothing
        when Regexp
          __assert(ex.message =~ errmsg) {
            "$error_message =~ #{errmsg.inspect}: failed.\n"\
            "    $error_message: #{ex.message.inspect}"
          }
        else
          __assert(errmsg == ex.message) {
            "$error_message == #{errmsg.inspect}: failed.\n"\
            "    $error_message: #{ex.message.inspect}"
          }
        end
      else
        ! errmsg  or
          raise ArgumentError.new("#{errmsg.inspect}: NOT.raise?() can't take errmsg.")
        begin
          proc_obj.call
        rescue Exception => ex
          __assert(! ex.is_a?(expected)) {
            "#{expected.inspect} should not be raised but got #{ex.inspect}."
          }
        end
      end
      self
    end

    #--
    #def not_raise?
    #  _done()
    #  ! @bool  or
    #    StandardError.new("ok().not_raise? is not available with '.NOT'.")
    #  proc_obj = @actual
    #  assert_nothing_raised(&proc_obj)
    #  self
    #end
    #++

    def in?(expected)
      _done()
      __assert(@bool == !! expected.include?(@actual)) {
        eq = @bool ? '' : ' == false'
        "$expected.include?($actual)#{eq}: failed.\n"\
        "    $actual:   #{@actual.inspect}\n"\
        "    $expected: #{expected.inspect}"
      }
      self
    end

    def include?(expected)
      _done()
      __assert(@bool == !! @actual.include?(expected)) {
        eq = @bool ? '' : ' == false'
        "$actual.include?($expected)#{eq}: failed.\n"\
        "    $actual:   #{@actual.inspect}\n"\
        "    $expected: #{expected.inspect}"
      }
      self
    end

    def attr(name, val=nil)
      _done()
      d = name.is_a?(Hash) ? name : {name=>val}
      d.each_pair do |k, v|
        attr_val = @actual.__send__(k)
        __assert(@bool == (attr_val == v)) {
          op = @bool ? '==' : '!='
          "$actual.#{k} #{op} $expected: failed.\n"\
          "    $actual.#{k}: #{attr_val}\n"\
          "    $expected: #{v.inspect}"\
        }
      end
      self
    end

    def length(n)
      _done()
      __assert(@bool == (@actual.length == n)) {
        op = @bool ? '==' : '!='
        "$actual.length #{op} #{n}: failed.\n"\
        "    $actual.length: #{@actual.length}\n"\
        "    $actual:   #{actual.inspect}"
      }
      self
    end

    #--
    #def empty?;     _done(); @actual.empty?       or flunk "#{@actual}.empty?: failed.";      self; end
    #def not_empty?; _done(); ! @actual.empty?     or flunk "! #{@actual}.empty?: failed.";    self; end
    #def truthy?;    _done(); !! @actual == true   or flunk "!! #{@actual} == true: failed.";  self; end
    #def falsy?;     _done(); !! @actual == false  or flunk "!! #{@actual} == false: failed."; self; end
    #++

    def truthy?
      _done()
      __assert(@bool == (!!@actual == true)) {
        op = @bool ? '==' : '!='
        "!!$actual #{op} true: failed.\n"\
        "    $actual:   #{@actual.inspect}"
      }
      self
    end

    def falsy?
      _done()
      __assert(@bool == (!!@actual == false)) {
        op = @bool ? '==' : '!='
        "!!$actual #{op} false: failed.\n"\
        "    $actual:   #{@actual.inspect}"
      }
      self
    end

    def file_exist?
      _done()
      __assert(@bool == File.file?(@actual)) {
        eq = @bool ? '' : ' == false'
        "File.file?($actual)#{eq}: failed.\n"\
        "    $actual:   #{@actual.inspect}"
      }
      self
    end

    def dir_exist?
      _done()
      __assert(@bool == File.directory?(@actual)) {
        eq = @bool ? '' : ' == false'
        "File.directory?($actual)#{eq}: failed.\n"\
        "    $actual:   #{@actual.inspect}"
      }
      self
    end

    def exist?
      _done()
      __assert(@bool == File.exist?(@actual)) {
        eq = @bool ? '' : ' == false'
        "File.exist?($actual)#{eq}: failed.\n"\
        "    $actual:   #{@actual.inspect}"
      }
      self
    end

  end


  class ScopeObject

    def initialize
      @children = []
      @fixtures = {}
    end

    attr_accessor :name, :parent, :children, :before, :after, :before_all, :after_all, :fixtures
    attr_accessor :_klass, :_prefix  #:nodoc:

    def add_child(child)
      if child.is_a?(ScopeObject)
        child.parent.nil?  or
          raise ArgumentError.new("add_child(): can't add child scope which already belongs to other.")
        child.parent = self
      end
      @children << child
    end

    def get_fixture_info(name)
      return @fixtures[name]
      #@fixtures ? @fixtures[name] : nil   # or [nil, nil, nil]?
    end

    def new_context
      return @_klass.new
    end

    def accept(runner, *args)
      raise NotImplementedError.new("#{self.class.name}#accept(): not implemented yet.")
    end

    def _repr(depth=0, buf="")
      indent = "  " * depth
      buf << "#{indent}-\n"
      instance_variables().sort.each do |name|
        next if name.to_s == "@children"
        buf << "#{indent}  #{name}: #{instance_variable_get(name).inspect}\n"
      end
      @children.each {|child| child._repr(depth+1, buf) }
      return buf
    end

    def +@
      self
    end

  end


  class FileScopeObject < ScopeObject

    attr_accessor :filename

    def initialize(filename=nil)
      super()
      @filename = filename
    end

    def accept(runner, *args)
      return runner.run_topic(self, *args)
    end

  end


  class TopicObject < ScopeObject

    def initialize(name=nil)
      super()
      @name = name
    end

    def accept(runner, *args)
      return runner.run_topic(self, *args)
    end

  end


  module ScopeClassMethods

    #attr_accessor :_scope

    def before(&block);     @_scope.before     = block;  end
    def after(&block);      @_scope.after      = block;  end
    def before_all(&block); @_scope.before_all = block;  end
    def after_all(&block);  @_scope.after_all  = block;  end

    def fixture(name, &block)
      location = caller(1).first
      argnames = block.arity > 0 ? Util.block_argnames(block, location) : nil
      @_scope.fixtures[name] = [block, argnames, location]
    end

    def topic(name, &block)
      topic = TopicObject.new(name)
      @_scope.add_child(topic)
      klass = Class.new(self)
      klass.class_eval do
        extend ScopeClassMethods
        include Test::Unit::Assertions
        include SpecHelper
        @_scope = topic
      end
      klass.class_eval(&block)
      topic._klass = klass
      topic._prefix = '*'
      return topic
    end

    def case_when(desc, &block)
      return __case_when("When #{desc}", &block)
    end

    def case_else(&block)
      return __case_when("Else", &block)
    end

    def __case_when(desc, &block)
      obj = topic(desc, &block)
      obj._prefix = '-'
      return obj
    end
    private :__case_when

    def spec(desc, &block)
      location = caller(1).first
      if block
        argnames = Util.block_argnames(block, location)
      else
        block = proc { raise TodoException.new("not implemented yet") }
        argnames = []
      end
      spec = SpecObject.new(desc, block, argnames, location)
      @_scope.add_child(spec)
      spec._prefix = '-'
      return spec
    end

  end


  FILESCOPES = []


  def self.scope(&block)
    filename = caller(1).first =~ /:\d+/ ? $` : nil
    filename = filename.sub(/\A\.\//, '')
    scope = FileScopeObject.new(filename)
    klass = Class.new
    klass.class_eval do
      extend ScopeClassMethods
      @_scope = scope
    end
    klass.class_eval(&block)
    scope._klass = klass
    FILESCOPES << scope
    return scope
  end


  class SpecObject

    def initialize(desc, block, argnames, location)
      @desc = desc
      @block = block
      @argnames = argnames
      @location = location   # necessary when raising fixture not found error
    end

    attr_reader :desc, :block, :argnames, :location #:nodoc:
    attr_accessor :_prefix   #:nodoc:

    def accept(runner, *args)       #:nodoc:
      runner.run_spec(self, *args)
    end

    def _repr(depth=0, buf="")       #:nodoc:
      buf << "  " * depth << "- #{@desc}\n"
      return buf
    end

    def -@
      self
    end

  end


  module SpecHelper

    attr_accessor :_TODO, :_at_end_blocks

    def skip_when(condition, reason)
      raise SkipException.new(reason) if condition
    end

    def TODO
      @_TODO = true
    end

    def at_end(&block)
      (@_at_end_blocks ||= []) << block
    end

    def tmp
      unless @_tmp
        require 'section9/tmp' unless defined?(Section9::Tmp)
        @_tmp = Section9::Tmp.new
        at_end { @_tmp.revert }
      end
      return @_tmp
    end

    def recorder
      require 'section9/recorder' unless defined?(Section9::Recorder)
      return Section9::Recorder.new
    end

  end


  STATUSES = [:PASS, :FAIL, :ERROR, :SKIP, :TODO]


  class Runner

    def initialize(reporter)
      @reporter = reporter
    end

    def run_topic(topic, depth, parent)
      @reporter.enter_topic(topic, depth)
      call_before_all_block(topic)
      topic.children.each do |child|
        child.accept(self, depth+1, topic)
      end
      call_after_all_block(topic)
      @reporter.exit_topic(topic, depth)
    end

    def run_spec(spec, depth, parent)
      return if ENV['SPEC'] && ENV['SPEC'] != spec.desc
      @reporter.enter_spec(spec, depth)
      topic = parent
      context = new_context(topic, spec)
      call_before_blocks(topic, context)
      status = :PASS
      ex = nil
      begin
        if spec.argnames.empty?
          call_spec_block(spec, context)
        else
          values = get_fixture_values(spec.argnames, topic, spec, context)
          call_spec_block(spec, context, *values)
        end
      rescue NoMemoryError   => ex;  raise ex
      rescue SignalException => ex;  raise ex
      rescue FAIL_EXCEPTION  => ex;  status = :FAIL
      rescue SKIP_EXCEPTION  => ex;  status = :SKIP
      rescue TODO_EXCEPTION  => ex;  status = :TODO
      rescue Exception       => ex;  status = :ERROR
      end
      if context._TODO
        if status == :PASS
          status = :FAIL
          ex = FAIL_EXCEPTION.new("spec should be failed (because not implemented yet), but passed unexpectedly.")
        elsif status == :FAIL
          status = :TODO
          ex = TODO_EXCEPTION.new("not implemented yet")
        end
        ex.set_backtrace([spec.location])
      end
      begin
        call_at_end_blocks(context)
      ensure
        call_after_blocks(topic, context)
      end
      @reporter.exit_spec(spec, depth, status, ex, parent)
    end

    def run_all
      @reporter.enter_all(self)
      while (scope = FILESCOPES.shift)
        run_filescope(scope)
      end
      @reporter.exit_all(self)
    end

    def run_filescope(filescope)
      @reporter.enter_file(filescope.filename)
      call_before_all_block(filescope)
      filescope.children.each do |child|
        child.accept(self, 0, nil)
      end
      call_after_all_block(filescope)
      @reporter.exit_file(filescope.filename)
    end

    private

    def new_context(topic, spec)
      return topic.new_context()
    end

    def get_fixture_values(names, topic, spec, context)
      return FixtureManager.instance.get_fixture_values(names, topic, spec, context)
    end

    def _call_blocks_parent_first(topic, name, obj)
      blocks = []
      while topic
        block = topic.__send__(name)
        blocks << block if block
        topic = topic.parent
      end
      blocks.reverse.each {|blk| obj.instance_eval(&blk) }
      blocks.clear
    end

    def _call_blocks_child_first(topic, name, obj)
      while topic
        block = topic.__send__(name)
        obj.instance_eval(&block) if block
        topic = topic.parent
      end
    end

    def call_before_blocks(topic, spec)
      _call_blocks_parent_first(topic, :before, spec)
    end

    def call_after_blocks(topic, spec)
      _call_blocks_child_first(topic, :after, spec)
    end

    def call_before_all_block(topic)
      block = topic.before_all
      topic.instance_eval(&block) if block
    end

    def call_after_all_block(topic)
      block = topic.after_all
      topic.instance_eval(&block) if block
    end

    def call_spec_block(spec, context, *args)
      if args.empty?
        context.instance_eval(&spec.block)
      else
        context.instance_exec(*args, &spec.block)
      end
    end

    def call_at_end_blocks(context)
      blocks = context._at_end_blocks
      if blocks
        blocks.reverse_each {|block| context.instance_eval(&block) }
        blocks.clear
      end
    end

  end


  RUNNER = Runner


  class FixtureManager

    def self.instance
      return @instance ||= self.new
    end

    def get_fixture_values(names, topic, spec, context, location=nil, resolved={}, resolving=[])
      location ||= spec.location
      return names.collect {|name|
        ! resolving.include?(name)  or
          raise _looped_dependency_error(name, resolving, location)
        get_fixture_value(name, topic, spec, context, location, resolved, resolving)
      }
    end

    def get_fixture_value(name, topic, spec, context, location=nil, resolved={}, resolving=[])
      return resolved[name] if resolved.key?(name)
      location ||= spec.location
      tuple = topic.get_fixture_info(name)
      if tuple
        block, argnames, location = tuple
        if argnames
          resolving << name
          args = get_fixture_values(argnames, topic, spec, context, location, resolved, resolving)
          (popped = resolving.pop) == name  or
            raise "** assertion failed: name=#{name.inspect}, resolvng[-1]=#{popped.inspect}"
          val = context.instance_exec(*args, &block)
        else
          val = context.instance_eval(&block)
        end
        resolved[name] = val
        return val
      elsif topic.parent
        return get_fixture_value(name, topic.parent, spec, context, location, resolved, resolving)
      else
        ex = FixtureNotFoundError.new("#{name}: fixture not found. (spec: #{spec.desc})")
        ex.set_backtrace([location])
        raise ex
      end
    end

    private

    def _looped_dependency_error(name, resolving, location)
      resolving << name
      i = resolving.index(name)
      s1 = resolving[0...i].join('->')
      s2 = resolving[i..-1].join('=>')
      loop = s1.empty? ? s2 : "#{s1}->#{s2}"
      #location = $1 if location =~ /(.*:\d+)/
      ex = LoopedDependencyError.new("fixture dependency is looped: #{loop}")
      ex.set_backtrace([location])
      return ex
    end

  end


  class FixtureNotFoundError < StandardError
  end

  class LoopedDependencyError < StandardError
  end


  class Reporter

    def enter_all(runner); end
    def exit_all(runner); end
    def enter_file(filename); end
    def exit_file(filename); end
    def enter_topic(topic, depth); end
    def exit_topic(topic, depth); end
    def enter_spec(spec, depth); end
    def exit_spec(spec, depth, status, error, parent); end
    #
    def counts; {}; end

  end


  class BaseReporter < Reporter

    LABELS = { :PASS=>'pass', :FAIL=>'Fail', :ERROR=>'ERROR', :SKIP=>'Skip', :TODO=>'TODO' }
    CHARS  = { :PASS=>'.', :FAIL=>'f', :ERROR=>'E', :SKIP=>'s', :TODO=>'t' }


    def initialize
      @exceptions = []
      @counts = {}
    end

    attr_reader :counts

    def enter_all(runner)
      reset_counts()
      @start_at = Time.now
    end

    def exit_all(runner)
      elapsed = Time.now - @start_at
      puts footer(elapsed)
    end

    def enter_file(filename)
    end

    def exit_file(filename)
    end

    def enter_topic(topic, depth)
    end

    def exit_topic(topic, depth)
    end

    def enter_spec(spec, depth)
    end

    def exit_spec(spec, depth, status, ex, parent)
      @counts[status] += 1
      @exceptions << [spec, status, ex, parent] if status == :FAIL || status == :ERROR
    end

    protected

    def reset_counts
      STATUSES.each {|sym| @counts[sym] = 0 }
    end

    def print_exceptions
      sep = '-' * 70
      @exceptions.each do |tuple|
        puts sep
        print_exc(*tuple)
        tuple.clear
      end
      puts sep if ! @exceptions.empty?
      @exceptions.clear
    end

    def print_exc(spec, status, ex, parent)
      label = Color.status(status, LABELS[status])
      topic = parent
      path = Color.topic(spec_path(spec, topic))
      topic = parent
      puts "[#{label}] #{path}"
      print_exc_backtrace(ex, status)
      print_exc_message(ex, status)
    end

    def print_exc_backtrace(ex, status)
      rexp = FILENAME_FILTER
      prev_file = prev_line = nil
      ex.backtrace.each_with_index do |str, i|
        next if str =~ rexp && ! (i == 0 && status == :ERROR)
        linestr = nil
        if str =~ /:(\d+)/
          file = $`         # file path
          line = $1.to_i    # line number
          next if file == prev_file && line == prev_line
          linestr = Util.file_line(file, line) if str && File.exist?(file)
          prev_file, prev_line = file, line
        end
        puts "    #{str}"
        puts "        #{linestr.strip}"  if linestr
      end
    end

    FILENAME_FILTER = %r`/(?:oktest|minitest/unit|test/unit(?:/assertions|/testcase)?)\.rbc?:` #:nodoc:

    def print_exc_message(ex, status)
      #puts Color.status(status, "#{ex.class.name}: #{ex}")
      if status == :FAIL
        msg = "#{ex}"
      else
        msg = "#{ex.class.name}: #{ex}"
      end
      lines = []
      msg.each_line {|line| lines << line }
      #puts Color.status(status, lines.shift.chomp)
      puts lines.shift.chomp
      puts lines.join.chomp unless lines.empty?
      puts ex.diff if ex.respond_to?(:diff) && ex.diff   # for oktest.rb
    end

    def footer(elapsed)
      total = 0; @counts.each {|k, v| total += v }
      buf = "## total:#{total}"
      STATUSES.each do |st|
        s = "#{st.to_s.downcase}:#{@counts[st]}"
        s = Color.status(st, s) if @counts[st] > 0
        buf << ", " << s
      end
      buf << "  (in %.3fs)" % elapsed
      return buf
    end

    def spec_path(spec, topic)
      arr = []
      while topic
        arr << topic.name.to_s if topic.name
        topic = topic.parent
      end
      arr.reverse!
      arr << spec.desc
      return arr.join(" > ")
    end

  end


  class VerboseReporter < BaseReporter

    LABELS = { :PASS=>'pass', :FAIL=>'Fail', :ERROR=>'ERROR', :SKIP=>'Skip', :TODO=>'TODO' }

    def enter_topic(topic, depth)
      super
      puts "#{'  ' * depth}#{topic._prefix} #{Color.topic(topic.name)}"
    end

    def exit_topic(topic, depth)
      print_exceptions()
    end

    def enter_spec(spec, depth)
      if $stdout.tty?
        str = "#{'  ' * depth}#{spec._prefix} [    ] #{spec.desc}"
        print Util.strfold(str, 79)
        $stdout.flush
      end
    end

    def exit_spec(spec, depth, status, error, parent)
      super
      if $stdout.tty?
        print "\r"    # clear line
        $stdout.flush
      end
      label = Color.status(status, LABELS[status] || '???')
      msg = "#{'  ' * depth}- [#{label}] #{spec.desc}"
      #msg << " (reason: #{error.message})" if error.is_a?(SkipException)
      msg << " " << Color.reason("(reason: #{error.message})") if error.is_a?(SkipException)
      puts msg
    end

  end


  class SimpleReporter < BaseReporter

    def enter_file(filename)
      print "#{filename}: "
    end

    def exit_file(filename)
      puts
      print_exceptions()
    end

    def exit_spec(spec, depth, status, error, parent)
      super
      print Color.status(status, CHARS[status] || '?')
      $stdout.flush
    end

  end


  class PlainReporter < BaseReporter

    def exit_all(runner)
      elapsed = Time.now - @start_at
      puts
      print_exceptions()
      puts footer(elapsed)
    end

    def exit_spec(spec, depth, status, error, parent)
      super
      print Color.status(status, CHARS[status] || '?')
      $stdout.flush
    end

  end


  REPORTER = VerboseReporter


  REPORTER_CLASSES = {
    'verbose' => VerboseReporter,  'v' => VerboseReporter,
    'simple'  => SimpleReporter,   's' => SimpleReporter,
    'plain'   => PlainReporter,    'p' => PlainReporter,
  }


  #def self.run(*topics)
  #  opts = topics[-1].is_a?(Hash) ? topics.pop() : {}
  #  topics = TOPICS if topics.empty?
  #  return if topics.empty?
  #  klass = (opts[:style] ? REPORTER_CLASSES[opts[:style]] : REPORTER)  or
  #    raise ArgumentError.new("#{opts[:style].inspect}: unknown style.")
  #  reporter = klass.new
  #  runner = Runner.new(reporter)
  #  runner.run_all(*topics)
  #  counts = reporter.counts
  #  return counts[:FAIL] + counts[:ERROR]
  #end
  def self.run(opts={})
    return if FILESCOPES.empty?
    klass = (opts[:style] ? REPORTER_CLASSES[opts[:style]] : REPORTER)  or
      raise ArgumentError.new("#{opts[:style].inspect}: unknown style.")
    reporter = klass.new
    runner = Runner.new(reporter)
    runner.run_all()
    FILESCOPES.clear
    counts = reporter.counts
    return counts[:FAIL] + counts[:ERROR]
  end


  module Util

    module_function

    def file_line(filename, linenum)
      return nil unless File.file?(filename)
      @cache ||= [nil, []]
      if @cache[0] != filename
        @cache[0] = filename
        @cache[1].clear
        @cache[1] = lines = File.open(filename, 'rb') {|f| f.to_a }
      else
        lines = @cache[1]
      end
      return lines[linenum-1]
    end

    def block_argnames(block, location)
      return nil unless block
      return [] if block.arity <= 0
      if block.respond_to?(:parameters)
        argnames = block.parameters.collect {|pair| pair.last }
      else
        location =~ /:(\d+)/
        filename = $`
        linenum  = $1.to_i
        File.file?(filename)  or
          raise ArgumentError.new("block_argnames(): #{filename.inspect}: source file not found.")
        linestr = file_line(filename, linenum) || ""
        linestr =~ /(?:\bdo|\{) *\|(.*)\|/  or
          raise ArgumentError.new("spec(): can't detect block parameters at #{filename}:#{linenum}")
        argnames = $1.split(/,/).collect {|var| var.strip.intern }
      end
      return argnames
    end

    def strfold(str, width=80, mark='...')
      return str if str.length <= width
      return str[0, width - mark.length] + mark if str =~ /\A[\x00-\x7f]*\z/
      limit = width - mark.length
      w = len = 0
      str.split(//u).each do |ch|
        n = ch.length
        w += n == 1 ? 1 : 2
        break if w >= limit
        len += n
      end
      str = str[0, len] + mark if w >= limit
      return str
    end
    def strfold(str, width=80, mark='...')
      return str if str.bytesize <= width
      return str[0, width - mark.length] + mark if str.ascii_only?
      limit = width - mark.length
      w = len = 0
      str.each_char do |ch|
        w += ch.bytesize == 1 ? 1 : 2
        break if w >= limit
        len += 1
      end
      str = str[0, len] + mark if w >= limit
      return str
    end if RUBY_VERSION >= '1.9'


    def chain_errors(*errors)
    end


    def _text2lines(text, no_newline_msg=nil)
      lines = []
      text.each_line {|line| line.chomp!; lines << line }
      lines[-1] << no_newline_msg if no_newline_msg && text[-1] && text[-1] != ?\n
      return lines
    end
    private :_text2lines

    ## platform independent, but requires 'diff-lcs' gem
    def unified_diff(text_old, text_new, label="--- old\n+++ new\n", context=3)
      msg = "\\ No newline at end of string"
      lines_old = _text2lines(text_old, msg)
      lines_new = _text2lines(text_new, msg)
      #
      buf = "#{label}"
      len = 0
      prevhunk = hunk = nil
      diffs = Diff::LCS.diff(lines_old, lines_new)
      diffs.each do |diff|
        hunk = Diff::LCS::Hunk.new(lines_old, lines_new, diff, context, len)
        if hunk.overlaps?(prevhunk)
          hunk.unshift(prevhunk)
        else
          buf << prevhunk.diff(:unified) << "\n"
        end if prevhunk
        len = hunk.file_length_difference
        prevhunk = hunk
      end
      buf << prevhunk.diff(:unified) << "\n" if prevhunk
      return buf
    end

    ## platform depend, but not require extra library
    def diff_unified(text_old, text_new, label="--- old\n+++ new\n", context=3)
      tmp_old = "_tmp.old.#{rand()}"
      tmp_new = "_tmp.new.#{rand()}"
      File.open(tmp_old, 'w') {|f| f.write(text_old) }
      File.open(tmp_new, 'w') {|f| f.write(text_new) }
      begin
        #diff = `diff -u #{tmp_old} #{tmp_new}`
        diff = `diff --unified=#{context} #{tmp_old} #{tmp_new}`
      ensure
        File.unlink(tmp_old)
        File.unlink(tmp_new)
      end
      diff.sub!(/\A\-\-\-.*\n\+\+\+.*\n/, label.to_s)
      return diff
    end

    ## when diff-lcs is not installed then use diff command
    begin
      require 'diff/lcs'
      #require 'diff/lcs/string'
      require 'diff/lcs/hunk'
    rescue LoadError
      alias _unified_diff unified_diff
      alias unified_diff diff_unified
      class << self
        alias _unified_diff unified_diff
        alias unified_diff diff_unified
      end
    end

  end


  class Config

    @os_windows      = RUBY_PLATFORM =~ /mswin|mingw/i
    @auto_run        = true
    @color_available = ! @os_windows
    @color_enabled   = @color_available
    @diff_command    = @os_windows ? "diff.exe -u" : "diff -u"
    @system_exit     = true     # exit() on Oktest.main()

    class << self
      attr_accessor :auto_run, :color_available, :color_enabled, :system_exit
    end

  end


  module Color

    module_function

    def normal (s);  return s; end
    def bold   (s);  return "\x1b[0;1m#{s}\x1b[22m"; end
    def black  (s);  return "\x1b[1;30m#{s}\x1b[0m"; end
    def red    (s);  return "\x1b[1;31m#{s}\x1b[0m"; end
    def green  (s);  return "\x1b[1;32m#{s}\x1b[0m"; end
    def yellow (s);  return "\x1b[1;33m#{s}\x1b[0m"; end
    def blue   (s);  return "\x1b[1;34m#{s}\x1b[0m"; end
    def magenta(s);  return "\x1b[1;35m#{s}\x1b[0m"; end
    def cyan   (s);  return "\x1b[1;36m#{s}\x1b[0m"; end
    def white  (s);  return "\x1b[1;37m#{s}\x1b[0m"; end

    def topic(s); Config.color_enabled ? bold(s)   : s; end
    def spec (s); Config.color_enabled ? normal(s) : s; end
    def pass (s); Config.color_enabled ? green(s)  : s; end
    def fail (s); Config.color_enabled ? red(s)    : s; end
    def error(s); Config.color_enabled ? red(s)    : s; end
    def skip (s); Config.color_enabled ? yellow(s) : s; end
    def todo (s); Config.color_enabled ? yellow(s) : s; end
    def reason(s); Config.color_enabled ? yellow(s) : s; end
    def status(status, s); __send__(status.to_s.downcase, s); end

  end


  class TestGenerator

    def parse(io)
      tree = _parse(io, [], nil)
      return tree
    end

    def _parse(io, tree, end_indent)
      while (line = io.gets())
        case line
        when /^([ \t]*)end\b/
          return tree if $1 == end_indent
        when /^([ \t]*)(module|class|def) +(\w+[.:\w]*)/
          indent, keyword, topic = $1, $2, $3
          next if line =~ /\bend$/
          if keyword == 'def'
            topic = topic =~ /^self\./ ? ".#{$'}" : "\##{topic}"
          end
          newtree = []
          _parse(io, newtree, indent)
          tree << [indent, keyword, topic, newtree]
        when /^([ \t]*)\#[:;] (.*)/
          indent, keyword, spec = $1, 'spec', $2
          tree << [indent, keyword, spec]
        end
      end
      end_indent == nil  or
        raise "parse error: end_indent=#{end_indent.inspect}"
      return tree
    end
    private :_parse

    def transform(tree, depth=0)
      buf = ''
      tree.each do |tuple|
        _transform(tuple, depth, buf)
      end
      return buf
    end

    def _transform(tuple, depth, buf)
      indent = '  ' * depth
      keyword = tuple[1]
      if keyword == 'spec'
        _, _, spec = tuple
        #buf << "\n"
        #buf << "#{indent}spec \"#{spec}\" do\n"
        #buf << "#{indent}end\n"
        escaped = spec.gsub(/"/, '\\\"')
        buf << "#{indent}spec \"#{escaped}\"\n"
        #buf << "#{indent}spec \"#{spec.gsub(/"/, '\\\"')}\"\n"  #
      else
        _, _, topic, children = tuple
        buf << "\n"
        buf << "#{indent}topic '#{topic}' do\n"  if keyword == 'def'
        buf << "#{indent}topic #{topic} do\n"    if keyword != 'def'
        buf << "\n" unless keyword == 'def'
        children.each do |child_tuple|
          _transform(child_tuple, depth+1, buf)
        end
        buf << "\n"
        buf << "#{indent}end\n"            if keyword == 'def'
        buf << "#{indent}end # #{topic}\n" if keyword != 'def'
        buf << "\n"
      end
    end
    private :_transform

    def generate(io)
      tree = parse(io)
      return <<END
# -*- coding: utf-8 -*-

require 'oktest'

Oktest.scope do

#{transform(tree)}
end
END
    end

  end


  class MainApp

    def main(args=nil)
      require 'optparse'
      begin
        status = run(args)
        exit(status) if Config.system_exit && status
        return status || 0
      rescue OptionParser::InvalidOption => ex
        command ||= File.basename($0)
        $stderr.write("#{command}: #{ex}\n")
        exit(1) if Config.system_exit
        return 1
      end
    end

    def run(args=nil)
      ## parse command-line options
      args = ARGV.dup if args.nil?
      #opts = Options.new
      #parser = option_parser(opts)
      #filenames = parser.parse(args)
      cmdopt = option_parser()
      opts = cmdopt.parse(args)
      filenames = args
      ## help, version
      if opts.help
        puts help_message()
        return 0
      end
      if opts.version
        puts VERSION
        return 0
      end
      ## fix not to load this file twice.
      $" << __FILE__ unless $".include?(__FILE__)
      ##
      if opts.generate
        ## generate test code from source code
        generate(filenames)
        exit()
      else
        ## load and run
        load_files(filenames)
        Oktest::Config.auto_run = false
        n_errors = Oktest.run(:style=>opts.style)
        AssertionObject.report_not_yet()
        return n_errors
      end
    end

    private

    class Options   #:nodoc:
      attr_accessor :help, :version, :style
    end

    #def option_parser(opts)
    #  require 'optparse'
    #  parser = OptionParser.new
    #  parser.on('-h', '--help')    {|val| opts.help = val }
    #  parser.on('-v', '--version') {|val| opts.version = val }
    #  parser.on('-s STYLE') {|val|
    #    REPORTER_CLASSES.key?(val)  or
    #      raise OptionParser::InvalidOption.new("-s #{val}: unknown style.")
    #    opts.style = val
    #  }
    #  return parser
    #end
    def option_parser()
      require 'section9/cmdopt'
      cmdopt = Section9::Cmdopt.new
      cmdopt.option("-h, --help",        "show help")
      cmdopt.option("-v, --version",     "print version")
      cmdopt.option("-s STYLE  #style",  "report style (verbose/simple/plain, or v/s/p)")\
            .validation {|val| "unknown style." unless REPORTER_CLASSES.key?(val) }
      cmdopt.option("-g, --generate",    "genearte test code from source file")
      return cmdopt
    end

    def help_message(command=nil)
      command ||= File.basename($0)
      buf = "Usage: #{command} [options] [file or directory...]\n"
      buf << "  -h, --help    : show help\n"
      buf << "  -v, --version : print version\n"
      buf << "  -s STYLE      : report style (verbose/simple/plain, or v/s/p)\n"
      return buf
    end

    def load_files(filenames)
      ## file exists?
      filenames.each do |fname|
        File.exist?(fname)  or
          raise OptionParser::InvalidOption.new("#{fname}: not found.")
      end
      ## load files
      filenames.each do |fname|
        File.directory?(fname) ? load_dir(fname) : load(fname)
      end
    end

    def load_dir(dir, pattern=/^(test_.*|.*_test)\.rb$/)
      Dir.glob("#{dir}/*").each do |path|
        if File.directory?(path)
          load_dir(path)
        elsif File.file?(path)
          load(path) if File.basename(path) =~ pattern
        else
          raise ArgumentError.new("#{path}: not a file nor directory.")
        end
      end
    end

    def generate(filenames)
      filenames.each do |fname|
        generator = TestGenerator.new
        File.open(fname) do |f|
          print generator.generate(f)
        end
      end
    end

  end


  def self.main(args=nil)
    return MainApp.new.main(args)
  end


end


Test::Unit::Assertions.module_eval do
  def ok
    location = caller(1).first
    actual = yield
    ass = Oktest::AssertionObject.new(actual, true, location)
    Oktest::AssertionObject::NOT_YET[ass.__id__] = ass
    return ass
  end
end


at_exit do
  if Oktest::FILESCOPES.empty?
    if defined?(Test::Unit::Runner)
      Test::Unit::Runner.class_variable_set(:@@stop_auto_run, false)
    end
  else
    ex = $!
    if (! ex || ex.is_a?(SystemExit)) && Oktest::Config.auto_run
      Oktest.main()
      raise ex if ex
    end
  end
end


if __FILE__ == $0
  ## prevent to load oktest.rb twice
  $LOADED_FEATURES << File.expand_path(__FILE__)
  ## run test scripts
  Oktest.main()
end
