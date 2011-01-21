###
### $Release: $
### $Copyright: copyright(c) 2011 kuwata-lab.com all rights reserved $
### $License: MIT License $
###


##
## Small eRuby implementation.
##
## examples.
##
##   ## load from file and render with context
##   context = {:name=>'Haruhi'}
##   print SmallEruby.load('user.rhtml').render(context)
##
##   ## create a cache file
##   print SmallEruby.load('user.rhtml', true).render(context)
##
##   ## convert string and render
##   input = File.read('user.rhtml')
##   print SmallEruby.new(input).render(context)
##
##   ## use a certain object as a context data
##   class User
##     def initialize(name)
##       @name = name
##     end
##   end
##   user = User.name('Haruhi')
##   print SmallEruby.load('user.rhtml').render(user)
##

class SmallEruby

  attr_accessor :filename, :script

  def initialize(input=nil)
    compile(convert(input)) if input
  end

  def self.load(filename, cache=false)
    if ! cache
      eruby = _load(filename)
    else
      cachename = "#{filename}.cache"
      mtime = File.mtime(filename)
      script = nil
      if File.file?(cachename) && File.mtime(cachename) == mtime
        script = File.open(cachename, 'rb') {|f| f.read }
        eruby = self.new
        eruby.compile(script, filename)
      else
        eruby = _load(filename)
        self._write_cache(cachename, script, mtime)
      end
      updated = File.mtime(filename) != mtime
      if updated
        mtime = File.mtime(filename)
        eruby = _load(filename)
        self._write_cache(cachename, script, mtime)
        updated = File.mtime(filename) != mtime
        updated  or raise "#{filename}: updated too much freqently."
      end
    end
    return eruby
  end

  private

  def self._load(filename)
    input = File.open(filename, 'rb') {|f| f.read }
    eruby = self.new
    script = eruby.convert(input)
    eruby.compile(script, filename)
    return eruby
  end

  def self._write_cache(cachename, script, mtime)
    tmpname = "#{cacheename}.#{rand().to_s[2, 8]}"
    File.open(tmpname, 'wb') {|f| f.write(script) }
    File.utime(mtime, mtime, tmpname)
    File.rename(tmpname, cachename)
  end

  public

  def render(context={})
    context = Context.new(context) if context.is_a?(Hash)
    return context.instance_eval(@_proc)
  end

  def compile(script, filename=nil)
    @script = script
    @filename = filename
    @_proc = eval("proc do #{script} end", nil, filename || '(eruby)')
  end

  def convert(input)
    script = ''
    script << "_buf = ''; "       # preamble
    parse(script, input)
    script << "\n" unless script[-1] == ?\n
    script << "_buf\n"            # postamble
    return script
  end

  private

  def embed_pattern
    return /(^[ \t]*)?<%(#+)?(=)? ?(.*?) ?%>([ \t]*\r?\n)?/m
  end

  def parse(script, input)
    pos = 0
    prev_rspace = buf = nil
    input.scan(embed_pattern) do |lspace, sharp, equal, code, rspace|
      m = Regexp.last_match
      len  = m.begin(0) - pos
      text = input[pos, len]
      pos  = m.end(0)
      text = "#{prev_rspace}#{text}" if prev_rspace
      is_statement = ! equal
      trim_spaces = is_statement && lspace && rspace
      if trim_spaces
        code = "#{lspace}#{code}#{rspace}"
        prev_rspace = nil
      else
        text << lspace if lspace
        prev_rspace = rspace
      end
      code = code.gsub(/^.*(\r?\n|\z)/, '\1') if sharp
      buf = add_text(buf, text)
      if is_statement
        script << close_buf(buf) if buf
        buf = nil
        script << code
        script << "; " unless code[-1] == ?\n
      else
        (buf ||= open_buf()) << '#{' << code << '}' unless code.strip.empty?
      end
    end
    rest = $' || input
    buf = add_text(buf, rest)
    script << close_buf(buf) if buf
  end

  def open_buf()
    return "_buf << %Q`"
  end

  def add_text(buf, text)
    (buf ||= open_buf()) << text.gsub(/[`\#\\]/, '\\\\\1') if text && ! text.empty?
    return buf
  end

  def close_buf(buf)
    #buf.sub!(/\r\n\z/, "\\r\\n\r\n") or buf.sub!(/\n\z/, "\\n\n") or buf << "`; "
    unless buf.sub!(/\r\n\z/, "\\r\\n`\r\n")
      unless buf.sub!(/\n\z/, "\\n`\n")
        buf << "`; "
      end
    end
    return buf
  end


  module Helper

    module_function

    def h(value)
      return value.to_s.gsub(/&/, '&amp;').gsub(/</, '&lt;').gsub(/>/, '&gt;').gsub(/"/, '&quot;')
    end

  end


  class Context
    include Helper

    def initialize(hash)
      hash.each do |k, v|
        instance_variable_set("@#{k}", v)
      end
    end

  end


end
