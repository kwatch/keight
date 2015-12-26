###
### $Release: $
### $Copyright: copyright(c) 2010-2011 kuwata-lab.com all rights reserved $
### $License: Public Domain $
###


module Benchmarker

  VERSION = "$Release: 0.0.0 $".split(/ /)[1]

  def self.new(opts={}, &block)
    #: creates runner object and returns it.
    runner = RUNNER.new(opts)
    if block
      runner._before_all()
      runner._run(&block)
      runner._after_all()
    end
    runner
  end

  def self.bm(width=30, &block)    # for compatibility with benchmark.rb
    return self.new(:width=>30, &block)
  end

  def self.platform()
    #: returns platform information.
    return <<END
benchmarker.rb:   release #{VERSION}
RUBY_VERSION:     #{RUBY_VERSION}
RUBY_PATCHLEVEL:  #{RUBY_PATCHLEVEL}
RUBY_PLATFORM:    #{RUBY_PLATFORM}
END
  end


  class Runner

    def initialize(opts={})
      #: takes :loop, :cycle, and :extra options.
      @loop  = opts[:loop]
      @cycle = opts[:cycle]
      @extra = opts[:extra]
      #:
      @tasks = []
      @report = REPORTER.new(opts)
      @stats  = STATS.new(@report, opts)
      @_section_title = ""
      @_section_started = false
    end

    attr_accessor :tasks, :report, :stats

    def task(label, opts={}, &block)
      #: prints section title if not printed yet.
      #: creates task objet and returns it.
      #: runs task when :skip option is not specified.
      #: skip block and prints message when :skip option is specified.
      #: subtracts times of empty task if exists.
      skip_message = opts[:skip]
      t = _new_task(label, skip_message, &block)
      #: saves created task object unless :skip optin is not specified.
      @tasks << t unless skip_message
      t
    end

    alias report task      # for compatibility with benchmark.rb

    def empty_task(label="(Empty)", &block)
      #:: clear @_empty_task.
      @_empty_task = nil
      #: prints section title if not printed yet.
      #: creates empty task object and returns it.
      t = _new_task(label, &block)
      #: saves empty task object.
      #:: don't add empty task to @tasks.
      @_empty_task = t
      t
    end

    #--
    #def skip_task(label, message="   ** skipped **")
    #  #: prints section title if not printed yet.
    #  t = _new_task(label)
    #  #: prints task label and message instead of times.
    #  @report.write(message + "\n")
    #  #: don't change @tasks.
    #end
    #++

    def _before_all   # :nodoc:
      #: prints Benchmarker.platform().
      print Benchmarker.platform()
    end

    def _after_all    # :nodoc:
      #: prints statistics out benchmarks.
      @stats.all(@tasks)
    end

    def _run   # :nodoc:
      #: when @cycle > 1...
      if @cycle && @cycle > 1
        @all_tasks = []
        #: prints output of cycle into stderr.
        @report._switch_out_to_err do
          #: yields block @cycle times when @extra is not specified.
          #: yields block @cycle + 2*@extra times when @extra is specified.
          i = 0
          cycle = @cycle
          cycle += 2 * @extra if @extra
          cycle.times do
            _reset_section("(##{i+=1})")
            @all_tasks << (@tasks = [])
            #: yields block with self as block paramter.
            yield self
          end
        end
        #: reports average of results.
        @tasks = _calc_averages(@all_tasks, @extra)
        _report_average_section(@tasks)
      #: when @cycle == 0 or not specified...
      else
        #: yields block only once.
        _reset_section("")
        #: yields block with self as block paramter.
        yield self
      end
    end

    private

    def _reset_section(section_title)
      @_section_started = false
      @_section_title = section_title
    end

    def _new_task(label, skip_message=nil, &block)
      #: prints section title if not printed yet.
      _report_section_title_if_not_printed_yet()
      #: creates task objet and returns it.
      t = TASK.new(label, @loop)
      @report.task_label(label)
      #: skip block and prints message when :skip option is specified.
      if skip_message
        @report.write(skip_message + "\n")
      #: runs task when :skip option is not specified.
      elsif block
        t.run(&block)
        #: subtracts times of empty task if exists.
        t.sub(@_empty_task) if @_empty_task
        @report.task_times(t.user, t.sys, t.total, t.real)
      end
      t
    end

    def _report_section_title_if_not_printed_yet
      if ! @_section_started
        @_section_started = true
        @report.section_title(@_section_title)\
               .section_headers("user", "sys", "total", "real")
      end
    end

    def _calc_averages(all_tasks, extra)
      #: calculates average times of tasks.
      tasks_list = _transform_all_tasks(all_tasks)
      if extra
        @report.section_title("Remove Min & Max").section_headers("min", "cycle", "max", "cycle")
        tasks_list = tasks_list.collect {|tasks| _remove_min_max(tasks, extra) }
      end
      avg_tasks = tasks_list.collect {|tasks| Task.average(tasks) }
      avg_tasks
    end

    def _transform_all_tasks(all_tasks)
      tasks_list = []
      all_tasks.each do |tasks|
        tasks.each_with_index do |task, i|
          (tasks_list[i] ||= []) << task
        end
      end
      tasks_list
    end

    def _remove_min_max(tasks, extra)
      #: reports min and max tasks.
      idx = -1
      pairs = tasks.collect {|task| [task, idx+=1] }
      pairs = pairs.sort_by {|task, idx| task.real }   # 1.8 doesn't support sort_by!
      j = -1
      while (j += 1) < extra
        @report.task_label(j == 0 ? pairs[j].first.label : '')
        task, idx = pairs[j]      # min
        @report.task_time(task.real).task_index(idx+1)
        task, idx = pairs[-j-1]   # max
        @report.task_time(task.real).task_index(idx+1)
        @report.text("\n")
      end
      #: removes min and max tasks, and returns remained tasks.
      remained_tasks = pairs[extra...-extra].collect {|task, idx| task }
      remained_tasks
    end

    def _report_average_section(tasks)
      title = _get_average_section_title()
      @report.section_title(title).section_headers("user", "sys", "total", "real")
      tasks.each do |t|
        @report.task_label(t.label).task_times(t.user, t.sys, t.total, t.real)
      end
    end

    def _get_average_section_title()
      #: returns 'Average of N (=x-2*y)' string if label width is enough wide.
      #: returns 'Average of N' string if label width is not enough wide.
      title = "Average of #{@cycle}"
      if @extra
        s = " (=#{@cycle+2*@extra}-2*#{@extra})"
        title << s if "## #{title}#{s}".length <= @report.label_width
      end
      title
    end

  end

  RUNNER = Runner


  class Task

    def initialize(label, loop=1, &block)
      #: takes label and loop.
      @label = label
      @loop  = loop
      #: sets all times to zero.
      @user = @sys = @total = @real = 0.0
    end

    attr_accessor :label, :loop, :user, :sys, :total, :real

    def run
      #: starts GC before running benchmark.
      GC.start
      #: yields block for @loop times.
      ntimes = @loop || 1
      pt1 = Process.times
      t1 = Time.now
      if ntimes > 1
        ntimes.times { yield }
      else
        yield
      end
      pt2 = Process.times
      t2 = Time.now
      #: measures times.
      @user  = pt2.utime - pt1.utime
      @sys   = pt2.stime - pt1.stime
      @total = @user + @sys
      @real  = t2 - t1
      return self
    end

    def add(other)
      #: adds other's times into self.
      @user  += other.user
      @sys   += other.sys
      @total += other.total
      @real  += other.real
      #: returns self.
      return self
    end

    def sub(other)
      #: substracts other's times from self.
      @user  -= other.user
      @sys   -= other.sys
      @total -= other.total
      @real  -= other.real
      #: returns self.
      return self
    end

    def mul(n)
      #: multiplies times with n.
      @user  *= n
      @sys   *= n
      @total *= n
      @real  *= n
      #: returns self.
      return self
    end

    def div(n)
      #: divides times by n.
      @user  /= n
      @sys   /= n
      @total /= n
      @real  /= n
      #: returns self.
      return self
    end

    def self.average(tasks)
      #: returns empty task when argument is empty.
      n = tasks.length
      return self.new(nil) if n == 0
      #: create new task with label.
      task = self.new(tasks.first.label)
      #: returns averaged task.
      tasks.each {|t| task.add(t) }
      task.div(n)
      return task
    end

  end

  TASK = Task


  class Reporter

    def initialize(opts={})
      #: takes :out, :err, :width, and :format options.
      @out = opts[:out] || $stdout
      @err = opts[:err] || $stderr
      self.label_width = opts[:width] || 30
      self.format_time = opts[:format] || "%9.4f"
    end

    attr_accessor :out, :err
    attr_reader :label_width, :format_time

    def _switch_out_to_err()   # :nodoc:
      #: switches @out to @err temporarily.
      begin
        out = @out
        @out = @err
        yield
      ensure
        @out = out
      end
    end

    def label_width=(width)
      #: sets @label_width.
      @label_width = width
      #: sets @format_label, too.
      @format_label = "%-#{width}s"
    end

    def format_time=(format)
      #: sets @format_time.
      @format_time = format
      #: sets @format_header, too.
      m = /%-?(\d+)\.\d+/.match(format)
      @format_header = "%#{$1.to_i}s" if m
    end

    def write(*args)
      #: writes arguments to @out with '<<' operator.
      args.each {|x| @out << x.to_s }
      #: saves the last argument.
      @_prev = args[-1]
      #: returns self.
      return self
    end
    alias text write

    def report_section_title(title)
      #: prints newline at first.
      write "\n"
      #: prints section title with @format_label.
      write @format_label % "## #{title}"
      #: returns self.
      return self
    end
    alias section_title report_section_title

    def report_section_headers(*headers)
      #: prints headers.
      headers.each do |header|
        report_section_header(header)
      end
      #: prints newline at end.
      write "\n"
      #: returns self.
      return self
    end
    alias section_headers report_section_headers

    def report_section_header(header)
      #: prints header with @format_header.
      write " ", @format_header % header
      #: returns self.
      return self
    end
    alias section_header report_section_header

    def report_task_label(label)
      #: prints task label with @format_label.
      write @format_label % label
      #: returns self.
      return self
    end
    alias task_label report_task_label

    def report_task_times(user, sys, total, real)
      #: prints task times with @format_time.
      fmt = @format_time
      write " ", fmt % user, " ", fmt % sys, " ", fmt % total, " ", fmt % real, "\n"
      #: returns self.
      return self
    end
    alias task_times report_task_times

    def report_task_time(time)
      #: prints task time with @format_titme.
      write " ", @format_time % time
      #: returns self.
      return self
    end
    alias task_time report_task_time

    def report_task_index(index)
      #: prints task time with @format_titme.
      write " ", @format_header % "(##{index})"
      #: returns self.
      return self
    end
    alias task_index report_task_index

  end

  REPORTER = Reporter


  class Stats

    def initialize(reporter, opts={})
      #: takes reporter object.
      @report   = reporter
      @key      = opts[:key] || 'real'
      @sort_key = opts[:sort_key] || 'real'
      @loop     = opts[:loop]
      @numerator = opts[:numerator]
    end

    def all(tasks)
      ranking(tasks)
      ratio_matrix(tasks)
    end

    def ranking(tasks)
      tasks = tasks.sort_by {|t| t.__send__(@sort_key) } if @sort_key
      #: prints ranking.
      key = @key
      @report.section_title("Ranking").section_headers(key.to_s)
      #base = tasks.min_by {|t| t.__send__(key) }.__send__(key)  # min_by() is available since 1.8.7
      base = tasks.collect {|t| t.__send__(key) }.min
      tasks.each do |task|
        sec = task.__send__(key).to_f
        val = 100.0 * base / sec
        @report.task_label(task.label).task_time(sec).text(" (%5.1f%%) " % val)
        #: prints barchart if @numerator is not specified.
        if ! @numerator
          bar = '*' * (val / 5.0).round
          @report.text(bar).text("\n")
        #: prints inverse number if @numerator specified.
        else
          @report.text("%12.2f per sec" % (@numerator/ sec)).text("\n")
        end
      end
    end

    def ratio_matrix(tasks)
      tasks = tasks.sort_by {|t| t.__send__(@sort_key) } if @sort_key
      #: prints matrix.
      key = @key
      @report.section_title("Matrix").section_header("real")
      tasks.each_with_index do |t, i|
        @report.text(" %8s" % ("[%02d]" % (i+1)))
      end
      @report.text("\n")
      i = 0
      tasks.each do |base_task|
        i += 1
        base = base_task.__send__(key).to_f
        @report.task_label("[%02d] %s" % [i, base_task.label]).task_time(base)
        tasks.each do |t|
          sec = t.__send__(key).to_f
          val = 100.0 * sec / base
          @report.text(" %7.1f%%" % val)
        end
        @report.text("\n")
      end
    end

  end

  STATS = Stats


end
