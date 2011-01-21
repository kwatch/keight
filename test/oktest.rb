###
### $Release: $
### $Copyright: copyright(c) 2010 kuwata-lab.com all rights reserved $
### $License: MIT License $
###

module Oktest

  DIFF = ENV['DIFF'] || File.file?('/usr/bin/diff')

  def self.DIFF=(command)
    remove_const(:DIFF)
    const_set(:DIFF, command)
  end

  def self.diff(actual, expected)
    ## actual and expected should be different
    return nil if actual == expected
    ## both actual and expected should be String
    return nil unless actual.is_a?(String) && expected.is_a?(String)
    ## either actual or expected should contain "\n"
    return nil unless actual.index("\n") || expected.index("\n")
    ## diff command
    command = Oktest::DIFF
    return nil unless command
    command = 'diff -u' if command == true
    ## diff
    require 'tempfile' unless defined?(Tempfile)
    output = nil
    #Tempfile.open('actual') do |af|    # af.path file is not removed. why?
    #  af.write(actual); af.flush()
    #  Tempfile.open('expected') do |ef|
    #    ef.write(expected); ef.flush()
    #    #output = `#{command} #{ef.path} #{af.path}`
    #    output = IO.popen(cmd="#{command} #{ef.path} #{af.path}") {|io| io.read }
    #  end
    #end
    af = ef = nil
    begin
      af = Tempfile.open('actual')   ; af.write(actual)   ; af.flush
      ef = Tempfile.open('expected') ; ef.write(expected) ; ef.flush
      #output = `#{command} #{ef.path} #{af.path}`
      output = IO.popen("#{command} #{ef.path} #{af.path}") {|io| io.read() }
    ensure
      af.close if ef
      ef.close if ef
    end
    return output.sub(/\A.*?\n.*?\n/, "--- expected\n+++ actual\n")
  end


  class AssertionFailed < Exception
    attr_accessor :diff
  end

  ASSERTION_FAILED = AssertionFailed


  class AssertionObject

    attr_reader :actual, :negative

    def initialize(this, actual, negative=false)
      @this = this
      @actual = actual
      @negative = negative
    end

    def ==(expected)
      begin
        do_assert(@actual == expected, expected, '==', '!=')
      rescue AssertionFailed => ex
        ex.diff = Oktest.diff(@actual, expected) if @actual != expected
        raise ex
      rescue ASSERTION_FAILED => ex
        diff = Oktest.diff(@actual, expected) if @actual != expected
        ex.message << "\n" << diff.chomp() if diff && ! diff.empty?
        raise ex
      end
    end

    if Object.new.respond_to?(:'!=')
      eval <<-'END'
    def !=(expected)
      do_assert(@actual == expected, expected, '!=', '==')
    end
      END
    end

    def >(expected)
      do_assert(@actual > expected, expected, '>', '<=')
    end

    def <(expected)
      do_assert(@actual < expected, expected, '<', '>=')
    end

    def >=(expected)
      do_assert(@actual >= expected, expected, '>=', '<')
    end

    def <=(expected)
      do_assert(@actual <= expected, expected, '<=', '>')
    end

    def ===(expected)
      do_assert(@actual === expected, expected, '===', '!==')
    end

    def =~(expected)
      do_assert(@actual =~ expected, expected, '=~', '!~')
    end

    def in_delta?(expected, delta)
      flag = expected - delta <= @actual && @actual <= expected + delta
      check2(flag) { "(#{(expected - delta).inspect} <= #{@actual.inspect} <= #{(expected + delta).inspect})" }
    end

    def file?
      check2(File.file?(@actual)) { "File.file?(#{@actual.inspect})" }
    end

    def dir?
      check2(File.directory?(@actual)) { "File.directory?(#{@actual.inspect})" }
    end

    def exist?
      check2(File.exist?(@actual)) { "File.exist?(#{@actual.inspect})" }
    end

    def same?(expected)
      check2(@actual.equal?(expected)) { "#{@actual.inspect}.equal?(#{expected.inspect})" }
    end

    def in?(expected)
      check2(expected.include?(@actual)) { "#{expected.inspect}.include?(#{@actual.inspect})" }
    end

    def include?(expected)
      check2(@actual.include?(expected)) { "#{@actual.inspect}.include?(#{expected.inspect})" }
    end

    def is_a?(expected)
      check2(@actual.is_a?(expected)) { "#{@actual.inspect}.is_a?(#{expected})" }
    end
    alias kind_of? is_a?

    def nil?
      check2(@actual.nil?) { "#{@actual.inspect}.nil?" }
    end

    def empty?
      check2(@actual.empty?) { "#{@actual.inspect}.empty?" }
    end

    def raise?(exception_class, message=nil)
      if @negative
        _should_not_raise(exception_class)
        ex = nil
      else
        ex = _should_raise(exception_class, message)
      end
      return ex
    end

    private

    def _should_raise(exception_class, message)
      not_raised = false
      begin
        @actual.call
        not_raised = true
      rescue Exception => ex
        @actual.instance_variable_set('@exception', ex)
        def @actual.exception; @exception; end
        ex.class <= exception_class  or
          raise new_assertion_failed("#{exception_class.name} expected but #{ex.class.name} raised.", 2)
        if message
          op = message.is_a?(Regexp) ? '=~' : '=='
          ex.message.__send__(op, message)  or
            raise new_assertion_failed("#{ex.message.inspect} #{op} #{message.inspect}: failed.", 2)
        end
      end
      raise new_assertion_failed("#{exception_class.name} expected but not raised.", 2) if not_raised
      return ex
    end

    def _should_not_raise(exception_class=Exception)
      begin
        @actual.call
      rescue Exception => ex
        @actual.instance_variable_set('@exception', ex)
        def @actual.exception; @exception; end
        if ex.class <= exception_class
          raise new_assertion_failed("unexpected #{ex.class.name} raised.", 2)
        end
      end
    end

    def do_assert(flag, expected, op, negative_op)
      flag, msg = check(flag, expected, op, negative_op)
      return true if flag
      raise new_assertion_failed(msg)
    end

    def new_assertion_failed(msg, depth=2)
      ex = AssertionFailed.new(msg)
      ex.set_backtrace(caller(depth+1))    # manipulate backtrace
      return ex
    end

    def check(flag, expected, op, negative_op)
      if @negative
        flag = ! flag
        op = negative_op
      end
      msg = flag ? nil : failed_message(expected, op)
      return flag, msg
    end

    def failed_message(expected, op)
      "#{@actual.inspect} #{op} #{expected.inspect}: failed."
    end

    def check2(flag)
      flag = ! flag if @negative
      return true if flag
      expr = yield
      expr = "! #{expr}" if @negative
      raise new_assertion_failed("#{expr}: failed.")
    end

  end


  module Helper

    module_function

    def ok(actual=nil)
      actual = yield if block_given?       # experimental
      return Oktest::AssertionObject.new(self, actual, false)
    end
    alias ok_ ok

    def not_ok(actual=nil)
      actual = yield if block_given?       # experimental
      return Oktest::AssertionObject.new(self, actual, true)
    end
    alias not_ok_ not_ok

    def capture_io(stdin_str=nil)
      require 'stringio' unless defined?(StringIO)
      stdout, stderr = $stdout, $stderr
      $stdout, $stderr = StringIO.new, StringIO.new
      stdin, $stdin = $stdin, StringIO.new(stdin_str) if stdin_str
      begin
        yield
        ret = [$stdout.string, $stderr.string]
      ensure
        $stdout, $stderr = stdout, stderr
        $stdin = stdin if stdin_str
      end
      return ret
    end

    def dummy_file(pairs)
      fnames = []
      begin
        pairs.each do |fname, content|
          fnames << fname
          File.open(fname, 'wb') {|f| f.write(content) }
          yield
        end
      ensure
        File.unlink(*fnames)
      end
    end

    def dummy_dir(*paths)
      require 'fileutils' unless defined?(FileUtils)
      begin
        paths.each {|path| FileUtils.mkdir_p(path) }
        yield
      ensure
        paths.reverse.each {|path| FileUtils.rm_rf(path) }
      end
    end

    ## marker method to represent pre-condition
    def pre_cond; yield; end

    ## marker method to represent post-condition
    def post_cond; yield; end

    ## marker method to describe target of specification
    def target(desc); yield; end

    ## marker method to describe specification
    #def spec(desc); yield if block_given?; end
    def spec(desc)
      reporter = @_oktest_runner && @_oktest_runner.reporter
      status = nil
      begin
        reporter.enter_spec(self, desc) if reporter
        if block_given?
          yield
          status = :ok
        else
          status = :empty
        end
      rescue AssertionFailed => ex
        status = :fail
        raise ex
      rescue => ex
        status = :error
        raise ex
      ensure
        reporter.exit_spec(self, status) if reporter
      end
    end

    ##
    ## intercept method call of object
    ##
    ## stub example.
    ##    class Hello
    ##      def hello(name); return "Hello #{name}!"; end
    ##    end
    ##    obj = Hello.new
    ##    intr = intercept(obj, :hello)
    ##    intr.called  #=> false
    ##    obj.hello('World')   #=> "Hello World!"
    ##    intr.called  #=> true
    ##    intr.args    #=> ["World"]
    ##    intr.return  #=> "Hello World!"
    ##
    ## mock example.
    ##    class Hello
    ##      def hello(name); return "Hello #{name}!"; end
    ##    end
    ##    obj = Hello.new
    ##    intr = intercept(obj, :hello) do |name|
    ##      "Bonjor #{name}!"   # or `obj.__intercepted_hello(name)'
    ##    end
    ##    intr.called  #=> false
    ##    obj.hello('World')   #=> "Bonjor World!"
    ##    intr.called  #=> true
    ##    intr.args    #=> ["World"]
    ##    intr.return  #=> "Bonjor World!"
    ##
    def intercept(object, method, &block)
      return Oktest::Util::Interceptor.new(object, method, &block)
    end

  end


  module ClassMethodHelper

    def method_added(name)
      dict = (@_test_method_names_dict ||= {})
      name = name.to_s
      if name =~ /\Atest_?/
        ## if test method name is duplicated, raise error
        dict[name].nil?  or
          raise NameError.new("#{self.name}##{name}(): already defined (please change test method name).")
        dict[name] = dict.size()
        ## if ENV['TEST'] is set, remove unmatched method
        if ENV['TEST']
          remove_method(name) unless name.sub(/\Atest_?/, '').index(ENV['TEST'])
        end
      end
    end

    def test(desc, &block)
      @_test_count ||= 0
      @_test_count += 1
      method_name = "test_%03d_%s" % [@_test_count, desc.to_s.gsub(/[^\w]/, '_')]
      define_method(method_name, block)
    end

  end


  module TestCase
    include Helper

    @_subclasses = []

    def self._subclasses    # :nodoc:
      return @_subclasses
    end

    def self.included(klass)
      @_subclasses << klass if klass.is_a?(Class)
      klass.class_eval do
        extend Oktest::ClassMethodHelper
      end
    end

  end


  class Reporter

    def before_all(klass)
    end

    def after_all(klass)
    end

    def before(obj)
    end

    def after(obj)
    end

    def print_ok(obj)
    end

    def print_failed(obj, ex)
    end

    def print_error(obj, ex)
    end

    def enter_spec(obj, desc)
    end

    def exit_spec(obj, status)
    end

  end


  class BaseReporter < Reporter

    def initialize(out=nil)
      @out = out || $stdout
      @_flush = @out.respond_to?(:flush)
    end

    def before_all(klass)
      @count_test = 0
      @count_spec = 0
    end

    def before(obj)
      @count_test += 1
      @spec_status = nil
    end

    def after(obj)
    end

    def enter_spec(obj, desc)
      @count_spec += 1
    end

    def exit_spec(obj, status)
      @spec_status = status
      case status
      when :ok      ; write('.')
      when :empty   ; write('_')
      when :fail    ; write('f')
      when :error   ; write('E')
      else
        raise "** internal error: status=#{status.inspect}"
      end
    end

    private

    def _test_ident(obj)
      return obj.instance_variable_get('@_test_method')
    end

    def write(str)
      @out << str
      @out.flush if @_flush
    end

    def print_backtrace(ex, out=@out)
      ex.backtrace.each do |str|
        out << "    #{str}\n"
        if str =~ /\A(.*):(\d+):in `(.*?)'/
          filepath, linenum, method = $1, $2.to_i, $3
          #break if method =~ /\Atest_?/
          line = get_line(filepath, linenum)
          out << "      #{line.strip}\n" if line
          break if method =~ /\Atest_?/
        end
      end
    end

    def get_line(filepath, linenum)
      return nil unless File.file?(filepath)
      linenum = linenum.to_i
      line = File.open(filepath) do |f|
        i = 0
        f.find { (i += 1) == linenum }
      end
      return line
    end

  end


  class SimpleReporter < BaseReporter

    def before_all(klass)
      super
      write("### %s: " % klass.name)
      @buf = ""
    end

    def after_all(klass)
      super
      write(" (#{@count_test} tests, #{@count_spec} specs)\n")
      @out << @buf.to_s
      @buf = nil
    end

    def print_ok(obj)
      write(".") unless @spec_status
    end

    def print_failed(obj, ex)
      write("f") unless @spec_status
      @buf << "Failed: #{_test_ident(obj)}()\n"
      @buf << "    #{ex.message}\n"
      print_backtrace(ex, @buf)
      #assert ex.is_a?(AssertionFailed)
      @buf << ex.diff if ex.diff
    end

    def print_error(obj, ex)
      write("E") unless @spec_status
      @buf << "ERROR: #{_test_ident(obj)}()\n"
      @buf << "    #{ex.class.name}: #{ex.message}\n"
      print_backtrace(ex, @buf)
    end

  end


  class VerboseReporter < BaseReporter

    def before_all(klass)
      super
      write("### %s\n" % klass.name)
    end

    def after_all(klass)
      super
      write(" (#{@count_test} tests, #{@count_spec} specs)\n")
    end

    def before(obj)
      super
      write("- #{_test_ident(obj)}: ")
    end

    def print_ok(obj)
      write(" ok\n")
    end

    def print_failed(obj, ex)
      write(" FAILED\n")
      write("    #{ex.message}\n")
      print_backtrace(ex, @out)
      #assert ex.is_a?(AssertionFailed)
      write(ex.diff) if ex.diff
    end

    def print_error(obj, ex)
      write(" ERROR\n")
      write("  #{ex.class.name}: #{ex.message}\n")
      print_backtrace(ex, @out)
    end

  end


  REPORTER = SimpleReporter
  #REPORTER = VerboseReporter

  def self.REPORTER=(reporter_class)
    remove_const(:REPORTER)
    const_set(:REPORTER, reporter_class)
  end


  class Runner

    def initialize(reporter=nil)
      @reporter = reporter || REPORTER.new
    end
    attr_accessor :reporter

    def test_method_names_from(klass)
      test_method_names = klass.instance_methods(true).collect {|sym| sym.to_s }.grep(/\Atest/).sort()
      dict = klass.instance_variable_get('@_test_method_names_dict')
      if dict
        dict = dict.dup()   # key: test method name (String), value: index (Integer)
        i = 0
        test_method_names.select {|name| ! dict.key?(name) }.reverse.each {|name| dict[name] = (i -= 1) }
        test_method_names = dict.sort_by {|k, v| v }.collect {|k, v| k }
      end
      return test_method_names
    end

    def warning(msg)
      warn "WARNING: #{msg}"
    end

    def run(klass)
      reporter = @reporter
      ## gather test methods
      test_method_names = test_method_names_from(klass)
      ## filer by $TEST environment variable
      pattern = ENV['TEST']
      test_method_names.delete_if {|x| x.index(pattern).nil? } if pattern
      ## sort by linenumber
      # nothing
      ## invoke before_all()
      reporter.before_all(klass)
      if klass.respond_to?(:before_all)
        klass.before_all()
      elsif klass.method_defined?(:before_all)
        warning "#{klass.name}#before_all() should be class method (but defined as instance method)"
      end
      ## invoke test methods
      count = 0
      flag_before   = klass.method_defined?(:before)
      flag_setup    = klass.method_defined?(:setup)
      flag_after    = klass.method_defined?(:after)
      flag_teardown = klass.method_defined?(:teardown)
      test_method_names.each do |method_name|
        ## create instance object for each test
        begin
          obj = klass.new
        rescue ArgumentError
          obj = klass.new(method_name)
        end
        obj.instance_variable_set('@_name', method_name.sub(/\Atest_?/, ''))
        obj.instance_variable_set('@_test_method', method_name)
        obj.instance_variable_set('@_oktest_runner', self)
        ## invoke before() or setup()
        reporter.before(obj)
        flag_before ? obj.before() : flag_setup ? obj.setup() : nil
        ## invoke test method
        begin
          obj.__send__(method_name)
          reporter.print_ok(obj)
        rescue Oktest::AssertionFailed => ex
          count += 1
          reporter.print_failed(obj, ex)
        rescue Exception => ex
          count += 1
          reporter.print_error(obj, ex)
        ensure
          ## invoke after() or teardown()
          flag_after ? obj.after() : flag_teardown ? obj.teardown() : nil
          reporter.after(obj)
        end
      end
      ## invoke after_all()
      if klass.respond_to?(:after_all)
        klass.after_all()
      elsif klass.method_defined?(:after_all)
        warning "#{klass.name}#after_all() should be class method (but defined as instance method)"
      end
      reporter.after_all(klass)
      ##
      return count
    end
  end


  def self.run(*classes)
    opts = classes.last.is_a?(Hash) ? classes.pop() : {}
    reporter_class = opts[:verbose] ? VerboseReporter : REPORTER
    reporter = reporter_class.new(opts[:out])
    runner = Runner.new(reporter)
    classes.each {|cls| runner.run(cls) }
    self.run_at_exit = false
  end

  def self.run_all(opts={})
    classes = Oktest::TestCase._subclasses()
    args = classes + [opts]
    self.run(*args)
  end

  @_run_at_exit = true

  def self.run_at_exit?
    return @_run_at_exit
  end

  def self.run_at_exit=(flag)
    @_run_at_exit = flag
  end


  module Util


    class Interceptor

      def initialize(object, method, &block)
        @object, @method, @block = object, method, block
        @called = false
        intercept()
      end

      attr_accessor :object, :method, :block, :called, :args, :return

      private

      def intercept
        intr = self
        (class << @object; self; end).class_eval do
          method = intr.method
          alias_name = "__intercepted_#{method}"
          alias_method alias_name, method
          define_method(method) do |*args|
            intr.called = true
            intr.args   = args
            intr.return = intr.block ? intr.block.call(*args) \
                                     : __send__(alias_name, *args)
            intr.return
          end
        end
        return self
      end

    end


  end #Util


end


at_exit do
  ex = $!
  if (! ex || ex.is_a?(SystemExit)) && Oktest.run_at_exit? # && ! defined?(Test::Unit)
    Oktest.run_all()
    raise ex if ex
  end
end
